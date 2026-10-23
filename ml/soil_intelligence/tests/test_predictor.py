"""
Phase 5 Tests: Soil Intelligence Predictor, Abstention Engine & Validation Gate
==============================================================================
Validates:
  1. Missing baseline laboratory reports.
  2. Insufficient or incomplete farm history / unrecorded gaps.
  3. Missing events never being silently interpreted as zero.
  4. Correct separation of measured values and estimates.
  5. Regional model outputs never being treated as measurements.
  6. Nutrient mass balance never being used as a direct soil-test prediction.
  7. Synthetic training data remaining permanently blocked.
  8. Cross-sectional data not qualifying as longitudinal validation.
  9. Unsupported confidence values and calibration claims being rejected.
 10. Invalid or missing units and plot identifiers triggering abstention.
 11. Correct abstention reasons and actionable data collection recommendations.
 12. Successful output only when the relevant gate permits it.
"""

import unittest
from datetime import datetime

from ml.soil_intelligence.schemas import (
    ProvenanceType,
    NutrientUnit,
    ChemicalForm,
    NutrientMeasurement,
    MeasuredLaboratoryReport,
    ModelledEnvironmentalContext,
    AgronomicTolerances,
    ComprehensiveEvaluationReport,
    NutrientEvaluationSummary,
    ToleranceReviewStatus,
    EvaluationTargetStatus
)
from ml.soil_intelligence.data_readiness import (
    DatasetAuditReport,
    GateStatus,
    SamplingDesign
)
from ml.soil_intelligence.timeline.timeline_manager import PlotTimelineManager
from ml.soil_intelligence.model.validation_gate import (
    ModelValidationGate,
    ModelValidationScope,
    ValidationGateDecision,
    ValidationEvidenceBundle
)
from ml.soil_intelligence.model.uncertainty import (
    UncertaintyEngine,
    CalibrationStatus
)
from ml.soil_intelligence.model.abstention import (
    AbstentionEngine,
    AbstentionReasonCode,
    RetestingUrgency
)
from ml.soil_intelligence.model.predictor import (
    SoilIntelligencePredictor,
    SoilIntelligenceReport,
    MODEL_VERSION
)


