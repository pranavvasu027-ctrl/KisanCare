"""Automated verification suite for KisanCare Plant Pathology & Disease Detection API.

Covers:
1. Successful multi-crop model loading and status (59 crops, 387 classes, ViT-B/14).
2. Correct preprocessing and label decoding.
3. Valid input and supported image formats (JPEG, PNG, WebP).
4. Invalid, corrupt, oversized, and tiny dimension inputs rejection (400 Bad Request).
5. Backend API response structure compliance (typed schema, top-5, CIBRC treatments).
6. Model-unavailable behavior without fake fallbacks (ModelUnavailableError).
7. Frontend backward compatible route `/api/v1/disease-detection`.
8. Repeatability and determinism for identical inputs.
9. Crop mismatch identification and warning generation.
10. Multi-crop Indian field coverage (Cotton, Potato, Tomato, Corn, Apple).
11. Safe out-of-distribution (OOD) / low-confidence abstention (< 40%).
12. Instant zero-risk rollback engine switching (india_multicrop <-> efficientnet).
13. Diagnostic safety: zero heuristic severity and no fake chemical fallbacks.
14. Metadata consistency: no contradictory taxonomy or fabricated crop disorders.
15. Candidate task and category separation (Disease vs Pest vs Healthy vs Deficiency).
16. Configurable abstention threshold validation.
17. Honest rejection messaging without false 'non-leaf image' claims.
18. Conflicting host-crop and disease prediction reporting.
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

TEST_DATA_DIR = Path(__file__).resolve().parent.parent / "models" / "disease_detection" / "test_data"
APPLE_SCAB_IMG = TEST_DATA_DIR / "apple_scab_bierny.jpg"
TOMATO_BLIGHT_IMG = TEST_DATA_DIR / "tomato_early_blight.jpg"
TOMATO_HEALTHY_IMG = TEST_DATA_DIR / "tomato_healthy.jpg"
CORN_RUST_IMG = TEST_DATA_DIR / "corn_common_rust.jpg"
POTATO_BLIGHT_IMG = Path(__file__).resolve().parent.parent / "frontend" / "public" / "test_images" / "potato_early_blight.jpg"


# 1. SUCCESSFUL MODEL LOADING
def test_01_model_loading_and_status():
    """Verify that the model service preloads and reports ready status with 387 classes and 59 crops."""
    status_resp = client.get("/api/disease/status")
    assert status_resp.status_code == 200
    data = status_resp.json()
    assert data["status"] == "ready"
    assert data["classes_count"] == 387
    assert data["crops_count"] == 59
    assert data["active_engine"] == "india_multicrop"
    assert data["primary_engine_available"] is True
    assert data["rollback_engine_available"] is True

    classes_resp = client.get("/api/disease/classes")
    assert classes_resp.status_code == 200
    classes_data = classes_resp.json()
    assert classes_data["num_classes"] == 387
    assert classes_data["crops_count"] == 59
    assert "Cotton" in classes_data["supported_crops"]
    assert "Rice" in classes_data["supported_crops"]
    assert "Wheat" in classes_data["supported_crops"]


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

    assert "scab" in res.condition.lower()
    assert res.scientific_name == "Venturia inaequalis"
    assert res.confidence > 0.80
    assert res.confidence_type == "uncalibrated_softmax"
    assert res.is_healthy is False
    assert res.severity == "Severity not assessed"
    assert res.crop_match is True
    assert len(res.top_5_predictions) >= 1
    assert "scab" in res.top_5_predictions[0].condition.lower()


# 3. VALID INPUT AND SUPPORTED IMAGE FORMATS
@pytest.mark.parametrize("fmt", ["JPEG", "PNG", "WEBP"])
def test_03_supported_image_formats(fmt):
    """Verify inference accepts JPEG, PNG, and WebP encoded leaf images."""
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
    assert "blight" in data["condition"].lower()
    assert data["is_healthy"] is False


# 4. INVALID, CORRUPT, OVERSIZED, AND MISSING INPUTS
def test_04_missing_image_rejected():
    """Verify that omitting image inputs returns 400 Bad Request."""
    response = client.post(
        "/api/disease/predict",
        data={"crop": "Tomato"},
    )
    assert response.status_code == 400
    assert "no image provided" in response.json()["detail"].lower()


def test_04_corrupted_image_rejected():
    """Verify that corrupt or random non-image bytes return 400 Bad Request."""
    corrupt_bytes = b"NOT_A_VALID_JPEG_HEADER_RANDOM_DATA_12345"
    response = client.post(
        "/api/disease/predict",
        files={"file": ("corrupt.jpg", corrupt_bytes, "image/jpeg")},
        data={"crop": "Tomato"},
    )
    assert response.status_code == 400
    detail = response.json()["detail"].lower()
    assert "decode" in detail or "corrupt" in detail or "failed" in detail


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
    assert "abstention" in data
    assert "diagnosed_crop" in data
    assert "crop_match" in data
    assert "top_5_predictions" in data
    assert "treatments" in data
    assert "preventive_management" in data
    assert "non_chemical_options" in data
    assert "provenance" in data
    assert "disclaimer" in data

    # Verify healthy semantics & safety
    assert data["is_healthy"] is True
    assert "Healthy" in data["severity"]
    assert "healthy" in data["condition"].lower()
    assert len(data["treatments"]["chemical"]) == 0


# 6. MODEL-UNAVAILABLE BEHAVIOR WITHOUT FAKE FALLBACKS
def test_06_model_unavailable_returns_error():
    """Verify that if both primary and rollback engines are unavailable, an explicit ModelUnavailableError is raised."""
    svc = DiseaseDetectionService()
    svc._primary_engine = None
    svc._rollback_engine = None

    with pytest.raises(ModelUnavailableError) as exc_info:
        svc.predict(sample_id="apple_scab")
    assert "no active disease detection engine is loaded" in str(exc_info.value).lower()


# 7. FRONTEND BACKWARD COMPATIBLE ROUTE
def test_07_frontend_backward_compatible_endpoint():
    """Verify `/api/v1/disease-detection` works identically with preset sample."""
    response = client.post(
        "/api/v1/disease-detection",
        data={"sample_id": "corn_rust", "crop": "Corn", "location_state": "Punjab"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "rust" in data["condition"].lower()
    assert data["crop_match"] is True
    assert len(data["non_chemical_options"]) > 0


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
    assert "Discrepancy" in data["crop_mismatch_warning"] or "Mismatch" in data["crop_mismatch_warning"]
    assert "Apple" in data["diagnosed_crop"]


# 10. MULTI-CROP INDIAN FIELD COVERAGE (POTATO)
def test_10_indian_crop_field_coverage():
    """Verify broad-coverage prediction on Potato Early Blight."""
    response = client.post(
        "/api/disease/predict",
        data={"sample_id": "potato_blight", "crop": "Potato", "location_state": "Uttar Pradesh"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "blight" in data["condition"].lower()
    assert data["diagnosed_crop"] == "Potato"
    assert data["confidence_percent"] >= 70
    assert data["abstention"] is False


# 11. OUT-OF-DISTRIBUTION ABSTENTION (< 40%)
def test_11_out_of_distribution_abstention():
    """Verify that ambiguous/synthetic non-leaf noise triggers diagnostic abstention."""
    gray_img = Image.new("RGB", (128, 128), color=(128, 128, 128))
    buf = io.BytesIO()
    gray_img.save(buf, format="JPEG")

    response = client.post(
        "/api/disease/predict",
        files={"file": ("noise.jpg", buf.getvalue(), "image/jpeg")},
        data={"crop": "Cotton", "location_state": "Maharashtra"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["abstention"] is True
    assert data["condition"] == "Inconclusive foliar diagnosis"
    assert data["condition_type"] == "inconclusive"
    assert data["confidence"] < 0.40
    assert "abstention" in data["treatment"].lower()
    assert "Severity not assessed" in data["severity"]
    assert data["scientific_name"] is None
    assert data["host_crop_status"] == "unverified"


# 12. INSTANT ZERO-RISK ROLLBACK SWITCHING
def test_12_instant_zero_risk_rollback():
    """Verify switching between 'india_multicrop' and 'efficientnet' engines."""
    # 1. Switch to rollback engine
    switch_resp = client.post("/api/disease/engine", json={"engine": "efficientnet"})
    assert switch_resp.status_code == 200
    assert switch_resp.json()["active_engine"] == "efficientnet"

    status_resp = client.get("/api/disease/engine")
    assert status_resp.json()["active_engine"] == "efficientnet"

    # 2. Run prediction under rollback engine
    rb_pred = client.post(
        "/api/disease/predict",
        data={"sample_id": "tomato_blight", "crop": "Tomato"},
    ).json()
    assert "blight" in rb_pred["condition"].lower()
    assert "EfficientNetV2-S" in rb_pred["model_type"]

    # 3. Switch back to primary multi-crop engine
    restore_resp = client.post("/api/disease/engine", json={"engine": "india_multicrop"})
    assert restore_resp.status_code == 200
    assert restore_resp.json()["active_engine"] == "india_multicrop"

    mc_pred = client.post(
        "/api/disease/predict",
        data={"sample_id": "tomato_blight", "crop": "Tomato"},
    ).json()
    assert "blight" in mc_pred["condition"].lower()
    assert "India Multi-Crop DINOv2" in mc_pred["model_type"]


# 13. DIAGNOSTIC SAFETY: ZERO HEURISTIC SEVERITY & NO FAKE CHEMICAL FALLBACKS
def test_13_diagnostic_safety_invariants():
    """Verify that severity is not inferred from confidence and no synthetic chemical fallbacks exist."""
    res = client.post(
        "/api/disease/predict",
        data={"sample_id": "tomato_blight", "crop": "Tomato"},
    ).json()

    # Severity invariant
    assert res["severity"] == "Severity not assessed"

    # Chemical safety invariant: If chemicals exist, they must have real active ingredients and registrations
    for chem in res["treatments"]["chemical"]:
        assert chem["chemical_name"]
        assert "CIBRC-FUNG-STD" not in chem.get("cpr_registration", "")
        assert "CIBRC-TRIAZOLE-STD" not in chem.get("cpr_registration", "")
        assert "CIBRC-SULPHUR-STD" not in chem.get("cpr_registration", "")


# 14. METADATA CONSISTENCY: NO CONTRADICTORY TAXONOMY OR FABRICATED CROP DISORDERS
def test_14_metadata_consistency_and_no_contradictory_taxonomy():
    """Verify that low-confidence/abstention never fabricates a Latin taxonomy from the declared crop."""
    gray_img = Image.new("RGB", (100, 100), color=(100, 120, 110))
    buf = io.BytesIO()
    gray_img.save(buf, format="JPEG")

    res = client.post(
        "/api/disease/predict",
        files={"file": ("ambiguous.jpg", buf.getvalue(), "image/jpeg")},
        data={"crop": "Cotton", "location_state": "Maharashtra"},
    ).json()

    assert res["abstention"] is True
    # Invariant: Must NOT fabricate 'Cotton foliar pathological disorder'
    assert res["scientific_name"] is None
    # Invariant: Host crop must NOT be attributed to a random class prefix like 'Soybean' when abstaining
    assert res["host_crop_status"] == "unverified"
    assert res["diagnosed_crop"] is None


# 15. CANDIDATE TASK AND CATEGORY SEPARATION
def test_15_candidate_task_and_category_separation():
    """Verify that candidates are properly tagged with category, task, and source_model."""
    res = client.post(
        "/api/disease/predict",
        data={"sample_id": "potato_blight", "crop": "Potato"},
    ).json()

    assert len(res["top_5_predictions"]) > 0
    for cand in res["top_5_predictions"]:
        assert cand["category"] in ["disease", "pest", "healthy", "deficiency"]
        assert cand["task"] == "foliar_classification"
        assert cand["source_model"]
        assert cand["crop"] is not None

    # Top disease candidates must strictly be diseases
    for d_cand in res["top_disease_candidates"]:
        assert d_cand["category"] == "disease"

    # Top pest candidates must strictly be pests
    for p_cand in res["top_pest_candidates"]:
        assert p_cand["category"] == "pest"


# 16. CONFIGURABLE ABSTENTION THRESHOLD
def test_16_configurable_abstention_threshold():
    """Verify that custom abstention thresholds are respected per-request and globally."""
    # With sample image that has ~75% confidence on Potato Early Blight:
    # 1. Normal threshold 0.40 -> Not abstained
    normal_res = client.post(
        "/api/disease/predict",
        data={"sample_id": "potato_blight", "crop": "Potato", "abstention_threshold": 0.40},
    ).json()
    assert normal_res["abstention"] is False

    # 2. Strict threshold 0.95 -> Should abstain!
    strict_res = client.post(
        "/api/disease/predict",
        data={"sample_id": "potato_blight", "crop": "Potato", "abstention_threshold": 0.95},
    ).json()
    assert strict_res["abstention"] is True
    assert strict_res["abstention_reason"] == "low_confidence"
    assert strict_res["abstention_threshold"] == 0.95


# 17. HONEST REJECTION MESSAGING WITHOUT FALSE NON-LEAF CLAIMS
def test_17_honest_rejection_no_false_non_leaf_claims():
    """Verify that low confidence responses do not claim the image is non-leaf when it's just low model confidence."""
    gray_img = Image.new("RGB", (100, 100), color=(110, 110, 110))
    buf = io.BytesIO()
    gray_img.save(buf, format="JPEG")

    res = client.post(
        "/api/disease/predict",
        files={"file": ("leaf_photo.jpg", buf.getvalue(), "image/jpeg")},
        data={"crop": "Cotton"},
    ).json()

    assert res["abstention"] is True
    assert res["condition"] == "Inconclusive foliar diagnosis"
    # Description should discuss confidence / ambiguity, not falsely assert 'non-leaf image'
    assert "Inconclusive" in res["condition"]
    assert "non-leaf image" not in res["condition"].lower()


