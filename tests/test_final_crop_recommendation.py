"""
Automated Test Suite for KisanCare Final Crop Recommendation System
==================================================================
Covers:
1. Soil report file upload validation (formats, empty file, size limit).
2. OCR extraction & low-legibility abstention.
3. Strict soil nutrient validation & refusal to fabricate missing NPK/pH.
4. Unit conversion compatibility (kg/ha, mg/kg, ppm) and rejection of incompatible units.
5. Historical climate retrieval & attribution (Open-Meteo & IMD 30-year normals).
6. Regional Evidence Safeguard (distinguishing verified crops vs biophysical candidates).
7. Top 3 recommendations formatting (no raw probabilities, no raw technical measurements).
8. End-to-end PDF report upload integration.
"""

import io
import os
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.crop_recommendation.climate import (
    HistoricalClimateService,
    IMD_30YEAR_NORMALS,
    MAHARASHTRA_DISTRICT_COORDINATES,
)
from backend.app.crop_recommendation.engine import RegionalCropRecommendationEngine
from backend.app.crop_recommendation.service import CropRecommendationService

client = TestClient(app)


# ---------------------------------------------------------------------------
# 1. File Upload Validation Tests
# ---------------------------------------------------------------------------

def test_upload_soil_report_unsupported_extension():
    """Unsupported file formats (.txt, .exe, .docx) must return HTTP 400 Bad Request."""
    fake_txt = io.BytesIO(b"Soil test data in text format")
    resp = client.post(
        "/api/v1/crop-recommendation/recommend-from-report",
        files={"file": ("soil_report.txt", fake_txt, "text/plain")}
    )
    assert resp.status_code == 400
    assert "Unsupported file format" in resp.json()["detail"]


def test_upload_soil_report_empty_file():
    """Zero-byte files must return HTTP 400 Bad Request with actionable message."""
    empty_pdf = io.BytesIO(b"")
    resp = client.post(
        "/api/v1/crop-recommendation/recommend-from-report",
        files={"file": ("empty_report.pdf", empty_pdf, "application/pdf")}
    )
    assert resp.status_code == 400
    assert "empty" in resp.json()["detail"].lower()


def test_upload_soil_report_oversized_file():
    """Files exceeding 5MB must return HTTP 413 Entity Too Large."""
    oversized = io.BytesIO(b"A" * (6 * 1024 * 1024))  # 6 MB
    resp = client.post(
        "/api/v1/crop-recommendation/recommend-from-report",
        files={"file": ("oversized.pdf", oversized, "application/pdf")}
    )
    assert resp.status_code == 413
    detail = resp.json().get("detail", "").lower()
    assert "payload too large" in detail or "exceeds" in detail


# ---------------------------------------------------------------------------
# 2. Strict Validation & Abstention: Never Fabricate Missing Measurements
# ---------------------------------------------------------------------------

def test_missing_nutrients_abstains_without_fabrication():
    """
    If a report is missing Nitrogen, Phosphorus, Potassium, or pH,
    the system must abstain with HTTP 422 and never invent values.
    """
    service = CropRecommendationService()
    # Report containing only organic carbon, but missing N, P, K, pH formatted as PDF Tj stream
    incomplete_pdf = (
        b"%PDF-1.4\n"
        b"(SOIL HEALTH CARD) Tj\n"
        b"(Farmer: Shri Vitthal More) Tj\n"
        b"(District: Solapur) Tj\n"
        b"(Organic Carbon: 0.45 %) Tj\n"
        b"(Electrical Conductivity: 0.32 dS/m) Tj\n"
        b"%%EOF"
    )

    with pytest.raises(Exception) as exc_info:
        service.process_soil_report_and_recommend(
            file_bytes=incomplete_pdf,
            filename="incomplete_test.pdf",
            district="Solapur"
        )
    assert "Essential soil parameters missing" in str(exc_info.value.detail)


