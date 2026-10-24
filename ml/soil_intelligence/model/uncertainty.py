"""
Uncertainty Representation & Error Decomposition
================================================
Models and decomposes the sources of uncertainty in soil nutrient intelligence.

SCIENTIFIC PRINCIPLES:
1. Never label uncertainty as "calibrated" unless empirical calibration has been
   demonstrated on independent, accredited holdout datasets (e.g. conformal prediction
   or quantile regression error bounds).
2. Decompose composite uncertainty into explicit physical sources:
   - Laboratory analytical measurement uncertainty
   - Farmer-recorded management variance (application uniformity, yield estimation)
   - Agronomic coefficient uncertainty (literature uptake benchmarks)
   - Temporal drift and unrecorded gap uncertainty
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, List, Optional, Any
import math


class CalibrationStatus(str, Enum):
    UNCALIBRATED_HEURISTIC_BOUND = "UNCALIBRATED_HEURISTIC_BOUND"
    EMPIRICALLY_CALIBRATED = "EMPIRICALLY_CALIBRATED"


class UncertaintySourceType(str, Enum):
    LABORATORY_ANALYTICAL = "LABORATORY_ANALYTICAL"
    FARMER_RECORDED_EVENT = "FARMER_RECORDED_EVENT"
    AGRONOMIC_COEFFICIENT = "AGRONOMIC_COEFFICIENT"
    TEMPORAL_DRIFT_AND_GAPS = "TEMPORAL_DRIFT_AND_GAPS"
    EMPIRICAL_MODEL_RESIDUAL = "EMPIRICAL_MODEL_RESIDUAL"


@dataclass
class SingleNutrientUncertainty:
    nutrient: str                            # 'N', 'P', 'K'
    measurement_variance_kg_ha: float        # Analytical lab variance
    farmer_event_variance_kg_ha: float       # Logging/uniformity variance
    agronomic_coeff_variance_kg_ha: float    # Literature benchmark variance
    temporal_gap_variance_kg_ha: float       # Unrecorded drift variance
    total_composite_bound_kg_ha: float       # ± combined bound
    calibration_status: CalibrationStatus = CalibrationStatus.UNCALIBRATED_HEURISTIC_BOUND
    assumptions: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['calibration_status'] = self.calibration_status.value
        return d


@dataclass
class SoilUncertaintyBreakdown:
    plot_id: str
    target_date: str
    calibration_status: CalibrationStatus
    nitrogen_uncertainty: SingleNutrientUncertainty
    phosphorus_uncertainty: SingleNutrientUncertainty
    potassium_uncertainty: SingleNutrientUncertainty
    general_disclaimer: str = (
        "SCIENTIFIC HONESTY DISCLAIMER: Uncertainty bounds are uncalibrated heuristic "
        "bounds propagated from known agronomic benchmarks. They MUST NOT be represented "
        "as empirically calibrated confidence intervals or statistical prediction bands "
        "until verified on independent ground-truth test sets."
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plot_id": self.plot_id,
            "target_date": self.target_date,
            "calibration_status": self.calibration_status.value,
            "nitrogen_uncertainty": self.nitrogen_uncertainty.to_dict(),
            "phosphorus_uncertainty": self.phosphorus_uncertainty.to_dict(),
            "potassium_uncertainty": self.potassium_uncertainty.to_dict(),
            "general_disclaimer": self.general_disclaimer,
        }


class UncertaintyEngine:
    """
    Decomposes and computes defensible, uncalibrated uncertainty bounds
    for nitrogen, phosphorus, and potassium.
    """

    @classmethod
    def decompose_uncertainty(
        cls,
        plot_id: str,
        target_date: str,
        baseline_n_kg_ha: Optional[float] = None,
        baseline_p_kg_ha: Optional[float] = None,
        baseline_k_kg_ha: Optional[float] = None,
        ledger_unc_n: float = 0.0,
        ledger_unc_p: float = 0.0,
        ledger_unc_k: float = 0.0,
        unrecorded_gap_days: int = 0,
        months_since_baseline: float = 0.0,
        has_unverified_proxies: bool = False
    ) -> SoilUncertaintyBreakdown:
        """
        Calculates separate physical uncertainty components per nutrient.
        """
        def compute_single(nutrient: str, baseline_val: Optional[float], ledger_unc: float) -> SingleNutrientUncertainty:
            assumptions = []
            limitations = [
                "Uncertainty terms are combined in quadrature assuming zero covariance.",
                "Systematic farmer under-reporting or continuous calibration drift may widen real error bounds."
            ]

            # 1. Laboratory analytical variance (~10% for N/K, ~15% for Olsen P)
            if baseline_val and baseline_val > 0:
                rel_lab_error = 0.15 if nutrient == "P" else 0.10
                lab_var = (baseline_val * rel_lab_error) ** 2
                assumptions.append(f"Laboratory testing analytical variance estimated at ±{rel_lab_error*100:.0f}% of measured baseline.")
            else:
                lab_var = 25.0 ** 2 if nutrient != "P" else 5.0 ** 2
                assumptions.append("No baseline test available; assigned default baseline uncertainty.")

            # 2. Farmer event variance (from mass-balance flux calculations)
            event_var = (ledger_unc * 0.60) ** 2
            assumptions.append("Farmer-recorded application rate non-uniformity and harvest yield estimation variance included.")

            # 3. Agronomic coefficient variance (literature benchmark variance)
            coeff_multiplier = 1.50 if has_unverified_proxies else 1.0
            coeff_var = ((ledger_unc * 0.40) * coeff_multiplier) ** 2
            if has_unverified_proxies:
                assumptions.append("Unverified crop proxy in history: coefficient variance increased by 50%.")

            # 4. Temporal drift and unrecorded gap uncertainty
            # Time drift increases with months elapsed and unrecorded gap days
            time_drift_factor = 0.08 if nutrient == "N" else (0.02 if nutrient == "P" else 0.05)
            gap_drift = (unrecorded_gap_days * time_drift_factor) + (months_since_baseline * 0.5)
            gap_var = gap_drift ** 2
            assumptions.append(f"Temporal mineralization/leaching drift variance scaled with {months_since_baseline:.1f} months elapsed.")

            total_var = lab_var + event_var + coeff_var + gap_var
            total_bound = round(math.sqrt(total_var), 2)

            return SingleNutrientUncertainty(
                nutrient=nutrient,
                measurement_variance_kg_ha=round(lab_var, 2),
                farmer_event_variance_kg_ha=round(event_var, 2),
                agronomic_coeff_variance_kg_ha=round(coeff_var, 2),
                temporal_gap_variance_kg_ha=round(gap_var, 2),
                total_composite_bound_kg_ha=total_bound,
                calibration_status=CalibrationStatus.UNCALIBRATED_HEURISTIC_BOUND,
                assumptions=assumptions,
                limitations=limitations
            )

        n_unc = compute_single("N", baseline_n_kg_ha, ledger_unc_n)
        p_unc = compute_single("P", baseline_p_kg_ha, ledger_unc_p)
        k_unc = compute_single("K", baseline_k_kg_ha, ledger_unc_k)

        return SoilUncertaintyBreakdown(
            plot_id=plot_id,
            target_date=target_date,
            calibration_status=CalibrationStatus.UNCALIBRATED_HEURISTIC_BOUND,
            nitrogen_uncertainty=n_unc,
            phosphorus_uncertainty=p_unc,
            potassium_uncertainty=k_unc
        )
