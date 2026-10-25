"""Comprehensive Validation Test Suite for Focused Two-Model Crop Disease Intelligence System.

Tests all requirements:
1. Only two specialists exist in registry: Cotton (DenseNet-121) and Soybean (ConvNeXt-Small).
2. Routing strictly directs Cotton to DenseNet and Soybean to ConvNeXt.
3. Unsupported crops (Tomato, Potato, Corn, Wheat, Rice, Apple, etc.) are strictly rejected/abstained.
4. Backend API rejects unsupported crops with HTTP 422.
5. Invalid/corrupted and empty images are properly handled (HTTP 400/422).
6. Missing photo upload is rejected with HTTP 400.
7. Simplified farmer guidance payload contract verification.
8. Zero-Chemical Safeguard enforcement under all uncertainty states and healthy crops.
9. Contract verification for /api/v1/diagnose, /api/v1/specialists, and /api/v1/disease-detection.
"""

import io
import pytest
from PIL import Image
from fastapi.testclient import TestClient

from disease_pest_ai.api.main import app
from disease_pest_ai.inference.pipeline import DiseasePestPipeline
from disease_pest_ai.specialists.registry import specialist_registry
from disease_pest_ai.specialists.router import intelligent_router


@pytest.fixture(scope="module")
def pipeline():
    return DiseasePestPipeline(primary_disease_model="specialist", lazy_load=False)


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def create_test_image(color=(34, 139, 34), size=(224, 224)):
    """Helper to generate a clean synthetic leaf image."""
    img = Image.new("RGB", size, color=color)
    return img


# 1. SPECIALIST REGISTRY AND AVAILABILITY TESTS
def test_specialist_registry_status():
    status = specialist_registry.get_registry_status()
    # Strictly 2 models configured and active
    assert status["total_configured"] == 2
    assert status["total_active_loaded"] == 2

    # Active specialists must be loaded
    assert status["specialists"]["soybean"]["is_loaded"] is True
    assert status["specialists"]["cotton"]["is_loaded"] is True

    # Other models must NOT exist in the registry
    assert "tomato" not in status["specialists"]
    assert "potato" not in status["specialists"]
    assert "corn" not in status["specialists"]
    assert "generalist" not in status["specialists"]
    assert "yolo_multicrop" not in status["specialists"]


def test_supported_crops_coverage():
    crops = specialist_registry.get_supported_crops()
    assert set(crops) == {"Cotton", "Soybean"}
    assert "Tomato" not in crops
    assert "Potato" not in crops
    assert "Corn" not in crops
    assert "Wheat" not in crops
    assert "Rice" not in crops


# 2. CROP-AWARE ROUTING TESTS
def test_routing_to_cotton_specialist(pipeline):
    img = create_test_image()
    res = intelligent_router.route(image=img, declared_crop="Cotton")
    assert res.crop == "Cotton"
    assert "FarmGuard/cotton-densenet121" in res.model_identifier
    assert res.routing_path == "cotton_specialist"
    assert len(res.competing_predictions) == 1


def test_routing_to_soybean_specialist(pipeline):
    img = create_test_image()
    res = intelligent_router.route(image=img, declared_crop="Soybean")
    assert res.crop == "Soybean"
    assert "ixrbhii/soybean-disease-convnext" in res.model_identifier
    assert res.routing_path == "soybean_specialist"
    assert len(res.competing_predictions) == 1


# 3. REJECTION OF UNSUPPORTED CROPS
def test_unsupported_crops_router_rejection(pipeline):
    img = create_test_image()
    unsupported = ["Tomato", "Potato", "Corn", "Grape", "Apple", "Rice", "Wheat", "Dragonfruit"]
    for c in unsupported:
        res = intelligent_router.route(image=img, declared_crop=c)
        assert res.abstention is True
        assert res.abstention_reason == "unsupported_crop"
        assert res.fusion_outcome == "unsupported_crop"
        assert res.model_identifier == "None"
        assert "Unsupported" in res.condition


# 4. ZERO-CHEMICAL SAFEGUARD UNDER UNCERTAINTY
def test_zero_chemical_safeguard_on_unsupported_crop(pipeline):
    img = create_test_image()
    result = pipeline.predict(
        plant_image=img,
        crop_name="Dragonfruit",
        location_state="Maharashtra",
        growth_stage="vegetative",
        image_type="leaf",
    )
    assert result.disease.status in ("unsupported_crop", "insufficient_evidence", "crop_mismatch")
    # Strictly zero chemical candidates
    assert len(result.treatment.disease_recommendations.chemical_candidates) == 0
    assert result.treatment.disease_recommendations.status.value in ("manual_review_required", "restricted_or_blocked")


def test_zero_chemical_safeguard_on_healthy_cotton(pipeline):
    img = create_test_image()
    result = pipeline.predict(
        plant_image=img,
        crop_name="Cotton",
        location_state="Maharashtra",
        growth_stage="vegetative",
        image_type="leaf",
    )
    if result.disease.condition_type.value == "healthy":
        assert len(result.treatment.disease_recommendations.chemical_candidates) == 0