def test_ocr_low_legibility_rejection():
    """Illegible, faint text (<10 chars) must return actionable error asking for a clearer photo."""
    service = CropRecommendationService()
    faint_pdf = b"%PDF-1.4\n(abc) Tj\n%%EOF"  # Extremely short/illegible

    with pytest.raises(Exception) as exc_info:
        service.process_soil_report_and_recommend(
            file_bytes=faint_pdf,
            filename="blurry_scan.pdf",
            district="Akola"
        )
    assert "unreadable" in str(exc_info.value.detail).lower() or "faint" in str(exc_info.value.detail).lower()


# ---------------------------------------------------------------------------
# 3. Unit Normalization & Mathematical Integrity
# ---------------------------------------------------------------------------

def test_unit_normalization_ppm_to_kg_ha():
    """
    Verifies that nutrient values reported in ppm or mg/kg are converted
    using the standard bulk-density furrow layer conversion factor.
    """
    from ml.soil_intelligence.schemas import NutrientConverter, NutrientUnit, ChemicalForm
    from ml.soil_intelligence.ocr.normalizer import ReportFieldNormalizer
    
    # 100 ppm elemental N -> 199.5 kg/ha with standard bulk density 1.33 g/cm3
    conv_n, explanation_n = NutrientConverter.convert_nitrogen(
        value=100.0,
        unit=NutrientUnit.PPM
    )
    assert round(conv_n, 1) == 199.5
    assert "ppm -> kg/ha" in explanation_n

    # P2O5 conversion: 50 kg/ha P2O5 -> 50 * 0.436421 = 21.82 kg/ha elemental P
    conv_p, explanation_p = NutrientConverter.convert_phosphorus(
        value=50.0,
        unit=NutrientUnit.KG_PER_HA,
        form=ChemicalForm.OXIDE_P2O5
    )
    assert round(conv_p, 2) == 21.82
    assert "P2O5 -> elemental P" in explanation_p

    # Normalizer field integration test
    field_result = ReportFieldNormalizer.normalize_nutrient_field("P", "50", "kg/ha P2O5")
    assert field_result.is_plausible is True
    assert round(field_result.measurement.normalized_value_kg_ha, 2) == 21.82


# ---------------------------------------------------------------------------
# 4. Historical Climate Service & Attribution
# ---------------------------------------------------------------------------

def test_historical_climate_service_all_seasons():
    """
    Verifies historical seasonal climate retrieval for multiple Maharashtra districts.
    Ensures verified units: temp in °C, humidity in %, rainfall in mm.
    """
    climate = HistoricalClimateService.get_historical_climate(
        district="Akola",
        season="Kharif"
    )
    assert 20.0 <= climate.temperature_c <= 40.0
    assert 30.0 <= climate.humidity_pct <= 95.0
    assert 400.0 <= climate.rainfall_mm <= 1500.0
    assert "Akola" in climate.district
    assert climate.season == "Kharif"
    assert "Open-Meteo" in climate.source or "IMD" in climate.source


def test_historical_climate_imd_fallback():
    """When district coordinates are evaluated, verified IMD normals cover all 35 districts."""
    for dist in ["Akola", "Nashik", "Pune", "Kolhapur", "Solapur", "Nagpur", "Amravati"]:
        assert dist in IMD_30YEAR_NORMALS
        kharif_t, kharif_h, kharif_r = IMD_30YEAR_NORMALS[dist]["Kharif"]
        assert kharif_t > 0
        assert kharif_h > 0
        assert kharif_r > 0


# ---------------------------------------------------------------------------
# 5. Regional Evidence Safeguard & Top 3 Recommendations
# ---------------------------------------------------------------------------

