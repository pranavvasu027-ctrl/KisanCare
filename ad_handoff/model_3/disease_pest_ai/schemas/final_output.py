"""
Final Standard Output Schemas for Disease & Pest AI (Section 12).

Defines the unified, comprehensive diagnostic payload:
- input: user contextual contract
- disease: foliar pathology diagnosis and confidence
- pests: spatial pest localization, bounding boxes, counts
- severity: visual disease severity assessment (or explicit unavailable status)
- treatment: independent disease and pest treatment recommendation blocks
- explainability: Grad-CAM heatmap paths and pest localization bounding boxes
- provenance: complete audit trail from image to model checkpoint and CIBRC sources
- warnings: aggregated operational, regulatory, and domain notices
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field, model_validator

from disease_pest_ai.schemas.outputs import (
    BoundingBox,
    ChemicalCandidate,
    ConditionType,
    DetectedPest,
    NonChemicalControl,
    PestPrediction,
    PredictionResult,
    ReasonCode,
    RecommendationStatus,
    TopPrediction,
    TreatmentRecommendation,
)


class InputSummary(BaseModel):
    """Echo of validated input contract."""
    crop: str = Field(..., description="User-specified crop name.")
    location_state: str = Field(..., description="User-specified location/state.")
    growth_stage: str = Field(..., description="Crop phenological growth stage.")
    image_type: str = Field(..., description="Modality of image capture.")

    model_config = ConfigDict(arbitrary_types_allowed=True)


class DiseaseSection(BaseModel):
    """Disease classification output section."""
    condition: str = Field(..., description="Diagnosed disease condition or 'Healthy'.")
    condition_type: ConditionType = Field(ConditionType.DISEASE, description="disease | healthy | unknown")
    score: float = Field(..., ge=0.0, le=1.0, description="Disease vision model confidence score.")
    top_predictions: List[TopPrediction] = Field(default_factory=list, description="Top-k ranked disease predictions.")
    crop_match: bool = Field(True, description="True if predicted disease is biologically compatible with user crop.")
    status: str = Field("diagnosed", description="diagnosed | healthy | crop_mismatch | low_score | unverified | bypassed")

    model_config = ConfigDict(arbitrary_types_allowed=True)


class PestSection(BaseModel):
    """Pest localization and detection output section."""
    detections: List[DetectedPest] = Field(default_factory=list, description="List of detected pests with bounding boxes.")
    count: int = Field(0, description="Total number of detected pests passing threshold.")
    crop_validation: Dict[str, Any] = Field(default_factory=dict, description="Crop pest validation summary.")
    status: str = Field("no_pest_detected", description="detected | no_pest_detected | low_score | crop_mismatch | bypassed")

    model_config = ConfigDict(arbitrary_types_allowed=True)


class SeverityAssessment(BaseModel):
    """
    Visual disease severity assessment (Section 13).
    Explicitly marked as 'unavailable' unless an audited severity estimation model is active.
    """
    value: Optional[float] = Field(None, description="Percentage affected leaf area (0.0 to 100.0) if measured.")
    status: str = Field("unavailable", description="'unavailable' | 'estimated' | 'not_applicable'")
    source: str = Field("unavailable", description="Source model or calculation method; 'unavailable' if unmeasured.")

    model_config = ConfigDict(arbitrary_types_allowed=True)


class TreatmentSection(BaseModel):
    """
    Independent treatment blocks for disease and pest (Sections 9, 10, 12).
    Chemical mixtures are NEVER combined automatically.
    """
    disease_recommendations: Optional[TreatmentRecommendation] = Field(
        None, description="Verified CIB&RC and IPM recommendations for disease."
    )
    pest_recommendations: Optional[TreatmentRecommendation] = Field(
        None, description="Verified CIB&RC and IPM recommendations for detected pests."
    )
    recommendation_status: str = Field(
        "no_action_needed",
        description="verified_candidates_found | manual_review_required | no_treatment_needed_healthy | no_action_needed"
    )

    @property
    def chemical_candidates(self) -> List[ChemicalCandidate]:
        candidates: List[ChemicalCandidate] = []
        if self.disease_recommendations:
            candidates.extend(self.disease_recommendations.chemical_candidates)
        if self.pest_recommendations:
            candidates.extend(self.pest_recommendations.chemical_candidates)
        return candidates

    @property
    def non_chemical_controls(self) -> List[NonChemicalControl]:
        controls: List[NonChemicalControl] = []
        if self.disease_recommendations:
            controls.extend(self.disease_recommendations.non_chemical_controls)
        if self.pest_recommendations:
            controls.extend(self.pest_recommendations.non_chemical_controls)
        return controls

    @property
    def sources(self) -> List[str]:
        s: List[str] = []
        if self.disease_recommendations:
            s.extend(self.disease_recommendations.sources)
        if self.pest_recommendations:
            s.extend(self.pest_recommendations.sources)
        return list(dict.fromkeys(s))

    @property
    def reason_code(self) -> Optional[Union[ReasonCode, str]]:
        if self.disease_recommendations:
            return self.disease_recommendations.reason_code
        if self.pest_recommendations:
            return self.pest_recommendations.reason_code
        return None

    @property
    def status(self) -> str:
        return self.recommendation_status

    model_config = ConfigDict(arbitrary_types_allowed=True)


class ExplainabilityOutputs(BaseModel):
    """Visual explanation references for classification and detection (Section 14)."""
    disease_heatmap: Optional[str] = Field(
        None, description="File path, base64 data, or attention coordinates for Grad-CAM disease attention."
    )
    pest_boxes: List[Dict[str, Any]] = Field(
        default_factory=list, description="Spatial bounding boxes with class labels and confidence."
    )
    explanation_type: str = Field(
        "gradcam_and_bounding_boxes",
        description="Type of explanation (gradcam, bounding_box, combined, none)."
    )

    model_config = ConfigDict(arbitrary_types_allowed=True)


class FinalProvenance(BaseModel):
    """Complete traceability audit log."""
    disease_model: str = Field(..., description="Vision model identifier for disease.")
    disease_model_version: str = Field("EfficientNetV2-S", description="Disease model version.")
    pest_model: Optional[str] = Field(None, description="Object detector identifier for pests.")
    pest_model_version: Optional[str] = Field(None, description="Pest model version.")
    treatment_sources: List[Dict[str, Any]] = Field(default_factory=list, description="Referenced statutory CIBRC/IPM sources.")
    dataset_sources: List[str] = Field(
        default_factory=lambda: ["PlantVillage", "IP102", "CIB&RC Major Uses (31/03/2024)", "DPPQS IPM Packages"],
        description="Training datasets and regulatory registers."
    )
    latency_breakdown_ms: Dict[str, float] = Field(default_factory=dict, description="Component latency measurements.")
    device: str = Field("cpu", description="Hardware execution device.")
    database_version: str = Field("1.0.0-20240331", description="CIBRC treatment database version.")
    treatment_source: str = Field(
        "Central Insecticides Board & Registration Committee (CIB&RC) / DPPQS",
        description="Statutory authority name."
    )
    source_date: str = Field("2024-03-31", description="Date of CIBRC publication.")
    context: Dict[str, Any] = Field(default_factory=dict, description="Pipeline contextual parameters.")
    pipeline: Dict[str, Any] = Field(default_factory=dict, description="Pipeline contextual metadata.")

    @property
    def vision_model(self) -> str:
        return self.disease_model

    def __contains__(self, item: str) -> bool:
        if item == "vision_model":
            return True
        return item in self.__dict__ or item in self.model_dump()

    def __getitem__(self, item: str) -> Any:
        if item == "vision_model":
            return self.disease_model
        if hasattr(self, item):
            return getattr(self, item)
        d = self.model_dump()
        if item in d:
            return d[item]
        raise KeyError(item)

    def get(self, item: str, default: Any = None) -> Any:
        try:
            return self[item]
        except (KeyError, AttributeError):
            return default

    model_config = ConfigDict(arbitrary_types_allowed=True)


class AgricultureDiseaseResult(BaseModel):
    """
    Unified end-to-end result schema for the Agriculture Disease & Pest AI system.
    Implements Section 12 structure while providing backward-compatible accessors.
    """
    input: InputSummary = Field(..., description="Input contract parameters.")
    disease: DiseaseSection = Field(..., description="Disease diagnostic findings.")
    pests: PestSection = Field(..., description="Pest localization and detection findings.")
    severity: SeverityAssessment = Field(default_factory=SeverityAssessment, description="Disease severity assessment.")
    treatment: TreatmentSection = Field(..., description="Dual-block treatment recommendations.")
    explainability: ExplainabilityOutputs = Field(default_factory=ExplainabilityOutputs, description="Visual explanations.")
    provenance: FinalProvenance = Field(..., description="Full audit trail and execution metadata.")
    warnings: List[str] = Field(default_factory=list, description="Consolidated operational and safety warnings.")

    # Underlying raw predictions for interoperability
    vision_prediction: Optional[PredictionResult] = None
    pest_prediction: Optional[PestPrediction] = None

    # =========================================================================
    # Backward Compatibility Properties (Preserves Phase 1, 2, and 3 APIs)
    # =========================================================================
    @property
    def crop(self) -> str:
        return self.input.crop

    @property
    def condition(self) -> str:
        return self.disease.condition

    @property
    def condition_type(self) -> ConditionType:
        return self.disease.condition_type

    @property
    def prediction_score(self) -> float:
        return self.disease.score

    @property
    def score(self) -> float:
        return self.disease.score

    @property
    def crop_match(self) -> bool:
        return self.disease.crop_match

    @property
    def crop_mismatch(self) -> bool:
        return not self.disease.crop_match

    @property
    def user_crop(self) -> str:
        return self.input.crop

    @property
    def pest_count(self) -> int:
        return self.pests.count

    @property
    def model_name(self) -> str:
        return self.provenance.disease_model

    # Compatibility bridge for code expecting result.treatment to have .chemical_candidates
    @property
    def primary_treatment(self) -> Optional[TreatmentRecommendation]:
        if self.treatment.disease_recommendations:
            return self.treatment.disease_recommendations
        return self.treatment.pest_recommendations

    @property
    def diagnosis(self) -> Any:
        from disease_pest_ai.schemas.outputs import DiagnosisDetails
        return DiagnosisDetails(
            crop=self.input.crop,
            condition=self.disease.condition,
            condition_type=self.disease.condition_type,
            prediction_score=self.disease.score,
            top_predictions=self.disease.top_predictions,
        )

    @property
    def validation(self) -> Any:
        from disease_pest_ai.schemas.outputs import ReasonCode, ValidationDetails
        rc = self.treatment.reason_code
        u_cond = (rc == "UNSUPPORTED_CONDITION" or rc == ReasonCode.UNSUPPORTED_CONDITION)
        u_crop = (rc == "UNSUPPORTED_CROP" or rc == ReasonCode.UNSUPPORTED_CROP)
        return ValidationDetails(
            crop_match=self.disease.crop_match,
            crop_mismatch=not self.disease.crop_match,
            unsupported_condition=u_cond,
            unsupported_crop=u_crop,
            reason_code=rc,
        )

    model_config = ConfigDict(arbitrary_types_allowed=True)
