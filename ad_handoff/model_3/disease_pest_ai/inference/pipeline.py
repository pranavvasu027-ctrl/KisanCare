"""
Standardized Disease & Pest Inference Pipeline (Phase 4).

Unified Multimodal Agriculture Pipeline:
INPUT IMAGE + METADATA (Crop, Location, Stage, Image Type)
  ↓
Image Type Routing Table (Section 2)
  - leaf / field_leaf / fruit / stem / whole_plant / field_crop: Run Disease Classifier + Pest Detector
  - trap_sticky_sheet: Bypass foliar disease classifier; Run Pest Detector with advisory
  ↓
Vision Inference:
  - Disease Classifier (Primary: BiernyVR EfficientNetV2-S)
  - Pest Detector (Primary: YOLO11s IP102 Object Detector)
  ↓
Condition Resolution & Crop Validation (ConditionResolver - Section 8)
  ↓
Explainability Generation (Grad-CAM + Pest Bounding Boxes - Section 14)
  ↓
Independent Dual Treatment Retrieval (TreatmentEngine - Sections 9 & 10)
  - Disease Recommendations (CIB&RC + IPM)
  - Pest Recommendations (CIB&RC + IPM)
  - Chemical candidates are NEVER combined into an ad-hoc tank mix
  ↓
Unified Diagnostic Schema (AgricultureDiseaseResult - Section 12)
"""

import logging
import time
from typing import Any, Dict, List, Optional, Union
from PIL import Image

from disease_pest_ai.inference.condition_resolver import ConditionResolver
from disease_pest_ai.inference.explainability import generate_explainability
from disease_pest_ai.models.base import BaseModelAdapter
from disease_pest_ai.models.disease.efficientnet_adapter import EfficientNetDiseaseAdapter
from disease_pest_ai.models.disease.yolo_disease_adapter import YoloDiseaseAdapter
from disease_pest_ai.models.pest.wadhwani_adapter import WadhwaniPestAdapter
from disease_pest_ai.models.pest.yolo_pest_adapter import YoloPestAdapter
from disease_pest_ai.recommendation.treatment_engine import TreatmentEngine
from disease_pest_ai.schemas.final_output import (
    AgricultureDiseaseResult,
    DiseaseSection,
    ExplainabilityOutputs,
    FinalProvenance,
    InputSummary,
    PestSection,
    SeverityAssessment,
    TreatmentSection,
)
from disease_pest_ai.schemas.inputs import DiseasePestInput, GrowthStage, ImageType
from disease_pest_ai.schemas.outputs import (
    ConditionType,
    PestPrediction,
    PredictionResult,
    ReasonCode,
    RecommendationStatus,
    TopPrediction,
    TreatmentRecommendation,
)

logger = logging.getLogger(__name__)


