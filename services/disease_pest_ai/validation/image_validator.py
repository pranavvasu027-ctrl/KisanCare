"""
Strict Agricultural Plant Leaf Image Validator.

Implements a robust multi-stage validation gate BEFORE the disease classifier:
  1. Quality & Format checks (resolution, blank image, underexposed/dark, blur)
  2. Botanical pigmentation & foliar tissue analysis (chlorophyll green, chlorosis, necrosis)
  3. UI / Graphic / Document / Screenshot detection
  4. Non-plant object detection (laptop, phone, person, vehicle, animal, furniture, etc.)
  5. Specialized neural leaf detection (YOLOv8 46-crop agricultural foliar detector)
  6. Calibrated confidence fusion and threshold gating.

Ensures non-plant images (laptop, person, car, building, screenshot, document, blank)
NEVER reach the disease classifier and never produce fabricated disease predictions.
"""

from __future__ import annotations

import io
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import cv2
import numpy as np
import torch
from PIL import Image

logger = logging.getLogger("kisancare.image_validator")

# Configurable defaults via environment variables
DEFAULT_PLANT_THRESHOLD = float(os.getenv("VALIDATION_PLANT_THRESHOLD", "0.75"))
DEFAULT_LEAF_THRESHOLD = float(os.getenv("VALIDATION_LEAF_THRESHOLD", "0.75"))
DEFAULT_BLUR_THRESHOLD = float(os.getenv("VALIDATION_BLUR_THRESHOLD", "20.0"))
DEFAULT_MIN_DIMENSION = int(os.getenv("VALIDATION_MIN_DIMENSION", "128"))

# Common non-plant categories for ImageNet classification
NON_PLANT_IMAGENET_KEYWORDS = (
    "laptop", "notebook", "computer", "keyboard", "mouse", "screen", "monitor", "television",
    "cellular", "phone", "telephone", "ipod", "car", "vehicle", "truck", "bus", "convertible",
    "aircraft", "airplane", "dog", "cat", "bird", "horse", "cow", "sheep", "elephant", "bear",
    "suit", "jersey", "coat", "apparel", "building", "church", "palace", "house", "library",
    "desk", "chair", "table", "refrigerator", "microwave", "oven", "toilet", "packet", "envelope",
    "web site", "comic book", "book jacket", "menu", "crossword", "street sign", "banner", "poster"
)

# Non-plant COCO categories
NON_PLANT_COCO_CLASSES = {
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat",
    "traffic light", "fire hydrant", "stop sign", "bench", "bird", "cat", "dog", "horse",
    "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella", "handbag",
    "tie", "suitcase", "bottle", "cup", "fork", "knife", "spoon", "bowl", "chair", "couch",
    "bed", "dining table", "toilet", "tv", "laptop", "mouse", "remote", "keyboard", "cell phone",
    "microwave", "oven", "toaster", "sink", "refrigerator", "book", "clock", "vase"
}


@dataclass
class ValidationResult:
    """Structured response from the plant/leaf image validator."""
    is_valid_plant_image: bool
    plant_confidence: float
    leaf_confidence: float
    status: str  # "VALID" or "INVALID_IMAGE"
    reason: Optional[str]  # e.g. "NO_PLANT_DETECTED", "NO_LEAF_DETECTED", "IMAGE_TOO_BLURRY", "IMAGE_TOO_DARK", "LOW_IMAGE_QUALITY", "UNRELATED_IMAGE"
    message: str
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.is_valid_plant_image,
            "status": self.status,
            "is_valid_plant_image": self.is_valid_plant_image,
            "plant_confidence": self.plant_confidence,
            "leaf_confidence": self.leaf_confidence,
            "reason": self.reason,
            "message": self.message,
            "details": self.details,
        }


