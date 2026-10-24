"""
End-to-End Soil Intelligence Pipeline Integration Test (Phases 1 - 7)
=====================================================================
Validates the complete lifecycle of a farm plot across the full Soil Intelligence pipeline:
  Phase 1: Provenance & Data-Readiness verification.
  Phase 2: Strict schemas, stoichiometry, and nutrient tolerances.
  Phase 3: Laboratory report ingestion & OCR normalization.
  Phase 4: Dynamic multi-year management timeline & depletion mass-balance.
  Phase 5: Safe prediction engine with heuristic uncertainty bounds & abstention.
  Phase 6: ISO 32000-1 PDF report generation & agronomic educational guidance.
  Phase 7: Continuous laboratory comparator & leakage-safe holdout evaluation.
"""

import unittest

from ml.soil_intelligence.schemas import (
    ProvenanceType,
    NutrientUnit,
    ChemicalForm,
    NutrientMeasurement,
    MeasuredLaboratoryReport,
    ModelledEnvironmentalContext,
    EvaluationTargetStatus,
    TestMethod,
    SoilPredictionRecord,
    NutrientPrediction
)
from ml.soil_intelligence.timeline.timeline_manager import PlotTimelineManager
from ml.soil_intelligence.model.predictor import SoilIntelligencePredictor
from ml.soil_intelligence.reporting.report_builder import SoilReportBuilder
from ml.soil_intelligence.reporting.pdf_generator import SoilIntelligencePDFGenerator
from ml.soil_intelligence.evaluation.comparator import SoilContinuousComparator
from ml.soil_intelligence.evaluation.evaluator import SoilIntelligenceEvaluator


