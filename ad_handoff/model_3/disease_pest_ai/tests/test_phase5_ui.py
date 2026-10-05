"""
Phase 5 UI and End-to-End System Validation Suite (Section 21).

Covers:
 TEST 1: Supported crop + valid disease image (Tomato + Early Blight)
 TEST 2: Healthy control image (Tomato + Healthy Control)
 TEST 3: Crop mismatch detection & chemical suppression (Cotton + Tomato Early Blight)
 TEST 4: Pest detection where supported (Corn + Corn Rust with Planthopper localization)
 TEST 5: Unsupported crop handling (Dragonfruit + Apple Scab)
 TEST 6: Invalid / corrupted image rejection
 TEST 7: Modal routing across supported image types (leaf vs trap_sticky_sheet)
 TEST 8: Streamlit App Initialization and Execution Test (AppTest)
"""

import io
from pathlib import Path
from PIL import Image
import pytest

from disease_pest_ai.inference.pipeline import DiseasePestPipeline
from disease_pest_ai.schemas.final_output import AgricultureDiseaseResult
from disease_pest_ai.schemas.outputs import ConditionType, RecommendationStatus
from disease_pest_ai.ui.components.inputs import validate_uploaded_image

TEST_DATA_DIR = Path(__file__).resolve().parent.parent / "test_data"
TOMATO_EB_IMG = TEST_DATA_DIR / "tomato_early_blight.jpg"
TOMATO_HEALTHY_IMG = TEST_DATA_DIR / "tomato_healthy.jpg"
APPLE_SCAB_IMG = TEST_DATA_DIR / "apple_scab_bierny.jpg"
CORN_RUST_IMG = TEST_DATA_DIR / "corn_common_rust.jpg"
COTTON_TRAP_IMG = TEST_DATA_DIR / "wadhwani_cotton_trap.jpg"


@pytest.fixture(scope="module")
def pipeline():
    return DiseasePestPipeline(
        primary_disease_model="efficientnet",
        primary_pest_model="yolo_pest",
        lazy_load=False,
    )


def test_01_supported_crop_valid_disease(pipeline):
    """TEST 1: Supported crop + valid disease image."""
    result = pipeline.predict(
        plant_image=TOMATO_EB_IMG,
        crop_name="Tomato",
        location_state="Maharashtra",
        growth_stage="fruiting",
        image_type="leaf",
    )

    assert result.disease.condition == "Early Blight"
    assert result.disease.crop_match is True
    assert result.disease.status == "diagnosed"
    assert result.disease.score > 0.80

    # Treatment must be verified
    assert result.treatment.disease_recommendations is not None
    assert result.treatment.disease_recommendations.status == RecommendationStatus.VERIFIED_CANDIDATES_FOUND
    assert len(result.treatment.disease_recommendations.chemical_candidates) > 0
    assert len(result.treatment.disease_recommendations.non_chemical_controls) > 0


def test_02_healthy_image(pipeline):
    """TEST 2: Healthy control image."""
    result = pipeline.predict(
        plant_image=TOMATO_HEALTHY_IMG,
        crop_name="Tomato",
        location_state="Karnataka",
        growth_stage="vegetative",
        image_type="leaf",
    )

    assert result.disease.condition == "Healthy"
    assert result.disease.condition_type == ConditionType.HEALTHY
    assert result.disease.status == "healthy"
    assert result.treatment.recommendation_status == "no_treatment_needed_healthy"
    assert len(result.treatment.chemical_candidates) == 0


def test_03_crop_mismatch(pipeline):
    """TEST 3: Crop mismatch detection and chemical suppression."""
    result = pipeline.predict(
        plant_image=TOMATO_EB_IMG,
        crop_name="Cotton",  # Mismatch: Tomato Early Blight submitted as Cotton
        location_state="Gujarat",
        growth_stage="vegetative",
        image_type="leaf",
    )

    assert result.disease.crop_match is False
    assert result.disease.status == "crop_mismatch"
    assert result.treatment.recommendation_status == "manual_review_required"
    # Crucial safety check: Zero chemicals recommended
    assert len(result.treatment.chemical_candidates) == 0
    assert any("Crop mismatch" in w or "Crop Mismatch" in w for w in result.warnings)


def test_04_pest_image_supported(pipeline):
    """TEST 4: Pest detection on supported foliar sample."""
    result = pipeline.predict(
        plant_image=CORN_RUST_IMG,
        crop_name="Corn",
        location_state="Bihar",
        growth_stage="vegetative",
        image_type="leaf",
    )

    assert result.pests.count >= 1
    top_pest = result.pests.detections[0]
    assert top_pest.score > 0.50
    assert len(top_pest.bounding_box) == 4
    assert result.explainability.pest_boxes is not None


def test_05_unsupported_crop(pipeline):
    """TEST 5: Unsupported crop rejected safely."""
    result = pipeline.predict(
        plant_image=APPLE_SCAB_IMG,
        crop_name="Dragonfruit",  # Unregistered crop
        location_state="Kerala",
        growth_stage="flowering",
        image_type="leaf",
    )

    assert result.disease.crop_match is False
    assert result.treatment.recommendation_status == "manual_review_required"
    assert len(result.treatment.chemical_candidates) == 0
    assert any("Unsupported Crop" in w for w in result.warnings)


def test_06_invalid_image_validation():
    """TEST 6: Invalid / corrupted image rejection by UI validation."""
    # Too small resolution
    tiny_img = Image.new("RGB", (64, 64), color="green")
    buf = io.BytesIO()
    tiny_img.save(buf, format="JPEG")
    _, err = validate_uploaded_image(buf.getvalue(), "tiny.jpg")
    assert err is not None
    assert "resolution" in err.lower()

    # Corrupt payload
    corrupt_bytes = b"CORRUPTED_NON_IMAGE_HEADER_BYTES"
    _, err_c = validate_uploaded_image(corrupt_bytes, "corrupt.jpg")
    assert err_c is not None


def test_07_image_type_modal_routing(pipeline):
    """TEST 7: Modal routing across supported image types (leaf vs trap_sticky_sheet)."""
    # 7a. Foliar leaf modality -> disease active
    res_leaf = pipeline.predict(
        plant_image=TOMATO_EB_IMG,
        crop_name="Tomato",
        location_state="Maharashtra",
        growth_stage="fruiting",
        image_type="leaf",
    )
    assert res_leaf.disease.status == "diagnosed"

    # 7b. Trap sticky sheet modality -> foliar disease bypassed
    res_trap = pipeline.predict(
        plant_image=COTTON_TRAP_IMG,
        crop_name="Cotton",
        location_state="Punjab",
        growth_stage="boll_formation",
        image_type="trap_sticky_sheet",
    )
    assert res_trap.disease.status == "bypassed"
    assert res_trap.disease.condition == "Not Applicable (Trap Sheet)"
    assert res_trap.disease.score == 0.0
    assert any("trap_sticky_sheet" in w for w in res_trap.warnings)


def test_08_streamlit_app_startup():
    """TEST 8: Verify Streamlit App initializes and renders without unhandled exceptions."""
    try:
        from streamlit.testing.v1 import AppTest
        app_path = str(Path(__file__).resolve().parent.parent / "ui" / "app.py")
        at = AppTest.from_file(app_path)
        at.run(timeout=30)
        assert not at.exception
    except ImportError:
        pytest.skip("streamlit.testing.v1.AppTest not available in current environment")
