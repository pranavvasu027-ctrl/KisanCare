"""
Lab Report Field Normalizer & Agronomic Range Validator
========================================================
Validates extracted soil test values against biological and chemical plausibility
bounds, standardizes units, and preserves original reported metadata.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import re

from ml.soil_intelligence.schemas import (
    NutrientUnit,
    ChemicalForm,
    NutrientMeasurement,
    NutrientConverter,
    TestMethod,
    STANDARD_BULK_DENSITY_G_CM3
)


# Agronomic plausibility boundaries (extreme outliers trigger mandatory review)
PLENARY_BOUNDS = {
    "pH": (3.5, 10.5, "Standard agricultural soil reaction limits (extremely acidic < 3.5 or alkali > 10.5)"),
    "EC": (0.0, 15.0, "Electrical conductivity in dS/m (values > 15 dS/m indicate extreme saline wasteland)"),
    "OC": (0.01, 5.0, "Soil Organic Carbon in % (mineral agricultural soils rarely exceed 5% OC)"),
    "N": (10.0, 1200.0, "Available Nitrogen in kg/ha elemental N"),
    "P": (0.5, 250.0, "Available Phosphorus in kg/ha elemental P"),
    "K": (10.0, 2000.0, "Available Potassium in kg/ha elemental K"),
}


@dataclass
class ValidationIssue:
    field_name: str
    reported_value: Any
    severity: str                           # 'WARNING' or 'ERROR'
    issue_code: str                         # e.g., 'OUT_OF_BOUNDS', 'UNKNOWN_UNIT'
    message: str


@dataclass
class FieldNormalizationResult:
    nutrient: str
    measurement: Optional[NutrientMeasurement]
    is_plausible: bool
    requires_review: bool
    issues: List[ValidationIssue] = field(default_factory=list)


class ReportFieldNormalizer:
    """
    Standardizes raw text segments from laboratory reports into validated
    NutrientMeasurement entities while retaining raw evidence and audit logs.
    """

    @staticmethod
    def detect_unit(raw_text: str) -> Tuple[NutrientUnit, Optional[str]]:
        """Parses unit string from raw text snippet."""
        text = raw_text.lower()
        if "kg/ha" in text or "kg / ha" in text or "kg/hectare" in text or "kg\\ha" in text or "kg \\ ha" in text:
            return NutrientUnit.KG_PER_HA, "Explicitly matched kg/ha"
        elif "mg/kg" in text or "mg / kg" in text or "mg\\kg" in text:
            return NutrientUnit.MG_PER_KG, "Explicitly matched mg/kg"
        elif "ppm" in text or "parts per million" in text:
            return NutrientUnit.PPM, "Explicitly matched ppm"
        elif "%" in text or "percent" in text or "0/0" in text or "o/o" in text:
            return NutrientUnit.PERCENT, "Explicitly matched %"
        elif "ds/m" in text or "ds / m" in text or "mmhos/cm" in text or "ds\\m" in text:
            return NutrientUnit.DS_PER_M, "Explicitly matched dS/m"
        elif "ph" in text:
            return NutrientUnit.PH_INDEX, "pH scale"
        return NutrientUnit.KG_PER_HA, "Default assumed kg/ha (Warning: Unit was not explicitly stated in text)"

    @staticmethod
    def detect_chemical_form(nutrient: str, raw_text: str) -> ChemicalForm:
        """Determines if phosphorus or potassium is expressed in elemental or oxide form."""
        text = raw_text.upper()
        if nutrient.upper() in ["P", "PHOSPHORUS"]:
            if "P2O5" in text or "P205" in text or "PHOSPHATE" in text or "P₂O₅" in text:
                return ChemicalForm.OXIDE_P2O5
            return ChemicalForm.ELEMENTAL_P
        elif nutrient.upper() in ["K", "POTASSIUM"]:
            if "K2O" in text or "K20" in text or "POTASH" in text or "K₂O" in text:
                return ChemicalForm.OXIDE_K2O
            return ChemicalForm.ELEMENTAL_K
        elif nutrient.upper() in ["N", "NITROGEN"]:
            return ChemicalForm.ELEMENTAL_N
        elif nutrient.upper() in ["OC", "ORGANIC_CARBON"]:
            return ChemicalForm.ORGANIC_CARBON
        return ChemicalForm.NOT_APPLICABLE

    @classmethod
    def normalize_nutrient_field(
        cls,
        nutrient: str,
        raw_val_str: str,
        surrounding_text: str = "",
        test_method: TestMethod = TestMethod.UNSPECIFIED,
        bulk_density_g_cm3: float = STANDARD_BULK_DENSITY_G_CM3
    ) -> FieldNormalizationResult:
        """
        Extracts, converts, and validates a nutrient parameter.
        """
        issues: List[ValidationIssue] = []

        # 1. Clean and parse float value (handle OCR space instead of decimal, e.g. '0 58' -> '0.58')
        raw_trimmed = raw_val_str.strip()
        if re.match(r"^\d+\s+\d{1,2}$", raw_trimmed):
            raw_trimmed = re.sub(r"\s+", ".", raw_trimmed)

        clean_num = re.sub(r"[^\d.-]", "", raw_trimmed)
        if not clean_num:
            return FieldNormalizationResult(
                nutrient=nutrient,
                measurement=None,
                is_plausible=False,
                requires_review=True,
                issues=[ValidationIssue(
                    field_name=nutrient,
                    reported_value=raw_val_str,
                    severity="ERROR",
                    issue_code="UNPARSABLE_NUMERIC",
                    message=f"Could not parse numeric float from raw string: '{raw_val_str}'"
                )]
            )

        try:
            val = float(clean_num)
        except ValueError:
            return FieldNormalizationResult(
                nutrient=nutrient,
                measurement=None,
                is_plausible=False,
                requires_review=True,
                issues=[ValidationIssue(
                    field_name=nutrient,
                    reported_value=raw_val_str,
                    severity="ERROR",
                    issue_code="NUMERIC_CONVERSION_FAILED",
                    message=f"Numeric casting failed for: '{clean_num}'"
                )]
            )

        # 2. Detect unit and form
        combined_text = f"{raw_val_str} {surrounding_text}"
        unit, unit_explanation = cls.detect_unit(combined_text)
        form = cls.detect_chemical_form(nutrient, combined_text)

        if "Default assumed" in unit_explanation:
            issues.append(ValidationIssue(
                field_name=nutrient,
                reported_value=val,
                severity="WARNING",
                issue_code="IMPLICIT_UNIT_ASSUMPTION",
                message=unit_explanation
            ))

        # 3. Apply scientific conversion to elemental kg/ha
        normalized_val: Optional[float] = None
        conversion_applied = ""
        conversion_verified = True

        try:
            if nutrient.upper() in ["P", "PHOSPHORUS"]:
                normalized_val, conversion_applied = NutrientConverter.convert_phosphorus(
                    val, unit, form, bulk_density_g_cm3
                )
            elif nutrient.upper() in ["K", "POTASSIUM"]:
                normalized_val, conversion_applied = NutrientConverter.convert_potassium(
                    val, unit, form, bulk_density_g_cm3
                )
            elif nutrient.upper() in ["N", "NITROGEN"]:
                normalized_val, conversion_applied = NutrientConverter.convert_nitrogen(
                    val, unit, bulk_density_g_cm3
                )
            else:
                # pH, EC, OC do not convert to kg/ha
                normalized_val = val
                conversion_applied = f"Preserved as standard scale ({unit.value})"
        except ValueError as e:
            issues.append(ValidationIssue(
                field_name=nutrient,
                reported_value=val,
                severity="ERROR",
                issue_code="CONVERSION_FAILED",
                message=str(e)
            ))
            conversion_verified = False

        # 4. Check agronomic plausibility bounds
        is_plausible = True
        key = nutrient.upper()
        if key in PLENARY_BOUNDS and normalized_val is not None:
            min_bound, max_bound, bound_desc = PLENARY_BOUNDS[key]
            if normalized_val < min_bound or normalized_val > max_bound:
                is_plausible = False
                issues.append(ValidationIssue(
                    field_name=nutrient,
                    reported_value=normalized_val,
                    severity="WARNING",
                    issue_code="OUT_OF_BOUNDS",
                    message=f"Value {normalized_val} falls outside standard agronomic bounds [{min_bound}, {max_bound}]. {bound_desc}"
                ))

        measurement = NutrientMeasurement(
            nutrient=nutrient,
            reported_value=val,
            reported_unit=unit,
            reported_form=form,
            normalized_value_kg_ha=normalized_val,
            conversion_applied=conversion_applied,
            conversion_verified=conversion_verified,
            test_method=test_method,
            raw_text=raw_val_str
        )

        requires_review = (not is_plausible) or any(iss.severity == "ERROR" for iss in issues) or len(issues) > 0

        return FieldNormalizationResult(
            nutrient=nutrient,
            measurement=measurement,
            is_plausible=is_plausible,
            requires_review=requires_review,
            issues=issues
        )
