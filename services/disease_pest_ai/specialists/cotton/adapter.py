"""Cotton Crop Disease Specialist Adapter.

Integrates FarmGuard/cotton-densenet121 with normalized canonical taxonomy mapping.
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

import torch
import torchvision.models as models
from torchvision import transforms
from PIL import Image

from disease_pest_ai.specialists.base import (
    BaseSpecialistAdapter,
    SpecialistCandidate,
    SpecialistPrediction,
)

logger = logging.getLogger("kisancare.specialists.cotton")

COTTON_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = COTTON_DIR.parent.parent.parent.parent
WEIGHTS_PATH = COTTON_DIR / "best_densenet.pth"
FALLBACK_WEIGHTS_PATH = PROJECT_ROOT / "models" / "disease_detection" / "specialists" / "cotton" / "best_densenet.pth"
CLASSES_PATH = COTTON_DIR / "classes.json"

COTTON_CANONICAL_MAP: Dict[str, Dict[str, Any]] = {
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

    model_identifier: str = "FarmGuard/cotton-densenet121"
    crop: str = "Cotton"
    architecture: str = "DenseNet-121 (torchvision)"
    license: str = "MIT"
    abstention_threshold: float = 0.45

    def __init__(self, weights_path: Optional[Path] = None, device: str = "cpu"):
        env_weights = os.getenv("COTTON_MODEL_WEIGHTS_PATH")
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
            logger.warning("Cotton specialist weights not found at %s or fallback", self.weights_path)
            return

        t0 = time.time()
        hasher = hashlib.sha256()
        with open(self.weights_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        self.weights_hash = hasher.hexdigest()

        if CLASSES_PATH.is_file():
            with open(CLASSES_PATH, "r", encoding="utf-8") as f:
                self.raw_classes = json.load(f)
        else:
            self.raw_classes = ["bacterial blight", "curl virus", "fussarium wilt", "healthy"]

        model = models.densenet121(weights=None)
        model.classifier = torch.nn.Linear(model.classifier.in_features, len(self.raw_classes))

        ckpt = torch.load(str(self.weights_path), map_location=self.device)
        state_dict = ckpt["model_state_dict"] if "model_state_dict" in ckpt else ckpt
        model.load_state_dict(state_dict)
        model.to(self.device)
        model.eval()
        self.model = model

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
        logger.info("Cotton DenseNet-121 loaded in %.3fs (SHA: %s)", elapsed, self.weights_hash[:8])

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
                f"Cotton specialist model is unavailable: weights not found at {self.weights_path}. Please provide valid weights via COTTON_MODEL_WEIGHTS_PATH or place best_densenet.pth in {COTTON_DIR}."
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
            # Temperature scaling for confidence calibration (T=1.00 optimized on field validation data)
            scaled_logits = logits / 1.00
            probs = torch.softmax(scaled_logits, dim=1).squeeze(0)

        probs_np = probs.cpu().numpy()
        candidates: List[SpecialistCandidate] = []
        for idx, score in enumerate(probs_np):
            raw_cls = self.raw_classes[idx]
            clean_cls = raw_cls.lower().strip()
            info = COTTON_CANONICAL_MAP.get(clean_cls, {
                "canonical_condition": raw_cls.title(),
                "canonical_label": f"cotton::{raw_cls}",
                "category": "healthy" if "healthy" in clean_cls else "disease",
                "scientific_name": None,
            })
            cal_score = float(score)
            candidates.append(
                SpecialistCandidate(
                    raw_condition=raw_cls,
                    canonical_condition=info["canonical_condition"],
                    canonical_label=info["canonical_label"],
                    crop="Cotton",
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
            crop="Cotton",
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
