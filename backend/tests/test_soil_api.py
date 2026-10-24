"""
Soil Intelligence FastAPI Integration Tests
===========================================
Validates the complete HTTP contract for the Soil Intelligence backend router:
1. Benchmarks & metadata discovery
2. Raw report OCR parsing & human review workflow
3. Baseline lab test confirmation
4. Multi-year agronomic event logging (fertilizer & crop harvest)
5. Plot digital twin status, depletion ledger, and agronomic advisory
6. ISO 32000-1 printable vector PDF streaming
7. Continuous laboratory comparator & drift evaluation
8. Plot timeline cleanup
"""

import io
import os
import pytest
from PIL import Image, ImageDraw
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.api.soil.store import SoilPlotStore

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_soil_store():
    """Resets the in-memory soil store before each test run."""
    store = SoilPlotStore.get_instance()
    store.reset()
    yield
    store.reset()


def test_get_benchmarks():
    """Tests the discovery endpoint for supported fertilizers, crops, and tolerances."""
    response = client.get("/api/v1/soil/benchmarks")
    assert response.status_code == 200
    data = response.json()
    assert "urea" in data["supported_fertilizers"]
    assert "dap" in data["supported_fertilizers"]
    assert "soybean" in data["supported_crops"]
    assert "wheat" in data["supported_crops"]
    assert data["tolerances"]["N_tolerance_kg_ha"] == 25.0
    assert data["tolerances"]["P_tolerance_kg_ha"] == 5.0
    assert data["tolerances"]["K_tolerance_kg_ha"] == 30.0