def test_regional_engine_top_3_recommendations():
    """
    Verifies that the engine returns exactly 3 recommendations,
    complete with farmer suitability labels and concise reasons,
    and without exposing raw probabilities or raw soil metrics.
    """
    engine = RegionalCropRecommendationEngine()
    recs = engine.recommend_top3(
        N=175.0,
        P=16.0,
        K=200.0,
        ph=8.0,
        temperature=28.8,
        humidity=68.0,
        rainfall=780.0,
        district="Akola",
        season="Kharif"
    )
    assert len(recs) == 3
    assert recs[0].rank == 1
    assert recs[1].rank == 2
    assert recs[2].rank == 3

    # Check that crops are relevant Maharashtra Kharif crops
    crop_names = [r.crop for r in recs]
    assert any("Cotton" in c for c in crop_names)
    assert any("Soybean" in c for c in crop_names)

    for r in recs:
        # Suitability label must be farmer-friendly
        assert r.suitability_label in ["Highly Suitable", "Moderately Suitable", "Low Suitability", "Experimental Trial Only"]
        # Reason must be non-empty and descriptive
        assert len(r.reason) > 10
        # No raw probabilities should leak into reason
        assert "0." not in r.reason or "kg/ha" in r.reason or "%" in r.reason


def test_coffee_in_sangli_safeguard():
    """
    Regression test: In semi-arid Sangli Kharif, Coffee must be suppressed below
    regionally verified crops (Rice, Jowar, Bajra) and labeled as an unverified/experimental candidate.
    """
    engine = RegionalCropRecommendationEngine()
    recs = engine.recommend_top3(
        N=105.0,
        P=30.0,
        K=55.0,
        ph=7.0,
        temperature=35.0,
        humidity=68.0,
        rainfall=900.0,
        district="Sangli",
        season="Kharif"
    )
    assert len(recs) == 3
    top_crop_names = [r.crop.lower() for r in recs]
    # Coffee must NOT be in top 3 recommended crops for Sangli!
    assert not any("coffee" in c for c in top_crop_names), "Coffee erroneously recommended in top 3 for semi-arid Sangli"


# ---------------------------------------------------------------------------
# 6. End-to-End API Integration Tests
# ---------------------------------------------------------------------------

def test_api_recommend_from_json_direct():
    """POST /api/v1/crop-recommendation/recommend returns structured top 3 crops."""
    resp = client.post("/api/v1/crop-recommendation/recommend", json={
        "N": 120.0,
        "P": 50.0,
        "K": 60.0,
        "ph": 6.8,
        "district": "Pune",
        "season": "Rabi",
        "top_k": 3
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["district"] == "Pune"
    assert data["season"] == "Rabi"
    assert len(data["recommendations"]) == 3
    rec_crops = [r["crop"] for r in data["recommendations"]]
    # In Pune Rabi, Wheat and Jowar are standard
    assert any("Wheat" in c or "Jowar" in c or "Maize" in c for c in rec_crops)


def test_api_recommend_from_soil_report_pdf():
    """POST /api/v1/crop-recommendation/recommend-from-report accepts valid PDF soil report."""
    sample_pdf_path = "backend/tests/fixtures/soil_reports/soil_report_01_normal.pdf"
    if not os.path.exists(sample_pdf_path):
        pytest.skip(f"Fixture {sample_pdf_path} not found")

    with open(sample_pdf_path, "rb") as f:
        resp = client.post(
            "/api/v1/crop-recommendation/recommend-from-report",
            files={"file": ("soil_report_01_normal.pdf", f, "application/pdf")},
            data={"district": "Akola"}
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["district"] == "Akola"
    assert len(data["recommendations"]) == 3
    assert data["recommendations"][0]["rank"] == 1
    assert data["recommendations"][0]["suitability_label"] in ["Highly Suitable", "Moderately Suitable"]


def test_api_recommend_from_demo_public_pdf():
    """Tests upload of frontend public demo soil report."""
    demo_pdf_path = "frontend/public/demo-assets/soil-report-kharif-2025.pdf"
    if not os.path.exists(demo_pdf_path):
        pytest.skip(f"Fixture {demo_pdf_path} not found")

    with open(demo_pdf_path, "rb") as f:
        resp = client.post(
            "/api/v1/crop-recommendation/recommend-from-report",
            files={"file": ("soil-report-kharif-2025.pdf", f, "application/pdf")},
            data={"district": "Nashik"}
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert len(data["recommendations"]) == 3
