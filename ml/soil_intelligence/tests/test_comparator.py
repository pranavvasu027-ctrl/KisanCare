"""
Unit Tests for Continuous Laboratory Report Comparator (Phase 7)
================================================================
Validates:
  1. Plot ID matching validation.
  2. Physical laboratory provenance enforcement (MEASURED required).
  3. Reverse temporal ordering rejection.
  4. Per-nutrient tolerance evaluation (absolute vs. relative rules).
  5. Immutable audit ledger recording.
  6. Directional drift and systematic bias detection.
"""

import unittest
from datetime import datetime

from ml.soil_intelligence.schemas import (
    ProvenanceType,
    NutrientUnit,
    ChemicalForm,
    NutrientMeasurement,
    MeasuredLaboratoryReport,
    NutrientPrediction,
    SoilPredictionRecord,
    TestMethod,
    AgronomicTolerances
)
from ml.soil_intelligence.evaluation.comparator import SoilContinuousComparator


class TestSoilContinuousComparator(unittest.TestCase):

    def setUp(self):
        self.comparator = SoilContinuousComparator()

    def _create_prediction(
        self,
        plot_id="PLOT_MH_001",
        pred_date="2024-05-01",
        n_pred=260.0,
        p_pred=18.0,
        k_pred=310.0
    ) -> SoilPredictionRecord:
        return SoilPredictionRecord(
            prediction_id=f"PRED_{plot_id}_{pred_date}",
            plot_id=plot_id,
            prediction_date=pred_date,
            model_version="soil-intelligence-v1.0.0",
            status=ProvenanceType.ESTIMATED,
            nitrogen=NutrientPrediction(
                nutrient="N", predicted_kg_ha=n_pred, uncertainty_lower_kg_ha=n_pred - 30, uncertainty_upper_kg_ha=n_pred + 30
            ),
            phosphorus=NutrientPrediction(
                nutrient="P", predicted_kg_ha=p_pred, uncertainty_lower_kg_ha=p_pred - 6, uncertainty_upper_kg_ha=p_pred + 6
            ),
            potassium=NutrientPrediction(
                nutrient="K", predicted_kg_ha=k_pred, uncertainty_lower_kg_ha=k_pred - 40, uncertainty_upper_kg_ha=k_pred + 40
            ),
            has_valid_baseline=True,
            input_data_coverage_score=0.90
        )

    def _create_lab_report(
        self,
        plot_id="PLOT_MH_001",
        sample_date="2024-05-15",
        n_val=250.0,
        p_val=16.0,
        k_val=300.0,
        prov=ProvenanceType.MEASURED
    ) -> MeasuredLaboratoryReport:
        return MeasuredLaboratoryReport(
            report_id=f"LAB_{plot_id}_{sample_date}",
            plot_id=plot_id,
            sample_date=sample_date,
            lab_name="District Soil Testing Laboratory",
            provenance=prov,
            nitrogen=NutrientMeasurement(
                nutrient="N", reported_value=n_val, reported_unit=NutrientUnit.KG_PER_HA,
                reported_form=ChemicalForm.ELEMENTAL_N, normalized_value_kg_ha=n_val,
                conversion_applied="reported in kg/ha", conversion_verified=True,
                test_method=TestMethod.ALKALINE_PERMANGANATE
            ),
            phosphorus=NutrientMeasurement(
                nutrient="P", reported_value=p_val, reported_unit=NutrientUnit.KG_PER_HA,
                reported_form=ChemicalForm.ELEMENTAL_P, normalized_value_kg_ha=p_val,
                conversion_applied="reported in kg/ha", conversion_verified=True,
                test_method=TestMethod.OLSEN_SODIUM_BICARBONATE
            ),
            potassium=NutrientMeasurement(
                nutrient="K", reported_value=k_val, reported_unit=NutrientUnit.KG_PER_HA,
                reported_form=ChemicalForm.ELEMENTAL_K, normalized_value_kg_ha=k_val,
                conversion_applied="reported in kg/ha", conversion_verified=True,
                test_method=TestMethod.AMMONIUM_ACETATE_FLAME
            )
        )

    # -----------------------------------------------------------------
    # Test 1: Plot Mismatch Validation
    # -----------------------------------------------------------------
    def test_plot_mismatch_raises_value_error(self):
        """Comparing predictions from PLOT_A with lab reports from PLOT_B must raise ValueError."""
        pred = self._create_prediction(plot_id="PLOT_A")
        lab = self._create_lab_report(plot_id="PLOT_B")

        with self.assertRaises(ValueError) as ctx:
            self.comparator.compare_prediction_to_actual(pred, lab)
        self.assertIn("Plot ID mismatch", str(ctx.exception))

    # -----------------------------------------------------------------
    # Test 2: Physical Laboratory Provenance Enforcement
    # -----------------------------------------------------------------
    def test_non_measured_actual_report_rejected(self):
        """Comparing against non-MEASURED data (e.g. ESTIMATED or REGIONAL_MODEL) must be rejected."""
        pred = self._create_prediction(plot_id="PLOT_001")
        lab = self._create_lab_report(plot_id="PLOT_001", prov=ProvenanceType.ESTIMATED)

        with self.assertRaises(ValueError) as ctx:
            self.comparator.compare_prediction_to_actual(pred, lab)
        self.assertIn("requires physical MEASURED laboratory report", str(ctx.exception))

    # -----------------------------------------------------------------
    # Test 3: Reverse Temporal Sequence Rejection
    # -----------------------------------------------------------------
    def test_reverse_chronological_sequence_rejected(self):
        """Ground truth test sampled BEFORE the prediction target date must raise ValueError."""
        # Pred date: 2024-06-01, Lab sample date: 2024-05-01
        pred = self._create_prediction(plot_id="PLOT_001", pred_date="2024-06-01")
        lab = self._create_lab_report(plot_id="PLOT_001", sample_date="2024-05-01")

        with self.assertRaises(ValueError) as ctx:
            self.comparator.compare_prediction_to_actual(pred, lab)
        self.assertIn("precedes prediction date", str(ctx.exception))

    # -----------------------------------------------------------------
    # Test 4: Nitrogen Absolute and Relative Tolerances
    # -----------------------------------------------------------------
    def test_nitrogen_tolerance_evaluation(self):
        """Nitrogen tolerance (±25 kg/ha or ±15%) passes via absolute or relative rule."""
        # 1. Within absolute tolerance: Pred=220, Actual=200 -> diff=20 <= 25 (rel is 10% <= 15%)
        pred1 = self._create_prediction(n_pred=220.0)
        lab1 = self._create_lab_report(n_val=200.0)
        rec1 = self.comparator.compare_prediction_to_actual(pred1, lab1)
        self.assertTrue(rec1.nitrogen_comparison.within_tolerance)
        self.assertEqual(rec1.nitrogen_comparison.absolute_error_kg_ha, 20.0)
        self.assertEqual(rec1.nitrogen_comparison.relative_error_pct, 10.0)

        # 2. Within relative tolerance: Pred=550, Actual=500 -> diff=50 (> 25), but rel is 10% (<= 15%)
        pred2 = self._create_prediction(n_pred=550.0)
        lab2 = self._create_lab_report(n_val=500.0)
        rec2 = self.comparator.compare_prediction_to_actual(pred2, lab2)
        self.assertTrue(rec2.nitrogen_comparison.within_tolerance)
        self.assertEqual(rec2.nitrogen_comparison.absolute_error_kg_ha, 50.0)
        self.assertEqual(rec2.nitrogen_comparison.relative_error_pct, 10.0)

        # 3. Failing both: Pred=300, Actual=200 -> diff=100 (> 25), rel=50% (> 15%)
        pred3 = self._create_prediction(n_pred=300.0)
        lab3 = self._create_lab_report(n_val=200.0)
        rec3 = self.comparator.compare_prediction_to_actual(pred3, lab3)
        self.assertFalse(rec3.nitrogen_comparison.within_tolerance)

    # -----------------------------------------------------------------
    # Test 5: Phosphorus Tolerance Boundaries
    # -----------------------------------------------------------------
    def test_phosphorus_tolerance_evaluation(self):
        """Phosphorus tolerance: ±5 kg/ha elemental P or ±20%."""
        # Within absolute: Pred=14, Actual=10 -> diff=4 <= 5
        pred_p = self._create_prediction(p_pred=14.0)
        lab_p = self._create_lab_report(p_val=10.0)
        rec_p = self.comparator.compare_prediction_to_actual(pred_p, lab_p)
        self.assertTrue(rec_p.phosphorus_comparison.within_tolerance)

        # Outside both: Pred=25, Actual=15 -> diff=10 (> 5), rel=66.7% (> 20%)
        pred_fail = self._create_prediction(p_pred=25.0)
        lab_fail = self._create_lab_report(p_val=15.0)
        rec_fail = self.comparator.compare_prediction_to_actual(pred_fail, lab_fail)
        self.assertFalse(rec_fail.phosphorus_comparison.within_tolerance)

    # -----------------------------------------------------------------
    # Test 6: Potassium Tolerance Boundaries
    # -----------------------------------------------------------------
    def test_potassium_tolerance_evaluation(self):
        """Potassium tolerance: ±30 kg/ha elemental K or ±15%."""
        # Within absolute: Pred=225, Actual=200 -> diff=25 <= 30
        pred_k = self._create_prediction(k_pred=225.0)
        lab_k = self._create_lab_report(k_val=200.0)
        rec_k = self.comparator.compare_prediction_to_actual(pred_k, lab_k)
        self.assertTrue(rec_k.potassium_comparison.within_tolerance)

        # Outside both: Pred=300, Actual=200 -> diff=100 (> 30), rel=50% (> 15%)
        pred_k_fail = self._create_prediction(k_pred=300.0)
        lab_k_fail = self._create_lab_report(k_val=200.0)
        rec_k_fail = self.comparator.compare_prediction_to_actual(pred_k_fail, lab_k_fail)
        self.assertFalse(rec_k_fail.potassium_comparison.within_tolerance)

    # -----------------------------------------------------------------
    # Test 7: All Tolerances Met Composite Flag
    # -----------------------------------------------------------------
    def test_all_tolerances_met_composite_flag(self):
        """all_tolerances_met is True only when N, P, and K all pass."""
        # All pass
        pred_pass = self._create_prediction(n_pred=255.0, p_pred=17.0, k_pred=315.0)
        lab_pass = self._create_lab_report(n_val=250.0, p_val=16.0, k_val=300.0)
        rec_pass = self.comparator.compare_prediction_to_actual(pred_pass, lab_pass)
        self.assertTrue(rec_pass.all_tolerances_met)

        # N & K pass, but P fails -> all_tolerances_met must be False
        pred_p_fail = self._create_prediction(n_pred=255.0, p_pred=40.0, k_pred=315.0)
        rec_p_fail = self.comparator.compare_prediction_to_actual(pred_p_fail, lab_pass)
        self.assertFalse(rec_p_fail.all_tolerances_met)
        self.assertTrue(rec_p_fail.nitrogen_comparison.within_tolerance)
        self.assertFalse(rec_p_fail.phosphorus_comparison.within_tolerance)
        self.assertTrue(rec_p_fail.potassium_comparison.within_tolerance)

    # -----------------------------------------------------------------
    # Test 8: Immutable Audit Ledger Recording
    # -----------------------------------------------------------------
    def test_immutable_audit_ledger_recording(self):
        """record_and_log_comparison records comparison in audit ledger."""
        pred = self._create_prediction(plot_id="PLOT_AUDIT_01")
        lab = self._create_lab_report(plot_id="PLOT_AUDIT_01")

        rec = self.comparator.record_and_log_comparison(pred, lab)
        history = self.comparator.get_comparison_history()

        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].comparison_id, rec.comparison_id)
        self.assertEqual(history[0].plot_id, "PLOT_AUDIT_01")

    # -----------------------------------------------------------------
    # Test 9: Systematic Drift and Directional Bias Detection
    # -----------------------------------------------------------------
    def test_systematic_drift_overestimation_alert(self):
        """Detects systematic overestimation bias when mean signed error exceeds half-tolerance."""
        # N tolerance absolute bound is 25 kg/ha; half-tolerance is 12.5 kg/ha.
        # Create 5 comparisons where model consistently predicts +20 kg N above actual
        records = []
        for i in range(5):
            pred = self._create_prediction(plot_id="PLOT_DRIFT", pred_date=f"2024-0{i+1}-01", n_pred=270.0)
            lab = self._create_lab_report(plot_id="PLOT_DRIFT", sample_date=f"2024-0{i+1}-15", n_val=250.0)
            rec = self.comparator.compare_prediction_to_actual(pred, lab)
            records.append(rec)

        drift = SoilContinuousComparator.detect_systematic_drift(records, nutrient="Nitrogen")
        self.assertEqual(drift["sample_count"], 5)
        self.assertEqual(drift["mean_signed_error_kg_ha"], 20.0)
        self.assertEqual(drift["bias_direction"], "SYSTEMATIC_OVERESTIMATION")
        self.assertTrue(drift["drift_alert"])

    def test_systematic_drift_neutral_unbiased(self):
        """Unbiased predictions (mean error near zero) register NEUTRAL_UNBIASED with no alert."""
        records = []
        # Oscillating errors: +5, -5, +3, -4
        errors = [5.0, -5.0, 3.0, -4.0]
        for i, err in enumerate(errors):
            pred = self._create_prediction(plot_id="PLOT_OK", pred_date=f"2024-0{i+1}-01", n_pred=250.0 + err)
            lab = self._create_lab_report(plot_id="PLOT_OK", sample_date=f"2024-0{i+1}-15", n_val=250.0)
            rec = self.comparator.compare_prediction_to_actual(pred, lab)
            records.append(rec)

        drift = SoilContinuousComparator.detect_systematic_drift(records, nutrient="Nitrogen")
        self.assertFalse(drift["drift_alert"])
        self.assertEqual(drift["bias_direction"], "NEUTRAL_UNBIASED")


if __name__ == "__main__":
    unittest.main()
