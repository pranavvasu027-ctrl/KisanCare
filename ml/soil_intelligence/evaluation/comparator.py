"""
KISANcare Soil Intelligence V1 - Continuous Laboratory Report Comparator
========================================================================
Continuously compares historical model predictions (ESTIMATED) against newly
received physical laboratory soil test reports (MEASURED) for identical plots.

Adheres strictly to scientific safeguards:
  1. Strict Provenance Separation: Physical laboratory ground truth is never
     overwritten, imputed, or conflated with estimates.
  2. Independent Nutrient Evaluation: Errors and tolerances are evaluated separately
     for Nitrogen (N), Phosphorus (P), and Potassium (K).
  3. Predefined Agronomic Tolerances: Evaluated using predefined thresholds
     (N: ±25 kg/ha or ±15%, P: ±5 kg/ha or ±20%, K: ±30 kg/ha or ±15%).
  4. Immutable Audit Trail: Every comparison record is preserved with timestamps,
     days elapsed, absolute errors, relative percentages, and tolerance pass/fail.
  5. Directional Drift & Bias Detection: Analyzes whether predictions systematically
     over- or under-estimate actual nutrient availability across seasons.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import uuid
import math

from ml.soil_intelligence.schemas import (
    ProvenanceType,
    NutrientUnit,
    SingleNutrientComparison,
    EvaluationComparisonRecord,
    PredefinedTolerance,
    AgronomicTolerances,
    MeasuredLaboratoryReport,
    SoilPredictionRecord
)


class SoilContinuousComparator:
    """
    Continuous comparison engine pairing predictions with newly arrived
    physical laboratory ground truth. Maintains an immutable comparison ledger.
    """

    def __init__(self):
        self._comparison_ledger: List[EvaluationComparisonRecord] = []

    def compare_prediction_to_actual(
        self,
        prediction: SoilPredictionRecord,
        actual_lab_report: MeasuredLaboratoryReport,
        comparison_id: Optional[str] = None
    ) -> EvaluationComparisonRecord:
        """
        Pairs an earlier prediction against a later physical laboratory test for the same plot.
        Calculates absolute and relative errors against predefined nutrient tolerances.
        """
        # 1. Validation: Plot matching
        if prediction.plot_id.strip() != actual_lab_report.plot_id.strip():
            raise ValueError(
                f"Plot ID mismatch: Prediction plot '{prediction.plot_id}' does not match "
                f"laboratory report plot '{actual_lab_report.plot_id}'."
            )

        # 2. Validation: Physical laboratory provenance required
        if actual_lab_report.provenance != ProvenanceType.MEASURED:
            raise ValueError(
                f"Ground-truth comparison requires physical MEASURED laboratory report. "
                f"Received provenance: {actual_lab_report.provenance.value}"
            )

        # 3. Validation: Temporal chronological order
        try:
            d_pred = datetime.strptime(prediction.prediction_date, "%Y-%m-%d")
            d_sample = datetime.strptime(actual_lab_report.sample_date, "%Y-%m-%d")
        except ValueError as e:
            # Handle timestamps with time components if present
            try:
                d_pred = datetime.fromisoformat(prediction.prediction_date.replace("Z", "+00:00"))
                d_sample = datetime.fromisoformat(actual_lab_report.sample_date.replace("Z", "+00:00"))
            except Exception:
                raise ValueError(f"Invalid date format: pred='{prediction.prediction_date}', sample='{actual_lab_report.sample_date}'")

        days_between = (d_sample.date() - d_pred.date()).days if hasattr(d_sample, 'date') else (d_sample - d_pred).days
        if days_between < 0:
            raise ValueError(
                f"Invalid temporal sequence: Ground-truth sample date ({actual_lab_report.sample_date}) "
                f"precedes prediction date ({prediction.prediction_date}) by {abs(days_between)} days. "
                "Cannot evaluate future laboratory measurements against past predictions."
            )

        # 4. Compare Nitrogen
        n_comp = None
        if prediction.nitrogen and actual_lab_report.nitrogen and actual_lab_report.nitrogen.normalized_value_kg_ha is not None:
            pred_n = prediction.nitrogen.predicted_kg_ha
            act_n = actual_lab_report.nitrogen.normalized_value_kg_ha
            tol_n = AgronomicTolerances.get_tolerance("N")
            within_n, abs_n, rel_n = tol_n.is_within_tolerance(predicted=pred_n, actual=act_n)
            n_comp = SingleNutrientComparison(
                nutrient="Nitrogen",
                predicted_kg_ha=pred_n,
                actual_measured_kg_ha=act_n,
                absolute_error_kg_ha=abs_n,
                relative_error_pct=rel_n,
                tolerance_applied=tol_n,
                within_tolerance=within_n
            )

        # 5. Compare Phosphorus
        p_comp = None
        if prediction.phosphorus and actual_lab_report.phosphorus and actual_lab_report.phosphorus.normalized_value_kg_ha is not None:
            pred_p = prediction.phosphorus.predicted_kg_ha
            act_p = actual_lab_report.phosphorus.normalized_value_kg_ha
            tol_p = AgronomicTolerances.get_tolerance("P")
            within_p, abs_p, rel_p = tol_p.is_within_tolerance(predicted=pred_p, actual=act_p)
            p_comp = SingleNutrientComparison(
                nutrient="Phosphorus",
                predicted_kg_ha=pred_p,
                actual_measured_kg_ha=act_p,
                absolute_error_kg_ha=abs_p,
                relative_error_pct=rel_p,
                tolerance_applied=tol_p,
                within_tolerance=within_p
            )

        # 6. Compare Potassium
        k_comp = None
        if prediction.potassium and actual_lab_report.potassium and actual_lab_report.potassium.normalized_value_kg_ha is not None:
            pred_k = prediction.potassium.predicted_kg_ha
            act_k = actual_lab_report.potassium.normalized_value_kg_ha
            tol_k = AgronomicTolerances.get_tolerance("K")
            within_k, abs_k, rel_k = tol_k.is_within_tolerance(predicted=pred_k, actual=act_k)
            k_comp = SingleNutrientComparison(
                nutrient="Potassium",
                predicted_kg_ha=pred_k,
                actual_measured_kg_ha=act_k,
                absolute_error_kg_ha=abs_k,
                relative_error_pct=rel_k,
                tolerance_applied=tol_k,
                within_tolerance=within_k
            )

        # 7. Check if all available nutrient tolerances were met
        available_comps = [c for c in [n_comp, p_comp, k_comp] if c is not None]
        if not available_comps:
            all_met = False
        else:
            all_met = all(c.within_tolerance for c in available_comps)

        cid = comparison_id or f"COMP_{prediction.plot_id}_{actual_lab_report.sample_date}_{uuid.uuid4().hex[:6]}"

        return EvaluationComparisonRecord(
            comparison_id=cid,
            plot_id=prediction.plot_id,
            prediction_id=prediction.prediction_id,
            prediction_date=prediction.prediction_date,
            lab_report_id=actual_lab_report.report_id,
            lab_sample_date=actual_lab_report.sample_date,
            days_between_pred_and_sample=days_between,
            nitrogen_comparison=n_comp,
            phosphorus_comparison=p_comp,
            potassium_comparison=k_comp,
            all_tolerances_met=all_met
        )

    def record_and_log_comparison(
        self,
        prediction: SoilPredictionRecord,
        actual_lab_report: MeasuredLaboratoryReport,
        comparison_id: Optional[str] = None
    ) -> EvaluationComparisonRecord:
        """
        Executes comparison and appends the resulting record to the immutable audit ledger.
        """
        record = self.compare_prediction_to_actual(prediction, actual_lab_report, comparison_id)
        self._comparison_ledger.append(record)
        return record

    def get_comparison_history(self, plot_id: Optional[str] = None) -> List[EvaluationComparisonRecord]:
        """
        Returns an immutable copy of the recorded comparisons, optionally filtered by plot_id.
        """
        if plot_id:
            return [r for r in self._comparison_ledger if r.plot_id == plot_id]
        return list(self._comparison_ledger)

    def clear_ledger(self) -> None:
        """Clears the in-memory comparison ledger (for testing only)."""
        self._comparison_ledger.clear()

    @staticmethod
    def detect_systematic_drift(
        records: List[EvaluationComparisonRecord],
        nutrient: str = "Nitrogen"
    ) -> Dict[str, Any]:
        """
        Analyzes directional bias (mean signed error) to detect whether predictions
        are systematically drifting above or below actual laboratory measurements.
        """
        norm_nut = nutrient.strip().lower()
        signed_errors: List[float] = []
        abs_errors: List[float] = []

        for r in records:
            comp: Optional[SingleNutrientComparison] = None
            if norm_nut in ['n', 'nitrogen']:
                comp = r.nitrogen_comparison
            elif norm_nut in ['p', 'phosphorus']:
                comp = r.phosphorus_comparison
            elif norm_nut in ['k', 'potassium']:
                comp = r.potassium_comparison

            if comp is not None:
                err = comp.predicted_kg_ha - comp.actual_measured_kg_ha
                signed_errors.append(err)
                abs_errors.append(abs(err))

        if not signed_errors:
            return {
                "nutrient": nutrient,
                "sample_count": 0,
                "mean_signed_error_kg_ha": 0.0,
                "mae_kg_ha": 0.0,
                "bias_direction": "INSUFFICIENT_DATA",
                "drift_alert": False,
                "interpretation": f"No paired comparisons on record for nutrient '{nutrient}'."
            }

        mean_signed_err = round(sum(signed_errors) / len(signed_errors), 2)
        mae = round(sum(abs_errors) / len(abs_errors), 2)

        tol = AgronomicTolerances.get_tolerance(nutrient)
        drift_threshold = tol.absolute_tolerance * 0.50

        drift_alert = abs(mean_signed_err) >= drift_threshold

        if mean_signed_err > drift_threshold:
            bias = "SYSTEMATIC_OVERESTIMATION"
            interp = (
                f"Model systematically overestimates available {nutrient} by an average of "
                f"+{mean_signed_err:.1f} kg/ha. Suggests crop nutrient removal is under-accounted "
                "or fertilizer availability is over-credited."
            )
        elif mean_signed_err < -drift_threshold:
            bias = "SYSTEMATIC_UNDERESTIMATION"
            interp = (
                f"Model systematically underestimates available {nutrient} by an average of "
                f"{mean_signed_err:.1f} kg/ha. Suggests native soil replenishment or unrecorded "
                "organic inputs are occurring."
            )
        else:
            bias = "NEUTRAL_UNBIASED"
            interp = (
                f"No significant directional bias detected for {nutrient} "
                f"(mean signed error {mean_signed_err:+.1f} kg/ha within ±{drift_threshold:.1f} kg/ha threshold)."
            )

        return {
            "nutrient": nutrient,
            "sample_count": len(signed_errors),
            "mean_signed_error_kg_ha": mean_signed_err,
            "mae_kg_ha": mae,
            "bias_direction": bias,
            "drift_alert": drift_alert,
            "interpretation": interp
        }
