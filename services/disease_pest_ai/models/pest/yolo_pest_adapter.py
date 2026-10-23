"""
Production YOLO Pest Detection Adapter (Phase 3).

Integrates the audited pretrained YOLO11s pest detection model:
- Primary Checkpoint: underdogquality/yolo11s-pest-detection (YOLO11s, IP102, 102 classes)
- Secondary Checkpoint: Yudsky/pest-detection-yolo11 (YOLO11m, IP102, 102 classes)

Full Object Detection Capabilities:
- Returns pest class, confidence score, and bounding boxes [x_min, y_min, x_max, y_max]
- Supports 0, 1, or multiple simultaneous pest detections
- Crop compatibility validation using canonical pest taxonomy
- Image validation (corrupt, low resolution, domain advisory for sticky traps)
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from PIL import Image
import torch
from ultralytics import YOLO

from disease_pest_ai.models.base import BaseModelAdapter, normalize_crop_name
from disease_pest_ai.schemas.outputs import (
    BoundingBox,
    DetectedPest,
    PestPrediction,
)

logger = logging.getLogger(__name__)

HF_REPO_PRIMARY = "underdogquality/yolo11s-pest-detection"
HF_REPO_SECONDARY = "Yudsky/pest-detection-yolo11"
TAXONOMY_PATH = Path(__file__).resolve().parent.parent.parent / "knowledge_base" / "pest_taxonomy.json"

DEFAULT_CONF_THRESHOLD = 0.25
DEFAULT_IOU_THRESHOLD = 0.45
MINIMUM_DIMENSION_PIXELS = 32


class YoloPestAdapter(BaseModelAdapter):
    """
    Standardized adapter for YOLO11 pest detection.
    """

    def __init__(
        self,
        model_variant: str = "primary",
        conf_threshold: float = DEFAULT_CONF_THRESHOLD,
        iou_threshold: float = DEFAULT_IOU_THRESHOLD,
        device: Optional[str] = None,
    ):
        """
        Args:
            model_variant: 'primary' (underdogquality/yolo11s) or 'secondary' (Yudsky/yolo11m).
            conf_threshold: Minimum confidence score for valid pest detection.
            iou_threshold: NMS IoU threshold.
            device: 'cpu' or 'cuda' (auto-detected if None).
        """
        self.model_variant = model_variant.lower()
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        
        if self.model_variant == "secondary":
            self._model_name = HF_REPO_SECONDARY
            self._model_version = "YOLO11m-IP102"
            self._imgsz = 512
        else:
            self._model_name = HF_REPO_PRIMARY
            self._model_version = "YOLO11s-IP102"
            self._imgsz = 896

        self.model: Optional[YOLO] = None
        self._taxonomy: Dict[int, Dict[str, Any]] = {}
        self._load_taxonomy()

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def model_version(self) -> str:
        return self._model_version

    def is_available(self) -> bool:
        return True

    def _load_taxonomy(self) -> None:
        """Load pest taxonomy with crop host associations."""
        if TAXONOMY_PATH.exists():
            with open(TAXONOMY_PATH, "r", encoding="utf-8") as f:
                records = json.load(f)
            for r in records:
                self._taxonomy[r["class_id"]] = r
        else:
            logger.warning(f"Pest taxonomy file not found at: {TAXONOMY_PATH}")

    def load_weights(self) -> None:
        """Load YOLO model weights from local cache or download from Hugging Face Hub."""
        if self.model is not None:
            return

        from huggingface_hub import hf_hub_download

        logger.info(f"Loading pest detector checkpoint from Hugging Face Hub: {self._model_name}")
        ckpt_path = hf_hub_download(self._model_name, "best.pt")
        self.model = YOLO(ckpt_path)
        logger.info(f"Loaded {self._model_name} successfully ({len(self.model.names)} classes)")

    def _validate_image(self, image: Any) -> Tuple[Image.Image, List[str]]:
        """Validate input image for corruptions, dimensions, and color channels."""
        warnings: List[str] = []

        if isinstance(image, (str, Path)):
            p = Path(image)
            if not p.exists():
                raise FileNotFoundError(f"Image file does not exist: {p}")
            try:
                pil_img = Image.open(p)
                pil_img.verify()
                # Reopen after verify
                pil_img = Image.open(p)
            except Exception as e:
                raise ValueError(f"Corrupt or unreadable image file '{p}': {e}")
        elif isinstance(image, Image.Image):
            pil_img = image
        else:
            raise TypeError(f"Unsupported image input type: {type(image)}. Expected PIL Image or file path.")

        # Check dimensions
        w, h = pil_img.size
        if w < MINIMUM_DIMENSION_PIXELS or h < MINIMUM_DIMENSION_PIXELS:
            warnings.append(
                f"Low Resolution Warning: Image dimensions ({w}x{h}) are extremely small. "
                f"Minimum recommended size is {MINIMUM_DIMENSION_PIXELS}x{MINIMUM_DIMENSION_PIXELS}. Detection may be degraded."
            )

        # Check channels
        if pil_img.mode != "RGB":
            warnings.append(
                f"Color Channel Notice: Image mode is '{pil_img.mode}'. Converting to standard 3-channel RGB for detector."
            )
            pil_img = pil_img.convert("RGB")

        return pil_img, warnings

    def predict(
        self,
        image: Any,
        crop_name: Optional[str] = None,
        location_state: Optional[str] = None,
        growth_stage: Optional[str] = None,
        image_type: Optional[str] = None,
    ) -> PestPrediction:
        """
        Execute pest detection inference with full spatial localization.
        """
        self.load_weights()
        assert self.model is not None

        # 1. Validate image
        pil_img, warnings = self._validate_image(image)

        # 2. Domain check for sticky trap
        img_type_str = str(image_type or "").lower()
        if "trap" in img_type_str:
            warnings.append(
                "Domain Notice: Selected model was trained on on-plant leaf imagery (IP102). "
                "Inference on pheromone sticky trap sheets ('trap_sticky_sheet') is out-of-domain and uncalibrated."
            )

        # 3. Execute YOLO detection
        t0 = time.perf_counter()
        results = self.model.predict(
            pil_img,
            imgsz=self._imgsz,
            conf=self.conf_threshold,
            iou=self.iou_threshold,
            device=self.device,
            verbose=False,
        )
        latency_ms = (time.perf_counter() - t0) * 1000

        result = results[0]
        boxes = result.boxes

        # 4. Parse bounding boxes and detections
        detected_pests: List[DetectedPest] = []
        standard_boxes: List[BoundingBox] = []
        scores: List[float] = []

        norm_user_crop = normalize_crop_name(crop_name) if crop_name else None
        crop_mismatches = 0

        for b in boxes:
            cls_id = int(b.cls[0].item())
            score = float(b.conf[0].item())
            xyxy = [float(coord) for coord in b.xyxy[0].tolist()]

            raw_label = self.model.names[cls_id]
            tax_entry = self._taxonomy.get(cls_id, {})
            canonical_name = tax_entry.get("canonical_name", raw_label.title())
            supported_crops = tax_entry.get("supported_crops", [])

            # Crop compatibility check
            crop_compatible = True
            if norm_user_crop and supported_crops:
                norm_supported = [normalize_crop_name(c) for c in supported_crops]
                if norm_user_crop not in norm_supported:
                    crop_compatible = False
                    crop_mismatches += 1

            det = DetectedPest(
                pest=canonical_name,
                raw_label=raw_label,
                score=score,
                bounding_box=xyxy,
                class_id=cls_id,
                supported_crops=supported_crops,
                crop_compatible=crop_compatible,
            )
            detected_pests.append(det)

            bbox = BoundingBox(
                box=xyxy,
                label=canonical_name,
                score=score,
                crop=crop_name,
                is_normalized=False,
            )
            standard_boxes.append(bbox)
            scores.append(score)

        # 5. Rank by score
        ranked_pests = sorted(detected_pests, key=lambda p: p.score, reverse=True)

        # 6. Determine status
        status = "detected"
        crop_val_dict: Dict[str, Any] = {
            "user_crop": crop_name,
            "crop_pest_mismatch": False,
            "compatible_count": len([p for p in detected_pests if p.crop_compatible]),
            "incompatible_count": crop_mismatches,
        }

        if len(detected_pests) == 0:
            status = "no_pest_detected"
        elif crop_mismatches > 0 and crop_mismatches == len(detected_pests):
            status = "crop_mismatch"
            crop_val_dict["crop_pest_mismatch"] = True
            warnings.append(
                f"Crop Pest Mismatch: Detected pest(s) are not documented hosts for user crop '{crop_name}'. "
                f"Manual inspection required."
            )
        elif all(p.score < self.conf_threshold for p in detected_pests):
            status = "low_score"

        source_meta = {
            "dataset": "IP102 Benchmark",
            "total_classes": len(self.model.names),
            "license": "MIT",
            "training_domain": "Macro photographs of agricultural pests on plant foliage",
            "author": self._model_name.split("/")[0],
        }

        provenance = {
            "latency_ms": round(latency_ms, 2),
            "device": self.device,
            "backend": "PyTorch / Ultralytics YOLO",
            "conf_threshold": self.conf_threshold,
            "iou_threshold": self.iou_threshold,
            "imgsz": self._imgsz,
        }

        return PestPrediction(
            pests=detected_pests,
            top_pests=ranked_pests,
            bounding_boxes=standard_boxes,
            scores=scores,
            crop=crop_name,
            crop_validation=crop_val_dict,
            model_name=self._model_name,
            model_version=self._model_version,
            source_metadata=source_meta,
            status=status,
            warnings=warnings,
            provenance=provenance,
        )
