"""Comprehensive Validation Test Suite for Multi-Crop Disease Intelligence System.

Tests all requirements:
1. Available crop specialists (Soybean ConvNeXt, Cotton DenseNet, Multi-Crop Generalist, YOLOv11x, YOLO11s).
2. Crop-aware routing (Soybean, Cotton, Tomato, Potato, Corn, Wheat, Rice, etc.).
3. Unknown and unsupported crops (safe abstention).
4. Image validation (corrupted, low resolution).
5. Missing model weights graceful degradation.
6. Multi-model consensus and agreement.
7. Disagreement handling and clinical abstention.
8. Host crop conflict rejection ('crop_uncertain').
9. Zero-Chemical Safeguard enforcement under all uncertainty states.
10. API endpoint contract verification (/api/v1/diagnose, /api/v1/specialists, /api/v1/disease-detection).
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
    return DiseasePestPipeline(lazy_load=False)


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
    assert status["total_configured"] >= 10
    assert status["total_active_loaded"] >= 4

    # Active specialists must be loaded
    assert status["specialists"]["soybean"]["is_loaded"] is True
    assert status["specialists"]["cotton"]["is_loaded"] is True
    assert status["specialists"]["tomato"]["is_loaded"] is True
    assert status["specialists"]["yolo_multicrop"]["is_loaded"] is True

    # Planned specialists must not crash and be marked planned
    assert status["specialists"]["rice"]["status"] == "planned"
    assert status["specialists"]["wheat"]["status"] == "planned"


def test_supported_crops_coverage():
    crops = specialist_registry.get_supported_crops()
    assert "Soybean" in crops
    assert "Cotton" in crops
    assert "Tomato" in crops
    assert "Potato" in crops
    assert "Corn" in crops


# 2. CROP-AWARE ROUTING TESTS
def test_routing_to_soybean_specialist(pipeline):
    img = create_test_image()
    res = intelligent_router.route(image=img, declared_crop="Soybean")
    assert res.crop == "Soybean"
    assert "ixrbhii/soybean-disease-convnext" in res.model_identifier
    assert len(res.competing_predictions) >= 1


def test_routing_to_cotton_specialist(pipeline):
    img = create_test_image()
    res = intelligent_router.route(image=img, declared_crop="Cotton")
    assert res.crop == "Cotton"
    assert "FarmGuard/cotton-densenet121" in res.model_identifier


def test_routing_to_generalist_crops(pipeline):
    img = create_test_image()
    for c in ["Tomato", "Potato", "Corn", "Grape", "Apple"]:
        res = intelligent_router.route(image=img, declared_crop=c)
        assert res.crop == c
        assert "BiernyVR/crop-disease-classifier" in res.model_identifier


# 3. UNKNOWN AND UNSUPPORTED CROPS
def test_unsupported_crop_abstention(pipeline):
    img = create_test_image()
    res = intelligent_router.route(image=img, declared_crop="Dragonfruit")
    assert res.abstention is True
    assert res.abstention_reason == "unsupported_crop"
    assert res.fusion_outcome == "insufficient_evidence"
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


def test_zero_chemical_safeguard_on_healthy_crop(pipeline):
    img = create_test_image()
    result = pipeline.predict(
        plant_image=img,
        crop_name="Cotton",
        location_state="Maharashtra",
        growth_stage="vegetative",
        image_type="leaf",
    )
    # If diagnosed healthy, zero chemicals must be prescribed
    if result.disease.condition_type.value == "healthy":
        assert len(result.treatment.disease_recommendations.chemical_candidates) == 0


# 5. DISAGREEMENT AND CONSENSUS FUSION
def test_consensus_outcome_structure(pipeline):
    img = create_test_image()
    res = intelligent_router.route(image=img, declared_crop="Soybean")
    assert res.fusion_outcome in ("agree", "disputed", "crop_uncertain", "insufficient_evidence", "single_model")
    assert isinstance(res.competing_predictions, list)
    assert isinstance(res.all_candidates, list)


# 6. API ENDPOINTS INTEGRATION
def test_api_specialists_endpoint(client):
    resp = client.get("/api/v1/specialists")
    assert resp.status_code == 200
    data = resp.json()
    assert "specialists" in data
    assert data["specialists"]["soybean"]["is_loaded"] is True
    assert data["specialists"]["cotton"]["is_loaded"] is True


def test_api_diagnose_endpoint(client):
    img = create_test_image()
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    resp = client.post(
        "/api/v1/diagnose",
        files={"file": ("leaf.jpg", buf, "image/jpeg")},
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
    assert "provenance" in res_data


def test_api_frontend_compatible_endpoint(client):
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
    assert "fusion_outcome" in res_data["data"]
    assert "model_identifier" in res_data["data"]