def test_parse_soil_report_high_confidence():
    """Tests parsing a standard Soil Health Card format with high confidence."""
    report_text = """
    GOVERNMENT OF MAHARASHTRA
    DISTRICT SOIL TESTING LABORATORY, LATUR
    Soil Health Card Certificate
    Sample No: MH6092432/2024-25/441209
    Date: 15-Oct-2024
    Plot No: PLOT_API_01
    Farmer Name: Ramesh Patil

    SOIL PARAMETERS:
    pH: 7.40 (Normal)
    EC: 0.65 dS/m
    Organic Carbon: 0.55 %
    Available Nitrogen: 240.0 kg/ha (Low)
    Available Phosphorus: 18.5 kg/ha P2O5 (Medium)
    Available Potassium: 310.0 kg/ha K2O (High)
    """
    response = client.post("/api/v1/soil/reports/parse", json={"report_text": report_text, "plot_id": "PLOT_API_01"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["confidence_score"] >= 0.8
    assert data["requires_human_review"] is False
    assert data["ph"] == 7.40
    assert data["ec_ds_m"] == 0.65
    assert data["organic_carbon_pct"] == 0.55

    # Check Nitrogen
    assert data["nitrogen"]["reported_value"] == 240.0
    assert data["nitrogen"]["normalized_value_kg_ha"] == 240.0

    # Check Phosphorus: 18.5 kg/ha P2O5 -> elemental P ~8.074 kg/ha
    assert data["phosphorus"]["reported_value"] == 18.5
    assert abs(data["phosphorus"]["normalized_value_kg_ha"] - 8.074) < 0.05

    # Check Potassium: 310.0 kg/ha K2O -> elemental K ~257.348 kg/ha
    assert data["potassium"]["reported_value"] == 310.0
    assert abs(data["potassium"]["normalized_value_kg_ha"] - 257.348) < 0.1


def test_parse_report_out_of_bounds_and_manual_correction():
    """Tests that out-of-bounds values trigger human review and can be corrected."""
    extreme_text = """
    Sample No: LAB_ERR_99
    Date: 2024-01-01
    Plot No: PLOT_REVIEW_01
    pH: 13.50
    Available Nitrogen: 12000.0 kg/ha
    """
    response = client.post("/api/v1/soil/reports/parse", json={"report_text": extreme_text})
    assert response.status_code == 200
    data = response.json()
    assert data["requires_human_review"] is True
    assert data["review_token"] is not None
    assert any(iss["issue_code"] == "OUT_OF_BOUNDS" for iss in data["validation_issues"])

    # Submit manual correction
    corr_resp = client.post("/api/v1/soil/reports/review/correct", json={
        "review_token": data["review_token"],
        "reviewer_id": "DR_AGRONOMIST_01",
        "corrections": {"Nitrogen": "220.0", "pH": "7.5"},
        "notes": "Typo corrected from OCR stream."
    })
    assert corr_resp.status_code == 200
    assert corr_resp.json()["status"] == "corrected"


def test_upload_soil_report_pdf():
    """Tests uploading a real PDF Soil Health Card document."""
    pdf_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "ml", "soil_intelligence", "reporting", "sample_illustrative_report.pdf"
    )
    assert os.path.exists(pdf_path), f"Sample PDF not found at {pdf_path}"

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    response = client.post(
        "/api/v1/soil/reports/upload",
        files={"file": ("sample_report.pdf", pdf_bytes, "application/pdf")},
        data={"plot_id": "PLOT_UPLOAD_PDF_01"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["plot_id"] == "PLOT_UPLOAD_PDF_01"
    assert data["report_id"] is not None


def test_upload_soil_report_image():
    """Tests uploading a real JPG/PNG image containing soil test values."""
    img = Image.new("RGB", (600, 200), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((20, 30), "GOVERNMENT OF MAHARASHTRA\npH: 7.40\nAvailable Nitrogen: 240.0 kg/ha", fill=(0, 0, 0))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    png_bytes = buf.getvalue()

    response = client.post(
        "/api/v1/soil/reports/upload",
        files={"file": ("soil_card.png", png_bytes, "image/png")},
        data={"plot_id": "PLOT_UPLOAD_IMG_01"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["plot_id"] == "PLOT_UPLOAD_IMG_01"


def test_upload_soil_report_unsupported_format():
    """Tests that uploading an unsupported format returns 400 Bad Request."""
    response = client.post(
        "/api/v1/soil/reports/upload",
        files={"file": ("soil_data.csv", b"pH,N,P,K\n7.2,240,18,300", "text/csv")}
    )
    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]


def test_upload_soil_report_empty_file():
    """Tests that uploading a 0-byte file returns 400 Bad Request."""
    response = client.post(
        "/api/v1/soil/reports/upload",
        files={"file": ("empty.pdf", b"", "application/pdf")}
    )
    assert response.status_code == 400
    assert "empty (0 bytes)" in response.json()["detail"]


def test_upload_soil_report_oversized_file():
    """Tests that uploading a file > 5MB returns 413 Request Entity Too Large."""
    oversized_bytes = b"0" * (5 * 1024 * 1024 + 512)
    response = client.post(
        "/api/v1/soil/reports/upload",
        files={"file": ("large_report.pdf", oversized_bytes, "application/pdf")}
    )
    assert response.status_code == 413
    detail = response.json().get("detail", "")
    assert "Payload too large" in detail or "exceeds the 5MB maximum limit" in detail


def test_full_plot_lifecycle():
    """Tests end-to-end plot lifecycle: baseline -> events -> status -> advisory -> PDF -> comparison."""
    plot_id = "PLOT_MAHA_001"

    # 1. Establish verified physical baseline
    baseline_payload = {
        "plot_id": plot_id,
        "farm_id": "FARM_LATUR_01",
        "sample_date": "2023-06-15",
        "lab_name": "District Soil Testing Laboratory, Latur",
        "lab_certificate_no": "STL-2023-8871",
        "lab_accreditation_id": "NABL-TC-8812",
        "accreditation_verified": True,
        "accreditation_source": "NABL State Portal",
        "nitrogen_kg_ha": 245.0,
        "phosphorus_kg_ha": 18.5,
        "potassium_kg_ha": 320.0,
        "ph": 7.80,
        "ec_ds_m": 0.35,
        "organic_carbon_pct": 0.52
    }
    resp_base = client.post("/api/v1/soil/reports/confirm", json=baseline_payload)
    assert resp_base.status_code == 200
    assert resp_base.json()["status"] == "confirmed"

    # 2. Add Fertilizer Event (DAP 100 kg/ha on 2023-06-20)
    fert_payload = {
        "fertilizer_grade": "DAP",
        "quantity_kg_ha": 100.0,
        "application_date": "2023-06-20",
        "notes": "Basal application at sowing"
    }
    resp_fert = client.post(f"/api/v1/soil/plots/{plot_id}/events/fertilizer", json=fert_payload)
    assert resp_fert.status_code == 200
    fert_data = resp_fert.json()
    assert fert_data["n_flux_kg_ha"] == 18.0
    assert abs(fert_data["p_flux_kg_ha"] - 20.075) < 0.1  # 46% P2O5 * 0.4364

    # 3. Add Crop Harvest Event (Soybean 2.2 t/ha on 2023-10-15)
    harvest_payload = {
        "crop_name": "Soybean",
        "yield_tonnes_ha": 2.2,
        "harvest_date": "2023-10-15",
        "residue_retained": False
    }
    resp_harv = client.post(f"/api/v1/soil/plots/{plot_id}/events/harvest", json=harvest_payload)
    assert resp_harv.status_code == 200
    harv_data = resp_harv.json()
    assert harv_data["n_flux_kg_ha"] < 0  # Crop removal is negative flux

    # 4. List Events
    resp_events = client.get(f"/api/v1/soil/plots/{plot_id}/events")
    assert resp_events.status_code == 200
    assert len(resp_events.json()) == 2

    # 5. Query Plot Status & Advisory
    resp_status = client.get(f"/api/v1/soil/plots/{plot_id}/status?as_of_date=2023-11-01")
    assert resp_status.status_code == 200
    status_data = resp_status.json()
    assert status_data["plot_id"] == plot_id
    assert status_data["has_baseline_lab_test"] is True
    assert status_data["accreditation_verified"] is True
    assert status_data["baseline_npk_kg_ha"]["N"] == 245.0
    assert status_data["net_mass_balance_ledger"] is not None
    assert status_data["is_operational_authorized"] is False  # Safe gate is strictly blocked
    assert len(status_data["advisories"]) > 0

    # 6. Stream Printable PDF Report
    resp_pdf = client.get(f"/api/v1/soil/plots/{plot_id}/report.pdf?target_date=2023-11-01")
    assert resp_pdf.status_code == 200
    assert resp_pdf.headers["content-type"] == "application/pdf"
    assert "attachment" in resp_pdf.headers["content-disposition"]
    pdf_bytes = resp_pdf.content
    assert pdf_bytes.startswith(b"%PDF-1.4")
    assert pdf_bytes.endswith(b"%%EOF\n")
    assert b"1. Laboratory Baseline Soil Measurements" in pdf_bytes
    assert b"VERIFIED ACCREDITED" in pdf_bytes

    # 7. Compare Subsequent Re-Test (Continuous Drift Evaluation)
    retest_payload = {
        "retest_date": "2024-05-15",
        "lab_name": "District Soil Testing Laboratory, Latur",
        "accreditation_verified": True,
        "nitrogen_kg_ha": 238.0,
        "phosphorus_kg_ha": 17.2,
        "potassium_kg_ha": 305.0,
        "ph": 7.75
    }
    resp_comp = client.post(f"/api/v1/soil/plots/{plot_id}/compare", json=retest_payload)
    assert resp_comp.status_code == 200
    comp_data = resp_comp.json()
    assert comp_data["plot_id"] == plot_id
    assert comp_data["retest_date"] == "2024-05-15"
    assert "nitrogen_comparison" in comp_data
    assert comp_data["nitrogen_comparison"]["provisional_tolerance_kg_ha"] == 25.0
    assert comp_data["phosphorus_comparison"]["provisional_tolerance_kg_ha"] == 5.0
    assert comp_data["potassium_comparison"]["provisional_tolerance_kg_ha"] == 30.0

    # 8. Reset / Delete Plot
    resp_del = client.delete(f"/api/v1/soil/plots/{plot_id}")
    assert resp_del.status_code == 200
    assert resp_del.json()["status"] == "deleted"

    # Verify plot is gone
    resp_gone = client.get(f"/api/v1/soil/plots/{plot_id}/status")
    assert resp_gone.status_code == 404


def test_upload_soil_report_01_normal_ground_truth():
    """Validates full OCR pipeline on ground-truth report 01 (normal values)."""
    fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", "soil_reports", "soil_report_01_normal.pdf")
    assert os.path.exists(fixture_path), f"Fixture not found: {fixture_path}"

    with open(fixture_path, "rb") as f:
        pdf_bytes = f.read()

    response = client.post(
        "/api/v1/soil/reports/upload",
        files={"file": ("soil_report_01_normal.pdf", pdf_bytes, "application/pdf")},
        data={"plot_id": "PLOT_GT_01"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["report_id"] == "KSC-TEST-001"
    assert data["sample_date"] == "18 October 2026"
    assert data["ph"] == 7.20
    assert data["ec_ds_m"] == 0.62
    assert data["organic_carbon_pct"] == 0.58
    assert data["nitrogen"]["reported_value"] == 235.0
    assert data["nitrogen"]["normalized_value_kg_ha"] == 235.0
    assert data["phosphorus"]["reported_value"] == 20.0
    assert abs(data["phosphorus"]["normalized_value_kg_ha"] - (20.0 * 0.4364)) < 0.05
    assert data["potassium"]["reported_value"] == 285.0
    assert abs(data["potassium"]["normalized_value_kg_ha"] - (285.0 * 0.8302)) < 0.1
    assert data["requires_human_review"] is False
    assert data["raw_ocr_text"] is not None
    assert len(data["raw_ocr_text"]) > 50


def test_upload_soil_report_02_review_flags_ground_truth():
    """Validates OCR pipeline on ground-truth report 02 with out-of-bounds flags."""
    fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", "soil_reports", "soil_report_02_review_flags.pdf")
    assert os.path.exists(fixture_path), f"Fixture not found: {fixture_path}"

    with open(fixture_path, "rb") as f:
        pdf_bytes = f.read()

    response = client.post(
        "/api/v1/soil/reports/upload",
        files={"file": ("soil_report_02_review_flags.pdf", pdf_bytes, "application/pdf")},
        data={"plot_id": "PLOT_GT_02"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["report_id"] == "KSC-TEST-002"
    assert data["sample_date"] == "20 October 2026"
    assert data["ph"] == 8.70
    assert data["ec_ds_m"] == 1.35
    assert data["organic_carbon_pct"] == 0.32
    assert data["nitrogen"]["reported_value"] == 410.0
    assert data["phosphorus"]["reported_value"] == 62.0
    assert data["potassium"]["reported_value"] == 720.0
    assert data["confidence_score"] >= 0.85
    assert data["raw_ocr_text"] is not None


def test_upload_soil_report_03_alternate_format_ground_truth():
    """Validates OCR pipeline on ground-truth report 03 (alternate lab layout)."""
    fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", "soil_reports", "soil_report_03_alternate_format.pdf")
    assert os.path.exists(fixture_path), f"Fixture not found: {fixture_path}"

    with open(fixture_path, "rb") as f:
        pdf_bytes = f.read()

    response = client.post(
        "/api/v1/soil/reports/upload",
        files={"file": ("soil_report_03_alternate_format.pdf", pdf_bytes, "application/pdf")},
        data={"plot_id": "PLOT_GT_03"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["report_id"] == "SAT-2026-031"
    assert data["sample_date"] == "22 October 2026"
    assert data["ph"] == 6.45
    assert data["ec_ds_m"] == 0.41
    assert data["organic_carbon_pct"] == 0.74
    assert data["nitrogen"]["reported_value"] == 198.0
    assert data["phosphorus"]["reported_value"] == 16.8
    assert data["potassium"]["reported_value"] == 198.0



# ---------------------------------------------------------------------------
# Persistence & Multi-Tenant Authorization Tests
# ---------------------------------------------------------------------------
import jwt

TEST_SECRET = "kisancare-soil-persistence-test-secret-key-32c"

def _make_auth(user_id: str) -> dict:
    token = jwt.encode({"sub": user_id}, TEST_SECRET, algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}


def test_soil_timeline_disk_persistence_and_reload(tmp_path):
    """Verify that plot timelines and agronomic events survive simulated server restarts."""
    from backend.app.api.soil.store import SoilPlotStore

    test_file = tmp_path / "soil_test_store.pickle"
    store1 = SoilPlotStore(persistence_file=test_file)

    # 1. Add timeline and events in store1
    tm1 = store1.get_or_create_timeline("PLOT_PERSIST_01", farm_id="FARM_PERSIST_01", owner_id="farmer_owner")
    tm1.record_crop_harvest("Cotton", 3.0, "2024-06-01")
    tm1.record_fertilizer_application("Urea", 50.0, "2024-06-15")
    store1.save()

    assert test_file.exists(), "Persistence file was not created on disk"
    assert (tmp_path / "soil_test_store.json").exists(), "JSON metadata file was not created"

    # 2. Simulate complete server restart by creating a new store instance from same file
    store2 = SoilPlotStore(persistence_file=test_file)
    assert "PLOT_PERSIST_01" in store2.list_plots()

    tm2 = store2.get_timeline("PLOT_PERSIST_01")
    assert tm2 is not None
    assert tm2.plot_id == "PLOT_PERSIST_01"
    assert tm2.farm_id == "FARM_PERSIST_01"
    assert len(tm2.flux_events) == 2
    assert tm2.flux_events[0].event_date == "2024-06-01"
    assert tm2.flux_events[1].event_date == "2024-06-15"


def test_soil_multi_tenant_cross_user_protection():
    """Verify Farmer A's plot timeline cannot be viewed, mutated, or deleted by Farmer B."""
    plot_id = "PLOT_SECURE_101"

    # 1. Farmer A establishes baseline
    baseline_payload = {
        "plot_id": plot_id,
        "farm_id": "FARM_ALICE_01",
        "sample_date": "2024-01-15",
        "lab_name": "District Soil Testing Laboratory, Akola",
        "nitrogen_kg_ha": 250.0,
        "phosphorus_kg_ha": 20.0,
        "potassium_kg_ha": 300.0,
        "ph": 7.20
    }
    r_base = client.post("/api/v1/soil/reports/confirm", json=baseline_payload, headers=_make_auth("farmer_alice"))
    assert r_base.status_code == 200

    # 2. Farmer Bob attempts to log fertilizer event on Alice's plot
    fert_payload = {
        "fertilizer_grade": "DAP",
        "quantity_kg_ha": 100.0,
        "application_date": "2024-02-01"
    }
    r_fert_bob = client.post(
        f"/api/v1/soil/plots/{plot_id}/events/fertilizer",
        json=fert_payload,
        headers=_make_auth("farmer_bob")
    )
    assert r_fert_bob.status_code == 403
    assert "Access denied" in r_fert_bob.json()["detail"]

    # 3. Farmer Bob attempts to log harvest event on Alice's plot
    harv_payload = {
        "crop_name": "Cotton",
        "yield_tonnes_ha": 2.5,
        "harvest_date": "2024-05-01"
    }
    r_harv_bob = client.post(
        f"/api/v1/soil/plots/{plot_id}/events/harvest",
        json=harv_payload,
        headers=_make_auth("farmer_bob")
    )
    assert r_harv_bob.status_code == 403
    assert "Access denied" in r_harv_bob.json()["detail"]

    # 4. Farmer Bob attempts to read Alice's status or PDF
    r_stat_bob = client.get(f"/api/v1/soil/plots/{plot_id}/status", headers=_make_auth("farmer_bob"))
    assert r_stat_bob.status_code == 403
    assert "Access denied" in r_stat_bob.json()["detail"]

    r_pdf_bob = client.get(f"/api/v1/soil/plots/{plot_id}/report.pdf", headers=_make_auth("farmer_bob"))
    assert r_pdf_bob.status_code == 403
    assert "Access denied" in r_pdf_bob.json()["detail"]

    # 5. Farmer Bob attempts to delete Alice's plot
    r_del_bob = client.delete(f"/api/v1/soil/plots/{plot_id}", headers=_make_auth("farmer_bob"))
    assert r_del_bob.status_code == 403
    assert "Access denied" in r_del_bob.json()["detail"]

    # 6. Farmer Alice successfully performs operations
    r_fert_alice = client.post(
        f"/api/v1/soil/plots/{plot_id}/events/fertilizer",
        json=fert_payload,
        headers=_make_auth("farmer_alice")
    )
    assert r_fert_alice.status_code == 200

    r_stat_alice = client.get(f"/api/v1/soil/plots/{plot_id}/status", headers=_make_auth("farmer_alice"))
    assert r_stat_alice.status_code == 200
