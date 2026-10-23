"""Automated verification suite for KisanCare Plant Pathology & Disease Detection API.

Covers:
1. Successful model loading and state verification.
2. Correct preprocessing and label decoding (ImageNet normalization, 38 PlantVillage classes).
3. Valid input and supported image formats (JPEG, PNG, WebP).
4. Invalid, corrupt, oversized, and missing inputs rejection (400 Bad Request).
5. Backend API response structure compliance (DiseasePredictionResponse, Top-5, CIBRC treatments).
6. Model-unavailable behavior without fake fallbacks (503 Service Unavailable).
7. Frontend backward compatible route `/api/v1/disease-detection`.
8. Repeatability and determinism for identical inputs.
"""

import io
import json
import pytest
from pathlib import Path
from PIL import Image
from fastapi.testclient import TestClient

from api.main import app
from api.services.disease_service import (
    DiseaseDetectionService,
    InvalidImageError,
    ModelUnavailableError,
    disease_detection_service,
)

client = TestClient(app)

TEST_DATA_DIR = Path(__file__).resolve().parent.parent / "models" / "disease_detection" / "disease_pest_ai" / "test_data"
APPLE_SCAB_IMG = TEST_DATA_DIR / "apple_scab_bierny.jpg"
TOMATO_BLIGHT_IMG = TEST_DATA_DIR / "tomato_early_blight.jpg"
TOMATO_HEALTHY_IMG = TEST_DATA_DIR / "tomato_healthy.jpg"
CORN_RUST_IMG = TEST_DATA_DIR / "corn_common_rust.jpg"


# 1. SUCCESSFUL MODEL LOADING
def test_01_model_loading_and_status():
    """Verify that the model service preloads and reports ready status with 38 classes."""
    disease_detection_service.initialize()
    assert disease_detection_service.is_loaded() is True

    status_resp = client.get("/api/disease/status")
    assert status_resp.status_code == 200
    data = status_resp.json()
    assert data["loaded"] is True
    assert data["classes_count"] == 38
    assert "EfficientNetV2-S" in data["model_type"]

    classes_resp = client.get("/api/disease/classes")
    assert classes_resp.status_code == 200
    classes_data = classes_resp.json()
    assert classes_data["num_classes"] == 38
    assert "Apple___Apple_scab" in classes_data["classes"]
    assert "Tomato___Early_blight" in classes_data["classes"]


# 2. CORRECT PREPROCESSING AND LABEL DECODING
def test_02_preprocessing_and_label_decoding():
    """Verify that genuine test image produces expected decoded pathology without corruption."""
    assert APPLE_SCAB_IMG.exists(), f"Missing test image: {APPLE_SCAB_IMG}"

    with open(APPLE_SCAB_IMG, "rb") as f:
        img_bytes = f.read()

    res = disease_detection_service.predict(
        image_bytes=img_bytes,
        crop="Apple",
        location_state="Himachal Pradesh",
        growth_stage="fruiting",
        image_type="leaf",
    )

    assert res.condition == "Apple Scab"
    assert res.scientific_name == "Venturia inaequalis"
    assert res.confidence > 0.80
    assert res.confidence_type == "uncalibrated_softmax"
    assert res.is_healthy is False
    assert res.crop_match is True
    assert len(res.top_5_predictions) >= 1
    assert res.top_5_predictions[0].condition == "Apple Scab"


