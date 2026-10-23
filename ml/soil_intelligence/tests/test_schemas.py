"""
Unit Tests for Soil Intelligence Schemas & Unit Conversions
===========================================================
Tests stoichiometric conversions (P2O5 -> P, K2O -> K), gravimetric conversions
(ppm -> kg/ha), tolerance compliance, provenance separation, and missing values.
"""

import unittest
from ml.soil_intelligence.schemas import (
    NutrientConverter,
    NutrientUnit,
    ChemicalForm,
    NutrientMeasurement,
    AgronomicTolerances,
    ToleranceReviewStatus,
    MeasuredLaboratoryReport,
    ModelledEnvironmentalContext,
    SoilPredictionRecord,
    DynamicPlotTimeline,
    AgronomicEvent,
    ProvenanceType,
    FACTOR_P2O5_TO_P,
    FACTOR_K2O_TO_K
)


class TestNutrientConverter(unittest.TestCase):

    def test_p2o5_to_elemental_p_stoichiometry(self):
        """P2O5 must convert to elemental P using molar mass ratio (factor ~0.4364)."""
        # 100 kg/ha of P2O5 = 43.642 kg/ha of elemental P
        val, steps = NutrientConverter.convert_phosphorus(
            value=100.0,
            unit=NutrientUnit.KG_PER_HA,
            form=ChemicalForm.OXIDE_P2O5
        )
        self.assertAlmostEqual(val, 43.642, places=2)
        self.assertIn("P2O5 -> elemental P", steps)

    def test_k2o_to_elemental_k_stoichiometry(self):
        """K2O must convert to elemental K using molar mass ratio (factor ~0.8302)."""
        # 100 kg/ha of K2O = 83.016 kg/ha of elemental K
        val, steps = NutrientConverter.convert_potassium(
            value=100.0,
            unit=NutrientUnit.KG_PER_HA,
            form=ChemicalForm.OXIDE_K2O
        )
        self.assertAlmostEqual(val, 83.016, places=2)
        self.assertIn("K2O -> elemental K", steps)

    def test_ppm_to_kg_ha_conversion(self):
        """ppm (mg/kg) must convert to kg/ha based on topsoil depth and bulk density."""
        # 10 ppm elemental P with standard 1.33 g/cm3 bulk density = 10 * 1.995 = 19.95 kg/ha
        val, steps = NutrientConverter.convert_phosphorus(
            value=10.0,
            unit=NutrientUnit.PPM,
            form=ChemicalForm.ELEMENTAL_P,
            bulk_density_g_cm3=1.33
        )
        self.assertAlmostEqual(val, 19.95, places=1)
        self.assertIn("ppm -> kg/ha", steps)

    def test_ppm_and_oxide_combined_conversion(self):
        """ppm of P2O5 must convert both gravimetrically and stoichiometrically."""
        # 10 ppm P2O5 -> 19.95 kg/ha P2O5 -> 19.95 * 0.43642 = 8.707 kg/ha elemental P
        val, steps = NutrientConverter.convert_phosphorus(
            value=10.0,
            unit=NutrientUnit.PPM,
            form=ChemicalForm.OXIDE_P2O5,
            bulk_density_g_cm3=1.33
        )
        self.assertAlmostEqual(val, 8.707, places=2)
        self.assertIn("P2O5 -> elemental P", steps)
        self.assertIn("ppm -> kg/ha", steps)

    def test_negative_values_rejected(self):
        """Negative nutrient values must raise ValueError."""
        with self.assertRaises(ValueError):
            NutrientConverter.convert_phosphorus(
                value=-5.0,
                unit=NutrientUnit.KG_PER_HA,
                form=ChemicalForm.OXIDE_P2O5
            )
        with self.assertRaises(ValueError):
            NutrientConverter.convert_nitrogen(
                value=-10.0,
                unit=NutrientUnit.KG_PER_HA
            )

    def test_invalid_units_rejected(self):
        """Incompatible units like pH or % for nitrogen must raise ValueError."""
        with self.assertRaises(ValueError):
            NutrientConverter.convert_nitrogen(
                value=7.0,
                unit=NutrientUnit.PH_INDEX
            )


class TestPredefinedTolerances(unittest.TestCase):

    def test_provisional_status_enforced(self):
        """All tolerances must be marked PROVISIONAL_PENDING_EXPERT_APPROVAL."""
        n_tol = AgronomicTolerances.get_tolerance("Nitrogen")
        p_tol = AgronomicTolerances.get_tolerance("Phosphorus")
        k_tol = AgronomicTolerances.get_tolerance("Potassium")

        self.assertEqual(n_tol.status, ToleranceReviewStatus.PROVISIONAL_PENDING_EXPERT_APPROVAL)
        self.assertEqual(p_tol.status, ToleranceReviewStatus.PROVISIONAL_PENDING_EXPERT_APPROVAL)
        self.assertEqual(k_tol.status, ToleranceReviewStatus.PROVISIONAL_PENDING_EXPERT_APPROVAL)

    def test_nitrogen_tolerance_eval(self):
        """Nitrogen tolerance: ±25 kg/ha or ±15%."""
        tol = AgronomicTolerances.get_tolerance("N")

        # Within absolute (diff = 20 <= 25)
        passed, abs_err, rel_err = tol.is_within_tolerance(predicted=220.0, actual=200.0)
        self.assertTrue(passed)
        self.assertEqual(abs_err, 20.0)

        # Within relative (diff = 40 on 400 = 10% <= 15%)
        passed, abs_err, rel_err = tol.is_within_tolerance(predicted=440.0, actual=400.0)
        self.assertTrue(passed)
        self.assertEqual(rel_err, 10.0)

        # Outside both (diff = 50 on 200 = 25% > 15%, abs 50 > 25)
        passed, abs_err, rel_err = tol.is_within_tolerance(predicted=250.0, actual=200.0)
        self.assertFalse(passed)

    def test_phosphorus_tolerance_eval(self):
        """Phosphorus tolerance: ±5 kg/ha or ±20%."""
        tol = AgronomicTolerances.get_tolerance("P")

        # Within absolute (diff = 4 <= 5)
        passed, _, _ = tol.is_within_tolerance(predicted=14.0, actual=10.0)
        self.assertTrue(passed)

        # Outside both (diff = 8 on 15 = 53.3% > 20%, abs 8 > 5)
        passed, _, _ = tol.is_within_tolerance(predicted=23.0, actual=15.0)
        self.assertFalse(passed)

    def test_potassium_tolerance_eval(self):
        """Potassium tolerance: ±30 kg/ha or ±15%."""
        tol = AgronomicTolerances.get_tolerance("K")

        # Within absolute (diff = 25 <= 30)
        passed, _, _ = tol.is_within_tolerance(predicted=225.0, actual=200.0)
        self.assertTrue(passed)

        # Outside both (diff = 60 on 200 = 30% > 15%, abs 60 > 30)
        passed, _, _ = tol.is_within_tolerance(predicted=260.0, actual=200.0)
        self.assertFalse(passed)