# 18. CONFLICTING HOST-CROP AND DISEASE PREDICTION REPORTING
def test_18_disputed_crop_reporting_when_confident():
    """Verify that when the model is confident in an Apple disease but crop is declared 'Tomato', crop is disputed."""
    res = client.post(
        "/api/disease/predict",
        data={"sample_id": "apple_scab", "crop": "Tomato"},
    ).json()

    assert res["abstention"] is False
    assert res["crop_match"] is False
    assert res["host_crop_status"] == "disputed"
    assert res["diagnosed_crop"] == "Apple"
    # Scientific name must reflect the diagnosed condition (Apple Scab -> Venturia inaequalis), NOT Tomato!
    assert res["scientific_name"] == "Venturia inaequalis"
    assert "Discrepancy" in res["crop_mismatch_warning"]


# 19. SPECIALIST REGISTRY ENDPOINT AUDIT
def test_19_specialist_registry_endpoint():
    """Verify that `/api/disease/specialists` exposes registry metadata, active models, and planned adapters."""
    resp = client.get("/api/disease/specialists")
    assert resp.status_code == 200
    data = resp.json()
    assert data["active_specialists_count"] >= 1
    assert "Cotton" in data["active_crops"]
    assert "cotton" in data["specialists"]
    cotton_spec = data["specialists"]["cotton"]
    assert cotton_spec["is_available"] is True
    assert cotton_spec["architecture"] == "DenseNet-121 (torchvision)"
    assert cotton_spec["license"] == "MIT"
    assert "Bacterial Blight" in cotton_spec["supported_classes"]


