"""
YOLOv11x Multi-Domain Plant Disease Detection Adapter.

Model: JK-TK/PlantDiseaseDetection (Hugging Face)
Architecture: YOLOv11x (57M parameters)
Dataset: Combined plantwild (89 classes) + FieldPlant (27 classes) = 116 classes
License: MIT
"""

import logging
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from PIL import Image

from disease_pest_ai.models.base import (
    BaseModelAdapter,
    check_crop_consistency,
    load_image_to_pil,
)
from disease_pest_ai.schemas.outputs import (
    BoundingBox,
    ConditionType,
    PredictionResult,
    TopPrediction,
)

logger = logging.getLogger(__name__)

HF_REPO_ID = "JK-TK/PlantDiseaseDetection"
DEFAULT_CHECKPOINT_NAME = "PlantDiseaseDetection.pt"


def parse_yolo_class(raw_name: str) -> Tuple[str, str, ConditionType]:
    """
    Parse YOLO 116-class name into (crop, condition, condition_type).
    Examples:
      'cherry leaf spot' -> ('Cherry', 'Leaf Spot', ConditionType.DISEASE)
      'cherry leaf' -> ('Cherry', 'Healthy Leaf', ConditionType.HEALTHY)
      'Corn Insects Damages' -> ('Corn', 'Insect Damage', ConditionType.PEST)
      'Cassava Healthy' -> ('Cassava', 'Healthy', ConditionType.HEALTHY)
    """
    clean = raw_name.strip()
    clean_lower = clean.lower()

    # Determine condition type
    if "healthy" in clean_lower:
        c_type = ConditionType.HEALTHY
    elif any(term in clean_lower for term in ["insect", "mite", "damage", "worm"]):
        c_type = ConditionType.PEST
    elif clean_lower.endswith(" leaf") and not any(d in clean_lower for d in ["spot", "blight", "rust", "curl", "mold", "scab"]):
        # Plantwild notation for healthy leaves: e.g. "cherry leaf", "apple leaf"
        c_type = ConditionType.HEALTHY
    else:
        c_type = ConditionType.DISEASE

    # Crop extraction heuristics
    known_crops = [
        "corn", "maize", "tomato", "potato", "apple", "grape", "cherry", "peach",
        "cassava", "banana", "citrus", "orange", "rice", "cucumber", "eggplant",
        "bell pepper", "pepper", "blueberry", "strawberry", "squash", "zucchini",
        "soybean", "coffee", "celery", "cabbage", "cauliflower", "broccoli",
        "garlic", "ginger", "basil", "lettuce", "bean", "plum", "carrot", "maple",
        "tobacco", "raspberry"
    ]

    detected_crop = "Unknown"
    for kc in known_crops:
        if clean_lower.startswith(kc) or f" {kc} " in f" {clean_lower} ":
            detected_crop = kc.title()
            break

    # Format condition title
    if c_type == ConditionType.HEALTHY:
        condition = "Healthy"
    else:
        # Strip crop prefix if present
        cond_text = clean
        if detected_crop != "Unknown" and cond_text.lower().startswith(detected_crop.lower()):
            cond_text = cond_text[len(detected_crop):].strip()
        condition = cond_text.title() if cond_text else clean.title()

    return detected_crop, condition, c_type