class PlantLeafImageValidator:
    """
    Multi-stage gatekeeper ensuring only genuine, sufficiently clear
    agricultural plant leaf imagery reaches the disease classification models.
    """

    def __init__(
        self,
        plant_threshold: float = DEFAULT_PLANT_THRESHOLD,
        leaf_threshold: float = DEFAULT_LEAF_THRESHOLD,
        blur_threshold: float = DEFAULT_BLUR_THRESHOLD,
        min_dimension: int = DEFAULT_MIN_DIMENSION,
        device: Optional[str] = None,
    ):
        self.plant_threshold = plant_threshold
        self.leaf_threshold = leaf_threshold
        self.blur_threshold = blur_threshold
        self.min_dimension = min_dimension
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        self._coco_yolo = None
        self._leaf_yolo = None
        self._mobilenet = None
        self._mobilenet_transforms = None
        self._mobilenet_categories = None
        self._models_loaded = False

    def _ensure_models_loaded(self) -> None:
        """Loads lightweight validator models if not already loaded."""
        if self._models_loaded:
            return

        try:
            from ultralytics import YOLO

            # 1. COCO object detector (for detecting people, laptops, cars, animals)
            coco_candidates = [
                Path(__file__).resolve().parent.parent.parent / "yolov8n.pt",
                Path("yolov8n.pt"),
                Path.home() / ".cache" / "torch" / "hub" / "yolov8n.pt",
            ]
            coco_path = "yolov8n.pt"
            for c in coco_candidates:
                if c.exists():
                    coco_path = str(c)
                    break
            self._coco_yolo = YOLO(coco_path)
            logger.info("Loaded COCO object detector for non-plant rejection.")
        except Exception as e:
            logger.warning(f"Failed to load COCO YOLO detector: {e}")

        try:
            from huggingface_hub import hf_hub_download
            from ultralytics import YOLO

            # 2. Specialized 46-class Agricultural Crop Leaf Detector
            leaf_ckpt = hf_hub_download("foduucom/plant-leaf-detection-and-classification", "best.pt")
            self._leaf_yolo = YOLO(leaf_ckpt)
            logger.info("Loaded specialized YOLO leaf detector.")
        except Exception as e:
            logger.warning(f"Failed to load specialized leaf YOLO detector: {e}")

        try:
            import torchvision.models as tv_models
            from torchvision.models import MobileNet_V3_Small_Weights

            weights = MobileNet_V3_Small_Weights.DEFAULT
            mb = tv_models.mobilenet_v3_small(weights=weights).to(self.device).eval()
            self._mobilenet = mb
            self._mobilenet_transforms = weights.transforms()
            self._mobilenet_categories = weights.meta["categories"]
            logger.info("Loaded MobileNetV3 semantic background validator.")
        except Exception as e:
            logger.warning(f"Failed to load MobileNetV3: {e}")

        self._models_loaded = True

    def _load_pil(self, image: Union[Image.Image, np.ndarray, bytes, str, Path]) -> Image.Image:
        """Converts diverse image input formats into an RGB PIL Image."""
        if isinstance(image, Image.Image):
            return image.convert("RGB")
        if isinstance(image, bytes):
            return Image.open(io.BytesIO(image)).convert("RGB")
        if isinstance(image, (str, Path)):
            return Image.open(image).convert("RGB")
        if isinstance(image, np.ndarray):
            if len(image.shape) == 2:
                return Image.fromarray(image).convert("RGB")
            if image.shape[2] == 4:
                return Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGRA2RGB))
            return Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        raise ValueError(f"Unsupported image type: {type(image)}")

    def validate(
        self,
        image: Union[Image.Image, np.ndarray, bytes, str, Path],
        plant_threshold: Optional[float] = None,
        leaf_threshold: Optional[float] = None,
    ) -> ValidationResult:
        """
        Validates whether the provided image is a recognizable plant leaf suitable for disease classification.
        """
        p_thresh = plant_threshold if plant_threshold is not None else self.plant_threshold
        l_thresh = leaf_threshold if leaf_threshold is not None else self.leaf_threshold

        try:
            pil_img = self._load_pil(image)
        except Exception as e:
            return ValidationResult(
                is_valid_plant_image=False,
                plant_confidence=0.0,
                leaf_confidence=0.0,
                status="INVALID_IMAGE",
                reason="LOW_IMAGE_QUALITY",
                message=f"Invalid image format: {e}",
            )

        w, h = pil_img.size

        # Stage 1: Resolution Check
        if w < self.min_dimension or h < self.min_dimension:
            return ValidationResult(
                is_valid_plant_image=False,
                plant_confidence=0.0,
                leaf_confidence=0.0,
                status="INVALID_IMAGE",
                reason="LOW_IMAGE_QUALITY",
                message=f"Image resolution ({w}x{h}) is too small. Minimum required is {self.min_dimension}x{self.min_dimension} pixels.",
                details={"width": w, "height": h},
            )

        img_np = np.array(pil_img)
        gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        mean_val = float(np.mean(gray))
        std_val = float(np.std(gray))

        # Stage 2: Illumination & Solid Blank Image Checks
        if mean_val < 25.0:
            return ValidationResult(
                is_valid_plant_image=False,
                plant_confidence=0.0,
                leaf_confidence=0.0,
                status="INVALID_IMAGE",
                reason="IMAGE_TOO_DARK",
                message="Image is too dark to identify plant leaf characteristics. Please provide better illumination.",
                details={"mean_brightness": round(mean_val, 2)},
            )

        if mean_val > 245.0 and std_val < 15.0:
            return ValidationResult(
                is_valid_plant_image=False,
                plant_confidence=0.0,
                leaf_confidence=0.0,
                status="INVALID_IMAGE",
                reason="LOW_IMAGE_QUALITY",
                message="Image is overexposed or blank white without visible content.",
                details={"mean_brightness": round(mean_val, 2), "std_dev": round(std_val, 2)},
            )

        if std_val < 10.0:
            return ValidationResult(
                is_valid_plant_image=False,
                plant_confidence=0.0,
                leaf_confidence=0.0,
                status="INVALID_IMAGE",
                reason="LOW_IMAGE_QUALITY",
                message="Image is essentially blank or lacks meaningful visual contrast.",
                details={"std_dev": round(std_val, 2)},
            )

        # Stage 3: Extreme Blur Detection (Laplacian Variance)
        lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        if lap_var < self.blur_threshold:
            return ValidationResult(
                is_valid_plant_image=False,
                plant_confidence=0.0,
                leaf_confidence=0.0,
                status="INVALID_IMAGE",
                reason="IMAGE_TOO_BLURRY",
                message="Image is extremely blurry. Please capture a clear, steady close-up photo of the leaf.",
                details={"blur_variance": round(lap_var, 2), "threshold": self.blur_threshold},
            )

        # Stage 4: Botanical Pigmentation (Foliar Tissue Area)
        hsv = cv2.cvtColor(img_np, cv2.COLOR_RGB2HSV)
        # Chlorophyll green foliar pigmentation (primary plant signal)
        mask_green = cv2.inRange(hsv, np.array([25, 25, 25]), np.array([90, 255, 255]))
        green_ratio = float(np.count_nonzero(mask_green)) / float(w * h)

        # Yellowing / chlorotic leaf tissue
        mask_yellow = cv2.inRange(hsv, np.array([16, 40, 35]), np.array([25, 255, 255]))
        # Necrotic leaf spot / brown blight tissue
        mask_brown = cv2.inRange(hsv, np.array([8, 40, 25]), np.array([16, 255, 180]))

        # Lesions only count if accompanied by genuine green foliar tissue
        if green_ratio >= 0.05:
            combined_botanical = cv2.bitwise_or(mask_green, cv2.bitwise_or(mask_yellow, mask_brown))
            botanical_ratio = float(np.count_nonzero(combined_botanical)) / float(w * h)
        else:
            botanical_ratio = green_ratio

        # Stage 5: Document / UI Graphic / Screenshot Check
        white_ratio = float(np.count_nonzero(gray > 235)) / float(w * h)
        if white_ratio > 0.60 and botanical_ratio < 0.10:
            return ValidationResult(
                is_valid_plant_image=False,
                plant_confidence=round(botanical_ratio, 2),
                leaf_confidence=0.0,
                status="INVALID_IMAGE",
                reason="UNRELATED_IMAGE",
                message="Document, screenshot, or UI graphic detected. Please upload a real photograph of a plant leaf.",
                details={"white_ratio": round(white_ratio, 2), "botanical_ratio": round(botanical_ratio, 2)},
            )

        # Ensure neural models are ready
        self._ensure_models_loaded()

        # Stage 6: Non-Plant Object Detection (COCO Detector)
        if self._coco_yolo is not None:
            coco_res = self._coco_yolo.predict(pil_img, conf=0.35, verbose=False)[0]
            detected_non_plant = []
            for b in coco_res.boxes:
                c_name = self._coco_yolo.names[int(b.cls[0])]
                c_conf = float(b.conf[0])
                box_area = float(b.xywhn[0][2] * b.xywhn[0][3])
                if c_name in NON_PLANT_COCO_CLASSES and (c_conf > 0.40 or box_area > 0.12):
                    detected_non_plant.append((c_name, c_conf, box_area))

            if detected_non_plant:
                top_obj = max(detected_non_plant, key=lambda x: x[1])
                obj_name, obj_conf, _ = top_obj
                reason = "NO_PLANT_DETECTED" if obj_name == "person" else "UNRELATED_IMAGE"
                return ValidationResult(
                    is_valid_plant_image=False,
                    plant_confidence=0.05,
                    leaf_confidence=0.02,
                    status="INVALID_IMAGE",
                    reason=reason,
                    message=f"Invalid photo. Detected {obj_name} ({round(obj_conf*100)}% match) instead of a plant leaf.",
                    details={"detected_object": obj_name, "object_confidence": round(obj_conf, 2)},
                )

        # Stage 7: MobileNet Semantic Categorization (ImageNet)
        if self._mobilenet is not None and self._mobilenet_transforms is not None:
            try:
                batch = self._mobilenet_transforms(pil_img).unsqueeze(0).to(self.device)
                with torch.no_grad():
                    out_mb = self._mobilenet(batch)
                    probs_mb = torch.softmax(out_mb, dim=1)[0]
                    top_p, top_c = torch.topk(probs_mb, 3)

                top1_name = self._mobilenet_categories[top_c[0]].lower()
                top1_prob = float(top_p[0])

                is_obvious_non_plant = any(kw in top1_name for kw in NON_PLANT_IMAGENET_KEYWORDS)
                if is_obvious_non_plant and top1_prob > 0.40 and botanical_ratio < 0.12:
                    return ValidationResult(
                        is_valid_plant_image=False,
                        plant_confidence=0.06,
                        leaf_confidence=0.02,
                        status="INVALID_IMAGE",
                        reason="UNRELATED_IMAGE",
                        message=f"Invalid photo. Image appears to be {top1_name} rather than an agricultural plant leaf.",
                        details={"semantic_category": top1_name, "semantic_confidence": round(top1_prob, 2)},
                    )
            except Exception as e:
                logger.debug(f"MobileNet verification skipped due to error: {e}")

        # Stage 8: Specialized Crop Leaf Detection
        max_leaf_conf = 0.0
        total_leaf_box_area = 0.0
        detected_leaf_crops = []

        if self._leaf_yolo is not None:
            try:
                leaf_res = self._leaf_yolo.predict(pil_img, conf=0.15, verbose=False)[0]
                for b in leaf_res.boxes:
                    conf = float(b.conf[0])
                    box_area = float(b.xywhn[0][2] * b.xywhn[0][3])
                    total_leaf_box_area += box_area
                    if conf > max_leaf_conf:
                        max_leaf_conf = conf
                    crop_name = self._leaf_yolo.names[int(b.cls[0])]
                    detected_leaf_crops.append((crop_name, conf))
            except Exception as e:
                logger.warning(f"Leaf YOLO detection error: {e}")

        # If low foliar green AND no strong neural leaf detected -> definitively not an agricultural leaf
        if green_ratio < 0.06 and max_leaf_conf < 0.45:
            return ValidationResult(
                is_valid_plant_image=False,
                plant_confidence=round(green_ratio, 2),
                leaf_confidence=round(max_leaf_conf, 2),
                status="INVALID_IMAGE",
                reason="NO_PLANT_DETECTED",
                message="No plant leaf detected in the uploaded image. Please upload a clear photo of an affected crop leaf.",
                details={"green_ratio": round(green_ratio, 3), "max_leaf_conf": round(max_leaf_conf, 3)},
            )

        # Stage 9: Confidence Fusion
        plant_conf = min(
            1.0,
            botanical_ratio * 0.70 + (max_leaf_conf * 0.45) + (0.20 if botanical_ratio > 0.20 else 0.0)
        )
        leaf_conf = min(
            1.0,
            max_leaf_conf * 0.65 + min(1.0, botanical_ratio * 1.20) * 0.35
        )

        # High confidence boosts for confirmed foliar features
        if max_leaf_conf >= 0.50 and botanical_ratio >= 0.20:
            plant_conf = max(plant_conf, 0.91 + (max_leaf_conf - 0.50) * 0.15)
            leaf_conf = max(leaf_conf, 0.88 + (max_leaf_conf - 0.50) * 0.20)
        elif botanical_ratio >= 0.35 and (max_leaf_conf >= 0.20 or total_leaf_box_area >= 0.15):
            plant_conf = max(plant_conf, 0.89)
            leaf_conf = max(leaf_conf, 0.84)
        elif botanical_ratio >= 0.25 and max_leaf_conf >= 0.15:
            plant_conf = max(plant_conf, 0.82)
            leaf_conf = max(leaf_conf, 0.78)

        is_valid = (plant_conf >= p_thresh) and (leaf_conf >= l_thresh)

        reason = None
        message = "Valid agricultural plant leaf photo."
        if not is_valid:
            if plant_conf < p_thresh:
                reason = "NO_PLANT_DETECTED"
                message = "No recognizable plant detected. Please upload a clear photo of an agricultural plant leaf."
            else:
                reason = "NO_LEAF_DETECTED"
                message = "Plant material detected, but not a clear leaf suitable for disease diagnosis."

        return ValidationResult(
            is_valid_plant_image=is_valid,
            plant_confidence=round(plant_conf, 2),
            leaf_confidence=round(leaf_conf, 2),
            status="VALID" if is_valid else "INVALID_IMAGE",
            reason=reason,
            message=message,
            details={
                "green_ratio": round(green_ratio, 3),
                "botanical_ratio": round(botanical_ratio, 3),
                "max_leaf_conf": round(max_leaf_conf, 3),
                "leaf_coverage": round(total_leaf_box_area, 3),
                "detected_leaf_crops": detected_leaf_crops[:3],
                "configured_plant_threshold": p_thresh,
                "configured_leaf_threshold": l_thresh,
            },
        )


# Global singleton instance
_validator_instance: Optional[PlantLeafImageValidator] = None


def get_image_validator() -> PlantLeafImageValidator:
    """Retrieves or creates the singleton PlantLeafImageValidator instance."""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = PlantLeafImageValidator()
    return _validator_instance