# 20. COTTON SPECIALIST ROUTING AND FUSION
def test_20_cotton_specialist_routing_and_fusion():
    """Verify that declaring crop='Cotton' with a cotton leaf image routes to the specialist and fuses predictions."""
    cotton_img_path = Path(__file__).resolve().parent.parent / "frontend" / "public" / "test_images" / "cotton_leaf_spot.jpg"
    assert cotton_img_path.is_file(), f"Missing test image: {cotton_img_path}"

    with open(cotton_img_path, "rb") as f:
        img_bytes = f.read()

    res = client.post(
        "/api/disease/predict",
        files={"file": ("cotton.jpg", img_bytes, "image/jpeg")},
        data={"crop": "Cotton", "location_state": "Gujarat"},
    ).json()

    assert res["abstention"] is False
    assert res["routing_path"] == "specialist_fused"
    assert "FarmGuard/cotton-densenet121" in res["model_identifier"]
    assert "Bacterial Blight" in res["condition"]
    assert res["confidence"] > 0.60
    assert res["confidence_type"] == "calibrated_specialist"
    assert res["raw_score"] is not None
    assert res["calibrated_confidence"] is not None
    assert "fusion_details" in res
    assert res["fusion_details"]["specialist_model"] == "FarmGuard/cotton-densenet121"
    assert res["fusion_details"]["generalist_model"] == "India Multi-Crop DINOv2 ViT-B/14"


