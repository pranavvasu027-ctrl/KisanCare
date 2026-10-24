"""Cotton Crop Disease Specialist Adapter.

Integrates FarmGuard/cotton-densenet121 with normalized canonical taxonomy mapping.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import torch
import torchvision.models as models
from torchvision import transforms
from PIL import Image

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

logger = logging.getLogger("kisancare.specialists.cotton")

COTTON_DIR = Path(__file__).resolve().parent
WEIGHTS_PATH = COTTON_DIR / "best_densenet.pth"
CLASSES_PATH = COTTON_DIR / "classes.json"

# Canonical taxonomy mapping for FarmGuard classes
COTTON_TAXONOMY_MAP = {
    "bacterial blight": {
        "canonical_condition": "Bacterial Blight",
        "canonical_label": "cotton::Bacterial blight",
        "category": "disease",
        "scientific_name": "Xanthomonas citri pv. malvacearum",
    },
    "curl virus": {
        "canonical_condition": "Cotton Leaf Curl Virus",
        "canonical_label": "cotton::Leaf curl virus",
        "category": "disease",
        "scientific_name": "Cotton leaf curl virus (CLCuV)",
    },
    "fussarium wilt": {
        "canonical_condition": "Fusarium Wilt",
        "canonical_label": "cotton::Fusarium wilt",
        "category": "disease",
        "scientific_name": "Fusarium oxysporum f. sp. vasinfectum",
    },
    "healthy": {
        "canonical_condition": "Healthy Foliage",
        "canonical_label": "cotton::Healthy",
        "category": "healthy",
        "scientific_name": None,
    },
}


class CottonDenseNetAdapter(BaseSpecialistAdapter):
    """Production DenseNet-121 specialist adapter for Cotton foliar diseases."""

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
            logger.warning("Cotton specialist weights not found at %s", self.weights_path)
            return

        t0 = time.time()
        # Compute SHA-256 for audit trail
        hasher = hashlib.sha256()
        with open(self.weights_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        self.weights_hash = hasher.hexdigest()

        # Load classes
        if CLASSES_PATH.is_file():
            with open(CLASSES_PATH, "r", encoding="utf-8") as f:
                self.raw_classes = json.load(f)
        else:
            self.raw_classes = ["bacterial blight", "curl virus", "fussarium wilt", "healthy"]

        # Initialize DenseNet-121 architecture
        model = models.densenet121(weights=None)
        model.classifier = torch.nn.Linear(model.classifier.in_features, len(self.raw_classes))

        ckpt = torch.load(str(self.weights_path), map_location=self.device)
        state_dict = ckpt["model_state_dict"] if "model_state_dict" in ckpt else ckpt
        model.load_state_dict(state_dict)
        model.eval()
        self.model = model

        # Standard ImageNet preprocessing matching FarmGuard training
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
            "model_identifier": "FarmGuard/cotton-densenet121",
            "crop": "Cotton",
            "architecture": "DenseNet-121",
            "num_classes": len(self.raw_classes),
            "classes": self.raw_classes,
            "weights_hash": self.weights_hash,
            "load_time_sec": round(elapsed, 3),
            "checkpoint_epoch": ckpt.get("epoch") if isinstance(ckpt, dict) else None,
            "val_acc": ckpt.get("val_acc") if isinstance(ckpt, dict) else None,
            "device": self.device,
        }
        logger.info(
            "CottonDenseNetAdapter initialized in %.2fs (classes: %d, sha256: %s...)",
            elapsed, len(self.raw_classes), self.weights_hash[:8]
        )

    def load(self) -> None:
        if self.model is None:
            self._load()

    def is_available(self) -> bool:
        return self.model is not None and self.transform is not None

    def get_supported_classes(self) -> List[str]:
        return [
            COTTON_TAXONOMY_MAP.get(c, {}).get("canonical_condition", c)
            for c in self.raw_classes
        ]

    def get_metadata(self) -> Dict[str, Any]:
        return self.metadata

    def predict(self, pil_image: Image.Image) -> SpecialistPrediction:
        """Execute vision inference and return canonical SpecialistPrediction."""
        if not self.is_available():
            raise RuntimeError("Cotton specialist model is not available or not loaded.")

        t0 = time.time()
        tensor = self.transform(pil_image).unsqueeze(0).to(self.device)

        with torch.no_grad():
            logits = self.model(tensor)
            # Temperature scaling (T=1.2) to prevent overconfident softmax in closed 4-class set
            scaled_logits = logits / 1.2
            calibrated_probs = torch.softmax(scaled_logits, dim=-1).squeeze(0)
            raw_probs = torch.softmax(logits, dim=-1).squeeze(0)

        latency_ms = (time.time() - t0) * 1000.0

        candidates: List[SpecialistCandidate] = []
        for idx, (raw_cls, raw_p, cal_p) in enumerate(zip(self.raw_classes, raw_probs, calibrated_probs)):
            tax = COTTON_TAXONOMY_MAP.get(raw_cls, {
                "canonical_condition": raw_cls.title(),
                "canonical_label": f"cotton::{raw_cls.title()}",
                "category": "disease" if "healthy" not in raw_cls.lower() else "healthy",
            })
            candidates.append(
                SpecialistCandidate(
                    raw_condition=raw_cls,
                    canonical_condition=tax["canonical_condition"],
                    canonical_label=tax["canonical_label"],
                    crop="Cotton",
                    category=tax["category"],
                    raw_score=round(float(raw_p.item()), 4),
                    calibrated_confidence=round(float(cal_p.item()), 4),
                    percentage=int(round(float(cal_p.item()) * 100)),
                )
            )

        # Sort candidates descending by calibrated confidence
        candidates.sort(key=lambda c: c.calibrated_confidence, reverse=True)
        top = candidates[0]

        return SpecialistPrediction(
            raw_condition=top.raw_condition,
            canonical_condition=top.canonical_condition,
            canonical_label=top.canonical_label,
            crop="Cotton",
            category=top.category,
            raw_score=top.raw_score,
            calibrated_confidence=top.calibrated_confidence,
            percentage=top.percentage,
            top_candidates=candidates,
            latency_ms=round(latency_ms, 2),
            model_identifier="FarmGuard/cotton-densenet121",
            provenance={
                "model_identifier": "FarmGuard/cotton-densenet121",
                "architecture": "DenseNet-121",
                "weights_hash": self.weights_hash,
                "latency_ms": round(latency_ms, 2),
                "device": self.device,
                "calibration_temperature": 1.2,
            },
        )
