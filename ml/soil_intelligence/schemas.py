"""
KISANcare Soil Intelligence V1 - Strict Schemas & Nutrient Tolerances
=====================================================================
Defines strict data models, scientific unit conversions, data provenance,
nutrient-specific tolerances, and evaluation comparison schemas.

Scientifically justified conversions:
  - P2O5 to elemental P: factor 2 * 30.973762 / 141.944524 = 0.4364205
  - K2O to elemental K: factor 2 * 39.0983 / 94.1960 = 0.830155
  - Elemental P to P2O5: factor 141.944524 / 61.947524 = 2.291369
  - Elemental K to K2O: factor 94.1960 / 78.1966 = 1.204605
  - ppm (mg/kg) to kg/ha for 0-15cm furrow slice at standard bulk density 1.33 g/cm3:
    mass = 10000 m2 * 0.15 m * 1333.33 kg/m3 = 2,000,000 kg -> factor 2.0
    (or custom factor when specific soil bulk density is provided).
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import math


# =====================================================================
# 1. ENUMS & CONSTANTS
# =====================================================================

class ProvenanceType(str, Enum):
    MEASURED = "MEASURED"                    # Certified laboratory / official Soil Health Card physical test
    ESTIMATED = "ESTIMATED"                  # Algorithmic prediction derived from history + agronomic balance
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"  # Data gap / baseline expired / cannot estimate
    REGIONAL_MODEL = "REGIONAL_MODEL"        # SoilGrids / ISRIC / ERA5-Land raster estimates (Context only)
    FARMER_RECORDED = "FARMER_RECORDED"      # Farmer logbook (fertilizer, crop harvest, irrigation)


class NutrientUnit(str, Enum):
    KG_PER_HA = "kg/ha"                      # Kilograms per hectare
    MG_PER_KG = "mg/kg"                      # Milligrams per kilogram (equivalent to ppm)
    PPM = "ppm"                              # Parts per million (equivalent to mg/kg)
    PERCENT = "%"                            # Percentage (common for Organic Carbon, Clay, Sand)
    DS_PER_M = "dS/m"                        # DeciSiemens per meter (Electrical Conductivity)
    PH_INDEX = "pH"                          # Standard pH scale (logarithmic hydrogen activity)


class ChemicalForm(str, Enum):
    ELEMENTAL_N = "ELEMENTAL_N"              # Available Nitrogen as N
    ELEMENTAL_P = "ELEMENTAL_P"              # Available Phosphorus as elemental P
    OXIDE_P2O5 = "OXIDE_P2O5"                # Available Phosphorus expressed as Phosphate (P2O5)
    ELEMENTAL_K = "ELEMENTAL_K"              # Available Potassium as elemental K
    OXIDE_K2O = "OXIDE_K2O"                  # Available Potassium expressed as Potash (K2O)
    ORGANIC_CARBON = "ORGANIC_CARBON"        # Soil Organic Carbon (Walkley-Black or Dumas)
    NOT_APPLICABLE = "NOT_APPLICABLE"


class TestMethod(str, Enum):
    # Nitrogen
    ALKALINE_PERMANGANATE = "Alkaline Permanganate (Subbiah & Asija 1956)"
    KJELDAHL_TOTAL = "Macro/Micro Kjeldahl Total N"
    # Phosphorus
    OLSEN_SODIUM_BICARBONATE = "Olsen 0.5M NaHCO3 (for neutral to alkaline soils, pH >= 6.5)"
    BRAY_KURTZ_NO1 = "Bray & Kurtz No. 1 (for acidic soils, pH < 6.5)"
    MEHLICH_3 = "Mehlich-3 Multi-Element"
    # Potassium
    AMMONIUM_ACETATE_FLAME = "Neutral 1N Ammonium Acetate Flame Photometry (Hanway & Heidel 1952)"
    # Reaction & Salinity
    PH_POTENTIOMETRIC_1_2 = "Potentiometric 1:2 or 1:2.5 soil:water suspension"
    EC_CONDUCTIVITY_1_2 = "Conductivity Bridge 1:2 or 1:2.5 soil:water suspension"
    # Organic Carbon
    WALKLEY_BLACK = "Walkley-Black Rapid Wet Oxidation"
    # Unknown/Unspecified
    UNSPECIFIED = "Unspecified Lab Protocol"


class ToleranceReviewStatus(str, Enum):
    PROVISIONAL_PENDING_EXPERT_APPROVAL = "PROVISIONAL_PENDING_EXPERT_APPROVAL"
    OFFICIALLY_RATIFIED = "OFFICIALLY_RATIFIED"


class EvaluationTargetStatus(str, Enum):
    MET = "MET"
    NOT_MET = "NOT_MET"
    NOT_YET_VALIDATED = "NOT_YET_VALIDATED"


# Scientifically exact stoichiometric molar ratios:
MOLAR_MASS_P = 30.973762
MOLAR_MASS_O = 15.9994
MOLAR_MASS_P2O5 = (2 * MOLAR_MASS_P) + (5 * MOLAR_MASS_O)  # 141.944524
FACTOR_P2O5_TO_P = (2 * MOLAR_MASS_P) / MOLAR_MASS_P2O5     # 0.4364205...
FACTOR_P_TO_P2O5 = MOLAR_MASS_P2O5 / (2 * MOLAR_MASS_P)     # 2.291369...

MOLAR_MASS_K = 39.0983
MOLAR_MASS_K2O = (2 * MOLAR_MASS_K) + MOLAR_MASS_O          # 94.1960
FACTOR_K2O_TO_K = (2 * MOLAR_MASS_K) / MOLAR_MASS_K2O       # 0.830155...
FACTOR_K_TO_K2O = MOLAR_MASS_K2O / (2 * MOLAR_MASS_K)       # 1.204605...

STANDARD_PLOW_DEPTH_M = 0.15                                # Standard 0-15 cm agricultural topsoil layer
STANDARD_BULK_DENSITY_G_CM3 = 1.33                          # Standard agricultural mineral soil bulk density (Mg/m3)
STANDARD_SOIL_MASS_HA_KG = 10000 * STANDARD_PLOW_DEPTH_M * (STANDARD_BULK_DENSITY_G_CM3 * 1000)  # ~1,995,000 to 2,000,000 kg


# =====================================================================
# 2. SCIENTIFIC NUTRIENT MEASUREMENT & CONVERSION
# =====================================================================

@dataclass
class NutrientMeasurement:
    """
    Represents an individual nutrient parameter reported by a laboratory or sensor.
    Preserves the original reported value and unit alongside normalized elemental kg/ha.
    """
    nutrient: str                           # 'N', 'P', 'K', 'pH', 'EC', 'OC'
    reported_value: float                   # Original numerical value extracted from report
    reported_unit: NutrientUnit             # Original unit stated on report
    reported_form: ChemicalForm             # Chemical form stated on report
    normalized_value_kg_ha: Optional[float] # Standardized available elemental nutrient in kg/ha
    conversion_applied: str                 # Exact mathematical formula and factors applied
    conversion_verified: bool               # Flag indicating conversion followed standard protocols
    test_method: TestMethod = TestMethod.UNSPECIFIED
    raw_text: Optional[str] = None          # Unaltered OCR/parsed string segment

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nutrient": self.nutrient,
            "reported_value": self.reported_value,
            "reported_unit": self.reported_unit.value,
            "reported_form": self.reported_form.value,
            "normalized_value_kg_ha": self.normalized_value_kg_ha,
            "conversion_applied": self.conversion_applied,
            "conversion_verified": self.conversion_verified,
            "test_method": self.test_method.value,
            "raw_text": self.raw_text,
        }


class NutrientConverter:
    """
    Scientifically justified conversion engine between oxide and elemental forms,
    and between gravimetric concentration (ppm, mg/kg) and spatial rate (kg/ha).
    """

    @classmethod
    def convert_phosphorus(
        cls,
        value: float,
        unit: NutrientUnit,
        form: ChemicalForm,
        bulk_density_g_cm3: float = STANDARD_BULK_DENSITY_G_CM3
    ) -> Tuple[float, str]:
        """Converts reported phosphorus to elemental P in kg/ha."""
        if value < 0:
            raise ValueError(f"Phosphorus concentration cannot be negative: {value}")

        steps = []
        val_kg_ha = value

        # 1. Convert ppm / mg/kg to kg/ha
        if unit in [NutrientUnit.MG_PER_KG, NutrientUnit.PPM]:
            # soil mass per ha = 10000 m2 * 0.15m * (bulk_density * 1000 kg/m3)
            soil_mass_kg = 10000 * STANDARD_PLOW_DEPTH_M * (bulk_density_g_cm3 * 1000)
            conversion_factor = soil_mass_kg / 1_000_000.0  # ~2.0 for 1.33 g/cm3
            val_kg_ha = value * conversion_factor
            steps.append(f"{unit.value} -> kg/ha via depth {STANDARD_PLOW_DEPTH_M}m & bulk density {bulk_density_g_cm3}g/cm3 (factor {conversion_factor:.4f})")
        elif unit == NutrientUnit.KG_PER_HA:
            steps.append("reported directly in kg/ha")
        else:
            raise ValueError(f"Invalid unit for Phosphorus: {unit}")

        # 2. Convert oxide (P2O5) to elemental P if needed
        elemental_p = val_kg_ha
        if form == ChemicalForm.OXIDE_P2O5:
            elemental_p = val_kg_ha * FACTOR_P2O5_TO_P
            steps.append(f"P2O5 -> elemental P via stoichiometric factor {FACTOR_P2O5_TO_P:.6f} [2*M(P)/M(P2O5)]")
        elif form == ChemicalForm.ELEMENTAL_P:
            steps.append("already elemental P")
        else:
            raise ValueError(f"Unsupported chemical form for Phosphorus: {form}")

        return round(elemental_p, 3), " | ".join(steps)

    @classmethod
    def convert_potassium(
        cls,
        value: float,
        unit: NutrientUnit,
        form: ChemicalForm,
        bulk_density_g_cm3: float = STANDARD_BULK_DENSITY_G_CM3
    ) -> Tuple[float, str]:
        """Converts reported potassium to elemental K in kg/ha."""
        if value < 0:
            raise ValueError(f"Potassium concentration cannot be negative: {value}")

        steps = []
        val_kg_ha = value

        # 1. Convert ppm / mg/kg to kg/ha
        if unit in [NutrientUnit.MG_PER_KG, NutrientUnit.PPM]:
            soil_mass_kg = 10000 * STANDARD_PLOW_DEPTH_M * (bulk_density_g_cm3 * 1000)
            conversion_factor = soil_mass_kg / 1_000_000.0
            val_kg_ha = value * conversion_factor
            steps.append(f"{unit.value} -> kg/ha via depth {STANDARD_PLOW_DEPTH_M}m & bulk density {bulk_density_g_cm3}g/cm3 (factor {conversion_factor:.4f})")
        elif unit == NutrientUnit.KG_PER_HA:
            steps.append("reported directly in kg/ha")
        else:
            raise ValueError(f"Invalid unit for Potassium: {unit}")

        # 2. Convert oxide (K2O) to elemental K if needed
        elemental_k = val_kg_ha
        if form == ChemicalForm.OXIDE_K2O:
            elemental_k = val_kg_ha * FACTOR_K2O_TO_K
            steps.append(f"K2O -> elemental K via stoichiometric factor {FACTOR_K2O_TO_K:.6f} [2*M(K)/M(K2O)]")
        elif form == ChemicalForm.ELEMENTAL_K:
            steps.append("already elemental K")
        else:
            raise ValueError(f"Unsupported chemical form for Potassium: {form}")

        return round(elemental_k, 3), " | ".join(steps)

    @classmethod
    def convert_nitrogen(
        cls,
        value: float,
        unit: NutrientUnit,
        bulk_density_g_cm3: float = STANDARD_BULK_DENSITY_G_CM3
    ) -> Tuple[float, str]:
        """Converts reported available nitrogen to elemental N in kg/ha."""
        if value < 0:
            raise ValueError(f"Nitrogen concentration cannot be negative: {value}")

        steps = []
        val_kg_ha = value

        if unit in [NutrientUnit.MG_PER_KG, NutrientUnit.PPM]:
            soil_mass_kg = 10000 * STANDARD_PLOW_DEPTH_M * (bulk_density_g_cm3 * 1000)
            conversion_factor = soil_mass_kg / 1_000_000.0
            val_kg_ha = value * conversion_factor
            steps.append(f"{unit.value} -> kg/ha via depth {STANDARD_PLOW_DEPTH_M}m & bulk density {bulk_density_g_cm3}g/cm3 (factor {conversion_factor:.4f})")
        elif unit == NutrientUnit.KG_PER_HA:
            steps.append("reported directly in kg/ha elemental N")
        else:
            raise ValueError(f"Invalid unit for Nitrogen: {unit}")

        return round(val_kg_ha, 3), " | ".join(steps)


# =====================================================================
# 3. PREDEFINED NUTRIENT-SPECIFIC TOLERANCES
# =====================================================================

@dataclass
class PredefinedTolerance:
    nutrient: str
    target_unit: NutrientUnit
    absolute_tolerance: float                # Max acceptable absolute error in target_unit
    relative_tolerance_pct: float            # Max acceptable percentage error (|pred - actual| / actual * 100)
    rule: str                                # E.g., 'max(absolute, relative)' or 'absolute'
    status: ToleranceReviewStatus
    agronomic_rationale: str

    def is_within_tolerance(self, predicted: float, actual: float) -> Tuple[bool, float, float]:
        """
        Calculates absolute error, relative error, and tolerance pass/fail.
        Returns: (is_within_tolerance, absolute_error, relative_error_pct)
        """
        abs_err = abs(predicted - actual)
        rel_err_pct = (abs_err / actual * 100.0) if actual > 0 else (0.0 if abs_err == 0 else 100.0)

        # Tolerance check based on defined rule
        if self.rule == "max_of_absolute_or_relative":
            allowed_by_abs = abs_err <= self.absolute_tolerance
            allowed_by_rel = (rel_err_pct <= self.relative_tolerance_pct) if actual > 0 else False
            within = allowed_by_abs or allowed_by_rel
        else:
            within = abs_err <= self.absolute_tolerance

        return within, round(abs_err, 3), round(rel_err_pct, 2)


class AgronomicTolerances:
    """
    Nutrient-specific error tolerance repository.
    Marked strictly as PROVISIONAL_PENDING_EXPERT_APPROVAL to maintain scientific integrity.
    """

    NITROGEN = PredefinedTolerance(
        nutrient="Nitrogen",
        target_unit=NutrientUnit.KG_PER_HA,
        absolute_tolerance=25.0,
        relative_tolerance_pct=15.0,
        rule="max_of_absolute_or_relative",
        status=ToleranceReviewStatus.PROVISIONAL_PENDING_EXPERT_APPROVAL,
        agronomic_rationale=(
            "Available N (Subbiah & Asija alkaline permanganate method) has high field spatial variance. "
            "Inter-laboratory testing variance is typically 10-15%. A tolerance of ±25 kg/ha or ±15% "
            "maintains fertilizer recommendation accuracy within half a classification tier (Low < 280, Medium 280-560)."
        )
    )

    PHOSPHORUS = PredefinedTolerance(
        nutrient="Phosphorus",
        target_unit=NutrientUnit.KG_PER_HA,
        absolute_tolerance=5.0,
        relative_tolerance_pct=20.0,
        rule="max_of_absolute_or_relative",
        status=ToleranceReviewStatus.PROVISIONAL_PENDING_EXPERT_APPROVAL,
        agronomic_rationale=(
            "Available elemental P values are numerically small (typically 5-60 kg/ha elemental P; Olsen extraction). "
            "A tolerance of ±5.0 kg/ha elemental P (or ±11.5 kg/ha P2O5) or ±20% accounts for rapid fixation kinetics "
            "and analytical lower-limit variance in alkaline calcareous soils."
        )
    )

    POTASSIUM = PredefinedTolerance(
        nutrient="Potassium",
        target_unit=NutrientUnit.KG_PER_HA,
        absolute_tolerance=30.0,
        relative_tolerance_pct=15.0,
        rule="max_of_absolute_or_relative",
        status=ToleranceReviewStatus.PROVISIONAL_PENDING_EXPERT_APPROVAL,
        agronomic_rationale=(
            "Available elemental K (Neutral Normal Ammonium Acetate Flame Photometry) ranges from 100-600 kg/ha. "
            "A tolerance of ±30 kg/ha elemental K (or ±36.1 kg/ha K2O) or ±15% preserves classification accuracy "
            "without imposing unrealistically tight bounds on flame photometric drift."
        )
    )

    @classmethod
    def get_tolerance(cls, nutrient: str) -> PredefinedTolerance:
        norm = nutrient.strip().lower()
        if norm in ['n', 'nitrogen']:
            return cls.NITROGEN
        elif norm in ['p', 'phosphorus']:
            return cls.PHOSPHORUS
        elif norm in ['k', 'potassium']:
            return cls.POTASSIUM
        raise KeyError(f"No predefined tolerance configured for nutrient: {nutrient}")


# =====================================================================
# 4. MEASURED LABORATORY REPORT SCHEMA
# =====================================================================

@dataclass
class MeasuredLaboratoryReport:
    """
    Represents a physical soil test report from a testing laboratory.
    Strictly isolated from estimates and modelled raster data.
    Accreditation/certification status must be explicitly verified via a
    trustworthy verification record; populated fields alone do not imply verification.
    """
    report_id: str
    plot_id: str
    sample_date: str                         # ISO-8601 (YYYY-MM-DD) or cycle string
    lab_name: str
    lab_certificate_no: Optional[str] = None
    lab_accreditation_id: Optional[str] = None
    accreditation_verified: bool = False     # Explicit verification record required (e.g., NABL registry)
    accreditation_source: Optional[str] = None # e.g. "NABL Testing Portal / State Soil Health Registry"
    provenance: ProvenanceType = ProvenanceType.MEASURED
    nitrogen: Optional[NutrientMeasurement] = None
    phosphorus: Optional[NutrientMeasurement] = None
    potassium: Optional[NutrientMeasurement] = None
    ph: Optional[float] = None
    ec_ds_m: Optional[float] = None
    organic_carbon_pct: Optional[float] = None
    soil_depth_cm: Optional[float] = 15.0
    extraction_confidence: float = 1.0       # 1.0 for manual/verified, <1.0 for automated OCR
    review_required: bool = False
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['provenance'] = self.provenance.value
        return d


# =====================================================================
# 5. REGIONAL SURFACE MODEL CONTEXT (SOILGRIDS / WEATHER)
# =====================================================================

@dataclass
class ModelledEnvironmentalContext:
    """
    Represents auxiliary environmental context derived from regional raster grids (SoilGrids, ERA5).
    EXPLICITLY ISOLATED from laboratory ground truth.
    """
    plot_id: str
    latitude: float
    longitude: float
    provenance: ProvenanceType = ProvenanceType.REGIONAL_MODEL
    sand_fraction_pct: Optional[float] = None     # SoilGrids ISRIC
    silt_fraction_pct: Optional[float] = None     # SoilGrids ISRIC
    clay_fraction_pct: Optional[float] = None     # SoilGrids ISRIC
    bulk_density_g_cm3: Optional[float] = None    # SoilGrids ISRIC
    mean_annual_rainfall_mm: Optional[float] = None
    mean_annual_temp_c: Optional[float] = None
    disclaimer: str = (
        "Regional raster models provide physical environmental texture only. "
        "They MUST NEVER be treated as ground truth or used to replace laboratory NPK measurements."
    )

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['provenance'] = self.provenance.value
        return d


# =====================================================================
# 6. MULTI-YEAR FARM HISTORY TIMELINE
# =====================================================================

@dataclass
class AgronomicEvent:
    """
    Individual dated event on a farm plot (crop harvest, fertilizer addition, lab test, irrigation).
    """
    event_id: str
    plot_id: str
    event_date: str                          # ISO-8601 (YYYY-MM-DD)
    event_type: str                          # 'LAB_TEST', 'FERTILIZER', 'CROP_HARVEST', 'IRRIGATION', 'MANURE'
    details: Dict[str, Any] = field(default_factory=dict)
    provenance: ProvenanceType = ProvenanceType.FARMER_RECORDED


@dataclass
class DynamicPlotTimeline:
    """
    Maintains a multi-year chronological history for a plot across any years
    (e.g., 2023, 2024, 2025, 2026, or earlier/later).
    Does not require fixed annual cadence.
    """
    plot_id: str
    farm_id: Optional[str] = None
    baseline_lab_reports: List[MeasuredLaboratoryReport] = field(default_factory=list)
    agronomic_events: List[AgronomicEvent] = field(default_factory=list)
    environmental_context: Optional[ModelledEnvironmentalContext] = None

    def get_last_measured_report(self, before_date: Optional[str] = None) -> Optional[MeasuredLaboratoryReport]:
        """Returns the most recent measured lab report prior to before_date."""
        if not self.baseline_lab_reports:
            return None
        valid = self.baseline_lab_reports
        if before_date:
            valid = [r for r in valid if r.sample_date <= before_date]
        if not valid:
            return None
        return sorted(valid, key=lambda r: r.sample_date)[-1]


# =====================================================================
# 7. MODEL PREDICTION & UNCERTAINTY SCHEMA
# =====================================================================

@dataclass
class NutrientPrediction:
    nutrient: str                            # 'N', 'P', 'K'
    predicted_kg_ha: float
    uncertainty_lower_kg_ha: float
    uncertainty_upper_kg_ha: float
    confidence_level: float = 0.90           # e.g., 90% confidence interval
    status: ProvenanceType = ProvenanceType.ESTIMATED
    baseline_used_id: Optional[str] = None
    days_since_baseline: Optional[int] = None


@dataclass
class SoilPredictionRecord:
    """
    Complete prediction payload for a plot at a specific target date.
    Strictly marked as ESTIMATED or INSUFFICIENT_DATA.
    """
    prediction_id: str
    plot_id: str
    prediction_date: str                     # ISO-8601
    model_version: str
    status: ProvenanceType                   # ESTIMATED or INSUFFICIENT_DATA
    nitrogen: Optional[NutrientPrediction] = None
    phosphorus: Optional[NutrientPrediction] = None
    potassium: Optional[NutrientPrediction] = None
    input_data_coverage_score: float = 0.0   # [0.0, 1.0]
    has_valid_baseline: bool = False
    months_since_last_test: Optional[float] = None
    abstain_reason: Optional[str] = None
    retesting_advice: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['status'] = self.status.value
        return d


# =====================================================================
# 8. EVALUATION & CONTINUOUS COMPARISON RECORD SCHEMA
# =====================================================================

@dataclass
class SingleNutrientComparison:
    nutrient: str
    predicted_kg_ha: float
    actual_measured_kg_ha: float
    absolute_error_kg_ha: float
    relative_error_pct: float
    tolerance_applied: PredefinedTolerance
    within_tolerance: bool


@dataclass
class EvaluationComparisonRecord:
    """
    Pairs an earlier prediction (ESTIMATED) against a later physical laboratory test (MEASURED).
    Provides an immutable record of model performance.
    """
    comparison_id: str
    plot_id: str
    prediction_id: str
    prediction_date: str
    lab_report_id: str
    lab_sample_date: str
    days_between_pred_and_sample: int
    nitrogen_comparison: Optional[SingleNutrientComparison] = None
    phosphorus_comparison: Optional[SingleNutrientComparison] = None
    potassium_comparison: Optional[SingleNutrientComparison] = None
    all_tolerances_met: bool = False
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class NutrientEvaluationSummary:
    """Summary metrics per individual nutrient across an evaluation test set."""
    nutrient: str
    sample_count: int
    mae: float
    rmse: float
    within_tolerance_count: int
    within_tolerance_rate_pct: float
    target_tolerance_rate_pct: float = 80.0
    target_status: EvaluationTargetStatus = EvaluationTargetStatus.NOT_YET_VALIDATED
    tolerance_definition: str = ""
    status_explanation: str = ""


@dataclass
class ComprehensiveEvaluationReport:
    """
    Complete evaluation report across N, P, and K.
    Never conceals one nutrient's poor performance behind another.
    """
    evaluation_id: str
    model_version: str
    evaluation_date: str
    split_strategy: str                      # 'GROUPED_PLOT_TIME_SERIES'
    nitrogen_summary: NutrientEvaluationSummary
    phosphorus_summary: NutrientEvaluationSummary
    potassium_summary: NutrientEvaluationSummary
    overall_gate_status: EvaluationTargetStatus
    data_provenance_verified: bool
    data_readiness_status: str
