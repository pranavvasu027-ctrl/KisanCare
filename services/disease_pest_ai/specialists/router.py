"""Focused Two-Crop Specialist Router.

Routes foliar disease queries exclusively to the verified model for Cotton or Soybean:
- Cotton  -> FarmGuard/cotton-densenet121 (DenseNet-121)
- Soybean -> ixrbhii/soybean-disease-convnext (ConvNeXt-Small)

All other crops are strictly rejected/abstained with reason 'unsupported_crop'.
No third model or generalist fallback is loaded or called.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from PIL import Image

from disease_pest_ai.specialists.base import (
    BaseSpecialistAdapter,
    SpecialistPrediction,
)
from disease_pest_ai.specialists.registry import specialist_registry

logger = logging.getLogger("kisancare.specialists.router")

SUPPORTED_CROPS = {"Cotton", "Soybean"}


@dataclass
class FusedDiagnosticResult:
    """Standardized result produced by specialist routing."""
    condition: str
    canonical_label: str
    crop: str
    category: str  # 'disease' | 'healthy' | 'inconclusive'
    raw_score: float
    calibrated_confidence: float
    confidence_percent: int
    is_healthy: bool
    abstention: bool
    abstention_reason: Optional[str]
    routing_path: str  # 'cotton_specialist' | 'soybean_specialist' | 'unsupported' | 'error'
    model_identifier: str
    specialist_agreement: Optional[bool]
    fusion_outcome: str  # 'single_model' | 'unsupported_crop' | 'insufficient_evidence' | 'execution_failure'
    fusion_details: Dict[str, Any] = field(default_factory=dict)
    competing_predictions: List[Dict[str, Any]] = field(default_factory=list)
    all_candidates: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    scientific_name: Optional[str] = None
    latency_ms: float = 0.0


class MultiCropSpecialistRouter:
    """Router dedicated exclusively to Cotton and Soybean neural specialists."""

    def __init__(self, registry=None):
        self.registry = registry or specialist_registry

    def route(
        self,
        image: Image.Image,
        declared_crop: str,
        confidence_threshold: Optional[float] = None,
    ) -> FusedDiagnosticResult:
        """Route to Cotton DenseNet or Soybean ConvNeXt. Reject any other crop."""
        t0 = time.time()
        crop_clean = declared_crop.strip().title() if declared_crop else "Unknown"

        # 1. Enforce strict crop restriction: ONLY Cotton and Soybean are supported
        if crop_clean not in SUPPORTED_CROPS:
            elapsed_ms = (time.time() - t0) * 1000.0
            return FusedDiagnosticResult(
                condition=f"Unsupported foliar host crop: '{crop_clean}'",
                canonical_label=f"{crop_clean.lower()}::unsupported",
                crop=crop_clean,
                category="inconclusive",
                raw_score=0.0,
                calibrated_confidence=0.0,
                confidence_percent=0,
                is_healthy=False,
                abstention=True,
                abstention_reason="unsupported_crop",
                routing_path="unsupported",
                model_identifier="None",
                specialist_agreement=None,
                fusion_outcome="unsupported_crop",
                warnings=[
                    f"Crop '{crop_clean}' is not supported. Active disease detection strictly supports Cotton and Soybean.",
                    "No fallback model is used to prevent misclassification."
                ],
                latency_ms=round(elapsed_ms, 2),
            )

        # 2. Retrieve verified specialist adapter
        adapter: Optional[BaseSpecialistAdapter] = self.registry.get_specialist(crop_clean)
        if adapter is None or not adapter.is_available():
            elapsed_ms = (time.time() - t0) * 1000.0
            return FusedDiagnosticResult(
                condition=f"{crop_clean} specialist weights not loaded or unavailable",
                canonical_label=f"{crop_clean.lower()}::execution_failure",
                crop=crop_clean,
                category="inconclusive",
                raw_score=0.0,
                calibrated_confidence=0.0,
                confidence_percent=0,
                is_healthy=False,
                abstention=True,
                abstention_reason="model_unavailable",
                routing_path="error",
                model_identifier="None",
                specialist_agreement=None,
                fusion_outcome="execution_failure",
                warnings=[f"Model checkpoint for {crop_clean} specialist could not be loaded."],
                latency_ms=round(elapsed_ms, 2),
            )

        # 3. Ensure valid PIL image
        pil_image = image
        if not isinstance(image, Image.Image):
            try:
                from disease_pest_ai.models.base import load_image_to_pil
                pil_image = load_image_to_pil(image)
            except Exception as err:
                logger.warning("Failed to convert image to PIL: %s", err)
                elapsed_ms = (time.time() - t0) * 1000.0
                return FusedDiagnosticResult(
                    condition="Invalid image payload",
                    canonical_label=f"{crop_clean.lower()}::invalid_image",
                    crop=crop_clean,
                    category="inconclusive",
                    raw_score=0.0,
                    calibrated_confidence=0.0,
                    confidence_percent=0,
                    is_healthy=False,
                    abstention=True,
                    abstention_reason="invalid_image",
                    routing_path="error",
                    model_identifier=adapter.model_identifier,
                    specialist_agreement=None,
                    fusion_outcome="execution_failure",
                    warnings=["Could not decode uploaded image into valid PIL Image."],
                    latency_ms=round(elapsed_ms, 2),
                )

        # 4. Execute dedicated specialist inference
        try:
            pred: SpecialistPrediction = adapter.predict(pil_image, requested_crop=crop_clean)
        except Exception as e:
            logger.error("Inference failed for %s specialist (%s): %s", crop_clean, adapter.model_identifier, e, exc_info=True)
            elapsed_ms = (time.time() - t0) * 1000.0
            return FusedDiagnosticResult(
                condition=f"Inference error in {crop_clean} specialist",
                canonical_label=f"{crop_clean.lower()}::inference_error",
                crop=crop_clean,
                category="inconclusive",
                raw_score=0.0,
                calibrated_confidence=0.0,
                confidence_percent=0,
                is_healthy=False,
                abstention=True,
                abstention_reason="inference_error",
                routing_path="error",
                model_identifier=adapter.model_identifier,
                specialist_agreement=None,
                fusion_outcome="execution_failure",
                warnings=[f"Inference execution error: {str(e)}"],
                latency_ms=round(elapsed_ms, 2),
            )

        # 5. Evaluate confidence threshold & abstention
        thresh = confidence_threshold if confidence_threshold is not None else adapter.abstention_threshold
        is_abstain = pred.is_abstaining or (pred.calibrated_confidence < thresh)
        abstain_reason = pred.abstention_reason or ("low_confidence" if is_abstain else None)
        fusion_outcome = "single_model" if not is_abstain else "insufficient_evidence"

        # Format candidates
        all_candidates_flat: List[Dict[str, Any]] = []
        for c in pred.top_candidates:
            all_candidates_flat.append({
                "condition": c.canonical_condition,
                "crop": c.crop,
                "percentage": c.percentage,
                "probability": round(c.calibrated_confidence, 4),
                "category": c.category,
                "model_identifier": pred.model_identifier,
                "scientific_name": c.scientific_name,
            })

        routing_tag = f"{crop_clean.lower()}_specialist"
        elapsed_ms = (time.time() - t0) * 1000.0

        return FusedDiagnosticResult(
            condition=pred.canonical_condition,
            canonical_label=pred.canonical_label,
            crop=crop_clean,
            category=pred.category,
            raw_score=round(pred.raw_score, 4),
            calibrated_confidence=round(pred.calibrated_confidence, 4),
            confidence_percent=pred.percentage,
            is_healthy="healthy" in pred.canonical_condition.lower(),
            abstention=is_abstain,
            abstention_reason=abstain_reason,
            routing_path=routing_tag,
            model_identifier=pred.model_identifier,
            specialist_agreement=None,
            fusion_outcome=fusion_outcome,
            competing_predictions=[{
                "model_identifier": pred.model_identifier,
                "architecture": adapter.architecture,
                "crop": crop_clean,
                "top_condition": pred.canonical_condition,
                "confidence_percent": pred.percentage,
                "calibrated_confidence": round(pred.calibrated_confidence, 4),
                "category": pred.category,
                "is_abstaining": is_abstain,
            }],
            all_candidates=all_candidates_flat,
            scientific_name=pred.scientific_name,
            warnings=["Confidence below safety threshold; chemical treatment withheld."] if is_abstain else [],
            latency_ms=round(elapsed_ms, 2),
        )


# Global singleton router instance
intelligent_router = MultiCropSpecialistRouter()
