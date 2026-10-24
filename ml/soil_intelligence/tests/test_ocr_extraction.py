"""
Tests for OCR Extraction, Field Normalization & Human Review Workflow
=====================================================================
Verifies that:
1. Laboratory reports in Soil Health Card format are parsed and validated.
2. Units and chemical forms (P2O5 vs elemental P) are converted accurately.
3. Out-of-bounds values trigger mandatory human review flags.
4. Human correction workflow re-normalizes values and maintains an immutable audit trail.
"""

import unittest
from ml.soil_intelligence.ocr.extractor import LabReportExtractor
from ml.soil_intelligence.ocr.normalizer import ReportFieldNormalizer
from ml.soil_intelligence.ocr.review_manager import LabReportReviewManager, ReviewStatus
from ml.soil_intelligence.schemas import NutrientUnit, ChemicalForm, ProvenanceType


class TestLabReportExtraction(unittest.TestCase):

    def setUp(self):
        self.sample_shc_text = """
        GOVERNMENT OF MAHARASHTRA
        DISTRICT SOIL TESTING LABORATORY, LATUR
        Soil Health Card Certificate
        Sample No: MH6092432/2024-25/441209
        Date: 15-Oct-2024
        Plot No: PLOT_NORTH_44
        Farmer Name: Ramesh Patil

        SOIL PARAMETERS:
        pH: 7.40 (Normal)
        EC: 0.65 dS/m
        Organic Carbon: 0.55 %
        Available Nitrogen: 240.0 kg/ha (Low)
        Available Phosphorus: 18.5 kg/ha P2O5 (Medium)
        Available Potassium: 310.0 kg/ha K2O (High)
        """

    def test_shc_text_extraction(self):
        """Extracts sample ID, dates, plot ID, and NPK from structured report text."""
        doc = LabReportExtractor.extract_from_text(self.sample_shc_text)

        self.assertIsNotNone(doc.extracted_report)
        report = doc.extracted_report

        self.assertEqual(report.report_id, "MH6092432/2024-25/441209")
        self.assertEqual(report.plot_id, "PLOT_NORTH_44")
        self.assertEqual(report.sample_date, "15-Oct-2024")
        self.assertEqual(report.ph, 7.40)
        self.assertEqual(report.ec_ds_m, 0.65)
        self.assertEqual(report.organic_carbon_pct, 0.55)

        # Nitrogen: 240.0 kg/ha
        self.assertIsNotNone(report.nitrogen)
        self.assertEqual(report.nitrogen.reported_value, 240.0)
        self.assertEqual(report.nitrogen.reported_unit, NutrientUnit.KG_PER_HA)
        self.assertEqual(report.nitrogen.normalized_value_kg_ha, 240.0)

        # Phosphorus: 18.5 kg/ha P2O5 -> elemental P = 18.5 * 0.4364 = ~8.074 kg/ha
        self.assertIsNotNone(report.phosphorus)
        self.assertEqual(report.phosphorus.reported_value, 18.5)
        self.assertEqual(report.phosphorus.reported_form, ChemicalForm.OXIDE_P2O5)
        self.assertAlmostEqual(report.phosphorus.normalized_value_kg_ha, 8.074, places=2)

        # Potassium: 310.0 kg/ha K2O -> elemental K = 310.0 * 0.8302 = ~257.348 kg/ha
        self.assertIsNotNone(report.potassium)
        self.assertEqual(report.potassium.reported_value, 310.0)
        self.assertEqual(report.potassium.reported_form, ChemicalForm.OXIDE_K2O)
        self.assertAlmostEqual(report.potassium.normalized_value_kg_ha, 257.348, places=1)

    def test_ppm_unit_normalization(self):
        """When P is reported in ppm (mg/kg), normalizer converts to elemental kg/ha."""
        res = ReportFieldNormalizer.normalize_nutrient_field(
            nutrient="P",
            raw_val_str="12.0",
            surrounding_text="Available Phosphorus: 12.0 ppm P2O5"
        )
        self.assertTrue(res.is_plausible)
        # 12 ppm * 1.995 (soil mass factor) = 23.94 kg/ha P2O5 -> * 0.43642 = 10.448 kg/ha elemental P
        self.assertAlmostEqual(res.measurement.normalized_value_kg_ha, 10.448, places=2)

    def test_out_of_bounds_triggers_review(self):
        """Values outside plausible bounds (e.g., pH 13.5 or N 5000) trigger human review flags."""
        extreme_text = """
        Sample No: LAB_ERR_01
        Date: 2024-01-01
        Plot No: P1
        pH: 13.50
        Available Nitrogen: 5000.0 kg/ha
        """
        doc = LabReportExtractor.extract_from_text(extreme_text)

        self.assertTrue(doc.requires_human_review)
        self.assertTrue(any(iss.issue_code == "OUT_OF_BOUNDS" for iss in doc.validation_issues))

    def test_human_correction_workflow(self):
        """Uncertain report is queued, manually corrected, re-normalized, and audit trail is logged."""
        mgr = LabReportReviewManager()

        uncertain_text = """
        Sample No: SHC_9912
        Date: 2024-05-10
        Plot No: PLOT_B
        pH: 7.20
        Available Nitrogen: 12000.0 kg/ha
        """
        doc = LabReportExtractor.extract_from_text(uncertain_text)
        self.assertTrue(doc.requires_human_review)

        report_id = mgr.queue_for_review(doc)
        self.assertIn(report_id, mgr.review_queue)

        # Agronomist submits correction: Nitrogen was a typo in OCR for 200.0 kg/ha
        review_record = mgr.submit_manual_correction(
            report_id=report_id,
            reviewer_id="AGRONOMIST_DR_SHARMA",
            corrections={"Nitrogen": "200.0"},
            notes="Corrected OCR digit duplication error (12000 -> 200.0)."
        )

        self.assertEqual(review_record.review_status, ReviewStatus.CORRECTED_AND_APPROVED)
        self.assertEqual(len(review_record.corrections_applied), 1)

        corrected_report = review_record.final_verified_report
        self.assertFalse(corrected_report.review_required)
        self.assertEqual(corrected_report.nitrogen.reported_value, 200.0)
        self.assertEqual(corrected_report.nitrogen.normalized_value_kg_ha, 200.0)
        self.assertIn("Corrected & approved", corrected_report.notes)


if __name__ == "__main__":
    unittest.main()
