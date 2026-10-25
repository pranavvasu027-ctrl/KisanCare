"""Intelligent Multi-Crop Router and Prediction Fusion Engine.

Implements Phase 3 safer disagreement handling and consensus logic:
- 'agree': Eligible models concordantly diagnose the same canonical pathology.
- 'disputed': Eligible models disagree on disease (abstains, strictly zero chemical pesticide).
- 'crop_uncertain': Visual symptoms conflict with declared host crop (abstains, zero chemical pesticide).
- 'insufficient_evidence': Low confidence / out-of-distribution (abstains, zero chemical pesticide).
- 'single_model': Only one eligible model contributes with validated criteria.

Part of KisanCare Unified Multi-Model Crop Disease Intelligence System.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from PIL import Image

from disease_pest_ai.specialists.base import (
    BaseSpecialistAdapter,
    SpecialistCandidate,
    SpecialistPrediction,
)
from disease_pest_ai.specialists.registry import specialist_registry

logger = logging.getLogger("kisancare.specialists.router")

SUPPORTED_CROPS = {"Cotton", "Soybean"}


@dataclass
class FusedDiagnosticResult:
    """Standardized result produced by routing and multi-model prediction fusion."""
    condition: str
    canonical_label: str
    crop: str
    category: str  # 'disease' | 'healthy' | 'pest' | 'deficiency' | 'inconclusive'
    raw_score: float
    calibrated_confidence: float
    confidence_percent: int
    is_healthy: bool
    abstention: bool
    abstention_reason: Optional[str]
    routing_path: str  # 'specialist_fused' | 'specialist_solo' | 'generalist_fallback'
    model_identifier: str
    specialist_agreement: Optional[bool]
    fusion_outcome: str  # 'agree' | 'disputed' | 'crop_uncertain' | 'insufficient_evidence' | 'single_model'
    fusion_details: Dict[str, Any] = field(default_factory=dict)
    competing_predictions: List[Dict[str, Any]] = field(default_factory=list)
    all_candidates: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    scientific_name: Optional[str] = None
    latency_ms: float = 0.0


class MultiCropSpecialistRouter:
    """Intelligent router that resolves host crops, invokes specialists, and evaluates consensus."""

    def __init__(self, registry=None):
        self.registry = registry or specialist_registry

    def route(
        self,
        image: Image.Image,
        declared_crop: str,
        confidence_threshold: float = 0.40,
    ) -> FusedDiagnosticResult:
        """Execute crop-aware routing, run eligible models, and perform consensus fusion."""
        t0 = time.time()
        crop_clean = declared_crop.strip().title() if declared_crop else "Unknown"

        eligible_models = self.registry.get_eligible_specialists(crop_clean)

        # 1. Unknown or Unsupported Crop Handling
        if not eligible_models:
            elapsed_ms = (time.time() - t0) * 1000.0
            return FusedDiagnosticResult(
                condition=f"Unsupported foliar host crop or unknown variety: '{crop_clean}'",
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
                fusion_outcome="insufficient_evidence",
                warnings=[f"Crop '{crop_clean}' is not supported by any active neural specialist."],
                latency_ms=round(elapsed_ms, 2),
            )

        # 2. Run Inference Across Eligible Models
        pil_image = image
        if not isinstance(image, Image.Image):
            try:
                from disease_pest_ai.models.base import load_image_to_pil
                pil_image = load_image_to_pil(image)
            except Exception as err:
                logger.warning("Failed to load image to PIL: %s", err)

        model_predictions: List[SpecialistPrediction] = []
        for adapter in eligible_models:
            try:
                pred = adapter.predict(pil_image, requested_crop=crop_clean)
                model_predictions.append(pred)
            except Exception as e:
                logger.warning("Error running specialist %s: %s", adapter.model_identifier, e)

        if not model_predictions:
            elapsed_ms = (time.time() - t0) * 1000.0
            return FusedDiagnosticResult(
                condition="Specialist models failed to initialize or execute",
                canonical_label=f"{crop_clean.lower()}::execution_failure",
                crop=crop_clean,
                category="inconclusive",
                raw_score=0.0,
                calibrated_confidence=0.0,
                confidence_percent=0,
                is_healthy=False,
                abstention=True,
                abstention_reason="execution_failure",
                routing_path="error",
                model_identifier="None",
                specialist_agreement=None,
                fusion_outcome="insufficient_evidence",
                warnings=["Model weights or dependencies unavailable."],
                latency_ms=round(elapsed_ms, 2),
            )

        # 3. Compile Competing Predictions
        competing: List[Dict[str, Any]] = []
        all_candidates_flat: List[Dict[str, Any]] = []
        for p in model_predictions:
            competing.append({
                "model_identifier": p.model_identifier,
                "crop": p.crop,
                "top_condition": p.canonical_condition,
                "confidence_percent": p.percentage,
                "raw_score": p.raw_score,
                "category": p.category,
                "is_abstaining": p.is_abstaining,
            })
            for c in p.top_candidates[:5]:
                all_candidates_flat.append({
                    "condition": c.canonical_condition,
                    "crop": c.crop,
                    "percentage": c.percentage,
                    "probability": c.calibrated_confidence,
                    "category": c.category,
                    "model_identifier": p.model_identifier,
                })

        # 4. Host Crop Conflict Check
        # If top prediction strongly diagnoses a different crop with high certainty
        lead_pred = model_predictions[0]
        crop_conflict = False
        if lead_pred.crop.lower() != "multi-crop" and lead_pred.crop.lower() != crop_clean.lower():
            if lead_pred.calibrated_confidence >= 0.50 and lead_pred.category == "disease":
                crop_conflict = True

        if crop_conflict:
            elapsed_ms = (time.time() - t0) * 1000.0
            return FusedDiagnosticResult(
                condition=f"Host Crop Conflict: Visual symptoms indicate '{lead_pred.crop}' rather than declared '{crop_clean}'",
                canonical_label=f"{crop_clean.lower()}::crop_conflict",
                crop=crop_clean,
                category="inconclusive",
                raw_score=lead_pred.raw_score,
                calibrated_confidence=lead_pred.calibrated_confidence,
                confidence_percent=lead_pred.percentage,
                is_healthy=False,
                abstention=True,
                abstention_reason="conflicting_crop",
                routing_path="crop_conflict_abstain",
                model_identifier=lead_pred.model_identifier,
                specialist_agreement=False,
                fusion_outcome="crop_uncertain",
                competing_predictions=competing,
                all_candidates=all_candidates_flat,
                warnings=[
                    f"Declared crop '{crop_clean}' conflicts with visual classification '{lead_pred.crop}'.",
                    "Chemical recommendations strictly withheld to avoid phytotoxic crop injury."
                ],
                latency_ms=round(elapsed_ms, 2),
            )

        # 5. Multi-Model Consensus Evaluation
        if len(model_predictions) > 1:
            p1 = model_predictions[0]
            p2 = model_predictions[1]

            # If both models abstain
            if p1.is_abstaining and p2.is_abstaining:
                is_abstain = True
                outcome = "insufficient_evidence"
                abstain_reason = "low_confidence"
                fused_conf = max(p1.calibrated_confidence, p2.calibrated_confidence)
                final_condition = p1.canonical_condition
                attribution = f"{p1.model_identifier} + {p2.model_identifier}"
                agreement_flag = None
                sci_name = p1.scientific_name
            # If only secondary model abstains (e.g. YOLO detects no lesion), lead specialist prevails
            elif not p1.is_abstaining and p2.is_abstaining:
                is_abstain = False
                outcome = "single_model"
                abstain_reason = None
                fused_conf = p1.calibrated_confidence
                final_condition = p1.canonical_condition
                attribution = f"{p1.model_identifier} (Secondary {p2.model_identifier} unconfirmed)"
                agreement_flag = None
                sci_name = p1.scientific_name
            # If only lead specialist abstains, secondary model provides signal
            elif p1.is_abstaining and not p2.is_abstaining:
                is_abstain = False
                outcome = "single_model"
                abstain_reason = None
                fused_conf = p2.calibrated_confidence
                final_condition = p2.canonical_condition
                attribution = f"{p2.model_identifier} (Lead {p1.model_identifier} abstaining)"
                agreement_flag = None
                sci_name = p2.scientific_name
            else:
                # Both models produced confident predictions
                cond1 = p1.canonical_condition.lower().strip()
                cond2 = p2.canonical_condition.lower().strip()

                agree = (cond1 == cond2 or cond1 in cond2 or cond2 in cond1)
                if agree:
                    fused_conf = max(p1.calibrated_confidence, p2.calibrated_confidence)
                    is_abstain = fused_conf < confidence_threshold
                    outcome = "agree" if not is_abstain else "insufficient_evidence"
                    abstain_reason = "low_confidence" if is_abstain else None
                    attribution = f"{p1.model_identifier} + {p2.model_identifier} (Concordant Agreement)"
                    agreement_flag = True
                    final_condition = p1.canonical_condition
                    sci_name = p1.scientific_name or p2.scientific_name
                else:
                    # Disagreement! Competing models support incompatible diseases
                    is_abstain = True
                    outcome = "disputed"
                    abstain_reason = "disputed_diagnosis"
                    agreement_flag = False
                    fused_conf = max(p1.calibrated_confidence, p2.calibrated_confidence)
                    final_condition = f"Diagnostic Disagreement: Conflicting foliar symptoms diagnosed on {crop_clean}"
                    attribution = f"{p1.model_identifier} vs {p2.model_identifier} (Disputed Disagreement)"
                    sci_name = None

            routing_path = "specialist_fused"
        else:
            # Single model path
            p = model_predictions[0]
            is_abstain = p.is_abstaining or p.calibrated_confidence < confidence_threshold
            outcome = "single_model" if not is_abstain else "insufficient_evidence"
            abstain_reason = "low_confidence" if is_abstain else None
            fused_conf = p.calibrated_confidence
            final_condition = p.canonical_condition
            attribution = f"{p.model_identifier} (Specialist Solo)"
            agreement_flag = None
            routing_path = "specialist_solo"
            sci_name = p.scientific_name

        elapsed_ms = (time.time() - t0) * 1000.0
        return FusedDiagnosticResult(
            condition=final_condition,
            canonical_label=f"{crop_clean.lower()}::{final_condition.lower()}",
            crop=crop_clean,
            category="healthy" if "healthy" in final_condition.lower() else "disease",
            raw_score=fused_conf,
            calibrated_confidence=fused_conf,
            confidence_percent=int(round(fused_conf * 100)),
            is_healthy="healthy" in final_condition.lower(),
            abstention=is_abstain,
            abstention_reason=abstain_reason,
            routing_path=routing_path,
            model_identifier=attribution,
            specialist_agreement=agreement_flag,
            fusion_outcome=outcome,
            competing_predictions=competing,
            all_candidates=all_candidates_flat,
            scientific_name=sci_name,
            latency_ms=round(elapsed_ms, 2),
        )


# Global singleton router instance
intelligent_router = MultiCropSpecialistRouter()