class YoloDiseaseAdapter(BaseModelAdapter):
    """
    Adapter for JK-TK/PlantDiseaseDetection (YOLOv11x).
    """

    model_name: str = "JK-TK/PlantDiseaseDetection"
    model_version: str = "YOLOv11x (116-class combined)"

    def __init__(
        self,
        checkpoint_path: Optional[Union[str, Path]] = None,
        conf_threshold: float = 0.15,
        device: Optional[str] = None,
        auto_download: bool = True,
    ):
        self.conf_threshold = conf_threshold
        self.device = device or ("cuda" if Path(checkpoint_path or "").exists() and False else "cpu")
        self.checkpoint_path = Path(checkpoint_path) if checkpoint_path else None
        self.auto_download = auto_download
        self.model = None

        self._ensure_loaded()

    def _ensure_loaded(self) -> None:
        """Ensure ultralytics model is loaded."""
        if self.model is not None:
            return

        from ultralytics import YOLO

        if not self.checkpoint_path or not self.checkpoint_path.exists():
            if self.auto_download:
                from huggingface_hub import hf_hub_download
                self.checkpoint_path = Path(hf_hub_download(HF_REPO_ID, DEFAULT_CHECKPOINT_NAME))
            else:
                raise FileNotFoundError("YOLO checkpoint not found and auto_download is False.")

        self.model = YOLO(str(self.checkpoint_path))
        logger.info(f"Loaded {self.model_name} from {self.checkpoint_path}")

    def is_available(self) -> bool:
        """Check if model is loaded and ready."""
        return self.model is not None

    def predict(
        self,
        image: Union[str, Path, bytes, Image.Image],
        crop_name: Optional[str] = None,
        location_state: Optional[str] = None,
        growth_stage: Optional[str] = None,
        image_type: Optional[str] = None,
    ) -> PredictionResult:
        """
        Run object detection inference.
        """
        self._ensure_loaded()
        t0 = time.perf_counter()

        pil_img = load_image_to_pil(image)
        w, h = pil_img.size

        # Ultralytics accepts PIL Image directly
        results = self.model(pil_img, conf=self.conf_threshold, verbose=False)
        latency_ms = (time.perf_counter() - t0) * 1000.0

        boxes_out: List[BoundingBox] = []
        top_predictions: List[TopPrediction] = []

        if len(results) > 0 and len(results[0].boxes) > 0:
            boxes = results[0].boxes
            for b in boxes:
                cls_id = int(b.cls[0])
                score = float(b.conf[0])
                raw_name = self.model.names[cls_id]
                c_crop, c_cond, c_type = parse_yolo_class(raw_name)
                xyxy = [float(x) for x in b.xyxy[0].tolist()]

                boxes_out.append(
                    BoundingBox(
                        box=xyxy,
                        label=raw_name,
                        score=score,
                        crop=c_crop,
                        is_normalized=False,
                    )
                )

                top_predictions.append(
                    TopPrediction(
                        condition=c_cond,
                        crop=c_crop,
                        score=score,
                        condition_type=c_type,
                        raw_label=raw_name,
                    )
                )

            # Sort top predictions by score descending
            top_predictions.sort(key=lambda x: x.score, reverse=True)
            top1 = top_predictions[0]
            condition = top1.condition
            condition_type = top1.condition_type
            score = top1.score
            predicted_crop = top1.crop

        else:
            condition = "No Visible Pathologies"
            condition_type = ConditionType.HEALTHY
            score = 1.0 - self.conf_threshold
            predicted_crop = crop_name or "Unknown"
            top_predictions = [
                TopPrediction(
                    condition=condition,
                    crop=predicted_crop,
                    score=score,
                    condition_type=condition_type,
                    raw_label="background_or_healthy",
                )
            ]

        # Crop validation
        crop_mismatch, warnings = check_crop_consistency(crop_name, predicted_crop)

        if image_type and image_type.lower() in ("trap_sticky_sheet", "trap"):
            warnings.append(
                "Image type 'trap_sticky_sheet' is incompatible with plant disease detector. "
                "Output is likely invalid."
            )

        provenance = {
            "latency_ms": round(latency_ms, 2),
            "device": str(self.device),
            "backend": "ultralytics",
            "detected_boxes_count": len(boxes_out),
            "input_resolution": [w, h],
            "context": {
                "user_crop": crop_name,
                "location_state": location_state,
                "growth_stage": growth_stage,
                "image_type": image_type,
            },
        }

        return PredictionResult(
            condition=condition,
            condition_type=condition_type,
            score=score,
            top_predictions=top_predictions[:5],
            bounding_boxes=boxes_out,
            crop=predicted_crop,
            user_crop=crop_name,
            crop_mismatch=crop_mismatch,
            model_name=self.model_name,
            model_version=self.model_version,
            warnings=warnings,
            provenance=provenance,
        )