class DiseasePestPipeline:
    """
    Unified Inference Pipeline for Agriculture AI Disease and Pest Diagnosis.
    Orchestrates disease classification, pest localization, crop validation,
    Grad-CAM explainability, and dual independent treatment retrieval.
    """

    def __init__(
        self,
        primary_disease_model: str = "efficientnet",
        primary_pest_model: str = "yolo_pest",
        lazy_load: bool = True,
        treatment_engine: Optional[TreatmentEngine] = None,
        condition_resolver: Optional[ConditionResolver] = None,
    ):
        """
        Args:
            primary_disease_model: 'efficientnet' (default primary) or 'yolo' (experimental).
            primary_pest_model: 'yolo_pest' (default primary YOLO11s) or 'wadhwani'.
            lazy_load: Whether to defer weights loading until first inference call.
            treatment_engine: Optional injected TreatmentEngine instance.
            condition_resolver: Optional injected ConditionResolver instance.
        """
        self.primary_disease_model_name = primary_disease_model.lower()
        self.primary_pest_model_name = primary_pest_model.lower()
        self._adapters: Dict[str, BaseModelAdapter] = {}
        self.lazy_load = lazy_load
        self.treatment_engine = treatment_engine or TreatmentEngine()
        self.condition_resolver = condition_resolver or ConditionResolver()

        if not lazy_load:
            self._get_adapter(self.primary_disease_model_name)
            self._get_adapter(self.primary_pest_model_name)

    def _get_adapter(self, model_key: str) -> BaseModelAdapter:
        """Get or initialize the specified adapter."""
        if model_key not in self._adapters:
            if model_key == "efficientnet":
                self._adapters[model_key] = EfficientNetDiseaseAdapter()
            elif model_key == "yolo":
                self._adapters[model_key] = YoloDiseaseAdapter()
            elif model_key in ("pest", "yolo_pest"):
                self._adapters[model_key] = YoloPestAdapter(model_variant="primary")
            elif model_key == "yolo_pest_secondary":
                self._adapters[model_key] = YoloPestAdapter(model_variant="secondary")
            elif model_key == "wadhwani":
                self._adapters[model_key] = WadhwaniPestAdapter()
            else:
                raise ValueError(
                    f"Unknown model identifier: '{model_key}'. Expected 'efficientnet', 'yolo', 'yolo_pest', or 'wadhwani'."
                )
        return self._adapters[model_key]

    def predict_vision_only(
        self,
        plant_image: Any,
        crop_name: str,
        location_state: str,
        growth_stage: Union[GrowthStage, str],
        image_type: Union[ImageType, str],
        model_override: Optional[str] = None,
    ) -> PredictionResult:
        """
        Execute raw computer vision inference and crop validation for disease.
        """
        input_payload = DiseasePestInput(
            plant_image=plant_image,
            crop_name=crop_name,
            location_state=location_state,
            growth_stage=growth_stage,
            image_type=image_type,
        )

        selected_model = model_override.lower() if model_override else self.primary_disease_model_name
        adapter = self._get_adapter(selected_model)

        if not adapter.is_available():
            raise RuntimeError(
                f"Selected model '{adapter.model_name}' has no usable pretrained checkpoint."
            )

        result = adapter.predict(
            image=input_payload.plant_image,
            crop_name=input_payload.crop_name,
            location_state=input_payload.location_state,
            growth_stage=str(input_payload.growth_stage),
            image_type=str(input_payload.image_type),
        )

        result.provenance["pipeline"] = {
            "version": "4.0.0",
            "selected_model": selected_model,
            "location_state": input_payload.location_state,
            "growth_stage": str(input_payload.growth_stage),
            "image_type": str(input_payload.image_type),
        }

        return result

    def predict_pest(
        self,
        plant_image: Any,
        crop_name: Optional[str] = None,
        location_state: Optional[str] = None,
        growth_stage: Optional[str] = None,
        image_type: Optional[str] = None,
        model_override: Optional[str] = None,
    ) -> PestPrediction:
        """
        Execute dedicated pest detection inference returning bounding boxes and scores.
        """
        selected_model = model_override.lower() if model_override else self.primary_pest_model_name
        adapter = self._get_adapter(selected_model)

        if not adapter.is_available():
            raise RuntimeError(
                f"Selected pest model '{adapter.model_name}' has no usable pretrained checkpoint."
            )

        return adapter.predict(
            image=plant_image,
            crop_name=crop_name,
            location_state=location_state,
            growth_stage=growth_stage,
            image_type=image_type,
        )

    def predict(
        self,
        plant_image: Any,
        crop_name: str,
        location_state: str,
        growth_stage: Union[GrowthStage, str],
        image_type: Union[ImageType, str],
        model_override: Optional[str] = None,
        run_pest_detection: bool = True,
        generate_visual_explanation: bool = True,
    ) -> AgricultureDiseaseResult:
        """
        Execute unified multimodal pipeline inference (Phase 4).

        1. Validates input contract.
        2. Routes models based on image_type (Section 2).
        3. Executes disease classification & pest detection.
        4. Normalizes taxonomy and performs biological crop validation (Section 8).
        5. Computes Grad-CAM explainability and bounding boxes (Section 14).
        6. Queries independent treatments for disease and pest (Sections 9 & 10).
        7. Returns complete AgricultureDiseaseResult (Section 12).
        """
        t_pipeline_start = time.perf_counter()

        # 1. Validate Input Contract
        input_payload = DiseasePestInput(
            plant_image=plant_image,
            crop_name=crop_name,
            location_state=location_state,
            growth_stage=growth_stage,
            image_type=image_type,
        )

        input_summary = InputSummary(
            crop=input_payload.crop_name,
            location_state=input_payload.location_state,
            growth_stage=str(input_payload.growth_stage),
            image_type=str(input_payload.image_type),
        )

        aggregated_warnings: List[str] = []
        latency_breakdown: Dict[str, float] = {}

        # 2. Image Type Routing (Section 2)
        img_type_str = str(input_payload.image_type).lower()
        is_trap_sheet = "trap" in img_type_str
        is_foliar_eligible = not is_trap_sheet

        # 3. Disease Model Inference
        vision_result: Optional[PredictionResult] = None
        disease_section: DiseaseSection
        disease_latency_ms: float = 0.0

        if is_foliar_eligible:
            t0_dis = time.perf_counter()
            vision_result = self.predict_vision_only(
                plant_image=input_payload.plant_image,
                crop_name=input_payload.crop_name,
                location_state=input_payload.location_state,
                growth_stage=input_payload.growth_stage,
                image_type=input_payload.image_type,
                model_override=model_override,
            )
            disease_latency_ms = (time.perf_counter() - t0_dis) * 1000
            latency_breakdown["disease_model_ms"] = round(disease_latency_ms, 2)
            aggregated_warnings.extend(vision_result.warnings)

            # Resolve condition and validate crop biological feasibility
            resolved_dis = self.condition_resolver.resolve_disease(
                raw_condition=vision_result.condition,
                user_crop=input_payload.crop_name,
                predicted_crop=vision_result.crop,
            )

            status_str = "diagnosed"
            if resolved_dis.status == "HEALTHY":
                status_str = "healthy"
            elif not resolved_dis.is_crop_match:
                status_str = "crop_mismatch"
            elif vision_result.score < 0.60:
                status_str = "low_score"

            disease_section = DiseaseSection(
                condition=resolved_dis.canonical_condition,
                condition_type=resolved_dis.condition_type,
                score=round(vision_result.score, 4),
                top_predictions=vision_result.top_predictions,
                crop_match=resolved_dis.is_crop_match,
                status=status_str,
            )
            for w in resolved_dis.warnings:
                if w not in aggregated_warnings:
                    aggregated_warnings.append(w)
        else:
            # Trap sheet: foliar disease classifier is bypassed
            aggregated_warnings.append(
                "Domain Notice: Foliar disease model bypassed for pheromone sticky trap sheet ('trap_sticky_sheet')."
            )
            disease_section = DiseaseSection(
                condition="Not Applicable (Trap Sheet)",
                condition_type=ConditionType.UNKNOWN,
                score=0.0,
                top_predictions=[],
                crop_match=True,
                status="bypassed",
            )

        # 4. Pest Model Inference
        pest_result: Optional[PestPrediction] = None
        pest_section: PestSection
        pest_latency_ms: float = 0.0

        if run_pest_detection:
            t0_pest = time.perf_counter()
            try:
                pest_result = self.predict_pest(
                    plant_image=input_payload.plant_image,
                    crop_name=input_payload.crop_name,
                    location_state=input_payload.location_state,
                    growth_stage=str(input_payload.growth_stage),
                    image_type=str(input_payload.image_type),
                )
                pest_latency_ms = (time.perf_counter() - t0_pest) * 1000
                latency_breakdown["pest_detector_ms"] = round(pest_latency_ms, 2)

                for w in pest_result.warnings:
                    if w not in aggregated_warnings:
                        aggregated_warnings.append(w)

                # Re-verify pest crop matches through condition resolver
                compatible_count = 0
                for p in pest_result.pests:
                    res_p = self.condition_resolver.resolve_pest(
                        raw_pest=p.pest,
                        user_crop=input_payload.crop_name,
                        score=p.score,
                    )
                    p.crop_compatible = res_p.is_crop_match
                    if res_p.is_crop_match:
                        compatible_count += 1
                    for pw in res_p.warnings:
                        if pw not in aggregated_warnings:
                            aggregated_warnings.append(pw)

                pest_status = pest_result.status
                if is_trap_sheet and not pest_result.pests:
                    pest_status = "no_pest_detected"

                pest_section = PestSection(
                    detections=pest_result.pests,
                    count=len(pest_result.pests),
                    crop_validation={
                        "user_crop": input_payload.crop_name,
                        "compatible_detections": compatible_count,
                        "mismatched_detections": len(pest_result.pests) - compatible_count,
                    },
                    status=pest_status,
                )
            except Exception as e:
                logger.warning(f"Pest detection failed or bypassed: {e}")
                pest_section = PestSection(
                    detections=[],
                    count=0,
                    crop_validation={},
                    status="bypassed",
                )
        else:
            pest_section = PestSection(
                detections=[],
                count=0,
                crop_validation={},
                status="bypassed",
            )

        # 5. Independent Treatment Recommendation (Sections 9 & 10)
        t0_tx = time.perf_counter()
        disease_tx: Optional[TreatmentRecommendation] = None
        pest_tx: Optional[TreatmentRecommendation] = None

        # Disease treatment query
        if is_foliar_eligible and vision_result:
            disease_tx = self.treatment_engine.get_treatment_recommendations(
                crop_name=input_payload.crop_name,
                condition=disease_section.condition,
                condition_type=disease_section.condition_type,
                location_state=input_payload.location_state,
                growth_stage=str(input_payload.growth_stage),
                prediction_score=disease_section.score,
                crop_mismatch=not disease_section.crop_match,
            )
            for w in disease_tx.warnings:
                if w not in aggregated_warnings:
                    aggregated_warnings.append(w)

        # Pest treatment query
        if pest_result and pest_result.pests:
            top_pest = pest_result.top_pests[0]
            pest_tx = self.treatment_engine.get_treatment_recommendations(
                crop_name=input_payload.crop_name,
                condition=top_pest.pest,
                condition_type="pest",
                location_state=input_payload.location_state,
                growth_stage=str(input_payload.growth_stage),
                prediction_score=top_pest.score,
                crop_mismatch=not top_pest.crop_compatible,
            )
            for w in pest_tx.warnings:
                if w not in aggregated_warnings:
                    aggregated_warnings.append(w)

        tx_latency_ms = (time.perf_counter() - t0_tx) * 1000
        latency_breakdown["treatment_retrieval_ms"] = round(tx_latency_ms, 2)

        # Overall recommendation status
        if (disease_tx and disease_tx.status == RecommendationStatus.VERIFIED_CANDIDATES_FOUND) or (
            pest_tx and pest_tx.status == RecommendationStatus.VERIFIED_CANDIDATES_FOUND
        ):
            rec_status = "verified_candidates_found"
        elif disease_section.status == "healthy":
            rec_status = "no_treatment_needed_healthy"
        elif (disease_tx and disease_tx.status == RecommendationStatus.MANUAL_REVIEW_REQUIRED) or (
            pest_tx and pest_tx.status == RecommendationStatus.MANUAL_REVIEW_REQUIRED
        ):
            rec_status = "manual_review_required"
        else:
            rec_status = "no_action_needed"

        treatment_section = TreatmentSection(
            disease_recommendations=disease_tx,
            pest_recommendations=pest_tx,
            recommendation_status=rec_status,
        )

        # 6. Severity Assessment (Section 13)
        severity_section = SeverityAssessment(
            value=None,
            status="unavailable",
            source="unavailable",
        )

        # 7. Explainability (Section 14)
        explainability_outputs: ExplainabilityOutputs
        dis_adapter = None
        top_idx = None
        if is_foliar_eligible:
            try:
                selected_model = model_override.lower() if model_override else self.primary_disease_model_name
                dis_adapter = self._get_adapter(selected_model)
                if hasattr(dis_adapter, "_last_top_idx"):
                    top_idx = dis_adapter._last_top_idx
            except Exception:
                pass

        if generate_visual_explanation:
            t0_exp = time.perf_counter()
            explainability_outputs = generate_explainability(
                disease_adapter=dis_adapter,
                image=input_payload.plant_image,
                top_class_idx=top_idx,
                pest_detections=pest_section.detections,
            )
            latency_breakdown["explainability_ms"] = round((time.perf_counter() - t0_exp) * 1000, 2)
        else:
            explainability_outputs = ExplainabilityOutputs(
                disease_heatmap=None,
                pest_boxes=[{"label": p.pest, "score": p.score, "box": p.bounding_box} for p in pest_section.detections],
                explanation_type="bounding_box" if pest_section.detections else "none",
            )

        # 8. Provenance & Audit Trail
        total_latency_ms = (time.perf_counter() - t_pipeline_start) * 1000
        latency_breakdown["total_pipeline_ms"] = round(total_latency_ms, 2)

        # Collect sources
        treatment_sources: List[Dict[str, Any]] = []
        if disease_tx and disease_tx.source_records:
            treatment_sources.extend(disease_tx.source_records)
        if pest_tx and pest_tx.source_records:
            for s in pest_tx.source_records:
                if s not in treatment_sources:
                    treatment_sources.append(s)

        dis_mod_name = vision_result.model_name if vision_result else "bypassed"
        dis_mod_ver = vision_result.model_version if vision_result else "N/A"
        pest_mod_name = pest_result.model_name if pest_result else None
        pest_mod_ver = pest_result.model_version if pest_result else None

        pipeline_ctx = {
            "version": "4.0.0",
            "location_state": input_payload.location_state,
            "growth_stage": str(input_payload.growth_stage),
            "image_type": str(input_payload.image_type),
            "disease_status": disease_section.status,
            "pest_status": pest_section.status,
        }

        provenance = FinalProvenance(
            disease_model=dis_mod_name,
            disease_model_version=dis_mod_ver,
            pest_model=pest_mod_name,
            pest_model_version=pest_mod_ver,
            treatment_sources=treatment_sources,
            dataset_sources=[
                "PlantVillage (38 Classes)",
                "IP102 Benchmark (102 Classes)",
                "CIB&RC Major Uses (31/03/2024)",
                "DPPQS IPM Packages",
            ],
            latency_breakdown_ms=latency_breakdown,
            device=str(getattr(dis_adapter, "device", "cpu")),
            database_version=self.treatment_engine.repository.database_version,
            context=pipeline_ctx,
            pipeline=pipeline_ctx,
        )

        return AgricultureDiseaseResult(
            input=input_summary,
            disease=disease_section,
            pests=pest_section,
            severity=severity_section,
            treatment=treatment_section,
            explainability=explainability_outputs,
            provenance=provenance,
            warnings=aggregated_warnings,
            vision_prediction=vision_result,
            pest_prediction=pest_result,
        )
