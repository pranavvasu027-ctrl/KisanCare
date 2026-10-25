"""
Strict Agricultural Plant / Leaf Image Validation Gate.

Validates uploaded images BEFORE passing them to deep learning disease classifiers.
Enforces image quality checks (blurriness, darkness, blankness, resolution) and
semantic presence of plant foliage/leaves via zero-shot vision classification.

Rejects:
- Laptops / computers / phones
- Persons / faces / selfies
- Buildings / architecture
- Vehicles / automobiles
- Animals / pets
- Cooked food / kitchen items
- Digital UI screenshots / documents / logos
- Furniture / household objects
- Blank, extremely dark, or severely blurry images
"""

import io
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

# Configurable confidence thresholds (default: 0.70)
DEFAULT_PLANT_CONFIDENCE_THRESHOLD = float(os.getenv("PLANT_VALIDATION_THRESHOLD", "0.70"))
DEFAULT_LEAF_CONFIDENCE_THRESHOLD = float(os.getenv("LEAF_VALIDATION_THRESHOLD", "0.70"))

# Semantic validation text prompts
LEAF_PROMPTS = [
    "a photo of a plant leaf",
    "a close-up photo of an agricultural crop leaf",
    "a photo of a healthy or diseased plant leaf",
    "a photo of crop foliage showing leaf symptoms",
    "a photo of a green or diseased leaf on a plant",
]

PLANT_NON_LEAF_PROMPTS = [
    "a photo of bare plant stems, tree bark, or branches without leaves",
    "a photo of bare agricultural field soil, dirt, or crop roots",
]

NON_PLANT_PROMPTS = [
    ("a photo of a laptop, computer screen, or keyboard", "UNRELATED_IMAGE", "Laptop or computer screen detected"),
    ("a photo of a mobile smartphone or electronic gadget", "UNRELATED_IMAGE", "Electronic device detected"),
    ("a photo of a person, human face, portrait, or selfie", "NO_PLANT_DETECTED", "Person or face detected"),
    ("a photo of a building, house, room interior, or architecture", "NO_PLANT_DETECTED", "Building or architectural structure detected"),
    ("a photo of a car, truck, motorcycle, or vehicle", "NO_PLANT_DETECTED", "Vehicle detected"),
    ("a photo of an animal, dog, cat, bird, or wildlife", "NO_PLANT_DETECTED", "Animal detected"),
    ("a photo of food, cooked meal, or kitchen dish", "NO_PLANT_DETECTED", "Food or kitchen item detected"),
    ("a computer screenshot, UI graphic, software window, document, text, or logo", "UNRELATED_IMAGE", "UI screenshot, graphic, or document detected"),
    ("a photo of furniture, chair, desk, or household object", "UNRELATED_IMAGE", "Household object or furniture detected"),
    ("a blank, solid color, black, or empty background", "LOW_IMAGE_QUALITY", "Blank or non-informative image detected"),
]


