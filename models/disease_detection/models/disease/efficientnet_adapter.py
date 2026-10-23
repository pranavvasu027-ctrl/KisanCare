"""
EfficientNetV2-S Disease Classification Adapter.

Model: BiernyVR/crop-disease-classifier (Hugging Face)
Architecture: EfficientNetV2-S (21.5M parameters)
Dataset: PlantVillage (38 classes, 14 crops)
License: MIT
"""

import json
import logging
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from PIL import Image

import numpy as np
import torch
import torch.nn as nn
from torchvision import models

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

HF_REPO_ID = "BiernyVR/crop-disease-classifier"
DEFAULT_CHECKPOINT_NAME = "efficientnet_v2_s_best.pth"
DEFAULT_CLASSES_NAME = "classes.json"


def parse_plantvillage_class(raw_class: str) -> Tuple[str, str, ConditionType]:
    """
    Parse raw PlantVillage class label into (crop, condition, condition_type).
    Example: 'Tomato___Early_blight' -> ('Tomato', 'Early Blight', ConditionType.DISEASE)
             'Apple___healthy' -> ('Apple', 'Healthy', ConditionType.HEALTHY)
             'Tomato___Spider_mites Two-spotted_spider_mite' -> ('Tomato', 'Spider Mites (Two-Spotted)', ConditionType.PEST)
    """
    if "___" in raw_class:
        crop_part, disease_part = raw_class.split("___", 1)
    else:
        crop_part = "Unknown"
        disease_part = raw_class

    # Format crop
    crop = crop_part.replace("_", " ").title()
    if "Cherry" in crop:
        crop = "Cherry"
    elif "Pepper" in crop:
        crop = "Bell Pepper"
    elif "Corn" in crop:
        crop = "Corn"

    # Format condition & type
    clean_disease = disease_part.replace("_", " ").strip()
    if clean_disease.lower() == "healthy":
        condition = "Healthy"
        c_type = ConditionType.HEALTHY
    elif "spider mite" in clean_disease.lower():
        condition = "Spider Mites (Two-Spotted Spider Mite)"
        c_type = ConditionType.PEST
    else:
        condition = clean_disease.title()
        c_type = ConditionType.DISEASE

    return crop, condition, c_type


