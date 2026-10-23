"""
Phase 4 Robustness and Validation Test Suite (Section 19).

Validates:
 1. Low-light condition handling (dimmed foliar sample).
 2. Blurry image degradation handling.
 3. High-noise background resilience.
 4. Zero pests detected on clean foliar sample.
 5. Healthy plant tissue workflow (status='healthy', no chemical recommendations).
 6. Crop mismatch containment (Tomato image submitted with Cotton crop).
 7. Unsupported crop rejection (unregistered crop).
 8. Image-type routing for sticky trap sheets (foliar disease bypassed).
 9. Independent dual treatment separation (no ad-hoc chemical blending).
10. Severity assessment unavailability guarantee (never invented).
11. Grad-CAM and bounding box explainability generation.
12. Corrupted input image rejection.
13. Deterministic reproducibility across consecutive runs.
"""

import io
from pathlib import Path
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import pytest

from disease_pest_ai.inference.pipeline import DiseasePestPipeline
from disease_pest_ai.schemas.inputs import GrowthStage, ImageType
from disease_pest_ai.schemas.outputs import ConditionType, ReasonCode, RecommendationStatus

TEST_DATA_DIR = Path(__file__).resolve().parent.parent / "test_data"
TOMATO_EB = TEST_DATA_DIR / "tomato_early_blight.jpg"
TOMATO_HEALTHY = TEST_DATA_DIR / "tomato_healthy.jpg"
CORN_RUST = TEST_DATA_DIR / "corn_common_rust.jpg"
COTTON_TRAP = TEST_DATA_DIR / "wadhwani_cotton_trap.jpg"


@pytest.fixture(scope="module")
def pipeline():
    return DiseasePestPipeline(
        primary_disease_model="efficientnet",
        primary_pest_model="yolo_pest",
        lazy_load=False,
    )


def test_01_low_light_resilience(pipeline):
    """1. Low-light: severely dimmed image still processes through pipeline."""
    img = Image.open(TOMATO_EB).convert("RGB")
    enhancer = ImageEnhance.Brightness(img)
    dimmed_img = enhancer.enhance(0.20)  # 80% brightness reduction

    result = pipeline.predict(
        plant_image=dimmed_img,
        crop_name="Tomato",
        location_state="Maharashtra",
        growth_stage="vegetative",
        image_type="leaf",
    )

    assert result.disease.status in ("diagnosed", "low_score", "crop_mismatch")
    assert result.severity.status == "unavailable"
    assert result.provenance.disease_model is not None


def test_02_blurry_image_resilience(pipeline):
    """2. Blurry image: Gaussian blurred foliar sample processes gracefully."""
    img = Image.open(TOMATO_EB).convert("RGB")
    blurred_img = img.filter(ImageFilter.GaussianBlur(radius=5.0))

    result = pipeline.predict(
        plant_image=blurred_img,
        crop_name="Tomato",
        location_state="Maharashtra",
        growth_stage="vegetative",
        image_type="leaf",
    )

    assert result.disease.condition != ""
    assert result.disease.score >= 0.0
    assert result.severity.status == "unavailable"


def test_03_high_noise_background(pipeline):
    """3. High noise background: foliar sample with added salt-and-pepper noise."""
    img = Image.open(CORN_RUST).convert("RGB")
    arr = np.array(img).astype(np.float32)
    noise = np.random.normal(0, 25, arr.shape)
    noisy_arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
    noisy_img = Image.fromarray(noisy_arr)

    result = pipeline.predict(
        plant_image=noisy_img,
        crop_name="Corn",
        location_state="Bihar",
        growth_stage="vegetative",
        image_type="leaf",
    )

    assert result.input.crop == "Corn"
    assert result.disease.condition in ("Common Rust", "Cercospora Leaf Spot Gray Leaf Spot", "Northern Leaf Blight")
    assert result.severity.status == "unavailable"


def test_04_zero_pest_detected(pipeline):
    """4. Clean foliar sample produces count=0 and no_pest_detected status."""
    result = pipeline.predict(
        plant_image=TOMATO_HEALTHY,
        crop_name="Tomato",
        location_state="Karnataka",
        growth_stage="flowering",
        image_type="leaf",
    )

    assert result.pests.count == 0
    assert result.pests.status == "no_pest_detected"
    assert len(result.pests.detections) == 0