# 21. GENERALIST FALLBACK FOR UNSPECIALIZED CROPS
def test_21_generalist_fallback_for_unspecialized_crops():
    """Verify that crops without specialists (e.g. Potato) route to generalist fallback."""
    res = client.post(
        "/api/disease/predict",
        data={"sample_id": "potato_blight", "crop": "Potato"},
    ).json()

    assert res["abstention"] is False
    assert res["routing_path"] == "generalist_fallback"
    assert "DINOv2" in res["model_type"]
    assert res["specialist_agreement"] is None
    assert res["fusion_details"]["concordance"] == "generalist_only"


# 22. PREDICTION FUSION DETAILS AND NON-SYNTHETIC CIBRC TREATMENTS
def test_22_prediction_fusion_treatments_and_safety():
    """Verify that fused cotton predictions return genuine CIBRC registrations without synthetic fallbacks."""
    cotton_img_path = Path(__file__).resolve().parent.parent / "frontend" / "public" / "test_images" / "cotton_leaf_spot.jpg"
    with open(cotton_img_path, "rb") as f:
        img_bytes = f.read()

    res = client.post(
        "/api/disease/predict",
        files={"file": ("cotton.jpg", img_bytes, "image/jpeg")},
        data={"crop": "Cotton", "location_state": "Maharashtra"},
    ).json()

    assert res["diagnosed_crop"] == "Cotton"
    assert len(res["top_5_predictions"]) > 0
    # Treatments must not use synthetic fallback registrations
    for chem in res["treatments"]["chemical"]:
        assert "CIBRC-FUNG-STD" not in chem.get("cpr_registration", "")
    assert len(res["preventive_management"]) > 0
    assert len(res["non_chemical_options"]) > 0