class TestProvenanceSeparation(unittest.TestCase):

    def test_measured_vs_estimated_isolation(self):
        """Measured lab reports and estimated predictions have distinct provenance."""
        lab = MeasuredLaboratoryReport(
            report_id="LAB_001",
            plot_id="PLOT_A",
            sample_date="2024-03-15",
            lab_name="District Soil Testing Lab, Pune",
            lab_certificate_no="DSTL/2024/8891"
        )
        self.assertEqual(lab.provenance, ProvenanceType.MEASURED)

        pred = SoilPredictionRecord(
            prediction_id="PRED_001",
            plot_id="PLOT_A",
            prediction_date="2025-06-01",
            model_version="soil-intelligence-v1.0.0",
            status=ProvenanceType.ESTIMATED
        )
        self.assertEqual(pred.status, ProvenanceType.ESTIMATED)

        env = ModelledEnvironmentalContext(
            plot_id="PLOT_A",
            latitude=18.52,
            longitude=73.85,
            sand_fraction_pct=25.0,
            clay_fraction_pct=45.0
        )
        self.assertEqual(env.provenance, ProvenanceType.REGIONAL_MODEL)
        self.assertIn("NEVER be treated as ground truth", env.disclaimer)

    def test_dynamic_multi_year_timeline(self):
        """Timeline accepts irregular events across 2023, 2024, 2025 without fixed annual cadence."""
        timeline = DynamicPlotTimeline(plot_id="PLOT_XYZ")

        # Add 2023 lab test
        lab_2023 = MeasuredLaboratoryReport(
            report_id="LAB_2023",
            plot_id="PLOT_XYZ",
            sample_date="2023-05-10",
            lab_name="KVK Lab",
            lab_certificate_no="KVK/23/1"
        )
        timeline.baseline_lab_reports.append(lab_2023)

        # Add 2024 fertilizer addition (no lab test in 2024)
        fert_2024 = AgronomicEvent(
            event_id="EVT_01",
            plot_id="PLOT_XYZ",
            event_date="2024-06-15",
            event_type="FERTILIZER",
            details={"fertilizer": "Urea", "amount_kg_ha": 100.0, "n_kg_ha": 46.0}
        )
        timeline.agronomic_events.append(fert_2024)

        # Add 2025 harvest
        harvest_2025 = AgronomicEvent(
            event_id="EVT_02",
            plot_id="PLOT_XYZ",
            event_date="2025-01-20",
            event_type="CROP_HARVEST",
            details={"crop": "Soybean", "yield_t_ha": 2.2}
        )
        timeline.agronomic_events.append(harvest_2025)

        # Baseline query
        last_report = timeline.get_last_measured_report(before_date="2025-06-01")
        self.assertIsNotNone(last_report)
        self.assertEqual(last_report.report_id, "LAB_2023")

    def test_lab_report_accreditation_verification_fields(self):
        """
        D-01: MeasuredLaboratoryReport accreditation verification fields defaults and behavior.
        Populated certificate or accreditation ID alone must NOT establish verified status.
        """
        # 1. Default report has accreditation_verified=False
        lab_default = MeasuredLaboratoryReport(
            report_id="LAB_DEF",
            plot_id="PLOT_DEF",
            sample_date="2024-01-01",
            lab_name="Generic Soil Testing Lab",
            lab_certificate_no="CERT-1234",
            lab_accreditation_id="ACC-889"
        )
        self.assertFalse(lab_default.accreditation_verified)
        self.assertIsNone(lab_default.accreditation_source)

        # 2. Explicitly verified report
        lab_verified = MeasuredLaboratoryReport(
            report_id="LAB_VER",
            plot_id="PLOT_VER",
            sample_date="2024-01-01",
            lab_name="NABL Certified Central Laboratory",
            lab_certificate_no="CERT-9999",
            lab_accreditation_id="NABL-TC-001",
            accreditation_verified=True,
            accreditation_source="NABL Official Accredited Laboratories Directory"
        )
        self.assertTrue(lab_verified.accreditation_verified)
        self.assertEqual(lab_verified.accreditation_source, "NABL Official Accredited Laboratories Directory")


if __name__ == "__main__":
    unittest.main()