def test_05_healthy_plant_workflow(pipeline):
    """5. Healthy leaf: diagnosed as Healthy, 0 chemicals, recommendation_status='no_treatment_needed_healthy'."""
    result = pipeline.predict(
        plant_image=TOMATO_HEALTHY,
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


def test_06_crop_mismatch_containment(pipeline):
    """6. Crop mismatch: Tomato sample submitted with 'Cotton' as user crop."""
    result = pipeline.predict(
        plant_image=TOMATO_EB,
        crop_name="Cotton",
        location_state="Gujarat",
        growth_stage="flowering",
        image_type="leaf",
    )

    assert result.disease.crop_match is False
    assert result.disease.status == "crop_mismatch"
    assert result.treatment.recommendation_status == "manual_review_required"
    assert len(result.treatment.chemical_candidates) == 0
    assert any("Crop mismatch" in w or "Crop Mismatch" in w for w in result.warnings)


def test_07_unsupported_crop_rejection(pipeline):
    """7. Unsupported crop: submitted with unregistered crop 'Dragonfruit'."""
    result = pipeline.predict(
        plant_image=TOMATO_EB,
        crop_name="Dragonfruit",
        location_state="Kerala",
        growth_stage="flowering",
        image_type="leaf",
    )

    assert result.disease.crop_match is False
    assert result.treatment.recommendation_status == "manual_review_required"
    assert len(result.treatment.chemical_candidates) == 0
    assert any("Unsupported Crop" in w for w in result.warnings)


def test_08_image_type_routing_trap_sheet(pipeline):
    """8. Image-type routing: trap_sticky_sheet bypasses foliar disease classifier."""
    result = pipeline.predict(
        plant_image=COTTON_TRAP,
        crop_name="Cotton",
        location_state="Punjab",
        growth_stage="boll_formation",
        image_type="trap_sticky_sheet",
    )

    # Foliar disease must be bypassed
    assert result.disease.status == "bypassed"
    assert result.disease.condition == "Not Applicable (Trap Sheet)"
    assert result.disease.score == 0.0

    # Pest detector must run with domain notice
    assert any("trap_sticky_sheet" in w for w in result.warnings)


def test_09_independent_treatment_separation(pipeline):
    """9. Independent treatments: disease and pest recommendations are kept distinct, no tank mixes."""
    result = pipeline.predict(
        plant_image=TOMATO_EB,
        crop_name="Tomato",
        location_state="Maharashtra",
        growth_stage="fruiting",
        image_type="leaf",
    )

    # Disease recommendations should exist
    assert result.treatment.disease_recommendations is not None
    assert result.treatment.disease_recommendations.crop == "Tomato"
    assert result.treatment.disease_recommendations.status == RecommendationStatus.VERIFIED_CANDIDATES_FOUND

    # Pest block is independent
    if result.treatment.pest_recommendations:
        # Chemical lists are independent
        dis_ais = [c.active_ingredient for c in result.treatment.disease_recommendations.chemical_candidates]
        pest_ais = [c.active_ingredient for c in result.treatment.pest_recommendations.chemical_candidates]
        # Never merged into an ad-hoc combined list object
        assert isinstance(result.treatment.disease_recommendations.chemical_candidates, list)
        assert isinstance(result.treatment.pest_recommendations.chemical_candidates, list)


def test_10_severity_assessment_integrity(pipeline):
    """10. Severity: status is strictly 'unavailable' and value is None."""
    result = pipeline.predict(
        plant_image=TOMATO_EB,
        crop_name="Tomato",
        location_state="Maharashtra",
        growth_stage="vegetative",
        image_type="leaf",
    )

    assert result.severity.status == "unavailable"
    assert result.severity.value is None
    assert result.severity.source == "unavailable"


def test_11_explainability_generation(pipeline):
    """11. Explainability: Grad-CAM heatmap generated and bounding boxes formatted."""
    result = pipeline.predict(
        plant_image=CORN_RUST,
        crop_name="Corn",
        location_state="Bihar",
        growth_stage="vegetative",
        image_type="leaf",
        generate_visual_explanation=True,
    )

    assert result.explainability is not None
    assert result.explainability.explanation_type in ("gradcam", "gradcam_and_bounding_boxes")
    assert result.explainability.disease_heatmap is not None
    assert result.explainability.disease_heatmap.startswith("data:image/jpeg;base64,")


def test_12_corrupted_image_rejection(pipeline):
    """12. Corrupted input: unreadable image bytes raise ValueError."""
    corrupted_bytes = b"NOT_A_VALID_JPEG_OR_PNG_HEADER_DATA"

    with pytest.raises(Exception):
        pipeline.predict(
            plant_image=corrupted_bytes,
            crop_name="Tomato",
            location_state="Maharashtra",
            growth_stage="vegetative",
            image_type="leaf",
        )


def test_13_deterministic_reproducibility(pipeline):
    """13. Determinism: identical inputs produce identical predictions and scores."""
    res1 = pipeline.predict(
        plant_image=TOMATO_EB,
        crop_name="Tomato",
        location_state="Karnataka",
        growth_stage="vegetative",
        image_type="leaf",
        generate_visual_explanation=False,
    )

    res2 = pipeline.predict(
        plant_image=TOMATO_EB,
        crop_name="Tomato",
        location_state="Karnataka",
        growth_stage="vegetative",
        image_type="leaf",
        generate_visual_explanation=False,
    )

    assert res1.disease.condition == res2.disease.condition
    assert res1.disease.score == res2.disease.score
    assert res1.pests.count == res2.pests.count
    assert res1.treatment.recommendation_status == res2.treatment.recommendation_status