class PlantLeafValidationResult:
    """Structured result of the plant/leaf validation gate."""

    def __init__(
        self,
        is_valid_plant_image: bool,
        plant_confidence: float,
        leaf_confidence: float,
        status: str,
        reason: Optional[str] = None,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.is_valid_plant_image = is_valid_plant_image
        self.plant_confidence = round(float(plant_confidence), 4)
        self.leaf_confidence = round(float(leaf_confidence), 4)
        self.status = status  # "VALID" or "INVALID_IMAGE"
        self.reason = reason or ("VALID" if is_valid_plant_image else "NO_PLANT_DETECTED")
        self.message = message or (
            "Valid plant leaf image."
            if is_valid_plant_image
            else "Invalid photo. Please upload a clear photo of a plant leaf."
        )
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary matching backend API contract."""
        data = {
            "success": self.is_valid_plant_image,
            "status": self.status,
            "is_valid_plant_image": self.is_valid_plant_image,
            "plant_confidence": self.plant_confidence,
            "leaf_confidence": self.leaf_confidence,
            "message": self.message,
        }
        if not self.is_valid_plant_image:
            data["reason"] = self.reason
        return data


class PlantLeafValidator:
    """
    Gatekeeper validator that intercepts images before the disease classification model.
    Applies multi-stage validation:
      1. Physical image quality checks (resolution, darkness, overexposure, blankness, blurriness)
      2. Zero-shot neural classification (plant vs non-plant, leaf vs non-leaf)
      3. Fallback color-space vegetation indices (if neural model unavailable)
    """

    def __init__(
        self,
        plant_threshold: float = DEFAULT_PLANT_CONFIDENCE_THRESHOLD,
        leaf_threshold: float = DEFAULT_LEAF_CONFIDENCE_THRESHOLD,
        lazy_load: bool = False,
    ):
        self.plant_threshold = plant_threshold
        self.leaf_threshold = leaf_threshold
        self._clip_model = None
        self._clip_processor = None
        self._text_features = None
        self._prompt_metadata: List[Tuple[str, str, str]] = []
        self._is_initialized = False

        if not lazy_load:
            self._initialize_clip()

    def _initialize_clip(self):
        """Loads pretrained CLIP ViT-B/32 model and precomputes text embeddings."""
        if self._is_initialized:
            return

        try:
            import torch
            from transformers import CLIPModel, CLIPProcessor

            model_id = "openai/clip-vit-base-patch32"
            logger.info("Initializing PlantLeafValidator CLIP zero-shot gate (%s)...", model_id)
            self._clip_model = CLIPModel.from_pretrained(model_id, local_files_only=True)
            self._clip_processor = CLIPProcessor.from_pretrained(model_id, local_files_only=True)
            self._clip_model.eval()

            # Prepare text prompts
            all_text: List[str] = []
            self._prompt_metadata = []

            for p in LEAF_PROMPTS:
                all_text.append(p)
                self._prompt_metadata.append(("leaf", "VALID", "Leaf"))

            for p in PLANT_NON_LEAF_PROMPTS:
                all_text.append(p)
                self._prompt_metadata.append(("plant_non_leaf", "NO_LEAF_DETECTED", "Plant Stem/Soil"))

            for prompt_str, reason_code, category_label in NON_PLANT_PROMPTS:
                all_text.append(prompt_str)
                self._prompt_metadata.append(("non_plant", reason_code, category_label))

            # Precompute text embeddings once
            with torch.no_grad():
                text_inputs = self._clip_processor(text=all_text, return_tensors="pt", padding=True)
                outputs = self._clip_model.text_model(**text_inputs)
                pooled = outputs.pooler_output
                text_embeds = self._clip_model.text_projection(pooled)
                self._text_features = text_embeds / text_embeds.norm(p=2, dim=-1, keepdim=True)

            self._is_initialized = True
            logger.info("✓ PlantLeafValidator CLIP gate ready with %d prompts.", len(all_text))

        except Exception as exc:
            logger.warning("Could not initialize CLIP for PlantLeafValidator: %s. Using heuristic gate.", exc)
            self._clip_model = None
            self._is_initialized = False

    def validate_image_quality(self, img: Image.Image) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validates basic image quality:
        - Resolution >= 128x128
        - Mean brightness (not pitch dark)
        - Overexposure (not pure washed out white)
        - Blankness / low variance (not solid flat color)
        - Blurriness (Laplacian variance)
        """
        img_rgb = img.convert("RGB")
        w, h = img_rgb.size

        # 1. Resolution check
        if w < 128 or h < 128:
            return (
                False,
                "LOW_IMAGE_QUALITY",
                f"Image resolution ({w}x{h}) is too low. Please upload a photo with at least 128x128 pixels.",
            )

        arr = np.array(img_rgb)
        mean_val = float(np.mean(arr))
        std_val = float(np.std(arr))

        # 2. Extreme darkness
        if mean_val < 20.0:
            return (
                False,
                "IMAGE_TOO_DARK",
                "Image is too dark. Please take a photo in clear, natural daylight.",
            )

        # 3. Severe overexposure or blank white
        if mean_val > 245.0 and std_val < 15.0:
            return (
                False,
                "LOW_IMAGE_QUALITY",
                "Image is essentially blank or severely overexposed. Please upload a clear photo of a plant leaf.",
            )

        # 4. Low visual information / flat color
        if std_val < 10.0:
            return (
                False,
                "LOW_IMAGE_QUALITY",
                "Image lacks meaningful visual content (uniform or flat background). Please upload a clear photo of a plant leaf.",
            )

        # 5. Extreme blurriness check (Laplacian variance)
        gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
        laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        if laplacian_var < 25.0:
            return (
                False,
                "IMAGE_TOO_BLURRY",
                "Image is too blurry for reliable disease diagnosis. Please hold the camera steady and focus on the plant leaf.",
            )

        return (True, None, None)

    def validate(self, img: Union[Image.Image, str, Path, bytes, bytearray]) -> PlantLeafValidationResult:
        """
        Validates whether the provided image is a genuine plant/leaf photo.
        Returns PlantLeafValidationResult.
        """
        # If path or bytes provided, load into PIL Image
        if isinstance(img, (str, Path)):
            img = Image.open(str(img))
        elif isinstance(img, (bytes, bytearray)):
            img = Image.open(io.BytesIO(img))

        # Ensure image is in RGB
        img_rgb = img.convert("RGB")

        # Stage 1: Quality gate
        is_quality_ok, quality_reason, quality_msg = self.validate_image_quality(img_rgb)
        if not is_quality_ok:
            return PlantLeafValidationResult(
                is_valid_plant_image=False,
                plant_confidence=0.05,
                leaf_confidence=0.02,
                status="INVALID_IMAGE",
                reason=quality_reason,
                message=quality_msg,
            )

        # Stage 2: Neural Zero-Shot CLIP Gate
        if not self._is_initialized:
            self._initialize_clip()

        if self._is_initialized and self._clip_model is not None and self._text_features is not None:
            return self._validate_with_clip(img_rgb)

        # Fallback: Color-space heuristic validator if CLIP unavailable
        return self._validate_with_color_heuristics(img_rgb)

    def _validate_with_clip(self, img_rgb: Image.Image) -> PlantLeafValidationResult:
        """Runs fast zero-shot CLIP classification against precomputed text features."""
        import torch

        try:
            image_inputs = self._clip_processor(images=img_rgb, return_tensors="pt")
            with torch.no_grad():
                vision_outputs = self._clip_model.vision_model(**image_inputs)
                pooled = vision_outputs.pooler_output
                image_embeds = self._clip_model.visual_projection(pooled)
                image_features = image_embeds / image_embeds.norm(p=2, dim=-1, keepdim=True)

                logit_scale = self._clip_model.logit_scale.exp()
                logits = (logit_scale * (image_features @ self._text_features.T)).squeeze(0)
                probs = logits.softmax(dim=-1).cpu().numpy().tolist()

            # Aggregate probabilities by category
            leaf_prob = 0.0
            plant_non_leaf_prob = 0.0
            non_plant_prob = 0.0
            top_non_plant_prob = 0.0
            top_non_plant_reason = "NO_PLANT_DETECTED"
            top_non_plant_desc = "Non-plant object"

            for i, (cat_type, reason_code, cat_label) in enumerate(self._prompt_metadata):
                p = probs[i]
                if cat_type == "leaf":
                    leaf_prob += p
                elif cat_type == "plant_non_leaf":
                    plant_non_leaf_prob += p
                else:
                    non_plant_prob += p
                    if p > top_non_plant_prob:
                        top_non_plant_prob = p
                        top_non_plant_reason = reason_code
                        top_non_plant_desc = cat_label

            plant_confidence = leaf_prob + plant_non_leaf_prob
            leaf_confidence = leaf_prob

            # Check threshold condition
            is_valid = (
                plant_confidence >= self.plant_threshold
                and leaf_confidence >= self.leaf_threshold
            )

            if is_valid:
                return PlantLeafValidationResult(
                    is_valid_plant_image=True,
                    plant_confidence=plant_confidence,
                    leaf_confidence=leaf_confidence,
                    status="VALID",
                    reason="VALID",
                    message="Plant leaf successfully validated.",
                    details={
                        "leaf_score": leaf_prob,
                        "plant_score": plant_confidence,
                        "threshold": self.plant_threshold,
                    },
                )

            # Failure branch
            if plant_confidence < self.plant_threshold:
                reason = top_non_plant_reason
                message = f"Invalid photo ({top_non_plant_desc}). Please upload a clear photo of an agricultural plant leaf."
            else:
                reason = "NO_LEAF_DETECTED"
                message = "No plant leaf detected. Please upload a clear photo focusing directly on the affected leaf."

            return PlantLeafValidationResult(
                is_valid_plant_image=False,
                plant_confidence=plant_confidence,
                leaf_confidence=leaf_confidence,
                status="INVALID_IMAGE",
                reason=reason,
                message=message,
                details={
                    "leaf_score": leaf_prob,
                    "plant_score": plant_confidence,
                    "top_non_plant": top_non_plant_desc,
                    "threshold": self.plant_threshold,
                },
            )

        except Exception as exc:
            logger.error("Error in CLIP validation inference: %s. Falling back to color heuristics.", exc)
            return self._validate_with_color_heuristics(img_rgb)

    def _validate_with_color_heuristics(self, img_rgb: Image.Image) -> PlantLeafValidationResult:
        """
        Color-space fallback validator when neural model is unavailable:
        Uses HSV green/yellow/brown foliar hue coverage and Excess Green Index (ExG).
        """
        arr = np.array(img_rgb)
        hsv = cv2.cvtColor(arr, cv2.COLOR_RGB2HSV)

        # Foliar hue range in OpenCV HSV (H: 0-180):
        # Green / yellow / olive: H in [20, 85], S >= 35, V >= 35
        # Brown / necrosis: H in [8, 25], S in [35, 200], V in [30, 180]
        mask_green = cv2.inRange(hsv, np.array([20, 35, 35]), np.array([85, 255, 255]))
        mask_brown = cv2.inRange(hsv, np.array([8, 35, 30]), np.array([25, 200, 180]))
        foliar_mask = cv2.bitwise_or(mask_green, mask_brown)

        foliar_ratio = float(np.count_nonzero(foliar_mask)) / float(arr.shape[0] * arr.shape[1])

        # ExG Index: 2*G - R - B
        r = arr[:, :, 0].astype(np.float32)
        g = arr[:, :, 1].astype(np.float32)
        b = arr[:, :, 2].astype(np.float32)
        exg = 2 * g - r - b
        mean_exg = float(np.mean(exg))

        is_valid = foliar_ratio >= 0.20 or mean_exg > 5.0
        conf = min(0.95, max(0.10, foliar_ratio * 1.5))

        if is_valid:
            return PlantLeafValidationResult(
                is_valid_plant_image=True,
                plant_confidence=conf,
                leaf_confidence=conf * 0.95,
                status="VALID",
                reason="VALID",
                message="Plant leaf validated via foliar chromatic analysis.",
            )
        else:
            return PlantLeafValidationResult(
                is_valid_plant_image=False,
                plant_confidence=conf,
                leaf_confidence=conf * 0.8,
                status="INVALID_IMAGE",
                reason="NO_PLANT_DETECTED",
                message="Invalid photo. No agricultural plant foliage detected in image.",
            )


# Global singleton validator instance
_validator_instance: Optional[PlantLeafValidator] = None


def get_plant_validator() -> PlantLeafValidator:
    """Returns singleton validator instance."""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = PlantLeafValidator()
    return _validator_instance
