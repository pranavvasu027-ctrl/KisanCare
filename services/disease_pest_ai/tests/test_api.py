"""Tests for the Disease & Pest AI FastAPI REST Service and API Key Security."""

import io
from pathlib import Path
from fastapi.testclient import TestClient
from PIL import Image
import pytest

from disease_pest_ai.api.config import API_KEY, API_KEY_NAME
from disease_pest_ai.api.main import app

client = TestClient(app)

TEST_DATA_DIR = Path(__file__).resolve().parent.parent / "test_data"
SAMPLE_IMG = TEST_DATA_DIR / "cotton_field_eval" / "bacterial_blight_1.jpg"
if not SAMPLE_IMG.exists():
    SAMPLE_IMG = TEST_DATA_DIR / "cotton_eval" / "bacterial_blight" / "bacterial_blight_1.jpg"


def test_root_endpoint():
    """Verify root endpoint returns service info and documentation links."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "service" in data
    assert "endpoints" in data


def test_health_check_endpoint():
    """Verify health check returns healthy status without authentication."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "disease_classifier" in data["models"]
    assert "pest_detector" in data["models"]


def test_diagnose_missing_api_key_rejected():
    """Verify missing API key raises 401 Unauthorized."""
    # Create sample image bytes
    img = Image.new("RGB", (200, 200), color="green")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    files = {"file": ("leaf.jpg", buf, "image/jpeg")}
    data = {
        "crop_name": "Cotton",
        "location_state": "Maharashtra",
        "growth_stage": "fruiting",
        "image_type": "leaf",
    }

    response = client.post("/api/v1/diagnose", files=files, data=data)
    assert response.status_code == 401
    assert "Missing API Key" in response.text


def test_diagnose_invalid_api_key_rejected():
    """Verify invalid API key raises 401 Unauthorized."""
    img = Image.new("RGB", (200, 200), color="green")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    files = {"file": ("leaf.jpg", buf, "image/jpeg")}
    data = {
        "crop_name": "Cotton",
        "location_state": "Maharashtra",
        "growth_stage": "fruiting",
        "image_type": "leaf",
    }
    headers = {API_KEY_NAME: "WRONG_UNAUTHORIZED_KEY"}

    response = client.post("/api/v1/diagnose", files=files, data=data, headers=headers)
    assert response.status_code == 401
    assert "Invalid API Key" in response.text


def test_diagnose_valid_api_key_authorized():
    """Verify valid API key successfully executes inference and returns diagnosis for supported crop."""
    assert SAMPLE_IMG.exists()

    with open(SAMPLE_IMG, "rb") as f:
        img_bytes = f.read()

    files = {"file": ("cotton_blight.jpg", io.BytesIO(img_bytes), "image/jpeg")}
    data = {
        "crop_name": "Cotton",
        "location_state": "Maharashtra",
        "growth_stage": "fruiting",
        "image_type": "leaf",
        "generate_visual_explanation": "false",
    }
    headers = {API_KEY_NAME: API_KEY}

    response = client.post("/api/v1/diagnose", files=files, data=data, headers=headers)
    assert response.status_code == 200
    res_json = response.json()
    assert "disease" in res_json
    assert res_json["disease"]["condition"] == "Bacterial Blight"
    assert res_json["disease"]["crop_match"] is True
    assert "treatment" in res_json


def test_diagnose_bearer_token_authorized():
    """Verify valid API key via Bearer token header successfully authorizes."""
    assert SAMPLE_IMG.exists()

    with open(SAMPLE_IMG, "rb") as f:
        img_bytes = f.read()

    files = {"file": ("cotton_blight.jpg", io.BytesIO(img_bytes), "image/jpeg")}
    data = {
        "crop_name": "Cotton",
        "location_state": "Maharashtra",
        "growth_stage": "fruiting",
        "image_type": "leaf",
        "generate_visual_explanation": "false",
    }
    headers = {"Authorization": f"Bearer {API_KEY}"}

    response = client.post("/api/v1/diagnose", files=files, data=data, headers=headers)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["disease"]["condition"] == "Bacterial Blight"


def test_diagnose_unsupported_crop_rejected():
    """Verify unsupported crops return 422 even with valid credentials."""
    img = Image.new("RGB", (200, 200), color="green")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    files = {"file": ("tomato.jpg", buf, "image/jpeg")}
    data = {
        "crop_name": "Tomato",
        "location_state": "Maharashtra",
    }
    headers = {API_KEY_NAME: API_KEY}

    response = client.post("/api/v1/diagnose", files=files, data=data, headers=headers)
    assert response.status_code == 422
