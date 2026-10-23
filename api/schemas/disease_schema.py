"""Pydantic schemas for KisanCare Plant Pathology & Disease Detection API."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TopPredictionSchema(BaseModel):
    """Candidate disease prediction with softmax probability."""
    condition: str = Field(..., description="Disease condition or healthy foliage class")
    probability: float = Field(..., ge=0.0, le=1.0, description="Softmax classification score (0.0 to 1.0)")
    percentage: int = Field(..., ge=0, le=100, description="Formatted probability percentage")


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
    sample_id: Optional[str] = Field(None, description="Preset test image identifier (e.g., apple_scab, tomato_blight, tomato_healthy, corn_rust)")
    crop: str = Field("Tomato", description="Declared host crop")
    location_state: str = Field("Maharashtra", description="Geographic state for regional/CIBRC compliance")
    growth_stage: str = Field("vegetative", description="Crop growth stage (seedling, vegetative, flowering, fruiting, maturity_harvest)")
    image_type: str = Field("leaf", description="Image modality (leaf, field_leaf, trap_sticky_sheet)")
    symptoms: Optional[List[str]] = Field(default_factory=list, description="Observed field symptoms")


class DiseasePredictionResponse(BaseModel):
    """Typed response schema for Disease Detection inference."""
    condition: str = Field(..., description="Diagnosed foliar condition or healthy foliage confirmation")
    scientific_name: Optional[str] = Field(None, description="Botanical / fungal scientific nomenclature")
    condition_type: str = Field(..., description="'disease' | 'healthy' | 'pest' | 'unknown'")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Vision model softmax score")
    confidence_percent: int = Field(..., ge=0, le=100, description="Display confidence percentage")
    confidence_type: str = Field("uncalibrated_softmax", description="Statistical confidence interpretation type")
    severity: str = Field("Medium", description="Pathology severity grade (Low, Medium, High)")
    is_healthy: bool = Field(False, description="Whether foliage is verified healthy")
    crop_match: bool = Field(True, description="Whether visual pathogen matches declared crop")
    crop_mismatch_warning: Optional[str] = Field(None, description="Warning if visual symptoms conflict with declared crop")
    description: str = Field(..., description="Diagnostic pathology summary")
    treatment: str = Field(..., description="Primary clinical protocol and advisory")
    treatments: TreatmentCatalogSchema = Field(default_factory=TreatmentCatalogSchema)
    preventive_management: List[str] = Field(default_factory=list, description="Preventive cultural field practices")
    non_chemical_options: List[str] = Field(default_factory=list, description="Organic and biocontrol options")
    top_5_predictions: List[TopPredictionSchema] = Field(default_factory=list, description="Top-5 candidate predictions")
    model_type: str = Field(..., description="Model architecture identifier")
    provenance: Dict[str, Any] = Field(default_factory=dict, description="Audit trail and inference metadata")
    warnings: List[str] = Field(default_factory=list, description="Agronomic and domain warnings")
    disclaimer: str = Field(
        "Machine learning foliar classification score. Not a confirmed laboratory diagnosis. "
        "Verify severe disease outbreaks with a certified plant pathologist or KVK agronomist before chemical application.",
        description="Mandatory scientific and legal disclaimer"
    )