# 23. SOYBEAN SPECIALIST ROUTING & CONCORDANT FUSION
def test_23_soybean_specialist_routing_and_concordant_fusion():
    """Verify that Soybean queries route to Soybean ConvNeXt specialist and execute prediction fusion."""
    soybean_test_img = Path(__file__).resolve().parent.parent / "models" / "disease_detection" / "test_data" / "soybean_eval" / "frogeye_leaf_spot_1.jpg"
    assert soybean_test_img.exists(), f"Missing soybean test image: {soybean_test_img}"

    with open(soybean_test_img, "rb") as f:
        img_bytes = f.read()

    res = client.post(
        "/api/disease/predict",
        files={"file": ("soybean.jpg", img_bytes, "image/jpeg")},
        data={"crop": "Soybean", "location_state": "Madhya Pradesh"},
    ).json()

    assert res["routing_path"] == "specialist_fused"
    assert "ixrbhii/soybean-disease-convnext" in res["model_identifier"]
    assert res["fusion_outcome"] in ["agree", "single_model", "disputed"]
    assert "fusion_details" in res
    assert res["fusion_details"]["specialist_model"] == "ixrbhii/soybean-disease-convnext"


# 24. DISPUTED DIAGNOSIS: SAFER DISAGREEMENT HANDLING (ZERO CHEMICALS)
def test_24_disputed_diagnosis_safer_disagreement_handling():
    """Verify that when specialist and generalist conflict on disease, diagnosis abstains and strictly withholds chemicals."""
    rust_test_img = Path(__file__).resolve().parent.parent / "models" / "disease_detection" / "test_data" / "soybean_eval" / "soybean_rust_1.jpg"
    assert rust_test_img.exists(), f"Missing rust test image: {rust_test_img}"

    with open(rust_test_img, "rb") as f:
        img_bytes = f.read()

    res = client.post(
        "/api/disease/predict",
        files={"file": ("soybean_rust.jpg", img_bytes, "image/jpeg")},
        data={"crop": "Soybean", "location_state": "Madhya Pradesh"},
    ).json()

    assert res["abstention"] is True
    assert res["fusion_outcome"] == "disputed"
    assert res["abstention_reason"] == "disputed"
    assert "Disputed" in res["condition"]
    # SAFETY INVARIANT: Strictly ZERO chemical pesticides on disputed diagnosis
    assert res["treatments"]["chemical"] == []
    # Competing predictions must be surfaced transparently
    assert len(res["competing_predictions"]) >= 2
    comp_models = [c["model"] for c in res["competing_predictions"]]
    assert any("convnext" in m.lower() for m in comp_models)
    assert any("dinov2" in m.lower() for m in comp_models)