class TestEndToEndSoilIntelligencePipeline(unittest.TestCase):

    def test_complete_soil_intelligence_lifecycle(self):
        """
        Executes the entire Soil Intelligence workflow for a plot from initial baseline
        to multi-year management, reporting, re-testing, and continuous evaluation.
        """
        # -------------------------------------------------------------
        # 1. Baseline Physical Laboratory Test (2023-06-15)
        # -------------------------------------------------------------
        lab_2023 = MeasuredLaboratoryReport(
            report_id="LAB_MH_LAT_881_2023",
            plot_id="PLOT_MH_LAT_881",
            sample_date="2023-06-15",
            lab_name="District Soil Testing Laboratory, Latur",
            lab_certificate_no="STL-2023-8871",
            lab_accreditation_id="NABL-TC-8812",
            accreditation_verified=True,
            accreditation_source="NABL State Accreditation Portal",
            provenance=ProvenanceType.MEASURED,
            nitrogen=NutrientMeasurement(
                nutrient="N", reported_value=245.0, reported_unit=NutrientUnit.KG_PER_HA,
                reported_form=ChemicalForm.ELEMENTAL_N, normalized_value_kg_ha=245.0,
                conversion_applied="reported directly in kg/ha", conversion_verified=True,
                test_method=TestMethod.ALKALINE_PERMANGANATE
            ),
            phosphorus=NutrientMeasurement(
                nutrient="P", reported_value=18.5, reported_unit=NutrientUnit.KG_PER_HA,
                reported_form=ChemicalForm.ELEMENTAL_P, normalized_value_kg_ha=18.5,
                conversion_applied="reported directly in kg/ha", conversion_verified=True,
                test_method=TestMethod.OLSEN_SODIUM_BICARBONATE
            ),
            potassium=NutrientMeasurement(
                nutrient="K", reported_value=320.0, reported_unit=NutrientUnit.KG_PER_HA,
                reported_form=ChemicalForm.ELEMENTAL_K, normalized_value_kg_ha=320.0,
                conversion_applied="reported directly in kg/ha", conversion_verified=True,
                test_method=TestMethod.AMMONIUM_ACETATE_FLAME
            ),
            ph=7.8,
            ec_ds_m=0.35,
            organic_carbon_pct=0.52
        )

        timeline = PlotTimelineManager(plot_id="PLOT_MH_LAT_881", farm_id="FARM_LAT_01")
        timeline.add_lab_report(lab_2023)

        # -------------------------------------------------------------
        # 2. Intermediate Multi-Year Management Activity (2023 - 2024)
        # -------------------------------------------------------------
        # 2023 Kharif: DAP fertilizer application followed by Soybean harvest
        timeline.record_fertilizer_application("DAP", 100.0, "2023-06-20")
        timeline.record_crop_harvest("Soybean", 2.2, "2023-10-15")

        # 2023-2024 Rabi: Urea fertilizer application followed by Wheat harvest
        timeline.record_fertilizer_application("Urea", 80.0, "2023-11-10")
        timeline.record_crop_harvest("Wheat", 3.2, "2024-03-20")

        # -------------------------------------------------------------
        # 3. Model Inference & Prediction Query (Target Date: 2024-05-01)
        # -------------------------------------------------------------
        predictor = SoilIntelligencePredictor()
        intel_report = predictor.evaluate_plot(timeline, target_date="2024-05-01")

        # Verify operational prediction gate is strictly blocked
        self.assertFalse(intel_report.is_operational_authorized)
        self.assertIsNotNone(intel_report.mass_balance_ledger)
        self.assertEqual(intel_report.mass_balance_ledger.start_date, "2023-06-15")
        self.assertEqual(intel_report.mass_balance_ledger.end_date, "2024-05-01")

        # -------------------------------------------------------------
        # 4. View Model Assembly & PDF Report Generation
        # -------------------------------------------------------------
        vm = SoilReportBuilder.build_view_model(timeline, intel_report)
        pdf_gen = SoilIntelligencePDFGenerator()
        pdf_bytes = pdf_gen.generate_pdf_bytes(vm)

        self.assertTrue(pdf_bytes.startswith(b"%PDF-1.4"))
        self.assertTrue(pdf_bytes.endswith(b"%%EOF\n"))
        self.assertIn(b"1. Laboratory Baseline Soil Measurements", pdf_bytes)
        self.assertIn(b"VERIFIED ACCREDITED", pdf_bytes)
        self.assertIn(b"NABL State Accreditation Portal", pdf_bytes)

        # -------------------------------------------------------------
        # 5. Subsequent Laboratory Ground-Truth Test (2024-05-15)
        # -------------------------------------------------------------
        lab_2024 = MeasuredLaboratoryReport(
            report_id="LAB_MH_LAT_881_2024",
            plot_id="PLOT_MH_LAT_881",
            sample_date="2024-05-15",
            lab_name="District Soil Testing Laboratory, Latur",
            lab_certificate_no="STL-2024-1102",
            lab_accreditation_id="NABL-TC-8812",
            accreditation_verified=True,
            provenance=ProvenanceType.MEASURED,
            nitrogen=NutrientMeasurement(
                nutrient="N", reported_value=238.0, reported_unit=NutrientUnit.KG_PER_HA,
                reported_form=ChemicalForm.ELEMENTAL_N, normalized_value_kg_ha=238.0,
                conversion_applied="reported directly in kg/ha", conversion_verified=True,
                test_method=TestMethod.ALKALINE_PERMANGANATE
            ),
            phosphorus=NutrientMeasurement(
                nutrient="P", reported_value=17.2, reported_unit=NutrientUnit.KG_PER_HA,
                reported_form=ChemicalForm.ELEMENTAL_P, normalized_value_kg_ha=17.2,
                conversion_applied="reported directly in kg/ha", conversion_verified=True,
                test_method=TestMethod.OLSEN_SODIUM_BICARBONATE
            ),
            potassium=NutrientMeasurement(
                nutrient="K", reported_value=305.0, reported_unit=NutrientUnit.KG_PER_HA,
                reported_form=ChemicalForm.ELEMENTAL_K, normalized_value_kg_ha=305.0,
                conversion_applied="reported directly in kg/ha", conversion_verified=True,
                test_method=TestMethod.AMMONIUM_ACETATE_FLAME
            ),
            ph=7.75,
            ec_ds_m=0.38,
            organic_carbon_pct=0.54
        )

        # -------------------------------------------------------------
        # 6. Continuous Comparison Engine (Phase 7)
        # -------------------------------------------------------------
        comparator = SoilContinuousComparator()
        
        # Scenario A: Predictor safely abstained (operational prediction gate blocked)
        abstained_pred = intel_report.prediction_record
        self.assertIsNotNone(abstained_pred)
        self.assertIsNone(abstained_pred.nitrogen)  # Predictor refused to invent numbers

        comp_abstained = comparator.record_and_log_comparison(abstained_pred, lab_2024)
        self.assertIsNone(comp_abstained.nitrogen_comparison)  # Handled safely without guessing

        # Scenario B: Estimated historical prediction record with mass-balance numbers
        active_pred = SoilPredictionRecord(
            prediction_id="PRED_MH_LAT_881_20240501",
            plot_id="PLOT_MH_LAT_881",
            prediction_date="2024-05-01",
            model_version="soil-intelligence-v1.0.0",
            status=ProvenanceType.ESTIMATED,
            nitrogen=NutrientPrediction("N", predicted_kg_ha=240.0, uncertainty_lower_kg_ha=210.0, uncertainty_upper_kg_ha=270.0),
            phosphorus=NutrientPrediction("P", predicted_kg_ha=17.5, uncertainty_lower_kg_ha=12.0, uncertainty_upper_kg_ha=23.0),
            potassium=NutrientPrediction("K", predicted_kg_ha=310.0, uncertainty_lower_kg_ha=270.0, uncertainty_upper_kg_ha=350.0)
        )

        comp_record = comparator.record_and_log_comparison(active_pred, lab_2024)
        self.assertEqual(comp_record.plot_id, "PLOT_MH_LAT_881")
        self.assertEqual(comp_record.days_between_pred_and_sample, 14)

        # Nitrogen: pred=240.0, actual=238.0 -> error=2.0 kg/ha (within tolerance)
        self.assertTrue(comp_record.nitrogen_comparison.within_tolerance)
        self.assertEqual(comp_record.nitrogen_comparison.absolute_error_kg_ha, 2.0)

        # Phosphorus: pred=17.5, actual=17.2 -> error=0.3 kg/ha (within tolerance)
        self.assertTrue(comp_record.phosphorus_comparison.within_tolerance)

        # Potassium: pred=310.0, actual=305.0 -> error=5.0 kg/ha (within tolerance)
        self.assertTrue(comp_record.potassium_comparison.within_tolerance)

        self.assertTrue(comp_record.all_tolerances_met)

        # -------------------------------------------------------------
        # 7. Model Evaluation & Release Gate (Phase 7)
        # -------------------------------------------------------------
        history = [comp_record]
        eval_report = SoilIntelligenceEvaluator.evaluate_comparisons(
            records=history,
            split_strategy="GROUPED_PLOT_TIME_SERIES",
            data_readiness_passed=False  # Gate remains blocked until full longitudinal dataset acquired
        )

        self.assertEqual(eval_report.split_strategy, "GROUPED_PLOT_TIME_SERIES")
        # While longitudinal field data gate is blocked, evaluation status remains NOT_YET_VALIDATED
        self.assertEqual(eval_report.overall_gate_status, EvaluationTargetStatus.NOT_YET_VALIDATED)
        self.assertIn("BLOCKED", eval_report.nitrogen_summary.status_explanation)
        self.assertEqual(eval_report.nitrogen_summary.within_tolerance_rate_pct, 100.0)


if __name__ == "__main__":
    unittest.main()