class TestSoilIntelligencePredictor(unittest.TestCase):

    def _create_sample_lab_report(self, plot_id="PLOT_MH_001", sample_date="2023-06-15"):
        """Helper to create a verified laboratory report."""
        return MeasuredLaboratoryReport(
            report_id=f"LAB_{plot_id}_{sample_date}",
            plot_id=plot_id,
            sample_date=sample_date,
            lab_name="District Soil Testing Laboratory, Latur",
            lab_certificate_no="STL-2023-8871",
            provenance=ProvenanceType.MEASURED,
            nitrogen=NutrientMeasurement(
                nutrient="N",
                reported_value=245.0,
                reported_unit=NutrientUnit.KG_PER_HA,
                reported_form=ChemicalForm.ELEMENTAL_N,
                normalized_value_kg_ha=245.0,
                conversion_applied="reported directly in kg/ha elemental N",
                conversion_verified=True
            ),
            phosphorus=NutrientMeasurement(
                nutrient="P",
                reported_value=18.5,
                reported_unit=NutrientUnit.KG_PER_HA,
                reported_form=ChemicalForm.ELEMENTAL_P,
                normalized_value_kg_ha=18.5,
                conversion_applied="reported directly in kg/ha elemental P",
                conversion_verified=True
            ),
            potassium=NutrientMeasurement(
                nutrient="K",
                reported_value=320.0,
                reported_unit=NutrientUnit.KG_PER_HA,
                reported_form=ChemicalForm.ELEMENTAL_K,
                normalized_value_kg_ha=320.0,
                conversion_applied="reported directly in kg/ha elemental K",
                conversion_verified=True
            ),
            ph=7.8,
            ec_ds_m=0.35,
            organic_carbon_pct=0.52,
            extraction_confidence=1.0,
            review_required=False
        )

    # -----------------------------------------------------------------
    # Test 1: Missing Baseline Laboratory Report Abstains
    # -----------------------------------------------------------------
    def test_missing_baseline_laboratory_report_abstains(self):
        """When no lab report exists, predictor must return INSUFFICIENT_DATA and actionable advice."""
        timeline = PlotTimelineManager(plot_id="PLOT_MH_EMPTY")
        predictor = SoilIntelligencePredictor(longitudinal_ground_truth_available=False)

        report = predictor.evaluate_plot(timeline, target_date="2025-06-01")

        self.assertEqual(report.overall_status, ProvenanceType.INSUFFICIENT_DATA)
        self.assertIsNotNone(report.abstention_decision)
        self.assertTrue(report.abstention_decision.should_abstain)
        self.assertIn(AbstentionReasonCode.MISSING_BASELINE_TEST, report.abstention_decision.reason_codes)
        self.assertIsNone(report.baseline_measured_report)
        self.assertIsNone(report.prediction_record.nitrogen)
        self.assertIsNone(report.prediction_record.phosphorus)
        self.assertIsNone(report.prediction_record.potassium)
        # Verify actionable sampling recommendation
        self.assertTrue(any("composite soil sample" in r.lower() for r in report.actionable_recommendations))
        self.assertEqual(report.abstention_decision.retesting_urgency, RetestingUrgency.IMMEDIATE_ACTION_REQUIRED)

    # -----------------------------------------------------------------
    # Test 2: Invalid or Missing Plot Identifiers Trigger Abstention
    # -----------------------------------------------------------------
    def test_invalid_or_missing_plot_identifier_abstains(self):
        """Missing or whitespace plot ID must trigger abstention with UNVERIFIED_PLOT_IDENTIFIER."""
        for invalid_id in ["", "   ", "UNKNOWN", "NONE"]:
            timeline = PlotTimelineManager(plot_id=invalid_id)
            predictor = SoilIntelligencePredictor(longitudinal_ground_truth_available=False)
            report = predictor.evaluate_plot(timeline, target_date="2025-06-01")

            self.assertEqual(report.overall_status, ProvenanceType.INSUFFICIENT_DATA)
            self.assertIn(AbstentionReasonCode.UNVERIFIED_PLOT_IDENTIFIER, report.abstention_decision.reason_codes)

    # -----------------------------------------------------------------
    # Test 3: Insufficient Farm History and Cropping Gaps Trigger Abstention
    # -----------------------------------------------------------------
    def test_insufficient_or_incomplete_farm_history_gap_abstention(self):
        """Unrecorded gap > 240 days must trigger safe abstention."""
        timeline = PlotTimelineManager(plot_id="PLOT_GAP_TEST")
        # Baseline in Jan 2023
        timeline.add_lab_report(self._create_sample_lab_report("PLOT_GAP_TEST", "2023-01-15"))
        # Event in Feb 2023
        timeline.record_crop_harvest("Wheat", 4.0, "2023-02-20")
        # Next event in May 2025 (>2 years unrecorded gap)
        timeline.record_crop_harvest("Soybean", 2.0, "2025-05-10")

        predictor = SoilIntelligencePredictor(longitudinal_ground_truth_available=False)
        report = predictor.evaluate_plot(timeline, target_date="2025-06-01")

        self.assertEqual(report.overall_status, ProvenanceType.INSUFFICIENT_DATA)
        self.assertIn(AbstentionReasonCode.UNRECORDED_CROPPING_GAPS, report.abstention_decision.reason_codes)
        self.assertGreater(report.abstention_decision.target_sampling_depth_cm, 0.0)

    # -----------------------------------------------------------------
    # Test 4: Missing Events Never Silently Interpreted as Zero
    # -----------------------------------------------------------------
    def test_missing_events_never_silently_interpreted_as_zero(self):
        """When 40 months pass with no records, system flags unrecorded drift instead of assuming 0 flux."""
        timeline = PlotTimelineManager(plot_id="PLOT_SILENT_ZERO")
        timeline.add_lab_report(self._create_sample_lab_report("PLOT_SILENT_ZERO", "2022-01-01"))
        # 0 events recorded up to 2025-06-01 (>41 months)

        predictor = SoilIntelligencePredictor(longitudinal_ground_truth_available=False)
        report = predictor.evaluate_plot(timeline, target_date="2025-06-01")

        self.assertEqual(report.overall_status, ProvenanceType.INSUFFICIENT_DATA)
        self.assertIn(AbstentionReasonCode.EXPIRED_TIME_HORIZON, report.abstention_decision.reason_codes)
        # Verify ledger marked unrecorded crop cycles rather than assuming clean zero depletion
        self.assertTrue(report.mass_balance_ledger.has_unrecorded_crop_cycles)
        self.assertTrue(any("FLAG" in f for f in report.mass_balance_ledger.data_quality_flags))

    # -----------------------------------------------------------------
    # Test 5: Correct Separation of Measured Values and Estimates
    # -----------------------------------------------------------------
    def test_correct_separation_of_measured_values_and_estimates(self):
        """Lab reports (MEASURED) are strictly isolated from model predictions and bookkeeping."""
        timeline = PlotTimelineManager(plot_id="PLOT_SEP_TEST")
        lab = self._create_sample_lab_report("PLOT_SEP_TEST", "2023-06-15")
        timeline.add_lab_report(lab)
        timeline.record_fertilizer_application("Urea", 100.0, "2023-07-01")

        predictor = SoilIntelligencePredictor(longitudinal_ground_truth_available=False)
        report = predictor.evaluate_plot(timeline, target_date="2023-09-01")

        # 1. Measured lab report preserves its genuine provenance and certified values
        self.assertIsNotNone(report.baseline_measured_report)
        self.assertEqual(report.baseline_measured_report.provenance, ProvenanceType.MEASURED)
        self.assertEqual(report.baseline_measured_report.nitrogen.reported_value, 245.0)

        # 2. Prediction record is separate and marked INSUFFICIENT_DATA (due to gate)
        self.assertEqual(report.prediction_record.status, ProvenanceType.INSUFFICIENT_DATA)

        # 3. Mass-balance is separate
        self.assertIsNotNone(report.mass_balance_ledger)
        self.assertNotEqual(report.baseline_measured_report.provenance, report.prediction_record.status)

    # -----------------------------------------------------------------
    # Test 6: Regional Model Outputs Never Treated as Measurements
    # -----------------------------------------------------------------
    def test_regional_model_outputs_never_treated_as_measurements(self):
        """SoilGrids context retains REGIONAL_MODEL provenance and explicit disclaimer."""
        timeline = PlotTimelineManager(plot_id="PLOT_GRID_TEST")
        timeline.add_lab_report(self._create_sample_lab_report("PLOT_GRID_TEST", "2024-01-01"))
        env = ModelledEnvironmentalContext(
            plot_id="PLOT_GRID_TEST",
            latitude=18.4088,
            longitude=76.5604,
            provenance=ProvenanceType.REGIONAL_MODEL,
            sand_fraction_pct=35.0,
            clay_fraction_pct=45.0,
            bulk_density_g_cm3=1.35
        )
        timeline.set_environmental_context(env)

        predictor = SoilIntelligencePredictor(longitudinal_ground_truth_available=False)
        report = predictor.evaluate_plot(timeline, target_date="2024-06-01")

        self.assertIsNotNone(report.environmental_context)
        self.assertEqual(report.environmental_context.provenance, ProvenanceType.REGIONAL_MODEL)
        self.assertIn("MUST NEVER be treated as ground truth", report.environmental_context.disclaimer)

    # -----------------------------------------------------------------
    # Test 7: Nutrient Mass Balance Never Used as Direct Soil-Test Prediction
    # -----------------------------------------------------------------
    def test_nutrient_mass_balance_never_used_as_direct_soil_test_prediction(self):
        """Mass-balance delta must remain in the ledger; never output as extractable NPK."""
        timeline = PlotTimelineManager(plot_id="PLOT_MB_GUARD")
        timeline.add_lab_report(self._create_sample_lab_report("PLOT_MB_GUARD", "2024-01-01"))
        timeline.record_fertilizer_application("Urea", 200.0, "2024-01-10")  # +92 kg N

        predictor = SoilIntelligencePredictor(longitudinal_ground_truth_available=False)
        report = predictor.evaluate_plot(timeline, target_date="2024-03-01")

        # Ledger records the flux
        self.assertEqual(report.mass_balance_ledger.net_balance_n_kg_ha, 92.0)

        # Prediction record must NOT have set predicted N to baseline (245) + delta (92) = 337
        self.assertIsNone(report.prediction_record.nitrogen)
        self.assertIn("DO NOT equal extractable available soil test NPK", report.scientific_disclaimer)

    # -----------------------------------------------------------------
    # Test 8: Synthetic Training Data Remains Blocked
    # -----------------------------------------------------------------
    def test_synthetic_training_data_remains_blocked(self):
        """Evaluating validation gate on synthetic data permanently blocks prediction authorization."""
        gate_decision = ModelValidationGate.evaluate_task(
            task_name="DYNAMIC_NPK_PREDICTION",
            is_synthetic_data=True
        )
        self.assertEqual(gate_decision.scope, ModelValidationScope.BLOCKED)
        self.assertFalse(gate_decision.is_authorized_for_operational_prediction)
        self.assertTrue(any("synthetic data" in r.lower() for r in gate_decision.rejection_reasons))

        predictor = SoilIntelligencePredictor(is_synthetic_data=True)
        self.assertFalse(predictor.gate_decision.is_authorized_for_operational_prediction)

    # -----------------------------------------------------------------
    # Test 9: Cross-Sectional Data Does Not Qualify as Longitudinal Validation
    # -----------------------------------------------------------------
    def test_cross_sectional_data_not_qualifying_as_longitudinal_validation(self):
        """Cross-sectional data cannot authorize longitudinal operational predictions."""
        # Task 1: Operational longitudinal prediction with cross-sectional data only -> BLOCKED
        gate_longitudinal = ModelValidationGate.evaluate_task(
            task_name="LONGITUDINAL_PREDICTION",
            cross_sectional_data_available=True,
            longitudinal_data_available=False
        )
        self.assertEqual(gate_longitudinal.scope, ModelValidationScope.BLOCKED)
        self.assertFalse(gate_longitudinal.is_authorized_for_operational_prediction)

        # Task 2: Cross-sectional baseline study -> RESEARCH_ONLY (never operational)
        gate_cross = ModelValidationGate.evaluate_task(
            task_name="CROSS_SECTIONAL_RESEARCH",
            cross_sectional_data_available=True
        )
        self.assertEqual(gate_cross.scope, ModelValidationScope.RESEARCH_ONLY)
        self.assertFalse(gate_cross.is_authorized_for_operational_prediction)

    # -----------------------------------------------------------------
    # Test 10: Unsupported Confidence Values and Calibration Claims Rejected
    # -----------------------------------------------------------------
    def test_unsupported_confidence_values_and_calibration_claims_rejected(self):
        """All uncertainty breakdowns must be marked UNCALIBRATED_HEURISTIC_BOUND."""
        timeline = PlotTimelineManager(plot_id="PLOT_UNC_TEST")
        timeline.add_lab_report(self._create_sample_lab_report("PLOT_UNC_TEST", "2023-06-15"))

        predictor = SoilIntelligencePredictor(longitudinal_ground_truth_available=False)
        report = predictor.evaluate_plot(timeline, target_date="2024-01-15")

        unc = report.uncertainty_breakdown
        self.assertIsNotNone(unc)
        self.assertEqual(unc.calibration_status, CalibrationStatus.UNCALIBRATED_HEURISTIC_BOUND)
        self.assertEqual(unc.nitrogen_uncertainty.calibration_status, CalibrationStatus.UNCALIBRATED_HEURISTIC_BOUND)
        # Verify physical decomposition into all 4 physical sources
        self.assertGreater(unc.nitrogen_uncertainty.measurement_variance_kg_ha, 0.0)
        self.assertGreaterEqual(unc.nitrogen_uncertainty.farmer_event_variance_kg_ha, 0.0)
        self.assertGreaterEqual(unc.nitrogen_uncertainty.agronomic_coeff_variance_kg_ha, 0.0)
        self.assertGreater(unc.nitrogen_uncertainty.temporal_gap_variance_kg_ha, 0.0)
        self.assertIn("MUST NOT be represented as empirically calibrated", unc.general_disclaimer)

    # -----------------------------------------------------------------
    # Test 11: Correct Abstention Reasons and Actionable Data Collection
    # -----------------------------------------------------------------
    def test_correct_abstention_reasons_and_suggested_data_collection(self):
        """Abstention report must clearly state missing evidence and actionable testing protocols."""
        timeline = PlotTimelineManager(plot_id="PLOT_RETEST_ADVICE")
        # No lab report added
        predictor = SoilIntelligencePredictor(longitudinal_ground_truth_available=False)
        report = predictor.evaluate_plot(timeline, target_date="2025-06-01")

        self.assertTrue(report.abstention_decision.should_abstain)
        self.assertGreater(len(report.abstention_decision.detailed_reasons), 0)
        self.assertGreater(len(report.abstention_decision.missing_evidence), 0)
        self.assertGreater(len(report.abstention_decision.actionable_recommendations), 0)
        # Check retesting guidance mentions plow depth
        self.assertEqual(report.abstention_decision.target_sampling_depth_cm, 15.0)

    def _create_valid_evidence_bundle(
        self,
        tolerance_status: ToleranceReviewStatus = ToleranceReviewStatus.OFFICIALLY_RATIFIED,
        split_strategy: str = "GROUPED_PLOT_TIME_SERIES",
        within_tolerance_rate: float = 85.0,
        sample_count: int = 50,
        is_synthetic: bool = False,
        sampling_design: SamplingDesign = SamplingDesign.LONGITUDINAL_PAIRED
    ) -> ValidationEvidenceBundle:
        """Helper to create a formal validation evidence bundle."""
        audit = DatasetAuditReport(
            file_path="verified_longitudinal_field_trials.csv",
            row_count=sample_count,
            column_count=12,
            provenance=ProvenanceType.MEASURED,
            sampling_design=sampling_design,
            is_synthetic=is_synthetic,
            synthetic_markers=[],
            has_nitrogen=True,
            has_phosphorus=True,
            has_potassium=True,
            has_ph=True,
            has_sample_dates=True,
            has_plot_identifiers=True,
            has_longitudinal_pairs=(sampling_design == SamplingDesign.LONGITUDINAL_PAIRED),
            gate_status=GateStatus.PASSED if not is_synthetic and sampling_design == SamplingDesign.LONGITUDINAL_PAIRED else GateStatus.BLOCKED,
            rejection_reasons=[],
            actionable_recommendations=[]
        )

        n_summary = NutrientEvaluationSummary(
            nutrient="Nitrogen",
            sample_count=sample_count,
            mae=14.2,
            rmse=18.5,
            within_tolerance_count=int(sample_count * (within_tolerance_rate / 100.0)),
            within_tolerance_rate_pct=within_tolerance_rate,
            target_status=EvaluationTargetStatus.MET if within_tolerance_rate >= 80.0 else EvaluationTargetStatus.NOT_MET
        )
        p_summary = NutrientEvaluationSummary(
            nutrient="Phosphorus",
            sample_count=sample_count,
            mae=3.1,
            rmse=4.2,
            within_tolerance_count=int(sample_count * (within_tolerance_rate / 100.0)),
            within_tolerance_rate_pct=within_tolerance_rate,
            target_status=EvaluationTargetStatus.MET if within_tolerance_rate >= 80.0 else EvaluationTargetStatus.NOT_MET
        )
        k_summary = NutrientEvaluationSummary(
            nutrient="Potassium",
            sample_count=sample_count,
            mae=18.6,
            rmse=23.4,
            within_tolerance_count=int(sample_count * (within_tolerance_rate / 100.0)),
            within_tolerance_rate_pct=within_tolerance_rate,
            target_status=EvaluationTargetStatus.MET if within_tolerance_rate >= 80.0 else EvaluationTargetStatus.NOT_MET
        )

        eval_report = ComprehensiveEvaluationReport(
            evaluation_id="EVAL_2026_HOLD_OUT",
            model_version=MODEL_VERSION,
            evaluation_date="2026-05-01",
            split_strategy=split_strategy,
            nitrogen_summary=n_summary,
            phosphorus_summary=p_summary,
            potassium_summary=k_summary,
            overall_gate_status=EvaluationTargetStatus.MET if within_tolerance_rate >= 80.0 else EvaluationTargetStatus.NOT_MET,
            data_provenance_verified=True,
            data_readiness_status="PASSED"
        )

        return ValidationEvidenceBundle(
            dataset_audit=audit,
            evaluation_report=eval_report,
            tolerance_signoff_status=tolerance_status,
            signoff_authority="State Agricultural University / ICAR Agronomy Review Board"
        )

    # -----------------------------------------------------------------
    # Test 12: Loose Boolean Flags Cannot Grant Validation
    # -----------------------------------------------------------------
    def test_loose_boolean_flags_cannot_grant_validation(self):
        """Passing loose boolean kwargs without a verified ValidationEvidenceBundle must be BLOCKED."""
        decision = ModelValidationGate.evaluate_task(
            task_name="OPERATIONAL_ESTIMATE",
            evidence_bundle=None,
            longitudinal_data_available=True,
            independent_holdout_evaluated=True,
            tolerance_target_met=True
        )
        self.assertEqual(decision.scope, ModelValidationScope.BLOCKED)
        self.assertFalse(decision.is_authorized_for_operational_prediction)
        self.assertTrue(any("loose boolean flags" in r.lower() for r in decision.rejection_reasons))

    # -----------------------------------------------------------------
    # Test 13: Evidence Bundle With Provisional Tolerance Rejected
    # -----------------------------------------------------------------
    def test_evidence_bundle_with_provisional_tolerance_rejected(self):
        """Bundle where tolerances are still PROVISIONAL_PENDING_EXPERT_APPROVAL must be BLOCKED."""
        bundle = self._create_valid_evidence_bundle(
            tolerance_status=ToleranceReviewStatus.PROVISIONAL_PENDING_EXPERT_APPROVAL
        )
        decision = ModelValidationGate.evaluate_task("OPERATIONAL_ESTIMATE", evidence_bundle=bundle)
        self.assertEqual(decision.scope, ModelValidationScope.BLOCKED)
        self.assertFalse(decision.is_authorized_for_operational_prediction)
        self.assertTrue(any("provisional" in r.lower() for r in decision.rejection_reasons))

    # -----------------------------------------------------------------
    # Test 14: Evidence Bundle With Sub-80% Tolerance Rejected
    # -----------------------------------------------------------------
    def test_evidence_bundle_with_sub_80_percent_tolerance_rejected(self):
        """Bundle where any nutrient has <80% pass rate must be BLOCKED."""
        bundle = self._create_valid_evidence_bundle(within_tolerance_rate=74.5)
        decision = ModelValidationGate.evaluate_task("OPERATIONAL_ESTIMATE", evidence_bundle=bundle)
        self.assertEqual(decision.scope, ModelValidationScope.BLOCKED)
        self.assertFalse(decision.is_authorized_for_operational_prediction)
        self.assertTrue(any("below required" in r.lower() or "does not achieve" in r.lower() for r in decision.rejection_reasons))

    # -----------------------------------------------------------------
    # Test 15: Evidence Bundle With Non-Grouped Split Strategy Rejected
    # -----------------------------------------------------------------
    def test_evidence_bundle_with_non_grouped_split_rejected(self):
        """Bundle with random split instead of GROUPED_PLOT_TIME_SERIES must be BLOCKED for leakage."""
        bundle = self._create_valid_evidence_bundle(split_strategy="RANDOM_K_FOLD")
        decision = ModelValidationGate.evaluate_task("OPERATIONAL_ESTIMATE", evidence_bundle=bundle)
        self.assertEqual(decision.scope, ModelValidationScope.BLOCKED)
        self.assertFalse(decision.is_authorized_for_operational_prediction)
        self.assertTrue(any("leakage-safe" in r.lower() for r in decision.rejection_reasons))

    # -----------------------------------------------------------------
    # Test 16: Synthetic Report Rejected From Physical Timeline
    # -----------------------------------------------------------------
    def test_synthetic_report_rejected_from_physical_timeline(self):
        """Attempting to add a synthetic lab report into a physical timeline must raise ValueError."""
        timeline = PlotTimelineManager(plot_id="PLOT_SYN_REJECT")
        fake_report = MeasuredLaboratoryReport(
            report_id="SYN_001",
            plot_id="PLOT_SYN_REJECT",
            sample_date="2024-01-01",
            lab_name="Synthetic Test Lab",
            provenance=ProvenanceType.MEASURED,
            notes="Generated via synthetic np.random.gamma distribution"
        )
        with self.assertRaises(ValueError):
            timeline.add_lab_report(fake_report)

    # -----------------------------------------------------------------
    # Test 17: Successful Output ONLY When Formal Evidence Bundle Is Verified
    # -----------------------------------------------------------------
    def test_successful_output_only_when_formal_evidence_verified(self):
        """Operational prediction is authorized ONLY when a complete valid bundle is provided."""
        valid_bundle = self._create_valid_evidence_bundle()
        pred_authorized = SoilIntelligencePredictor(evidence_bundle=valid_bundle)

        self.assertEqual(pred_authorized.gate_decision.scope, ModelValidationScope.VALIDATED_FOR_SCOPE)
        self.assertTrue(pred_authorized.gate_decision.is_authorized_for_operational_prediction)

        # Plot with complete valid history
        timeline = PlotTimelineManager(plot_id="PLOT_AUTH_TEST")
        timeline.add_lab_report(self._create_sample_lab_report("PLOT_AUTH_TEST", "2024-01-01"))
        timeline.record_crop_harvest("Wheat", 4.0, "2024-04-15")

        report = pred_authorized.evaluate_plot(timeline, target_date="2024-05-01")
        self.assertEqual(report.overall_status, ProvenanceType.ESTIMATED)
        self.assertTrue(report.is_operational_authorized)
        self.assertEqual(report.validation_scope, ModelValidationScope.VALIDATED_FOR_SCOPE)
        self.assertIsNotNone(report.prediction_record.nitrogen)
        self.assertEqual(report.prediction_record.nitrogen.predicted_kg_ha, 245.0)


if __name__ == "__main__":
    unittest.main()