# 25. CROP UNCERTAIN: CROP CONFLICT SAFETY ABSTENTION (ZERO CHEMICALS)
def test_25_crop_uncertain_safety_abstention():
    """Verify that when an apple scab image is uploaded with crop='Soybean', crop conflict triggers abstention and withholds chemicals."""
    assert APPLE_SCAB_IMG.exists(), f"Missing test image: {APPLE_SCAB_IMG}"

    with open(APPLE_SCAB_IMG, "rb") as f:
        img_bytes = f.read()

    res = client.post(
        "/api/disease/predict",
        files={"file": ("apple_as_soybean.jpg", img_bytes, "image/jpeg")},
        data={"crop": "Soybean", "location_state": "Madhya Pradesh"},
    ).json()

    assert res["abstention"] is True
    assert res["fusion_outcome"] == "crop_uncertain"
    assert res["abstention_reason"] == "crop_uncertain"
    assert "Host crop uncertain" in res["condition"]
    # SAFETY INVARIANT: Strictly ZERO chemicals on crop uncertainty
    assert res["treatments"]["chemical"] == []
    assert len(res["competing_predictions"]) >= 2


# 26. INSUFFICIENT EVIDENCE: LOW CONFIDENCE ABSTENTION
def test_26_insufficient_evidence_safety_abstention():
    """Verify that low-quality/ambiguous image triggers insufficient_evidence outcome and withholds chemicals."""
    # Synthetic flat image
    flat_img = Image.new("RGB", (224, 224), color=(128, 128, 128))
    buf = io.BytesIO()
    flat_img.save(buf, format="JPEG")
    img_bytes = buf.getvalue()

    res = client.post(
        "/api/disease/predict",
        files={"file": ("flat.jpg", img_bytes, "image/jpeg")},
        data={"crop": "Soybean", "abstention_threshold": 0.85},
    ).json()

    assert res["abstention"] is True
    assert res["fusion_outcome"] == "insufficient_evidence"
    assert res["treatments"]["chemical"] == []


# 27. SOYBEAN SPECIALIST CANONICAL CLASSES AND REJECTION
def test_27_soybean_canonical_classes_and_rejection():
    """Verify that Soybean specialist has exactly 6 canonical classes and rejects unsupported class fabrication."""
    try:
        from specialists.soybean.adapter import SoybeanConvNeXtAdapter, SOYBEAN_TAXONOMY_MAP
    except ImportError:
        from models.disease_detection.specialists.soybean.adapter import SoybeanConvNeXtAdapter, SOYBEAN_TAXONOMY_MAP

    adapter = SoybeanConvNeXtAdapter()
    assert len(adapter.classes) == 6
    expected_classes = [
        "Downy Mildew",
        "Frogeye Leaf Spot",
        "Healthy",
        "Mosaic Virus",
        "Rust",
        "Septoria Brown Spot",
    ]
    for exp in expected_classes:
        assert exp in adapter.classes
        assert exp in SOYBEAN_TAXONOMY_MAP

    # Ensure out-of-distribution classes are not in native specialist map
    assert "Bacterial Blight" not in SOYBEAN_TAXONOMY_MAP
    assert "Early Blight" not in SOYBEAN_TAXONOMY_MAP
    assert "Apple Scab" not in SOYBEAN_TAXONOMY_MAP


