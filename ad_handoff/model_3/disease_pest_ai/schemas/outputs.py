"""
Standardized Prediction and Treatment Result Schemas for Disease & Pest AI Module.
Implements Section 13 Reason Codes, Section 14 TreatmentRecommendation, and Section 18 AgricultureDiseaseResult breakdown.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field, model_validator


class ConditionType(str, Enum):
    DISEASE = "disease"
    PEST = "pest"
    HEALTHY = "healthy"
    UNKNOWN = "unknown"


class RecommendationStatus(str, Enum):
    VERIFIED_CANDIDATES_FOUND = "verified_candidates_found"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"
    NO_TREATMENT_NEEDED_HEALTHY = "no_treatment_needed_healthy"
    NO_CANDIDATES_FOUND = "no_candidates_found"


class ReasonCode(str, Enum):
    UNSUPPORTED_CROP = "UNSUPPORTED_CROP"
    UNSUPPORTED_CONDITION = "UNSUPPORTED_CONDITION"
    CROP_CONDITION_MISMATCH = "CROP_CONDITION_MISMATCH"
    NO_VERIFIED_TREATMENT = "NO_VERIFIED_TREATMENT"
    INCOMPLETE_SOURCE_DATA = "INCOMPLETE_SOURCE_DATA"
    LOW_MODEL_SCORE = "LOW_MODEL_SCORE"
    MANUAL_REVIEW_REQUIRED = "MANUAL_REVIEW_REQUIRED"


class NonChemicalCategory(str, Enum):
    CULTURAL = "cultural"
    MECHANICAL = "mechanical"
    BIOLOGICAL = "biological"
    PREVENTIVE_MONITORING = "preventive_monitoring"


class BoundingBox(BaseModel):
    """
    Standardized bounding box for object detection models (e.g. YOLO / SSD).
    Coordinates are in [x_min, y_min, x_max, y_max] format.
    """
    box: List[float] = Field(..., description="[x_min, y_min, x_max, y_max] coordinates.")
    label: str = Field(..., description="Detected class/condition name.")
    score: float = Field(..., ge=0.0, le=1.0, description="Confidence score.")
    crop: Optional[str] = Field(None, description="Crop associated with this box.")
    is_normalized: bool = Field(False, description="Whether coordinates are normalized [0, 1] or pixel values.")


class TopPrediction(BaseModel):
    """
    Single prediction candidate among top-k results.
    """
    condition: str = Field(..., description="Diagnosed condition or disease name.")
    crop: str = Field(..., description="Predicted crop name.")
    score: float = Field(..., ge=0.0, le=1.0, description="Confidence score.")
    condition_type: ConditionType = Field(ConditionType.DISEASE, description="Category of condition.")
    raw_label: Optional[str] = Field(None, description="Raw label string from model taxonomy.")


class PredictionResult(BaseModel):
    """
    Standardized output result returned by all Disease/Pest adapters.
    """
    condition: str = Field(..., description="Primary diagnosed condition or disease.")
    condition_type: ConditionType = Field(..., description="disease | pest | healthy | unknown")
    score: float = Field(..., ge=0.0, le=1.0, description="Primary confidence score (0.0 to 1.0).")
    top_predictions: List[TopPrediction] = Field(default_factory=list, description="Top-k ranked predictions.")
    bounding_boxes: List[BoundingBox] = Field(default_factory=list, description="List of bounding boxes for detection models.")
    crop: str = Field(..., description="Crop detected/predicted by the model.")
    user_crop: Optional[str] = Field(None, description="Crop originally provided by the user.")
    crop_mismatch: bool = Field(False, description="True if model-predicted crop conflicts with user_crop.")
    model_name: str = Field(..., description="Name of the model that produced this prediction.")
    model_version: str = Field(..., description="Version of the model checkpoint used.")
    warnings: List[str] = Field(default_factory=list, description="Non-fatal notices or advisory warnings.")
    provenance: Dict[str, Any] = Field(default_factory=dict, description="Metadata including execution latency, backend, device.")

    model_config = ConfigDict(arbitrary_types_allowed=True)


class DetectedPest(BaseModel):
    """
    Standardized single pest detection with localization bounding box.
    """
    pest: str = Field(..., description="Canonical or common name of the detected pest.")
    raw_label: str = Field(..., description="Exact class label string from model taxonomy.")
    score: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0.0 to 1.0).")
    bounding_box: List[float] = Field(..., description="[x_min, y_min, x_max, y_max] bounding box in pixel coordinates.")
    class_id: int = Field(..., description="Model class index (0-101 for IP102).")
    supported_crops: List[str] = Field(default_factory=list, description="Host crops associated with this pest.")
    crop_compatible: bool = Field(True, description="True if pest is biologically compatible with user crop.")

    model_config = ConfigDict(arbitrary_types_allowed=True)


class PestPrediction(BaseModel):
    """
    Standardized output result returned by Pest Detection adapters (Section 10).
    """
    pests: List[DetectedPest] = Field(default_factory=list, description="All detected pests passing operational threshold.")
    top_pests: List[DetectedPest] = Field(default_factory=list, description="Top detected pests ranked by confidence.")
    bounding_boxes: List[BoundingBox] = Field(default_factory=list, description="Standard bounding boxes list.")
    scores: List[float] = Field(default_factory=list, description="List of confidence scores.")
    crop: Optional[str] = Field(None, description="User-specified or validated crop name.")
    crop_validation: Dict[str, Any] = Field(default_factory=dict, description="Crop validation status and details.")
    model_name: str = Field(..., description="Name of the pest detection model.")
    model_version: str = Field(..., description="Version of the model checkpoint used.")
    source_metadata: Dict[str, Any] = Field(default_factory=dict, description="Model training dataset/source metadata.")
    status: str = Field("detected", description="detected | no_pest_detected | low_score | crop_mismatch | manual_review_required")
    warnings: List[str] = Field(default_factory=list, description="Domain advisories or threshold warnings.")
    provenance: Dict[str, Any] = Field(default_factory=dict, description="Execution latency, device, backend.")

    @property
    def pest_count(self) -> int:
        """Count of detected pests."""
        return len(self.pests)

    model_config = ConfigDict(arbitrary_types_allowed=True)


class NonChemicalControl(BaseModel):
    """
    Verified Non-Chemical IPM management recommendation.
    """
    category: NonChemicalCategory = Field(..., description="cultural | mechanical | biological | preventive_monitoring")
    title: str = Field(..., description="Title of the practice.")
    description: str = Field(..., description="Detailed instructions for the farmer.")
    source_title: str = Field(..., description="Official publication name (e.g. DPPQS IPM Package).")
    source_url: str = Field(..., description="URL of official source.")
    source_date: str = Field(..., description="Publication date of source.")

    model_config = ConfigDict(arbitrary_types_allowed=True)


class ChemicalCandidate(BaseModel):
    """
    Individual registered chemical candidate from CIB&RC.
    """
    active_ingredient: str = Field(..., description="Name of the active chemical ingredient.")
    formulation: Optional[str] = Field(None, description="Approved formulation (e.g., '75% WP', '25% EC').")
    registered_for_crop: bool = Field(True, description="Whether registered for crop.")
    registered_for_target: bool = Field(True, description="Whether explicitly registered for this crop+target pair in CIBRC.")
    approved_crop: str = Field(..., description="Crop name as recorded on CIBRC label.")
    approved_target: str = Field(..., description="Target pest/disease as recorded on CIBRC label.")
    application_method: Optional[str] = Field(None, description="Approved application method (e.g., 'Foliar Spray').")
    dose_information: str = Field(
        ...,
        description="Authoritative numerical dosage if published; otherwise 'Follow the current registered product label.'"
    )
    source_id: Optional[str] = Field(None, description="Source ID reference in sources.json (e.g. SRC-CIBRC-2024).")
    source_title: str = Field(..., description="Official document name.")
    source_url: str = Field(..., description="Official URL.")
    source_date: str = Field(..., description="Official source publication date.")
    verification_date: Optional[str] = Field("2026-10-04", description="Verification date.")
    verification_status: str = Field("verified", description="verified | unverified | guidance_only")
    geographic_scope: str = Field("India", description="Geographic jurisdiction (national 'India' or state).")
    stage_specific_guidance: str = Field("unavailable", description="Growth stage guidance if documented, else 'unavailable'.")
    safety_notes: Optional[str] = Field(None, description="Toxicity, waiting period, PPE, or environmental notes.")
    notes: Optional[str] = Field(None, description="Agronomic guidance or FRAC resistance rotation group.")

    model_config = ConfigDict(arbitrary_types_allowed=True)


class TreatmentRecommendation(BaseModel):
    """
    Standardized Treatment Recommendation payload produced by TreatmentEngine.
    """
    status: RecommendationStatus = Field(..., description="Status of the recommendation.")
    reason_code: Optional[Union[ReasonCode, str]] = Field(None, description="Explicit failure or audit reason code.")
    crop: str = Field(..., description="Target crop.")
    condition: str = Field(..., description="Diagnosed condition.")
    condition_type: ConditionType = Field(..., description="disease | pest | healthy | unknown")
    non_chemical_controls: List[NonChemicalControl] = Field(default_factory=list, description="IPM non-chemical practices.")
    chemical_candidates: List[ChemicalCandidate] = Field(default_factory=list, description="Registered chemical options.")
    verification_status: str = Field("verified", description="verified | manual_review_required")
    label_verification_required: bool = Field(True, description="Strict safety requirement to check physical container label.")
    field_validation_required: bool = Field(True, description="Strict safety requirement for local extension officer validation.")
    stage_specific_guidance: str = Field("unavailable", description="Stage guidance status.")
    geographic_scope: str = Field("India", description="Geographic validity scope.")
    sources: List[str] = Field(default_factory=list, description="Authoritative reference sources.")
    source_records: List[Dict[str, Any]] = Field(default_factory=list, description="Structured source references.")
    safety_notes: List[str] = Field(default_factory=list, description="Mandatory farmer safety and handling advisories.")
    warnings: List[str] = Field(default_factory=list, description="Operational and regulatory warnings.")

    @property
    def recommendation_status(self) -> str:
        """Alias matching Section 18 property name."""
        return self.status.value

    model_config = ConfigDict(arbitrary_types_allowed=True)


class DiagnosisDetails(BaseModel):
    """Diagnosis section per Section 18."""
    crop: str = Field(..., description="Diagnosed crop name.")
    condition: str = Field(..., description="Diagnosed condition or disease.")
    condition_type: ConditionType = Field(..., description="disease | pest | healthy | unknown")
    prediction_score: float = Field(..., ge=0.0, le=1.0, description="Model prediction score.")
    top_predictions: List[TopPrediction] = Field(default_factory=list, description="Top-k predictions.")


class ValidationDetails(BaseModel):
    """Validation section per Section 18."""
    crop_match: bool = Field(..., description="True if predicted crop matches user crop.")
    crop_mismatch: bool = Field(..., description="True if predicted crop conflicts with user crop.")
    unsupported_condition: bool = Field(False, description="True if condition is unsupported.")
    unsupported_crop: bool = Field(False, description="True if user crop is unsupported.")
    reason_code: Optional[Union[ReasonCode, str]] = Field(None, description="Explicit validation failure code.")


class AgricultureDiseaseResult(BaseModel):
    """
    Unified end-to-end result schema for the Disease & Pest AI system.
    Conforms strictly to Section 18 breakdown (diagnosis, validation, treatment, provenance, warnings)
    while maintaining full backward compatibility.
    """
    diagnosis: DiagnosisDetails = Field(..., description="Section 18 Diagnosis breakdown.")
    validation: ValidationDetails = Field(..., description="Section 18 Validation breakdown.")
    treatment: TreatmentRecommendation = Field(..., description="Section 18 Treatment recommendation breakdown.")
    provenance: Dict[str, Any] = Field(default_factory=dict, description="Section 18 Provenance audit breakdown.")
    warnings: List[str] = Field(default_factory=list, description="Section 18 Warnings list.")
    vision_prediction: Optional[PredictionResult] = Field(None, description="Underlying vision model prediction result.")
    pest_prediction: Optional[PestPrediction] = Field(None, description="Section 15 Pest prediction breakdown.")
    user_crop: Optional[str] = Field(None, description="Original crop specified by the user.")

    # Backward compatibility helper constructor
    @model_validator(mode="before")
    @classmethod
    def populate_sections_if_missing(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # If diagnosis is not passed directly, construct from flat fields
            if "diagnosis" not in data and "crop" in data and "condition" in data:
                top_preds = []
                if "vision_prediction" in data and data["vision_prediction"]:
                    vp = data["vision_prediction"]
                    if hasattr(vp, "top_predictions"):
                        top_preds = vp.top_predictions
                    elif isinstance(vp, dict):
                        top_preds = vp.get("top_predictions", [])

                data["diagnosis"] = DiagnosisDetails(
                    crop=data.get("crop", ""),
                    condition=data.get("condition", ""),
                    condition_type=data.get("condition_type", ConditionType.DISEASE),
                    prediction_score=data.get("prediction_score", 0.0),
                    top_predictions=top_preds,
                )

            # If validation is not passed directly, construct from flat fields
            if "validation" not in data:
                crop_m = data.get("crop_match", True)
                crop_mm = not crop_m if "crop_match" in data else data.get("crop_mismatch", False)
                u_cond = False
                rc = None
                if "treatment" in data and hasattr(data["treatment"], "reason_code"):
                    rc = data["treatment"].reason_code
                elif "treatment" in data and isinstance(data["treatment"], dict):
                    rc = data["treatment"].get("reason_code")

                if rc == ReasonCode.UNSUPPORTED_CONDITION or rc == "UNSUPPORTED_CONDITION":
                    u_cond = True

                data["validation"] = ValidationDetails(
                    crop_match=not crop_mm,
                    crop_mismatch=crop_mm,
                    unsupported_condition=u_cond,
                    reason_code=rc,
                )

        return data

    @property
    def crop(self) -> str:
        """Backward compatibility: crop name."""
        return self.diagnosis.crop

    @property
    def condition(self) -> str:
        """Backward compatibility: condition name."""
        return self.diagnosis.condition

    @property
    def condition_type(self) -> ConditionType:
        """Backward compatibility: condition type."""
        return self.diagnosis.condition_type

    @property
    def prediction_score(self) -> float:
        """Backward compatibility: prediction score."""
        return self.diagnosis.prediction_score

    @property
    def score(self) -> float:
        """Backward compatibility: prediction score alias."""
        return self.diagnosis.prediction_score

    @property
    def crop_match(self) -> bool:
        """Backward compatibility: crop match."""
        return self.validation.crop_match

    @property
    def crop_mismatch(self) -> bool:
        """Backward compatibility: crop mismatch."""
        return self.validation.crop_mismatch

    @property
    def model_name(self) -> str:
        """Backward compatibility: vision model name."""
        if self.vision_prediction:
            return self.vision_prediction.model_name
        return str(self.provenance.get("vision_model", ""))

    @property
    def pests(self) -> List[DetectedPest]:
        """Convenience property for detected pests."""
        if self.pest_prediction:
            return self.pest_prediction.pests
        return []

    @property
    def pest_count(self) -> int:
        """Count of detected pests."""
        if self.pest_prediction:
            return self.pest_prediction.pest_count
        return 0

    model_config = ConfigDict(arbitrary_types_allowed=True)
