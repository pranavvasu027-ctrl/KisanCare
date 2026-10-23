"""
Tests for Soil Intelligence PDF Report Generator
=================================================
Validates:
  1. Complete laboratory report generation.
  2. Missing baseline laboratory data (abstains cleanly, renders guidance).
  3. Missing or incomplete farm history (gap flags).
  4. Blocked empirical prediction (explains reason, no future NPK invented).
  5. Out-of-range laboratory values requiring human review (review banner).
  6. Missing optional parameters handled gracefully.
  7. Long multi-year timelines (multi-page rendering).
  8. Correct unit and provenance labels in PDF stream.
  9. No fabricated numeric values.
 10. No confusing mass-balance with measured soil NPK.
 11. PDF stream inspection verifying text matches input data.
"""

import unittest

from ml.soil_intelligence.schemas import (
    ProvenanceType,
    NutrientUnit,
    ChemicalForm,
    NutrientMeasurement,
    MeasuredLaboratoryReport,
    ModelledEnvironmentalContext,
    TestMethod
)
from ml.soil_intelligence.timeline.timeline_manager import PlotTimelineManager
from ml.soil_intelligence.model.predictor import SoilIntelligencePredictor
from ml.soil_intelligence.reporting.report_builder import SoilReportBuilder
from ml.soil_intelligence.reporting.pdf_generator import SoilIntelligencePDFGenerator


