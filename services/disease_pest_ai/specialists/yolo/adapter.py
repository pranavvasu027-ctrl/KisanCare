"""YOLOv11x Multi-Crop Spatial Detection Specialist Adapter.

Wraps JK-TK/PlantDiseaseDetection (YOLOv11x) as a spatial lesion detector
and secondary candidate validator across 37 crop species.
Part of KisanCare Unified Multi-Model Crop Disease Intelligence System.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional
from PIL import Image

from disease_pest_ai.models.disease.yolo_disease_adapter import YoloDiseaseAdapter
from disease_pest_ai.specialists.base import (
    BaseSpecialistAdapter,
    SpecialistCandidate,
    SpecialistPrediction,
)

logger = logging.getLogger("kisancare.specialists.yolo")


class YoloSpecialistAdapter(BaseSpecialistAdapter):
    """Adapter wrapping YOLOv11x for multi-crop lesion detection and spatial localization."""

    model_identifier: str = "JK-TK/PlantDiseaseDetection"
    crop: str = "Multi-Crop Spatial Detector"
    architecture: str = "YOLOv11x (Ultralytics)"
    license: str = "MIT"
    abstention_threshold: float = 0.20

    def __init__(self, device: Optional[str] = None):
        self.underlying_adapter = YoloDiseaseAdapter(device=device, auto_download=True)

    def is_available(self) -> bool:
        return self.underlying_adapter.is_available()

    def get_supported_classes(self) -> List[str]:
        return ["YOLOv11x 116-Class Combined Dataset (37 Crops)"]

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "model_identifier": self.model_identifier,
            "crop": self.crop,
            "architecture": self.architecture,
            "num_classes": 116,
            "license": self.license,
            "role": "spatial_lesion_detector_and_candidate_generator",
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
            raw_condition="No focal lesions detected",
            canonical_condition="No focal lesions detected",
            canonical_label="yolo::no_lesions",
            crop=requested_crop or "Unknown",
            category="healthy",
            raw_score=0.10,
            calibrated_confidence=0.10,
            percentage=10,
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
