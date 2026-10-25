"""
Regression Test Suite: Potassium (K) and Soil pH Extraction & Table Layout Resilience
=====================================================================================
Validates:
1. Exact failing Ashwamedh laboratory report:
   - Nitrogen: 542.0 kg/ha
   - Phosphorus: 144.0 kg/ha
   - Potassium: 3147.0 kg/ha
   - Confirms Soil pH is identified as genuinely absent (does not invent or fabricate pH).
   - Confirms HTTP 422 structured error accurately reports ONLY Soil pH as missing,
     and lists Potassium under partially readable nutrients.
2. Robustness to Potassium heading and OCR variants:
   - Available Potassium (as K), Available Potassium (K2O), Available K, K (kg/ha), Potash,
     and common OCR misspellings (Availoble, Potossiumk, Avateble, Palassium, etc.).
3. Robustness to Soil pH headings and dilution ratios:
   - Soil Reaction (pH 1:2.5), pH (1:2.5 suspension), pH (1:2.5 soil-water suspension),
     pH Value, pH Index, table layouts.
4. End-to-end crop recommendation generation when a complete laboratory report is supplied.
"""

import os
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.crop_recommendation.service import CropRecommendationService
from ml.soil_intelligence.ocr.extractor import LabReportExtractor
from ml.soil_intelligence.ocr.normalizer import ReportFieldNormalizer
from ml.soil_intelligence.schemas import ChemicalForm, NutrientUnit

client = TestClient(app)
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "backend", "tests", "fixtures", "soil_reports")


def test_failing_ashwamedh_report_extracts_potassium_and_identifies_missing_ph():
    """
    Validates the exact real-world failing report (images.png / nashik_soil_report_missing_ph.png).
    Ensures Potassium (3147.0 kg/ha) is successfully extracted and no longer reported as missing.
    Ensures Soil pH is accurately reported as missing without fabrication.
    """
    fixture_path = os.path.join(FIXTURES_DIR, "nashik_soil_report_missing_ph.png")
    assert os.path.exists(fixture_path), f"Fixture missing: {fixture_path}"

    with open(fixture_path, "rb") as f:
        file_bytes = f.read()

    service = CropRecommendationService()
    with pytest.raises(HTTPException) as exc_info:
        service.process_soil_report_and_recommend(
            file_bytes=file_bytes,
            filename="nashik_soil_report_missing_ph.png"
        )

    err = exc_info.value
    assert err.status_code == 422
    detail = str(err.detail)

    # 1. Soil pH must be listed as missing
    assert "Soil pH" in detail

    # 2. Potassium must NOT be listed as missing
    assert "Potassium (K)" not in detail.split("Partially readable:")[0]

    # 3. Nitrogen, Phosphorus, and Potassium must all be listed under Partially readable
    assert "Nitrogen (542.0 kg/ha)" in detail
    assert "Phosphorus (144.0 kg/ha)" in detail
    assert "Potassium (3147.0 kg/ha)" in detail


def test_potassium_text_variants_and_ocr_confusions():
    """Validates that various Potassium headings and OCR noise patterns normalize accurately."""
    test_cases = [
        ("4.  Available Potassium (as K)  3147  kg/ha", 3147.0, ChemicalForm.ELEMENTAL_K),
        ("Available Potassium(K2O)  300.0  kg/ha", 300.0 * 0.8302, ChemicalForm.OXIDE_K2O),
        ("Available Potassium : 280 kg/ha", 280.0, ChemicalForm.ELEMENTAL_K),
        ("Potassium (K) : 310 kg/ha", 310.0, ChemicalForm.ELEMENTAL_K),
        ("K (kg/ha) 280", 280.0, ChemicalForm.ELEMENTAL_K),
        ("Available K : 250 kg/ha", 250.0, ChemicalForm.ELEMENTAL_K),
        ("Potash (K2O) : 320 kg/ha", 320.0 * 0.8302, ChemicalForm.OXIDE_K2O),
        ("Availoble Potossiumk(os K)  3147  kgyha", 3147.0, ChemicalForm.ELEMENTAL_K),
        ("Avaltoble Potosslum (os K)  3147  kq/ha", 3147.0, ChemicalForm.ELEMENTAL_K),
        ("Avateble Palassium (as K)  3147  kg/ha", 3147.0, ChemicalForm.ELEMENTAL_K),
    ]

    for line_text, expected_val, expected_form in test_cases:
        doc = LabReportExtractor.extract_from_text(f"Physico-Chemical Analysis\n{line_text}")
        rep = doc.extracted_report
        assert rep is not None, f"Report extraction failed for: {line_text}"
        assert rep.potassium is not None, f"Potassium was not extracted for: {line_text}"
        assert rep.potassium.normalized_value_kg_ha is not None, f"Normalized K is None for: {line_text}"
        assert abs(rep.potassium.normalized_value_kg_ha - expected_val) < 1.0, (
            f"Expected {expected_val}, got {rep.potassium.normalized_value_kg_ha} for {line_text}"
        )
        assert rep.potassium.reported_form == expected_form, (
            f"Expected form {expected_form}, got {rep.potassium.reported_form} for {line_text}"
        )


def test_ph_text_variants_and_dilution_ratios():
    """Validates that Soil pH with dilution ratios (1:2.5) and table formats parse cleanly."""
    test_cases = [
        ("Soil Reaction (pH) : 7.35", 7.35),
        ("Soil Reaction (pH 1:2.5) 7.20", 7.20),
        ("pH (1:2.5 soil-water suspension) : 7.40", 7.40),
        ("pH (1:2.5) : 7.25", 7.25),
        ("pH Value: 8.10", 8.10),
        ("pH : 6.50", 6.50),
        ("p.H. : 7.20", 7.20),
        ("pH Index : 7.50", 7.50),
        ("Soil Reaction 7.65", 7.65),
        ("Soil Reaction (pH)  7.35  pHIndex", 7.35),
    ]

    for line_text, expected_val in test_cases:
        doc = LabReportExtractor.extract_from_text(f"Physico-Chemical Analysis\n{line_text}")
        rep = doc.extracted_report
        assert rep is not None, f"Report extraction failed for: {line_text}"
        assert rep.ph is not None, f"pH was not extracted for: {line_text}"
        assert abs(rep.ph - expected_val) < 0.05, f"Expected pH {expected_val}, got {rep.ph} for {line_text}"


def test_complete_report_generates_recommendations_end_to_end():
    """Validates that a complete report with N, P, K, and pH produces valid top 3 recommendations."""
    pdf_fixture = os.path.join(FIXTURES_DIR, "soil_report_01_normal.pdf")
    assert os.path.exists(pdf_fixture)

    with open(pdf_fixture, "rb") as f:
        file_bytes = f.read()

    service = CropRecommendationService()
    res = service.process_soil_report_and_recommend(
        file_bytes=file_bytes,
        filename="soil_report_01_normal.pdf"
    )

    assert res.success is True
    assert res.district == "Pune"
    assert len(res.recommendations) == 3
    for rec in res.recommendations:
        assert rec.crop
        assert rec.suitability_label in ["Highly Suitable", "Moderately Suitable", "Low Suitability"]
        assert len(rec.reason) > 10
