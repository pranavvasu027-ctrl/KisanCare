"""Generalist Crop Disease Specialist Adapter (EfficientNetV2-S).

Wraps BiernyVR/crop-disease-classifier to provide specialist interface
for Tomato, Potato, Corn, Grape, Apple, Peach, Pepper, Cherry, Strawberry, Squash.
Part of KisanCare Unified Multi-Model Crop Disease Intelligence System.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from PIL import Image

from disease_pest_ai.models.disease.efficientnet_adapter import (
    EfficientNetDiseaseAdapter,
    parse_plantvillage_class,
)
from disease_pest_ai.specialists.base import (
    BaseSpecialistAdapter,
    SpecialistCandidate,
    SpecialistPrediction,
)

logger = logging.getLogger("kisancare.specialists.generalist")


class GeneralistEfficientNetAdapter(BaseSpecialistAdapter):
    """Adapter wrapping 38-class EfficientNetV2-S for supported multi-crop foliar diagnosis."""

    model_identifier: str = "BiernyVR/crop-disease-classifier"
    crop: str = "Multi-Crop Generalist"
    architecture: str = "EfficientNetV2-S (torchvision)"
    license: str = "MIT"
    abstention_threshold: float = 0.40

    def __init__(self, device: Optional[str] = None):
        self.underlying_adapter = EfficientNetDiseaseAdapter(device=device, auto_download=True)
        self.raw_classes = list(self.underlying_adapter.classes) if hasattr(self.underlying_adapter, "classes") else []

    def is_available(self) -> bool:
        return self.underlying_adapter.is_available()

    def get_supported_classes(self) -> List[str]:
        return list(self.raw_classes)

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "model_identifier": self.model_identifier,
            "crop": self.crop,
            "architecture": self.architecture,
            "num_classes": len(self.raw_classes),
            "classes": self.raw_classes,
            "license": self.license,
            "abstention_threshold": self.abstention_threshold,
        }

    def predict(self, image: Image.Image, requested_crop: Optional[str] = None) -> SpecialistPrediction:
        if not self.is_available():
            raise RuntimeError(f"{self.model_identifier} model not loaded. Check weights.")

        t0 = time.time()
        res = self.underlying_adapter.predict(image, crop_name=requested_crop)
        elapsed_ms = (time.time() - t0) * 1000.0

        candidates: List[SpecialistCandidate] = []
        for tp in res.top_predictions:
            candidates.append(
                SpecialistCandidate(
                    raw_condition=tp.condition,
                    canonical_condition=tp.condition,
                    canonical_label=f"{tp.crop.lower()}::{tp.condition.lower()}",
                    crop=tp.crop,
                    category="healthy" if tp.condition_type.value == "healthy" else "disease",
                    raw_score=float(tp.score),
                    calibrated_confidence=float(tp.score),
                    percentage=int(round(float(tp.score) * 100)),
                    scientific_name=None,
                )
            )

        top = candidates[0] if candidates else SpecialistCandidate(
            raw_condition="Unknown",
            canonical_condition="Unknown",
            canonical_label="unknown::unknown",
            crop=requested_crop or "Unknown",
            category="disease",
            raw_score=0.0,
            calibrated_confidence=0.0,
            percentage=0,
        )

        is_abstaining = top.calibrated_confidence < self.abstention_threshold
        abstention_reason = "low_confidence" if is_abstaining else None

        return SpecialistPrediction(
            raw_condition=top.raw_condition,
            canonical_condition=top.canonical_condition,
            canonical_label=top.canonical_label,
            crop=top.crop,
            category=top.category,
            raw_score=top.raw_score,
            calibrated_confidence=top.calibrated_confidence,
            percentage=top.percentage,
            scientific_name=top.scientific_name,
            top_candidates=candidates,
            latency_ms=round(elapsed_ms, 2),
            model_identifier=self.model_identifier,
            weights_hash=self.underlying_adapter.model_version,
            is_abstaining=is_abstaining,
            abstention_reason=abstention_reason,
        )