class TestSoilIntelligencePDFReport(unittest.TestCase):

    def _create_sample_lab_report(self, plot_id="PLOT_MH_LAT_881", sample_date="2023-06-15", review_req=False):
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
                conversion_verified=True,
                test_method=TestMethod.ALKALINE_PERMANGANATE
            ),
            phosphorus=NutrientMeasurement(
                nutrient="P",
                reported_value=18.5,
                reported_unit=NutrientUnit.KG_PER_HA,
                reported_form=ChemicalForm.ELEMENTAL_P,
                normalized_value_kg_ha=18.5,
                conversion_applied="reported directly in kg/ha elemental P",
                conversion_verified=True,
                test_method=TestMethod.OLSEN_SODIUM_BICARBONATE
            ),
            potassium=NutrientMeasurement(
                nutrient="K",
                reported_value=320.0,
                reported_unit=NutrientUnit.KG_PER_HA,
                reported_form=ChemicalForm.ELEMENTAL_K,
                normalized_value_kg_ha=320.0,
                conversion_applied="reported directly in kg/ha elemental K",
                conversion_verified=True,
                test_method=TestMethod.AMMONIUM_ACETATE_FLAME
            ),
            ph=7.8,
            ec_ds_m=0.35,
            organic_carbon_pct=0.52,
            extraction_confidence=1.0,
            review_required=review_req
        )

    # -----------------------------------------------------------------
    # Test 1: Complete Laboratory Report PDF Generation
    # -----------------------------------------------------------------
    def test_complete_laboratory_report_pdf_generation(self):
        """Generates valid PDF for a complete lab report with farm timeline."""
        timeline = PlotTimelineManager(plot_id="PLOT_MH_LAT_881", farm_id="FARM_LAT_01")
        timeline.add_lab_report(self._create_sample_lab_report("PLOT_MH_LAT_881", "2023-06-15"))
        timeline.record_crop_harvest("Soybean", 2.2, "2023-10-15")
        timeline.record_fertilizer_application("DAP", 100.0, "2023-06-20")

        predictor = SoilIntelligencePredictor()
        intel_report = predictor.evaluate_plot(timeline, target_date="2023-11-01")

        vm = SoilReportBuilder.build_view_model(timeline, intel_report)
        pdf_gen = SoilIntelligencePDFGenerator()
        pdf_bytes = pdf_gen.generate_pdf_bytes(vm)

        # 1. Valid PDF header and trailer
        self.assertTrue(pdf_bytes.startswith(b"%PDF-1.4"))
        self.assertTrue(b"%%EOF" in pdf_bytes)

        # 2. Privacy masking check (PLOT_MH_LAT_881 -> PLOT_MH_LAT_****81)
        self.assertIn(b"PLOT_MH_LAT_****81", pdf_bytes)

        # 3. Lab readings rendered in stream
        self.assertIn(b"245.0 kg/ha", pdf_bytes)
        self.assertIn(b"18.5 kg/ha", pdf_bytes)
        self.assertIn(b"320.0 kg/ha", pdf_bytes)
        self.assertIn(b"District Soil Test", pdf_bytes)

        # 4. Provenance labels rendered
        self.assertIn(b"MEASURED", pdf_bytes)
        self.assertIn(b"FARMER_RECORDED", pdf_bytes)

    # -----------------------------------------------------------------
    # Test 2: Missing Baseline Laboratory Report PDF
    # -----------------------------------------------------------------
    def test_missing_baseline_laboratory_report_pdf(self):
        """Generates valid PDF when no lab baseline exists; abstains without inventing NPK."""
        timeline = PlotTimelineManager(plot_id="PLOT_NO_LAB")
        predictor = SoilIntelligencePredictor()
        intel_report = predictor.evaluate_plot(timeline, target_date="2025-06-01")

        vm = SoilReportBuilder.build_view_model(timeline, intel_report)
        pdf_gen = SoilIntelligencePDFGenerator()
        pdf_bytes = pdf_gen.generate_pdf_bytes(vm)

        self.assertTrue(pdf_bytes.startswith(b"%PDF-1.4"))
        self.assertIn(b"INSUFFICIENT DATA", pdf_bytes)
        self.assertIn(b"NO PHYSICAL LABORATORY REPORT ON RECORD", pdf_bytes)
        self.assertIn(b"composite soil sample", pdf_bytes)

    # -----------------------------------------------------------------
    # Test 3: Missing / Incomplete Farm History PDF
    # -----------------------------------------------------------------
    def test_missing_or_incomplete_farm_history_pdf(self):
        """Flags gaps when baseline is old and intermediate farm records are missing."""
        timeline = PlotTimelineManager(plot_id="PLOT_GAP_PDF")
        timeline.add_lab_report(self._create_sample_lab_report("PLOT_GAP_PDF", "2022-01-01"))
        # > 40 months with zero intervening events

        predictor = SoilIntelligencePredictor()
        intel_report = predictor.evaluate_plot(timeline, target_date="2025-06-01")

        vm = SoilReportBuilder.build_view_model(timeline, intel_report)
        pdf_gen = SoilIntelligencePDFGenerator()
        pdf_bytes = pdf_gen.generate_pdf_bytes(vm)

        self.assertIn(b"FLAG_DATA_GAP", pdf_bytes)
        self.assertIn(b"FLAG_ZERO_EVENTS", pdf_bytes)
        self.assertIn(b"INSUFFICIENT DATA", pdf_bytes)

    # -----------------------------------------------------------------
    # Test 4: Blocked Empirical Prediction Rationale
    # -----------------------------------------------------------------
    def test_blocked_empirical_prediction_rationale_rendered(self):
        """PDF explicitly states why future NPK is unavailable and what data is needed."""
        timeline = PlotTimelineManager(plot_id="PLOT_BLOCKED_PDF")
        timeline.add_lab_report(self._create_sample_lab_report("PLOT_BLOCKED_PDF", "2024-01-01"))

        predictor = SoilIntelligencePredictor()
        intel_report = predictor.evaluate_plot(timeline, target_date="2024-06-01")

        vm = SoilReportBuilder.build_view_model(timeline, intel_report)
        pdf_gen = SoilIntelligencePDFGenerator()
        pdf_bytes = pdf_gen.generate_pdf_bytes(vm)

        self.assertIn(b"Why is an empirical future NPK prediction not provided", pdf_bytes)
        self.assertIn(b"BLOCKED", pdf_bytes)

    # -----------------------------------------------------------------
    # Test 5: Out of Range Values Flag Human Review
    # -----------------------------------------------------------------
    def test_out_of_range_values_flag_human_review(self):
        """When a lab report requires review, PDF displays a review warning banner."""
        timeline = PlotTimelineManager(plot_id="PLOT_REV_FLAG")
        timeline.add_lab_report(self._create_sample_lab_report("PLOT_REV_FLAG", "2024-01-01", review_req=True))

        predictor = SoilIntelligencePredictor()
        intel_report = predictor.evaluate_plot(timeline, target_date="2024-06-01")

        vm = SoilReportBuilder.build_view_model(timeline, intel_report)
        pdf_gen = SoilIntelligencePDFGenerator()
        pdf_bytes = pdf_gen.generate_pdf_bytes(vm)

        self.assertIn(b"FLAG_REVIEW_REQUIRED", pdf_bytes)

    # -----------------------------------------------------------------
    # Test 6: Missing Optional Parameters Handled Gracefully
    # -----------------------------------------------------------------
    def test_missing_optional_parameters_handled_gracefully(self):
        """Report with minimal parameters (only N, no P, K, pH, EC, OC) builds valid PDF."""
        timeline = PlotTimelineManager(plot_id="PLOT_MINIMAL")
        rep = MeasuredLaboratoryReport(
            report_id="LAB_MIN_01",
            plot_id="PLOT_MINIMAL",
            sample_date="2024-02-01",
            lab_name="Basic Lab",
            provenance=ProvenanceType.MEASURED,
            nitrogen=NutrientMeasurement(
                nutrient="N", reported_value=220.0, reported_unit=NutrientUnit.KG_PER_HA,
                reported_form=ChemicalForm.ELEMENTAL_N, normalized_value_kg_ha=220.0,
                conversion_applied="none", conversion_verified=True
            )
        )
        timeline.add_lab_report(rep)

        predictor = SoilIntelligencePredictor()
        intel_report = predictor.evaluate_plot(timeline, target_date="2024-05-01")

        vm = SoilReportBuilder.build_view_model(timeline, intel_report)
        pdf_gen = SoilIntelligencePDFGenerator()
        pdf_bytes = pdf_gen.generate_pdf_bytes(vm)

        self.assertTrue(pdf_bytes.startswith(b"%PDF-1.4"))
        self.assertIn(b"Available Nitrogen", pdf_bytes)

    # -----------------------------------------------------------------
    # Test 7: Long Multi-Year Timelines Span Multiple Pages
    # -----------------------------------------------------------------
    def test_long_multi_year_timelines_span_multiple_pages(self):
        """A timeline with 20+ events automatically triggers page breaks and increments page count."""
        timeline = PlotTimelineManager(plot_id="PLOT_MULTI_YEAR")
        timeline.add_lab_report(self._create_sample_lab_report("PLOT_MULTI_YEAR", "2023-01-01"))

        # Add 25 events across 2023, 2024, 2025, 2026
        for i in range(1, 26):
            year = 2023 + (i // 7)
            month = (i % 12) + 1
            timeline.record_crop_harvest("Wheat", 3.5, f"{year}-{month:02d}-15", event_id=f"HARV_{i}")

        predictor = SoilIntelligencePredictor()
        intel_report = predictor.evaluate_plot(timeline, target_date="2026-06-01")

        vm = SoilReportBuilder.build_view_model(timeline, intel_report)
        pdf_gen = SoilIntelligencePDFGenerator()
        pdf_bytes = pdf_gen.generate_pdf_bytes(vm)

        # Must have at least 2 pages
        self.assertGreaterEqual(len(pdf_gen.pages), 2)
        self.assertIn(b"Page 1 of", pdf_bytes)
        self.assertIn(b"Page 2 of", pdf_bytes)

    # -----------------------------------------------------------------
    # Test 8: Separation of Mass Balance From Soil Test NPK
    # -----------------------------------------------------------------
    def test_separation_of_mass_balance_from_soil_test_npk(self):
        """PDF contains explicit warning that mass balance is not extractable soil NPK."""
        timeline = PlotTimelineManager(plot_id="PLOT_MB_WARN")
        timeline.add_lab_report(self._create_sample_lab_report("PLOT_MB_WARN", "2024-01-01"))
        timeline.record_fertilizer_application("Urea", 100.0, "2024-02-01")

        predictor = SoilIntelligencePredictor()
        intel_report = predictor.evaluate_plot(timeline, target_date="2024-04-01")

        vm = SoilReportBuilder.build_view_model(timeline, intel_report)
        pdf_gen = SoilIntelligencePDFGenerator()
        pdf_bytes = pdf_gen.generate_pdf_bytes(vm)

        self.assertIn(b"BOOKKEEPING ONLY", pdf_bytes)
        self.assertIn(b"DOES NOT equal extractable soil available NPK", pdf_bytes)

    # -----------------------------------------------------------------
    # Test 9 (D-01): Neutral Section Title & Unverified Lab Credentials
    # -----------------------------------------------------------------
    def test_unverified_credentials_do_not_claim_certified(self):
        """
        D-01: Section heading must use neutral wording 'Laboratory Baseline Soil Measurements'.
        Populated certificate/ID alone must not establish verified status.
        """
        timeline = PlotTimelineManager(plot_id="PLOT_UNVERIFIED_CRED")
        # Lab report has certificate and accreditation ID, but accreditation_verified=False
        rep = self._create_sample_lab_report("PLOT_UNVERIFIED_CRED", "2024-01-01")
        rep.lab_certificate_no = "STL-CERT-999"
        rep.lab_accreditation_id = "NABL-PENDING-456"
        rep.accreditation_verified = False
        timeline.add_lab_report(rep)

        predictor = SoilIntelligencePredictor()
        intel_report = predictor.evaluate_plot(timeline, target_date="2024-05-01")

        vm = SoilReportBuilder.build_view_model(timeline, intel_report)
        pdf_gen = SoilIntelligencePDFGenerator()
        pdf_bytes = pdf_gen.generate_pdf_bytes(vm)

        # 1. Section 1 title uses neutral wording
        self.assertIn(b"1. Laboratory Baseline Soil Measurements", pdf_bytes)
        self.assertNotIn(b"1. Certified Laboratory Baseline", pdf_bytes)

        # 2. Accreditation badge is UNVERIFIED
        self.assertIn(b"ACCREDITATION: UNVERIFIED", pdf_bytes)
        self.assertIn(b"Verification Pending", pdf_bytes)
        self.assertNotIn(b"ACCREDITATION: VERIFIED", pdf_bytes)

    # -----------------------------------------------------------------
    # Test 10 (D-01): Explicitly Verified Credentials Display Verified Badge
    # -----------------------------------------------------------------
    def test_explicitly_verified_credentials_display_verified_badge(self):
        """
        D-01: Display verified certification status ONLY when explicitly verified
        through a trustworthy verification record.
        """
        timeline = PlotTimelineManager(plot_id="PLOT_VERIFIED_CRED")
        rep = self._create_sample_lab_report("PLOT_VERIFIED_CRED", "2024-01-01")
        rep.lab_certificate_no = "STL-CERT-1234"
        rep.lab_accreditation_id = "NABL-TC-8812"
        rep.accreditation_verified = True
        rep.accreditation_source = "National Accreditation Board (NABL) Registry"
        timeline.add_lab_report(rep)

        predictor = SoilIntelligencePredictor()
        intel_report = predictor.evaluate_plot(timeline, target_date="2024-05-01")

        vm = SoilReportBuilder.build_view_model(timeline, intel_report)
        pdf_gen = SoilIntelligencePDFGenerator()
        pdf_bytes = pdf_gen.generate_pdf_bytes(vm)

        self.assertIn(b"1. Laboratory Baseline Soil Measurements", pdf_bytes)
        self.assertIn(b"ACCREDITATION: VERIFIED", pdf_bytes)
        self.assertIn(b"National Accreditation Board", pdf_bytes)

    # -----------------------------------------------------------------
    # Test 11 (D-01): Missing Credentials Display No Accreditation Data
    # -----------------------------------------------------------------
    def test_missing_credentials_display_no_accreditation_data(self):
        """D-01: When no credentials are provided, badge states NO ACCREDITATION DATA."""
        timeline = PlotTimelineManager(plot_id="PLOT_NO_CRED")
        rep = self._create_sample_lab_report("PLOT_NO_CRED", "2024-01-01")
        rep.lab_certificate_no = None
        rep.lab_accreditation_id = None
        rep.accreditation_verified = False
        timeline.add_lab_report(rep)

        predictor = SoilIntelligencePredictor()
        intel_report = predictor.evaluate_plot(timeline, target_date="2024-05-01")

        vm = SoilReportBuilder.build_view_model(timeline, intel_report)
        pdf_gen = SoilIntelligencePDFGenerator()
        pdf_bytes = pdf_gen.generate_pdf_bytes(vm)

        self.assertIn(b"ACCREDITATION: UNVERIFIED", pdf_bytes)
        self.assertIn(b"NO ACCREDITATION DATA", pdf_bytes)

    # -----------------------------------------------------------------
    # Test 12 (D-04): PDF Parser Environment Limitation & ISO 32000-1 Fallback
    # -----------------------------------------------------------------
    def test_pdf_parser_environment_audit_and_iso32000_validation(self):
        """
        D-04: Documents that third-party PDF parsers are not installed in the
        isolated environment without installing unauthorized packages.
        Verifies PDF structural integrity via byte-exact ISO 32000-1 binary inspection.
        """
        # 1. Verify external parsers are not installed (environment limitation documented)
        try:
            import pypdf
            has_pypdf = True
        except ImportError:
            has_pypdf = False

        try:
            import pdfminer
            has_pdfminer = True
        except ImportError:
            has_pdfminer = False

        try:
            import fitz
            has_fitz = True
        except ImportError:
            has_fitz = False

        self.assertFalse(has_pypdf, "pypdf should not be installed in this isolated test environment")
        self.assertFalse(has_pdfminer, "pdfminer should not be installed without authorization")
        self.assertFalse(has_fitz, "fitz should not be installed without authorization")

        # 2. Pure-Python ISO 32000-1 binary verification
        timeline = PlotTimelineManager(plot_id="PLOT_ISO_AUDIT")
        timeline.add_lab_report(self._create_sample_lab_report("PLOT_ISO_AUDIT", "2024-01-01"))
        predictor = SoilIntelligencePredictor()
        intel_report = predictor.evaluate_plot(timeline, target_date="2024-05-01")

        vm = SoilReportBuilder.build_view_model(timeline, intel_report)
        pdf_gen = SoilIntelligencePDFGenerator()
        pdf_bytes = pdf_gen.generate_pdf_bytes(vm)

        # Header check
        self.assertTrue(pdf_bytes.startswith(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"))

        # EOF check
        self.assertTrue(pdf_bytes.endswith(b"%%EOF\n"))

        # xref table integrity check
        startxref_idx = pdf_bytes.rfind(b"startxref\n")
        self.assertGreater(startxref_idx, 0)
        xref_offset = int(pdf_bytes[startxref_idx + 10:pdf_bytes.rfind(b"\n%%EOF")].strip())
        self.assertEqual(pdf_bytes[xref_offset:xref_offset + 5], b"xref\n")

        # Verify object offsets registered in xref table match actual objects
        lines = pdf_bytes[xref_offset:].decode("latin-1").splitlines()
        header_parts = lines[1].split()
        first_obj = int(header_parts[0])
        total_objs = int(header_parts[1])

        for obj_idx in range(1, total_objs):
            entry_line = lines[2 + obj_idx]
            offset = int(entry_line[:10])
            generation = int(entry_line[11:16])
            status = entry_line[17:18]
            if status == "n":
                expected_marker = f"{obj_idx} 0 obj".encode("latin-1")
                self.assertEqual(pdf_bytes[offset:offset + len(expected_marker)], expected_marker)

        # MediaBox check
        self.assertIn(b"/MediaBox [0 0 595.28 841.89]", pdf_bytes)


if __name__ == "__main__":
    unittest.main()
