"""Pydantic schemas for KisanCare Plant Pathology & Disease Detection API."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TopPredictionSchema(BaseModel):
    """Candidate foliar prediction with raw softmax score and task/category attribution."""
    condition: str = Field(..., description="Disease condition, pest, or healthy foliage class")
    crop: Optional[str] = Field(None, description="Host crop taxonomy tag")
    category: str = Field("disease", description="'disease' | 'pest' | 'healthy' | 'deficiency'")
    task: str = Field("foliar_classification", description="Underlying model prediction task")
    source_model: str = Field("India Multi-Crop DINOv2 ViT-B/14", description="Model generating this prediction")
    probability: float = Field(..., ge=0.0, le=1.0, description="Uncalibrated softmax classification score (0.0 to 1.0)")
    percentage: int = Field(..., ge=0, le=100, description="Formatted softmax score percentage")


class ChemicalTreatmentSchema(BaseModel):
    """CIBRC registered chemical intervention."""
    chemical_name: str = Field(..., description="Active ingredient and formulation (e.g. Difenoconazole 25% EC)")
    dosage: str = Field(..., description="Approved application dosage")
    cpr_registration: Optional[str] = Field(None, description="CIBRC regulatory registration code")
    waiting_period_days: Optional[int] = Field(None, description="Pre-harvest interval / waiting period in days")


class BiologicalTreatmentSchema(BaseModel):
    """Biological biocontrol agent recommendation."""
    agent: str = Field(..., description="Bio-agent name (e.g. Bacillus subtilis, Trichoderma viride)")
    notes: Optional[str] = Field(None, description="Agronomic application guidelines")


class TreatmentCatalogSchema(BaseModel):
    """Structured CIBRC and IPM treatment recommendations."""
    chemical: List[ChemicalTreatmentSchema] = Field(default_factory=list)
    biological: List[BiologicalTreatmentSchema] = Field(default_factory=list)
    cultural: List[str] = Field(default_factory=list)


class DiseasePredictionRequestJSON(BaseModel):
    """JSON request schema for Disease Detection inference."""
    image_base64: Optional[str] = Field(None, description="Base64-encoded image string")
    sample_id: Optional[str] = Field(None, description="Preset test image identifier (e.g., apple_scab, tomato_blight, tomato_healthy, corn_rust, potato_blight, cotton_leaf)")
    crop: str = Field("Tomato", description="Declared host crop")
    location_state: str = Field("Maharashtra", description="Geographic state for regional/CIBRC compliance")
    growth_stage: str = Field("vegetative", description="Crop growth stage (seedling, vegetative, flowering, fruiting, maturity_harvest)")
    image_type: str = Field("leaf", description="Image modality (leaf, field_leaf, trap_sticky_sheet)")
    symptoms: Optional[List[str]] = Field(default_factory=list, description="Observed field symptoms")
    abstention_threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="Configurable abstention cutoff score (0.0-1.0)")


class DiseasePredictionResponse(BaseModel):
    """Typed response schema for Disease Detection inference."""
    condition: str = Field(..., description="Diagnosed foliar condition or healthy foliage confirmation")
    scientific_name: Optional[str] = Field(None, description="Botanical / fungal scientific nomenclature")
    condition_type: str = Field(..., description="'disease' | 'healthy' | 'pest' | 'deficiency' | 'inconclusive'")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Vision model raw softmax score")
    confidence_percent: int = Field(..., ge=0, le=100, description="Display confidence percentage")
    confidence_type: str = Field("uncalibrated_softmax", description="Statistical confidence interpretation type")
    severity: str = Field("Severity not assessed", description="Pathology severity grade ('Severity not assessed' unless calibrated field severity estimator is present)")
    is_healthy: bool = Field(False, description="Whether foliage is verified healthy")
    is_supported: bool = Field(True, description="Whether the condition or host crop is within verified model distribution")
    abstention: bool = Field(False, description="Whether the model abstained due to low confidence, high entropy, or OOD input")
    abstention_reason: Optional[str] = Field(None, description="'low_confidence' | 'unsupported_crop' | 'non_leaf' | 'conflicting_crop'")
    abstention_threshold: float = Field(0.40, description="Safety cutoff threshold below which diagnosis abstains")
    diagnosed_crop: Optional[str] = Field(None, description="Visual host crop associated with model prediction")
    host_crop_status: str = Field("verified", description="'verified' | 'unverified' | 'disputed'")
    crop_match: bool = Field(True, description="Whether visual pathogen matches declared crop")
    crop_mismatch_warning: Optional[str] = Field(None, description="Warning if visual symptoms conflict with declared crop")
    description: str = Field(..., description="Diagnostic pathology summary")
    treatment: str = Field(..., description="Primary clinical protocol and advisory")
    treatments: TreatmentCatalogSchema = Field(default_factory=TreatmentCatalogSchema)
    preventive_management: List[str] = Field(default_factory=list, description="Preventive cultural field practices")
    non_chemical_options: List[str] = Field(default_factory=list, description="Organic and biocontrol options")
    top_5_predictions: List[TopPredictionSchema] = Field(default_factory=list, description="Top candidate predictions (all categories)")
    top_disease_candidates: List[TopPredictionSchema] = Field(default_factory=list, description="Top foliar disease candidates")
    top_pest_candidates: List[TopPredictionSchema] = Field(default_factory=list, description="Top foliar pest damage candidates")
    model_type: str = Field(..., description="Model architecture identifier")
    model_identifier: Optional[str] = Field(None, description="Specific specialist or ensemble model identifier")
    routing_path: str = Field("generalist_fallback", description="'specialist_primary' | 'specialist_fused' | 'generalist_fallback'")
    specialist_agreement: Optional[bool] = Field(None, description="Concordance between specialist and generalist models")
    fusion_outcome: Optional[str] = Field(None, description="'agree' | 'disputed' | 'crop_uncertain' | 'insufficient_evidence' | 'single_model'")
    competing_predictions: List[Dict[str, Any]] = Field(default_factory=list, description="Competing candidate diagnoses when disputed or crop uncertain")
    fusion_details: Dict[str, Any] = Field(default_factory=dict, description="Multi-model fusion and cross-model agreement details")
    raw_score: Optional[float] = Field(None, description="Raw uncalibrated vision model output score")
    calibrated_confidence: Optional[float] = Field(None, description="Calibrated confidence score")
    provenance: Dict[str, Any] = Field(default_factory=dict, description="Audit trail and inference metadata")
    warnings: List[str] = Field(default_factory=list, description="Agronomic and domain warnings")
    disclaimer: str = Field(
        "Raw softmax foliar classification score. Not a confirmed laboratory diagnosis or calibrated Bayesian probability. "
        "Verify severe disease outbreaks with a certified plant pathologist or KVK agronomist before chemical application.",
        description="Mandatory scientific and legal disclaimer"
    )
