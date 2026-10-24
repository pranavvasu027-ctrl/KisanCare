"""Soybean Crop Disease Specialist Adapter.

Integrates ixrbhii/soybean-disease-convnext (ConvNeXt-Small) with canonical taxonomy mapping.
Part of KisanCare Unified Multi-Model Crop Disease Intelligence System.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import timm
import torch
from torchvision import transforms
from PIL import Image
from safetensors.torch import load_file

from disease_pest_ai.specialists.base import (
    BaseSpecialistAdapter,
    SpecialistCandidate,
    SpecialistPrediction,
)

logger = logging.getLogger("kisancare.specialists.soybean")

SOYBEAN_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SOYBEAN_DIR.parent.parent.parent.parent
WEIGHTS_PATH = SOYBEAN_DIR / "model.safetensors"
FALLBACK_WEIGHTS_PATH = PROJECT_ROOT / "models" / "disease_detection" / "specialists" / "soybean" / "model.safetensors"
CONFIG_PATH = SOYBEAN_DIR / "config.json"

SOYBEAN_CANONICAL_MAP: Dict[str, Dict[str, Any]] = {
    "downy mildew": {
        "canonical_condition": "Downy Mildew",
        "canonical_label": "soybean::Downy mildew",
        "category": "disease",
        "scientific_name": "Peronospora manshurica",
    },
    "frogeye leaf spot": {
        "canonical_condition": "Frogeye Leaf Spot",
        "canonical_label": "soybean::Frogeye leaf spot",
        "category": "disease",
        "scientific_name": "Cercospora sojina",
    },
    "healthy": {
        "canonical_condition": "Healthy Foliage",
        "canonical_label": "soybean::Healthy",
        "category": "healthy",
        "scientific_name": None,
    },
    "mosaic virus": {
        "canonical_condition": "Soybean Mosaic Virus",
        "canonical_label": "soybean::Mosaic virus",
        "category": "disease",
        "scientific_name": "Soybean mosaic virus (SMV)",
    },
    "rust": {
        "canonical_condition": "Asian Soybean Rust",
        "canonical_label": "soybean::Rust",
        "category": "disease",
        "scientific_name": "Phakopsora pachyrhizi",
    },
    "septoria brown spot": {
        "canonical_condition": "Brown Spot (Septoria)",
        "canonical_label": "soybean::Septoria brown spot",
        "category": "disease",
        "scientific_name": "Septoria glycines",
    },
}


class SoybeanConvNeXtAdapter(BaseSpecialistAdapter):
    """Production ConvNeXt-Small specialist adapter for Soybean foliar diseases."""

    model_identifier: str = "ixrbhii/soybean-disease-convnext"
    crop: str = "Soybean"
    architecture: str = "ConvNeXt-Small (timm)"
    license: str = "CC-BY-4.0"
    abstention_threshold: float = 0.40

    def __init__(self, weights_path: Optional[Path] = None, device: str = "cpu"):
        env_weights = os.getenv("SOYBEAN_MODEL_WEIGHTS_PATH")
        if weights_path and Path(weights_path).is_file():
            self.weights_path = Path(weights_path)
        elif env_weights and Path(env_weights).is_file():
            self.weights_path = Path(env_weights)
        elif WEIGHTS_PATH.is_file():
            self.weights_path = WEIGHTS_PATH
        elif FALLBACK_WEIGHTS_PATH.is_file():
            self.weights_path = FALLBACK_WEIGHTS_PATH
        else:
            self.weights_path = WEIGHTS_PATH

        self.device = device
        self.model: Optional[torch.nn.Module] = None
        self.transform = None
        self.raw_classes: List[str] = []
        self.weights_hash: str = ""
        self.metadata: Dict[str, Any] = {}
        self._load()

    def _load(self):
        if not self.weights_path.is_file():
            logger.warning("Soybean specialist weights not found at %s or fallback", self.weights_path)
            return

        t0 = time.time()
        hasher = hashlib.sha256()
        with open(self.weights_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        self.weights_hash = hasher.hexdigest()

        if CONFIG_PATH.is_file():
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg_data = json.load(f)
                self.raw_classes = cfg_data.get("label_names", [])
        if not self.raw_classes:
            self.raw_classes = [
                "Downy Mildew",
                "Frogeye Leaf Spot",
                "Healthy",
                "Mosaic Virus",
                "Rust",
                "Septoria Brown Spot",
            ]

        model = timm.create_model("convnext_small", pretrained=False, num_classes=len(self.raw_classes))
        state_dict = load_file(str(self.weights_path))
        model.load_state_dict(state_dict)
        model.to(self.device)
        model.eval()
        self.model = model

        self.transform = transforms.Compose([
            transforms.Resize(235, interpolation=transforms.InterpolationMode.BICUBIC),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225],
            ),
        ])

        elapsed = time.time() - t0
        self.metadata = {
            "model_identifier": self.model_identifier,
            "crop": self.crop,
            "architecture": self.architecture,
            "num_classes": len(self.raw_classes),
            "classes": self.raw_classes,
            "weights_hash": self.weights_hash,
            "load_time_sec": round(elapsed, 3),
            "license": self.license,
            "abstention_threshold": self.abstention_threshold,
        }
        logger.info("Soybean ConvNeXt loaded in %.3fs (SHA: %s)", elapsed, self.weights_hash[:8])

    def is_available(self) -> bool:
        return self.model is not None

    def get_supported_classes(self) -> List[str]:
        return list(self.raw_classes)

    def get_metadata(self) -> Dict[str, Any]:
        return dict(self.metadata)

    def predict(self, image: Any, requested_crop: Optional[str] = None) -> SpecialistPrediction:
        if not isinstance(image, Image.Image):
            from disease_pest_ai.models.base import load_image_to_pil
            image = load_image_to_pil(image)
        if not self.is_available():
            raise RuntimeError(
                f"Soybean specialist model is unavailable: weights not found at {self.weights_path}. Please provide valid weights via SOYBEAN_MODEL_WEIGHTS_PATH or place model.safetensors in {SOYBEAN_DIR}."
            )

        t0 = time.time()
        rgb_image = image.convert("RGB")

        # Phase 4 Reliability: Reject excessively small or blank/flat images
        w, h = rgb_image.size
        is_insufficient_quality = w < 32 or h < 32
        if not is_insufficient_quality:
            import numpy as np
            im_arr = np.array(rgb_image)
            if float(np.std(im_arr)) < 8.0:
                is_insufficient_quality = True

        tensor = self.transform(rgb_image).unsqueeze(0).to(self.device)

        with torch.no_grad():
            logits = self.model(tensor)
            # Temperature scaling for confidence calibration (T=1.15)
            scaled_logits = logits / 1.15
            probs = torch.softmax(scaled_logits, dim=1).squeeze(0)

        probs_np = probs.cpu().numpy()
        candidates: List[SpecialistCandidate] = []
        for idx, score in enumerate(probs_np):
            raw_cls = self.raw_classes[idx]
            clean_cls = raw_cls.lower().strip()
            info = SOYBEAN_CANONICAL_MAP.get(clean_cls, {
                "canonical_condition": raw_cls,
                "canonical_label": f"soybean::{raw_cls}",
                "category": "healthy" if "healthy" in clean_cls else "disease",
                "scientific_name": None,
            })
            cal_score = float(score)
            candidates.append(
                SpecialistCandidate(
                    raw_condition=raw_cls,
                    canonical_condition=info["canonical_condition"],
                    canonical_label=info["canonical_label"],
                    crop="Soybean",
                    category=info["category"],
                    raw_score=cal_score,
                    calibrated_confidence=cal_score,
                    percentage=int(round(cal_score * 100)),
                    scientific_name=info.get("scientific_name"),
                )
            )

        candidates.sort(key=lambda c: c.raw_score, reverse=True)
        top = candidates[0]
        elapsed_ms = (time.time() - t0) * 1000.0

        if is_insufficient_quality:
            is_abstaining = True
            abstention_reason = "insufficient_evidence: image quality or contrast too low"
        else:
            is_abstaining = top.calibrated_confidence < self.abstention_threshold
            abstention_reason = "low_confidence" if is_abstaining else None

        return SpecialistPrediction(
            raw_condition=top.raw_condition,
            canonical_condition=top.canonical_condition,
            canonical_label=top.canonical_label,
            crop="Soybean",
            category=top.category,
            raw_score=top.raw_score,
            calibrated_confidence=top.calibrated_confidence,
            percentage=top.percentage,
            scientific_name=top.scientific_name,
            top_candidates=candidates,
            latency_ms=round(elapsed_ms, 2),
            model_identifier=self.model_identifier,
            weights_hash=self.weights_hash,
            is_abstaining=is_abstaining,
            abstention_reason=abstention_reason,
        )