# 5. API ENDPOINTS INTEGRATION & VALIDATION
def test_api_specialists_endpoint(client):
    resp = client.get("/api/v1/specialists")
    assert resp.status_code == 200
    data = resp.json()
    assert "specialists" in data
    assert len(data["specialists"]) == 2
    assert data["specialists"]["soybean"]["is_loaded"] is True
    assert data["specialists"]["cotton"]["is_loaded"] is True
    assert set(data["supported_crops"]) == {"Cotton", "Soybean"}


def test_api_diagnose_cotton_success(client):
    img = create_test_image()
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    resp = client.post(
        "/api/v1/diagnose",
        files={"file": ("cotton_leaf.jpg", buf, "image/jpeg")},
        data={
            "crop_name": "Cotton",
            "location_state": "Maharashtra",
            "growth_stage": "vegetative",
            "image_type": "leaf",
            "generate_visual_explanation": "false",
        },
        headers={"X-API-Key": "kc_disease_pest_sec_key_2026_prod"},
    )
    assert resp.status_code == 200
    res_data = resp.json()
    assert "disease" in res_data
    assert "treatment" in res_data
    assert "provenance" in res_data


def test_api_diagnose_soybean_success(client):
    img = create_test_image()
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    resp = client.post(
        "/api/v1/diagnose",
        files={"file": ("soybean_leaf.jpg", buf, "image/jpeg")},
        data={
            "crop_name": "Soybean",
            "location_state": "Maharashtra",
            "growth_stage": "vegetative",
            "image_type": "leaf",
            "generate_visual_explanation": "false",
        },
        headers={"X-API-Key": "kc_disease_pest_sec_key_2026_prod"},
    )
    assert resp.status_code == 200
    res_data = resp.json()
    assert "disease" in res_data
    assert "treatment" in res_data


def test_api_diagnose_unsupported_crop_rejected(client):
    """API must reject non-Cotton/Soybean crops with HTTP 422."""
    img = create_test_image()
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    resp = client.post(
        "/api/v1/diagnose",
        files={"file": ("leaf.jpg", buf, "image/jpeg")},
        data={
            "crop_name": "Tomato",
            "location_state": "Maharashtra",
            "growth_stage": "vegetative",
            "image_type": "leaf",
        },
        headers={"X-API-Key": "kc_disease_pest_sec_key_2026_prod"},
    )
    assert resp.status_code == 422
    assert "not supported" in resp.json()["detail"].lower()


def test_api_frontend_compatible_endpoint_cotton(client):
    img = create_test_image()
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    resp = client.post(
        "/api/v1/disease-detection",
        files={"file": ("leaf.jpg", buf, "image/jpeg")},
        data={
            "crop": "Cotton",
            "location_state": "Maharashtra",
            "growth_stage": "vegetative",
            "image_type": "leaf",
        },
    )
    assert resp.status_code == 200
    res_data = resp.json()
    assert res_data["status"] == "success"
    assert "data" in res_data
    assert "condition" in res_data["data"]
    assert "treatments" in res_data["data"]
    assert "farmer_guidance" in res_data["data"]
    guidance = res_data["data"]["farmer_guidance"]
    assert guidance["crop"] == "Cotton"
    assert guidance["status"] in ("healthy", "disease_detected", "unable_to_determine")
    assert len(guidance["recommended_steps"]) > 0


def test_api_frontend_compatible_endpoint_soybean(client):
    img = create_test_image()
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    resp = client.post(
        "/api/v1/disease-detection",
        files={"file": ("soy_leaf.jpg", buf, "image/jpeg")},
        data={
            "crop": "Soybean",
            "location_state": "Maharashtra",
            "growth_stage": "vegetative",
            "image_type": "leaf",
        },
    )
    assert resp.status_code == 200
    res_data = resp.json()
    assert res_data["status"] == "success"
    guidance = res_data["data"]["farmer_guidance"]
    assert guidance["crop"] == "Soybean"
    assert guidance["status"] in ("healthy", "disease_detected", "unable_to_determine")
    assert len(guidance["recommended_steps"]) > 0


def test_api_frontend_compatible_unsupported_crop_rejected(client):
    img = create_test_image()
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    resp = client.post(
        "/api/v1/disease-detection",
        files={"file": ("leaf.jpg", buf, "image/jpeg")},
        data={
            "crop": "Apple",
            "location_state": "Maharashtra",
            "growth_stage": "vegetative",
            "image_type": "leaf",
        },
    )
    assert resp.status_code == 422
    assert "not supported" in resp.json()["detail"].lower()


def test_api_missing_file_rejected(client):
    resp = client.post(
        "/api/v1/disease-detection",
        data={"crop": "Cotton"},
    )
    assert resp.status_code == 400
    assert "required" in resp.json()["detail"].lower() or "photo" in resp.json()["detail"].lower()


def test_api_empty_file_rejected(client):
    resp = client.post(
        "/api/v1/disease-detection",
        files={"file": ("empty.jpg", b"", "image/jpeg")},
        data={"crop": "Cotton"},
    )
    assert resp.status_code == 400
    assert "empty" in resp.json()["detail"].lower()


def test_api_corrupt_file_rejected(client):
    resp = client.post(
        "/api/v1/disease-detection",
        files={"file": ("corrupt.jpg", b"not-a-valid-image-bytes-data", "image/jpeg")},
        data={"crop": "Cotton"},
    )
    assert resp.status_code == 422
    assert "invalid" in resp.json()["detail"].lower() or "corrupt" in resp.json()["detail"].lower()
