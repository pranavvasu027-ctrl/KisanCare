"""
Pydantic Request & Response Schemas for Soil Intelligence API Layer
===================================================================
Provides clean, validated data transfer objects decoupling the HTTP/FastAPI
contract from the internal ml.soil_intelligence domain models.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class NutrientUnitEnum(str, Enum):
    KG_PER_HA = "kg/ha"
    PPM = "ppm"
    MG_PER_KG = "mg/kg"
    PERCENT = "%"


class ChemicalFormEnum(str, Enum):
    ELEMENTAL_N = "N"
    OXIDE_P2O5 = "P2O5"
    ELEMENTAL_P = "P"
    OXIDE_K2O = "K2O"
    ELEMENTAL_K = "K"


class TestMethodEnum(str, Enum):
    ALKALINE_PERMANGANATE = "Alkaline Permanganate (Subbiah & Asija 1956)"
    OLSEN_SODIUM_BICARBONATE = "Olsen 0.5M NaHCO3 (Olsen et al. 1954)"
    BRAY_KURTZ_P1 = "Bray & Kurtz P1"
    AMMONIUM_ACETATE_FLAME = "Neutral 1N NH4OAc Flame Photometry (Hanway & Heidel 1952)"
    POTASSIUM_DICHROMATE_OC = "Walkley-Black Wet Oxidation (Walkley & Black 1934)"
    POTENTIOMETRIC_1_2_WATER = "1:2.5 Soil:Water Suspension pH Meter"
    ELECTRICAL_CONDUCTIVITY = "1:2 Soil:Water Conductivity Bridge"
    UNSPECIFIED = "Unspecified Standard Analytical Method"


# ---------------------------------------------------------------------------
# OCR Report Ingestion Schemas
# ---------------------------------------------------------------------------

class ParseReportRequest(BaseModel):
    """Request to parse raw soil report text or OCR text stream."""
    report_text: str = Field(..., min_length=10, description="Raw text extracted from Soil Health Card or lab certificate.")
    plot_id: Optional[str] = Field(None, description="Optional plot identifier to associate if known.")
    farm_id: Optional[str] = Field(None, description="Optional farm identifier.")


class ValidationIssueResponse(BaseModel):
    field: str
    issue_code: str
    message: str
    severity: str


class ExtractedNutrientResponse(BaseModel):
    nutrient: str
    reported_value: Optional[float] = None
    reported_unit: Optional[str] = None
    reported_form: Optional[str] = None
    normalized_value_kg_ha: Optional[float] = None
    conversion_applied: Optional[str] = None
    test_method: Optional[str] = None


class ParseReportResponse(BaseModel):
    success: bool
    report_id: Optional[str] = None
    plot_id: Optional[str] = None
    sample_date: Optional[str] = None
    ph: Optional[float] = None
    ec_ds_m: Optional[float] = None
    organic_carbon_pct: Optional[float] = None
    nitrogen: Optional[ExtractedNutrientResponse] = None
    phosphorus: Optional[ExtractedNutrientResponse] = None
    potassium: Optional[ExtractedNutrientResponse] = None
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    requires_human_review: bool
    validation_issues: List[ValidationIssueResponse] = []
    review_token: Optional[str] = None
    raw_ocr_text: Optional[str] = None


class ManualCorrectionRequest(BaseModel):
    """Agronomist manual correction for an uncertain or out-of-bounds report."""
    review_token: str
    reviewer_id: str
    corrections: Dict[str, str] = Field(..., description="Field name to corrected string value, e.g. {'Nitrogen': '240.0'}")
    notes: Optional[str] = None


# ---------------------------------------------------------------------------
# Baseline Laboratory Report Schemas
# ---------------------------------------------------------------------------

class ConfirmBaselineReportRequest(BaseModel):
    """Direct or confirmed laboratory baseline test submission."""
    plot_id: str = Field(..., min_length=1, description="Plot identifier.")
    farm_id: Optional[str] = Field("FARM_DEFAULT", description="Parent farm identifier.")
    report_id: Optional[str] = Field(None, description="Lab report or certificate serial number.")
    sample_date: str = Field(..., description="Sampling date in YYYY-MM-DD or DD-Mon-YYYY format.")
    lab_name: str = Field("District Soil Testing Laboratory", description="Name of the testing laboratory.")
    lab_certificate_no: Optional[str] = None
    lab_accreditation_id: Optional[str] = None
    accreditation_verified: bool = False
    accreditation_source: Optional[str] = None

    # Soil chemical parameters (measured / normalized)
    nitrogen_kg_ha: float = Field(..., ge=0.0, le=2000.0, description="Available Nitrogen in kg/ha.")
    phosphorus_kg_ha: float = Field(..., ge=0.0, le=500.0, description="Available Phosphorus (elemental P) in kg/ha.")
    potassium_kg_ha: float = Field(..., ge=0.0, le=3000.0, description="Available Potassium (elemental K) in kg/ha.")
    ph: float = Field(..., ge=3.0, le=11.0, description="Soil pH.")
    ec_ds_m: Optional[float] = Field(None, ge=0.0, le=20.0, description="Electrical Conductivity in dS/m.")
    organic_carbon_pct: Optional[float] = Field(None, ge=0.0, le=10.0, description="Organic Carbon percentage.")

    notes: Optional[str] = None


# ---------------------------------------------------------------------------
# Agronomic Management Events
# ---------------------------------------------------------------------------

class FertilizerEventRequest(BaseModel):
    fertilizer_grade: str = Field(..., description="Fertilizer grade or manure type (e.g., 'Urea', 'DAP', 'MOP', '10:26:26', 'FYM', 'Vermicompost').")
    quantity_kg_ha: float = Field(..., gt=0.0, le=50000.0, description="Application rate in kg/ha.")
    application_date: str = Field(..., description="Application date in YYYY-MM-DD format.")
    event_id: Optional[str] = None
    notes: Optional[str] = None


class HarvestEventRequest(BaseModel):
    crop_name: str = Field(..., description="Crop name (e.g., 'Soybean', 'Wheat', 'Cotton', 'Rice', 'Maize', 'Pigeon Pea').")
    yield_tonnes_ha: float = Field(..., gt=0.0, le=150.0, description="Harvested economic yield in metric tons per hectare.")
    harvest_date: str = Field(..., description="Harvest date in YYYY-MM-DD format.")
    residue_retained: bool = Field(False, description="Whether crop residue/straw was returned and incorporated into the soil.")
    event_id: Optional[str] = None
    notes: Optional[str] = None


class AgronomicEventResponse(BaseModel):
    event_id: str
    event_type: str
    event_date: str
    description: str
    n_flux_kg_ha: float
    p_flux_kg_ha: float
    k_flux_kg_ha: float
    source_citation: str


# ---------------------------------------------------------------------------
# Status & Advisory Schemas
# ---------------------------------------------------------------------------

class AdvisoryItemResponse(BaseModel):
    parameter: str
    status_tier: str
    status_label: Optional[str] = None
    reported_value: Optional[float] = None
    reported_unit: str
    educational_interpretation: str
    management_considerations: List[str] = []
    scientific_reference: str


class PlotStatusResponse(BaseModel):
    plot_id: str
    farm_id: Optional[str]
    as_of_date: str
    has_baseline_lab_test: bool
    baseline_date: Optional[str] = None
    baseline_lab_name: Optional[str] = None
    accreditation_verified: bool = False
    
    # Baseline measurements
    baseline_npk_kg_ha: Optional[Dict[str, float]] = None
    soil_ph: Optional[float] = None
    organic_carbon_pct: Optional[float] = None
    ec_ds_m: Optional[float] = None

    # Management ledger
    recorded_events_count: int
    net_mass_balance_ledger: Optional[Dict[str, Any]] = None

    # Operational prediction gate & abstention
    is_operational_authorized: bool = False
    abstention_reason: Optional[str] = None
    abstention_recommendation: Optional[str] = None

    # Advisory Guidance
    advisories: List[AdvisoryItemResponse] = []
    general_recommendations: List[str] = []
    agronomic_disclaimer: str


# ---------------------------------------------------------------------------
# Continuous Comparator Schemas
# ---------------------------------------------------------------------------

class CompareRetestRequest(BaseModel):
    """Subsequent accredited laboratory re-test to evaluate model performance and drift."""
    retest_date: str = Field(..., description="Date of the subsequent physical soil sample (YYYY-MM-DD).")
    retest_report_id: Optional[str] = None
    lab_name: str = Field(..., description="Testing laboratory name.")
    lab_certificate_no: Optional[str] = None
    lab_accreditation_id: Optional[str] = None
    accreditation_verified: bool = False

    nitrogen_kg_ha: float = Field(..., ge=0.0, le=2000.0)
    phosphorus_kg_ha: float = Field(..., ge=0.0, le=500.0)
    potassium_kg_ha: float = Field(..., ge=0.0, le=3000.0)
    ph: Optional[float] = Field(None, ge=3.0, le=11.0)
    organic_carbon_pct: Optional[float] = None


class SingleNutrientComparisonResponse(BaseModel):
    nutrient: str
    estimated_or_predicted_kg_ha: Optional[float]
    actual_lab_kg_ha: float
    absolute_error_kg_ha: Optional[float]
    relative_error_pct: Optional[float]
    provisional_tolerance_kg_ha: float
    within_tolerance: Optional[bool]
    directional_bias: str


class ComparisonResponse(BaseModel):
    comparison_id: str
    plot_id: str
    retest_date: str
    days_elapsed: int
    is_operational_prediction_evaluated: bool
    nitrogen_comparison: SingleNutrientComparisonResponse
    phosphorus_comparison: SingleNutrientComparisonResponse
    potassium_comparison: SingleNutrientComparisonResponse
    all_tolerances_met: Optional[bool] = None
    drift_alert: Optional[str] = None


# ---------------------------------------------------------------------------
# Benchmarks & Generic Responses
# ---------------------------------------------------------------------------

class BenchmarksResponse(BaseModel):
    supported_fertilizers: List[str]
    supported_crops: List[str]
    tolerances: Dict[str, float]
    provenance_types: List[str]


class GenericMessageResponse(BaseModel):
    status: str
    message: str
    plot_id: Optional[str] = None