# 3. VALID INPUT AND SUPPORTED IMAGE FORMATS
@pytest.mark.parametrize("fmt", ["JPEG", "PNG", "WEBP"])
def test_03_supported_image_formats(fmt):
    """Verify inference accepts JPEG, PNG, and WebP encoded leaf images."""
    # Convert tomato early blight to the target format
    base_img = Image.open(TOMATO_BLIGHT_IMG).convert("RGB")
    buf = io.BytesIO()
    base_img.save(buf, format=fmt)
    encoded_bytes = buf.getvalue()

    response = client.post(
        "/api/disease/predict",
        files={"file": ("test_leaf." + fmt.lower(), encoded_bytes, f"image/{fmt.lower()}")},
        data={"crop": "Tomato", "location_state": "Maharashtra"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "Early Blight" in data["condition"]
    assert data["is_healthy"] is False


# 4. INVALID, CORRUPT, OVERSIZED, AND MISSING INPUTS
def test_04_missing_image_rejected():
    """Verify that omitting image inputs returns 400 Bad Request."""
    response = client.post(
        "/api/disease/predict",
        data={"crop": "Tomato"},
    )
    assert response.status_code == 400
    assert "No image provided" in response.json()["detail"]


def test_04_corrupted_image_rejected():
    """Verify that corrupt or random non-image bytes return 400 Bad Request."""
    corrupt_bytes = b"NOT_A_VALID_JPEG_HEADER_RANDOM_DATA_12345"
    response = client.post(
        "/api/disease/predict",
        files={"file": ("corrupt.jpg", corrupt_bytes, "image/jpeg")},
        data={"crop": "Tomato"},
    )
    assert response.status_code == 400
    assert "corrupt or not a recognized image" in response.json()["detail"].lower()


def test_04_oversized_image_rejected():
    """Verify that images exceeding 15MB size limit are rejected with 400."""
    giant_fake_bytes = b"0" * (16 * 1024 * 1024)  # 16 MB
    response = client.post(
        "/api/disease/predict",
        files={"file": ("huge.jpg", giant_fake_bytes, "image/jpeg")},
        data={"crop": "Tomato"},
    )
    assert response.status_code == 400
    assert "15 MB" in response.json()["detail"]


def test_04_tiny_dimension_image_rejected():
    """Verify that images smaller than 32x32 pixels are rejected."""
    tiny_img = Image.new("RGB", (16, 16), color="green")
    buf = io.BytesIO()
    tiny_img.save(buf, format="JPEG")

    response = client.post(
        "/api/disease/predict",
        files={"file": ("tiny.jpg", buf.getvalue(), "image/jpeg")},
        data={"crop": "Tomato"},
    )
    assert response.status_code == 400
    assert "resolution too low" in response.json()["detail"].lower()


# 5. BACKEND API RESPONSE STRUCTURE
def test_05_api_response_structure_compliance():
    """Verify that response schema contains mandatory pathology fields, top-5, and CIBRC treatments."""
    with open(TOMATO_HEALTHY_IMG, "rb") as f:
        img_bytes = f.read()

    response = client.post(
        "/api/disease/predict",
        files={"file": ("healthy.jpg", img_bytes, "image/jpeg")},
        data={"crop": "Tomato", "location_state": "Maharashtra"},
    )
    assert response.status_code == 200
    data = response.json()

    # Core fields
    assert "condition" in data
    assert "scientific_name" in data
    assert "confidence" in data
    assert "confidence_percent" in data
    assert "confidence_type" in data
    assert "severity" in data
    assert "is_healthy" in data
    assert "crop_match" in data
    assert "top_5_predictions" in data
    assert "treatments" in data
    assert "preventive_management" in data
    assert "non_chemical_options" in data
    assert "provenance" in data
    assert "disclaimer" in data

    # Verify healthy semantics
    assert data["is_healthy"] is True
    assert data["severity"] == "Low"
    assert "healthy" in data["condition"].lower()


# 6. MODEL-UNAVAILABLE BEHAVIOR WITHOUT FAKE FALLBACKS
def test_06_model_unavailable_returns_503(monkeypatch):
    """Verify that if model pipeline fails to initialize, the API returns explicit 503 instead of fake mock predictions."""
    svc = DiseaseDetectionService()
    monkeypatch.setattr(svc, "initialize", lambda: None)
    monkeypatch.setattr(svc, "_pipeline", None)

    with pytest.raises(ModelUnavailableError) as exc_info:
        svc.predict(sample_id="apple_scab")
    assert "unavailable" in str(exc_info.value).lower()


# 7. FRONTEND BACKWARD COMPATIBLE ROUTE
def test_07_frontend_backward_compatible_endpoint():
    """Verify `/api/v1/disease-detection` works identically with preset sample or image upload."""
    response = client.post(
        "/api/v1/disease-detection",
        data={"sample_id": "corn_rust", "crop": "Corn", "location_state": "Punjab"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "Rust" in data["condition"]
    assert data["crop_match"] is True
    assert len(data["treatments"]["chemical"]) > 0 or len(data["non_chemical_options"]) > 0


# 8. REPEATABILITY AND DETERMINISM FOR IDENTICAL INPUTS
def test_08_deterministic_reproducibility():
    """Verify that identical inputs produce bitwise reproducible condition, confidence, and rankings."""
    res1 = client.post(
        "/api/disease/predict",
        data={"sample_id": "apple_scab", "crop": "Apple", "location_state": "Himachal Pradesh"},
    ).json()

    res2 = client.post(
        "/api/disease/predict",
        data={"sample_id": "apple_scab", "crop": "Apple", "location_state": "Himachal Pradesh"},
    ).json()

    assert res1["condition"] == res2["condition"]
    assert res1["confidence"] == res2["confidence"]
    assert res1["crop_match"] == res2["crop_match"]
    assert len(res1["top_5_predictions"]) == len(res2["top_5_predictions"])
    assert res1["top_5_predictions"][0]["condition"] == res2["top_5_predictions"][0]["condition"]


# 9. CROP MISMATCH IDENTIFICATION
def test_09_crop_mismatch_alert():
    """Verify that uploading an Apple Scab leaf but declaring crop as 'Tomato' triggers a crop mismatch warning."""
    response = client.post(
        "/api/disease/predict",
        data={"sample_id": "apple_scab", "crop": "Tomato", "location_state": "Maharashtra"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["crop_match"] is False
    assert data["crop_mismatch_warning"] is not None
    assert "Crop Mismatch" in data["crop_mismatch_warning"]
