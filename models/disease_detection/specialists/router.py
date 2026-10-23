"""Intelligent Router and Prediction Fusion Engine with Explicit Outcomes.

Implements Phase 3 safer disagreement handling:
- 'agree': Eligible models support the same canonical diagnosis.
- 'disputed': Eligible models disagree on disease (abstains, no chemical pesticide).
- 'crop_uncertain': Models disagree on host crop (abstains, no chemical pesticide).
- 'insufficient_evidence': Low confidence / out-of-distribution (abstains, no chemical pesticide).
- 'single_model': Only one eligible model contributes with validated criteria.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from PIL import Image

try:
    from models.disease_detection.specialists.base import (
        BaseSpecialistAdapter,
        SpecialistCandidate,
        SpecialistPrediction,
    )
    from models.disease_detection.specialists.registry import specialist_registry
except ImportError:
    from specialists.base import (
        BaseSpecialistAdapter,
        SpecialistCandidate,
        SpecialistPrediction,
    )
    from specialists.registry import specialist_registry

logger = logging.getLogger("kisancare.specialists.router")


@dataclass
class FusedDiagnosticResult:
    """Standardized result produced by routing and prediction fusion."""
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
    disease_candidates: List[Dict[str, Any]] = field(default_factory=list)
    pest_candidates: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    latency_ms: float = 0.0


def normalize_condition_name(raw_name: str) -> str:
    """Normalize strings for fuzzy condition comparison."""
    return (
        raw_name.lower()
        .replace("_", " ")
        .replace("-", " ")
        .replace("fussarium", "fusarium")
        .replace("cotton leaf curl virus", "curl virus")
        .replace("asian soybean rust", "rust")
        .replace("soybean rust", "rust")
        .replace("brown spot (septoria)", "septoria")
        .replace("septoria brown spot", "septoria")
        .strip()
    )


class IntelligentRouter:
    """Intelligent router and fusion coordinator for multi-model plant disease intelligence."""

    def __init__(self, registry=specialist_registry):
        self.registry = registry

    def route_and_fuse(
        self,
        pil_image: Image.Image,
        declared_crop: str,
        generalist_engine: Any,
        abstention_threshold: float = 0.40,
    ) -> FusedDiagnosticResult:
        """Route input image to appropriate specialist and/or generalist and perform prediction fusion."""
        has_specialist = self.registry.has_specialist(declared_crop)
        specialist = self.registry.get_specialist(declared_crop) if has_specialist else None

        # 1. Execute Generalist Multi-Crop Inference
        gen_preds: List[Tuple[str, float]] = []
        gen_latency: float = 0.0
        if generalist_engine is not None:
            try:
                gen_preds, gen_latency = generalist_engine.predict(pil_image)
            except Exception as exc:
                logger.warning("Generalist engine failed during fusion: %s", exc)

        # 2. Case: No specialist available -> Pure Generalist Routing
        if specialist is None:
            return self._format_generalist_result(
                gen_preds=gen_preds,
                declared_crop=declared_crop,
                generalist_engine=generalist_engine,
                latency_ms=gen_latency,
                threshold=abstention_threshold,
            )

        # 3. Case: Specialist Available -> Execute Specialist Inference
        spec_pred: Optional[SpecialistPrediction] = None
        spec_error: Optional[str] = None
        try:
            spec_pred = specialist.predict(pil_image)
        except Exception as exc:
            logger.error("Specialist %s inference failed: %s", declared_crop, exc)
            spec_error = str(exc)

        # If specialist execution failed, gracefully fall back to generalist
        if spec_pred is None:
            res = self._format_generalist_result(
                gen_preds=gen_preds,
                declared_crop=declared_crop,
                generalist_engine=generalist_engine,
                latency_ms=gen_latency,
                threshold=abstention_threshold,
            )
            res.warnings.append(f"Specialist fallback: {declared_crop} specialist unavailable ({spec_error}). Used generalist.")
            return res

        # 4. Prediction Fusion: Compare Specialist and Generalist with Explicit Outcomes
        return self._fuse_predictions(
            spec_pred=spec_pred,
            gen_preds=gen_preds,
            declared_crop=declared_crop,
            abstention_threshold=abstention_threshold,
            spec_latency=spec_pred.latency_ms,
            gen_latency=gen_latency,
        )

    def _fuse_predictions(
        self,
        spec_pred: SpecialistPrediction,
        gen_preds: List[Tuple[str, float]],
        declared_crop: str,
        abstention_threshold: float,
        spec_latency: float,
        gen_latency: float,
    ) -> FusedDiagnosticResult:
        """Perform cross-model agreement evaluation and calibrated fusion with explicit outcomes."""
        warnings: List[str] = []
        notes: List[str] = []
        competing: List[Dict[str, Any]] = []

        spec_cond_norm = normalize_condition_name(spec_pred.canonical_condition)
        spec_is_healthy = (spec_pred.category == "healthy")

        # Parse generalist candidates
        gen_top_label = gen_preds[0][0] if gen_preds else "Unknown"
        gen_top_prob = gen_preds[0][1] if gen_preds else 0.0

        gen_crop_norm = declared_crop.strip().lower()
        gen_matching_crop_candidates = []
        gen_pest_candidates = []

        for label, prob in gen_preds:
            if "::" in label:
                c_crop, c_cond = label.split("::", 1)
            else:
                c_crop, c_cond = "Unknown", label

            cond_lower = c_cond.lower()
            if any(term in cond_lower for term in ["(pest)", "pest", "weevil", "borer", "aphid", "mite", "thrips", "whitefly"]):
                gen_pest_candidates.append({
                    "crop": c_crop.replace("_", " ").title(),
                    "condition": c_cond,
                    "category": "pest",
                    "task": "foliar_classification",
                    "source_model": "India Multi-Crop DINOv2 ViT-B/14",
                    "probability": round(prob, 4),
                    "percentage": int(round(prob * 100)),
                })

            if c_crop.lower() == gen_crop_norm:
                gen_matching_crop_candidates.append((c_cond, prob))

        # Check for Strong Crop Mismatch from Generalist (e.g. apple scab uploaded with crop=Cotton)
        gen_top_crop = gen_top_label.split("::", 1)[0].replace("_", " ").lower() if "::" in gen_top_label else "unknown"
        crop_conflict = (
            gen_top_prob >= 0.55
            and gen_top_crop != "unknown"
            and gen_top_crop != gen_crop_norm
            and spec_pred.calibrated_confidence < 0.60
        )

        # Flag separate pest detections if present in generalist
        if gen_pest_candidates and not spec_is_healthy:
            top_pest = gen_pest_candidates[0]
            if top_pest["probability"] >= 0.15:
                warnings.append(
                    f"Concurrent Foliar Pest Alert: Generalist detected visual signs of {top_pest['condition']} "
                    f"({top_pest['percentage']}%) alongside foliar pathology."
                )

        # Prepare unified candidate list
        all_candidates = []
        for cand in spec_pred.top_candidates:
            all_candidates.append({
                "condition": cand.canonical_condition,
                "crop": declared_crop,
                "category": cand.category,
                "task": "foliar_classification",
                "source_model": spec_pred.model_identifier,
                "probability": cand.calibrated_confidence,
                "percentage": cand.percentage,
            })

        disease_candidates = [c for c in all_candidates if c["category"] == "disease"]
        total_latency = spec_latency + gen_latency
        fused_model_name = f"{spec_pred.model_identifier} + India Multi-Crop DINOv2 (Fused)"

        # --- OUTCOME EVALUATION ---

        # 1. Case: Crop Conflict / Crop Uncertain
        if crop_conflict:
            fusion_outcome = "crop_uncertain"
            abstain = True
            abstention_reason = "crop_uncertain"
            condition_str = "Host crop uncertain"
            competing = [
                {
                    "model": spec_pred.model_identifier,
                    "crop": declared_crop,
                    "condition": spec_pred.canonical_condition,
                    "score": spec_pred.calibrated_confidence,
                },
                {
                    "model": "India Multi-Crop DINOv2 ViT-B/14",
                    "crop": gen_top_crop.title(),
                    "condition": gen_top_label.split("::", 1)[-1] if "::" in gen_top_label else gen_top_label,
                    "score": round(gen_top_prob, 4),
                },
            ]
            warnings.append(
                f"Crop Conflict Detected: Declared host crop '{declared_crop}' conflicts with generalist visual classification '{gen_top_crop.title()}'. Diagnosis abstained."
            )
            return FusedDiagnosticResult(
                condition=condition_str,
                canonical_label=f"{declared_crop.lower()}::Disputed",
                crop=declared_crop,
                category="inconclusive",
                raw_score=spec_pred.raw_score,
                calibrated_confidence=spec_pred.calibrated_confidence,
                confidence_percent=spec_pred.percentage,
                is_healthy=False,
                abstention=True,
                abstention_reason=abstention_reason,
                routing_path="specialist_fused",
                model_identifier=fused_model_name,
                specialist_agreement=False,
                fusion_outcome=fusion_outcome,
                fusion_details={
                    "routing_path": "specialist_fused",
                    "fusion_outcome": fusion_outcome,
                    "concordance": "crop_conflict",
                    "specialist_agreement": False,
                    "notes": ["Declared crop conflicts with vision features. Abstaining from chemical advisory."],
                },
                competing_predictions=competing,
                all_candidates=all_candidates,
                disease_candidates=disease_candidates,
                pest_candidates=gen_pest_candidates[:3],
                warnings=warnings,
                latency_ms=round(total_latency, 2),
            )

        # 2. Case: Insufficient Evidence / Low Confidence
        if spec_pred.calibrated_confidence < abstention_threshold and gen_top_prob < abstention_threshold:
            fusion_outcome = "insufficient_evidence"
            abstain = True
            abstention_reason = "insufficient_evidence"
            warnings.append(
                f"Diagnostic Abstention: Highest candidate score ({spec_pred.percentage}%) is below "
                f"the {int(round(abstention_threshold * 100))}% safety threshold. Inadequate visual evidence."
            )
            return FusedDiagnosticResult(
                condition="Inconclusive foliar diagnosis",
                canonical_label=spec_pred.canonical_label,
                crop=declared_crop,
                category="inconclusive",
                raw_score=spec_pred.raw_score,
                calibrated_confidence=spec_pred.calibrated_confidence,
                confidence_percent=spec_pred.percentage,
                is_healthy=False,
                abstention=True,
                abstention_reason=abstention_reason,
                routing_path="specialist_fused",
                model_identifier=fused_model_name,
                specialist_agreement=None,
                fusion_outcome=fusion_outcome,
                fusion_details={
                    "routing_path": "specialist_fused",
                    "fusion_outcome": fusion_outcome,
                    "concordance": "insufficient_evidence",
                    "specialist_agreement": None,
                    "notes": ["Calibrated scores below threshold across candidate models."],
                },
                competing_predictions=[],
                all_candidates=all_candidates,
                disease_candidates=disease_candidates,
                pest_candidates=gen_pest_candidates[:3],
                warnings=warnings,
                latency_ms=round(total_latency, 2),
            )

        # 3. Check Agreement between Specialist and Generalist Crop Candidates
        agreement: Optional[bool] = None
        concordance: str = "specialist_dominant"

        if gen_matching_crop_candidates:
            gen_best_crop_cond, gen_best_crop_prob = gen_matching_crop_candidates[0]
            gen_cond_norm = normalize_condition_name(gen_best_crop_cond)

            # Both models identified condition on the same crop
            if spec_cond_norm in gen_cond_norm or gen_cond_norm in spec_cond_norm:
                agreement = True
                fusion_outcome = "agree"
                concordance = "concordant"
                notes.append(f"Strong cross-model concordance: Both specialist and generalist agree on {spec_pred.canonical_condition}.")
            else:
                agreement = False
                fusion_outcome = "disputed"
                concordance = "disputed"
                competing = [
                    {
                        "model": spec_pred.model_identifier,
                        "crop": declared_crop,
                        "condition": spec_pred.canonical_condition,
                        "score": spec_pred.calibrated_confidence,
                    },
                    {
                        "model": "India Multi-Crop DINOv2 ViT-B/14",
                        "crop": declared_crop,
                        "condition": gen_best_crop_cond,
                        "score": round(gen_best_crop_prob, 4),
                    },
                ]
                notes.append(
                    f"Cross-model discrepancy: Specialist diagnosed '{spec_pred.canonical_condition}' ({spec_pred.percentage}%), "
                    f"while generalist crop head suggested '{gen_best_crop_cond}' ({int(round(gen_best_crop_prob * 100))}%)."
                )
                warnings.append(
                    f"Diagnostic Disagreement: Models conflict on {declared_crop} foliar diagnosis. Definitive chemical recommendation withheld."
                )
        else:
            # Generalist probability mass was diffused across out-of-crop classes
            # Only the crop specialist contributed confident evidence
            agreement = None
            fusion_outcome = "single_model"
            concordance = "specialist_isolated"
            notes.append(
                f"Single-model diagnostic contribution: Generalist distributed probability mass across 387 classes (top: {gen_top_label} at {int(round(gen_top_prob * 100))}%)."
            )

        # MANDATORY SAFETY RULE:
        # For 'disputed', 'crop_uncertain' and 'insufficient_evidence', abstain from definitive diagnosis!
        if fusion_outcome in ["disputed", "crop_uncertain", "insufficient_evidence"]:
            abstain = True
            abstention_reason = fusion_outcome
            condition_str = (
                "Disputed foliar diagnosis"
                if fusion_outcome == "disputed"
                else ("Host crop uncertain" if fusion_outcome == "crop_uncertain" else "Inconclusive foliar diagnosis")
            )
        else:
            # 'agree' or 'single_model'
            if spec_pred.calibrated_confidence < abstention_threshold:
                abstain = True
                abstention_reason = "insufficient_evidence"
                condition_str = "Inconclusive foliar diagnosis"
                fusion_outcome = "insufficient_evidence"
            else:
                abstain = False
                abstention_reason = None
                condition_str = spec_pred.canonical_condition

        return FusedDiagnosticResult(
            condition=condition_str,
            canonical_label=spec_pred.canonical_label,
            crop=declared_crop,
            category="inconclusive" if abstain else spec_pred.category,
            raw_score=spec_pred.raw_score,
            calibrated_confidence=spec_pred.calibrated_confidence,
            confidence_percent=spec_pred.percentage,
            is_healthy=spec_is_healthy and not abstain,
            abstention=abstain,
            abstention_reason=abstention_reason,
            routing_path="specialist_fused",
            model_identifier=fused_model_name,
            specialist_agreement=agreement,
            fusion_outcome=fusion_outcome,
            fusion_details={
                "routing_path": "specialist_fused",
                "fusion_outcome": fusion_outcome,
                "specialist_model": spec_pred.model_identifier,
                "generalist_model": "India Multi-Crop DINOv2 ViT-B/14",
                "concordance": concordance,
                "specialist_agreement": agreement,
                "specialist_condition": spec_pred.canonical_condition,
                "specialist_raw_score": spec_pred.raw_score,
                "specialist_calibrated_score": spec_pred.calibrated_confidence,
                "generalist_top_1_label": gen_top_label,
                "generalist_top_1_score": round(gen_top_prob, 4),
                "notes": notes,
            },
            competing_predictions=competing,
            all_candidates=all_candidates,
            disease_candidates=disease_candidates,
            pest_candidates=gen_pest_candidates[:3],
            warnings=warnings,
            latency_ms=round(total_latency, 2),
        )

    def _format_generalist_result(
        self,
        gen_preds: List[Tuple[str, float]],
        declared_crop: str,
        generalist_engine: Any,
        latency_ms: float,
        threshold: float,
    ) -> FusedDiagnosticResult:
        """Format purely generalist diagnostic output when no crop specialist is active."""
        if not gen_preds:
            return FusedDiagnosticResult(
                condition="Inconclusive foliar diagnosis",
                canonical_label="unknown::Inconclusive",
                crop=declared_crop,
                category="inconclusive",
                raw_score=0.0,
                calibrated_confidence=0.0,
                confidence_percent=0,
                is_healthy=False,
                abstention=True,
                abstention_reason="model_unavailable",
                routing_path="generalist_fallback",
                model_identifier="India Multi-Crop DINOv2 ViT-B/14 (Generalist)",
                specialist_agreement=None,
                fusion_outcome="insufficient_evidence",
                latency_ms=latency_ms,
            )

        top_label, top_prob = gen_preds[0]
        if "::" in top_label:
            top_crop, top_cond = top_label.split("::", 1)
            crop_clean = top_crop.replace("_", " ").title()
        else:
            crop_clean, top_cond = "Unknown", top_label

        cond_lower = top_cond.lower()
        if "healthy" in cond_lower:
            cat = "healthy"
        elif any(t in cond_lower for t in ["(pest)", "pest", "aphid", "mite", "borer", "thrips"]):
            cat = "pest"
        elif "deficiency" in cond_lower:
            cat = "deficiency"
        else:
            cat = "disease"

        declared_norm = declared_crop.strip().lower()
        diagnosed_norm = crop_clean.strip().lower()
        crop_conflict = (top_prob >= 0.50 and diagnosed_norm != "unknown" and diagnosed_norm != declared_norm)

        abstain = top_prob < threshold or crop_conflict
        pct = int(round(top_prob * 100))

        if crop_conflict:
            fusion_outcome = "crop_uncertain"
            abstention_reason = "crop_uncertain"
            cond_name = "Host crop uncertain"
        elif top_prob < threshold:
            fusion_outcome = "insufficient_evidence"
            abstention_reason = "insufficient_evidence"
            cond_name = "Inconclusive foliar diagnosis"
        else:
            fusion_outcome = "single_model"
            abstention_reason = None
            cond_name = top_cond

        all_cands = []
        dis_cands = []
        pest_cands = []
        for l, p in gen_preds:
            c_cr, c_cd = l.split("::", 1) if "::" in l else ("Unknown", l)
            c_norm = c_cd.lower()
            c_cat = "healthy" if "healthy" in c_norm else ("pest" if "pest" in c_norm else "disease")
            item = {
                "condition": c_cd,
                "crop": c_cr.replace("_", " ").title(),
                "category": c_cat,
                "task": "foliar_classification",
                "source_model": "India Multi-Crop DINOv2 ViT-B/14",
                "probability": round(p, 4),
                "percentage": int(round(p * 100)),
            }
            all_cands.append(item)
            if c_cat == "disease" and len(dis_cands) < 4:
                dis_cands.append(item)
            elif c_cat == "pest" and len(pest_cands) < 4:
                pest_cands.append(item)

        warnings = []
        if crop_conflict:
            warnings.append(f"Host Crop Conflict: Diagnosed crop '{crop_clean}' conflicts with declared crop '{declared_crop}'.")
        elif top_prob < threshold:
            warnings.append(f"Diagnostic Abstention: Highest candidate score ({pct}%) is below {int(round(threshold * 100))}% safety cutoff.")

        return FusedDiagnosticResult(
            condition=cond_name,
            canonical_label=top_label,
            crop=crop_clean,
            category="inconclusive" if abstain else cat,
            raw_score=round(top_prob, 4),
            calibrated_confidence=round(top_prob, 4),
            confidence_percent=pct,
            is_healthy=(cat == "healthy") and not abstain,
            abstention=abstain,
            abstention_reason=abstention_reason,
            routing_path="generalist_fallback",
            model_identifier="India Multi-Crop DINOv2 ViT-B/14 (Generalist)",
            specialist_agreement=None,
            fusion_outcome=fusion_outcome,
            fusion_details={
                "routing_path": "generalist_fallback",
                "fusion_outcome": fusion_outcome,
                "specialist_model": None,
                "generalist_model": "India Multi-Crop DINOv2 ViT-B/14",
                "concordance": "generalist_only",
                "specialist_agreement": None,
                "notes": [f"No active specialist for declared crop '{declared_crop}'. Evaluated by multi-crop generalist."],
            },
            competing_predictions=[],
            all_candidates=all_cands[:5],
            disease_candidates=dis_cands,
            pest_candidates=pest_cands,
            warnings=warnings,
            latency_ms=round(latency_ms, 2),
        )


# Singleton intelligent router
intelligent_router = IntelligentRouter()
