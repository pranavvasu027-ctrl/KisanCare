"""Soybean Crop Disease Specialist Adapter.

Integrates ixrbhii/soybean-disease-convnext (ConvNeXt-Small) with canonical taxonomy mapping.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import timm
import torch
from torchvision import transforms
from PIL import Image
from safetensors.torch import load_file

try:
    from models.disease_detection.specialists.base import (
        BaseSpecialistAdapter,
        SpecialistCandidate,
        SpecialistPrediction,
    )
except ImportError:
    from specialists.base import (
        BaseSpecialistAdapter,
        SpecialistCandidate,
        SpecialistPrediction,
    )

logger = logging.getLogger("kisancare.specialists.soybean")

SOYBEAN_DIR = Path(__file__).resolve().parent
WEIGHTS_PATH = SOYBEAN_DIR / "model.safetensors"
CONFIG_PATH = SOYBEAN_DIR / "config.json"

# Verified taxonomic mapping for ixrbhii/soybean-disease-convnext classes
SOYBEAN_TAXONOMY_MAP = {
    "Downy Mildew": {
        "canonical_condition": "Downy Mildew",
        "canonical_label": "soybean::Downy mildew",
        "category": "disease",
        "scientific_name": "Peronospora manshurica",
    },
    "Frogeye Leaf Spot": {
        "canonical_condition": "Frogeye Leaf Spot",
        "canonical_label": "soybean::Frogeye leaf spot",
        "category": "disease",
        "scientific_name": "Cercospora sojina",
    },
    "Healthy": {
        "canonical_condition": "Healthy Foliage",
        "canonical_label": "soybean::Healthy",
        "category": "healthy",
        "scientific_name": None,
    },
    "Mosaic Virus": {
        "canonical_condition": "Soybean Mosaic Virus",
        "canonical_label": "soybean::Mosaic virus",
        "category": "disease",
        "scientific_name": "Soybean mosaic virus (SMV)",
    },
    "Rust": {
        "canonical_condition": "Asian Soybean Rust",
        "canonical_label": "soybean::Rust",
        "category": "disease",
        "scientific_name": "Phakopsora pachyrhizi",
    },
    "Septoria Brown Spot": {
        "canonical_condition": "Brown Spot (Septoria)",
        "canonical_label": "soybean::Septoria brown spot",
        "category": "disease",
        "scientific_name": "Septoria glycines",
    },
}


class SoybeanConvNeXtAdapter(BaseSpecialistAdapter):
    """Production ConvNeXt-Small specialist adapter for Soybean foliar diseases."""

    def __init__(self, weights_path: Optional[Path] = None, device: str = "cpu"):
        self.weights_path = Path(weights_path) if weights_path else WEIGHTS_PATH
        self.device = device
        self.model: Optional[torch.nn.Module] = None
        self.transform = None
        self.raw_classes: List[str] = []
        self.weights_hash: str = ""
        self.metadata: Dict[str, Any] = {}
        self._load()

    def _load(self):
        if not self.weights_path.is_file():
            logger.warning("Soybean specialist weights not found at %s", self.weights_path)
            return

        t0 = time.time()
        # Compute cryptographic SHA-256
        hasher = hashlib.sha256()
        with open(self.weights_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        self.weights_hash = hasher.hexdigest()

        # Load class labels from config
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

        # Initialize ConvNeXt-Small architecture with 6 target classes
        model = timm.create_model("convnext_small", pretrained=False, num_classes=len(self.raw_classes))
        state_dict = load_file(str(self.weights_path))
        model.load_state_dict(state_dict)
        model.to(self.device)
        model.eval()
        self.model = model

        # ConvNeXt preprocessing (256 resize, 224 center crop, ImageNet normalization)
        self.transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225],
            ),
        ])

        elapsed = time.time() - t0
        self.metadata = {
            "model_identifier": "ixrbhii/soybean-disease-convnext",
            "crop": "Soybean",
            "architecture": "ConvNeXt-Small (timm)",
            "num_classes": len(self.raw_classes),
            "classes": self.raw_classes,
            "weights_hash": self.weights_hash,
            "load_time_sec": round(elapsed, 3),
            "license": "CC-BY-4.0",
            "device": self.device,
        }
        logger.info(
            "SoybeanConvNeXtAdapter initialized in %.2fs (classes: %d, sha256: %s...)",
            elapsed, len(self.raw_classes), self.weights_hash[:8]
        )

    def load(self) -> None:
        if self.model is None:
            self._load()

    def is_available(self) -> bool:
        return self.model is not None and self.transform is not None

    @property
    def classes(self) -> List[str]:
        return list(self.raw_classes)

    def get_supported_classes(self) -> List[str]:
        return [
            SOYBEAN_TAXONOMY_MAP.get(c, {}).get("canonical_condition", c)
            for c in self.raw_classes
        ]

    def get_metadata(self) -> Dict[str, Any]:
        return self.metadata

    def predict(self, pil_image: Image.Image) -> SpecialistPrediction:
        """Execute vision inference and return canonical SpecialistPrediction."""
        if not self.is_available():
            raise RuntimeError("Soybean specialist model is not available or not loaded.")

        t0 = time.time()
        tensor = self.transform(pil_image).unsqueeze(0).to(self.device)

        with torch.no_grad():
            logits = self.model(tensor)
            # Temperature scaling (T=1.15) for safe probability calibration
            scaled_logits = logits / 1.15
            calibrated_probs = torch.softmax(scaled_logits, dim=-1).squeeze(0)
            raw_probs = torch.softmax(logits, dim=-1).squeeze(0)

        latency_ms = (time.time() - t0) * 1000.0

        candidates: List[SpecialistCandidate] = []
        for idx, (raw_cls, raw_p, cal_p) in enumerate(zip(self.raw_classes, raw_probs, calibrated_probs)):
            tax = SOYBEAN_TAXONOMY_MAP.get(raw_cls, {
                "canonical_condition": raw_cls.title(),
                "canonical_label": f"soybean::{raw_cls.title()}",
                "category": "disease" if "healthy" not in raw_cls.lower() else "healthy",
            })
            candidates.append(
                SpecialistCandidate(
                    raw_condition=raw_cls,
                    canonical_condition=tax["canonical_condition"],
                    canonical_label=tax["canonical_label"],
                    crop="Soybean",
                    category=tax["category"],
                    raw_score=round(float(raw_p.item()), 4),
                    calibrated_confidence=round(float(cal_p.item()), 4),
                    percentage=int(round(float(cal_p.item()) * 100)),
                )
            )

        # Sort descending by calibrated confidence
        candidates.sort(key=lambda c: c.calibrated_confidence, reverse=True)
        top = candidates[0]

        return SpecialistPrediction(
            raw_condition=top.raw_condition,
            canonical_condition=top.canonical_condition,
            canonical_label=top.canonical_label,
            crop="Soybean",
            category=top.category,
            raw_score=top.raw_score,
            calibrated_confidence=top.calibrated_confidence,
            percentage=top.percentage,
            top_candidates=candidates,
            latency_ms=round(latency_ms, 2),
            model_identifier="ixrbhii/soybean-disease-convnext",
            provenance={
                "model_identifier": "ixrbhii/soybean-disease-convnext",
                "architecture": "ConvNeXt-Small",
                "weights_hash": self.weights_hash,
                "latency_ms": round(latency_ms, 2),
                "device": self.device,
                "calibration_temperature": 1.15,
            },
        )