class EfficientNetDiseaseAdapter(BaseModelAdapter):
    """
    Adapter for BiernyVR/crop-disease-classifier (EfficientNetV2-S).
    """

    model_name: str = "BiernyVR/crop-disease-classifier"
    model_version: str = "EfficientNetV2-S (38-class PlantVillage)"

    def __init__(
        self,
        checkpoint_path: Optional[Union[str, Path]] = None,
        classes_path: Optional[Union[str, Path]] = None,
        device: Optional[str] = None,
        auto_download: bool = True,
    ):
        self.device = torch.device(
            device if device else ("cuda" if torch.cuda.is_available() else "cpu")
        )
        self.auto_download = auto_download
        self.checkpoint_path = Path(checkpoint_path) if checkpoint_path else None
        self.classes_path = Path(classes_path) if classes_path else None
        
        self.model: Optional[nn.Module] = None
        self.classes: List[str] = []
        self.image_size: int = 224
        self.mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        self.std = np.array([0.229, 0.224, 0.225], dtype=np.float32)

        self._ensure_loaded()

    def _ensure_loaded(self) -> None:
        """Download (if needed) and load model state dict."""
        if self.model is not None:
            return

        # 1. Resolve classes path
        if not self.classes_path or not self.classes_path.exists():
            if self.auto_download:
                from huggingface_hub import hf_hub_download
                self.classes_path = Path(hf_hub_download(HF_REPO_ID, DEFAULT_CLASSES_NAME))
            else:
                raise FileNotFoundError("classes.json not found and auto_download is False.")

        with open(self.classes_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
            self.classes = meta.get("classes", meta) if isinstance(meta, dict) else meta
            self.image_size = meta.get("image_size", 224) if isinstance(meta, dict) else 224

        # 2. Resolve checkpoint path
        if not self.checkpoint_path or not self.checkpoint_path.exists():
            if self.auto_download:
                from huggingface_hub import hf_hub_download
                self.checkpoint_path = Path(hf_hub_download(HF_REPO_ID, DEFAULT_CHECKPOINT_NAME))
            else:
                raise FileNotFoundError("Model checkpoint not found and auto_download is False.")

        # 3. Build architecture
        model = models.efficientnet_v2_s(weights=None)
        in_features = model.classifier[-1].in_features
        model.classifier[-1] = nn.Linear(in_features, len(self.classes))

        # 4. Load weights
        ckpt = torch.load(self.checkpoint_path, map_location=self.device, weights_only=False)
        state = ckpt["model_state_dict"] if isinstance(ckpt, dict) and "model_state_dict" in ckpt else ckpt

        cleaned_state = {}
        for k, v in state.items():
            if "classifier.1.1." in k:
                cleaned_state[k.replace("classifier.1.1.", "classifier.1.")] = v
            else:
                cleaned_state[k] = v

        try:
            model.load_state_dict(cleaned_state, strict=True)
        except Exception as e:
            logger.warning(f"Strict loading failed ({e}); attempting flexible classification head match.")
            model.classifier[-1] = nn.Sequential(nn.Dropout(p=0.0), nn.Linear(in_features, len(self.classes)))
            model.load_state_dict(state, strict=False)

        model.to(self.device).eval()
        self.model = model
        logger.info(f"Loaded {self.model_name} on {self.device}")

    def is_available(self) -> bool:
        """Check if model is successfully loaded."""
        return self.model is not None and len(self.classes) > 0

    def preprocess(self, pil_image: Image.Image) -> torch.Tensor:
        """Resize, normalize, and convert image to PyTorch tensor [1, 3, H, W]."""
        resized = pil_image.resize((self.image_size, self.image_size), Image.Resampling.BILINEAR)
        arr = np.array(resized, dtype=np.float32) / 255.0
        arr = (arr - self.mean) / self.std
        arr = np.transpose(arr, (2, 0, 1))  # HWC -> CHW
        tensor = torch.from_numpy(np.expand_dims(arr, 0)).to(self.device)
        return tensor

    def predict(
        self,
        image: Union[str, Path, bytes, Image.Image],
        crop_name: Optional[str] = None,
        location_state: Optional[str] = None,
        growth_stage: Optional[str] = None,
        image_type: Optional[str] = None,
        topk: int = 5,
    ) -> PredictionResult:
        """
        Execute prediction on single leaf image.
        """
        self._ensure_loaded()
        t0 = time.perf_counter()

        pil_img = load_image_to_pil(image)
        tensor = self.preprocess(pil_img)

        with torch.no_grad():
            logits = self.model(tensor)
            probs = torch.softmax(logits, dim=1).cpu().numpy()[0]

        latency_ms = (time.perf_counter() - t0) * 1000.0

        # Rank predictions
        top_indices = np.argsort(probs)[::-1][:topk]
        self._last_top_idx = int(top_indices[0])
        top_predictions: List[TopPrediction] = []

        for idx in top_indices:
            raw_cls = self.classes[idx]
            c_crop, c_cond, c_type = parse_plantvillage_class(raw_cls)
            top_predictions.append(
                TopPrediction(
                    condition=c_cond,
                    crop=c_crop,
                    score=float(probs[idx]),
                    condition_type=c_type,
                    raw_label=raw_cls,
                )
            )

        top1 = top_predictions[0]
        predicted_crop = top1.crop
        condition = top1.condition
        condition_type = top1.condition_type
        score = top1.score

        # Contextual validation
        crop_mismatch, warnings = check_crop_consistency(crop_name, predicted_crop)

        # Check image type warning
        if image_type and image_type.lower() in ("trap_sticky_sheet", "trap"):
            warnings.append(
                "Image type 'trap_sticky_sheet' is incompatible with leaf disease classifier. "
                "Output is likely invalid."
            )

        provenance = {
            "latency_ms": round(latency_ms, 2),
            "device": str(self.device),
            "backend": "pytorch",
            "framework_version": torch.__version__,
            "raw_class": top1.raw_label,
            "input_resolution": [self.image_size, self.image_size],
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
            top_predictions=top_predictions,
            bounding_boxes=[],  # Classification model produces no bounding boxes
            crop=predicted_crop,
            user_crop=crop_name,
            crop_mismatch=crop_mismatch,
            model_name=self.model_name,
            model_version=self.model_version,
            warnings=warnings,
            provenance=provenance,
        )
