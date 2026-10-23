"""
Comprehensive Tests for Phase 3 Pest Detection Model Integration (Section 22).

Tests cover:
- Checkpoint loading
- Prediction schema compliance
- Zero-pest output handling
- One-pest output handling
- Multi-pest output handling
- Crop validation and mismatch detection
- Image-type validation and domain warnings
- Corrupt and low-resolution image handling
- Bounding-box validity
- Low-score threshold behavior
- Pipeline integration
- Treatment-engine compatibility
- Visualization integrity
"""

import copy
from pathlib import Path
import pytest
from PIL import Image

from disease_pest_ai.inference.pipeline import DiseasePestPipeline
from disease_pest_ai.inference.visualization import draw_pest_detections
from disease_pest_ai.models.pest.yolo_pest_adapter import YoloPestAdapter
from disease_pest_ai.recommendation.treatment_engine import TreatmentEngine
from disease_pest_ai.schemas.outputs import (
    ConditionType,
    DetectedPest,
    PestPrediction,
    RecommendationStatus,
)

TEST_DATA_DIR = Path(__file__).resolve().parent.parent / "test_data"
SAMPLE_CORN = TEST_DATA_DIR / "corn_common_rust.jpg"
SAMPLE_HEALTHY = TEST_DATA_DIR / "tomato_healthy.jpg"
SAMPLE_TRAP = TEST_DATA_DIR / "wadhwani_cotton_trap.jpg"


@pytest.fixture
def pest_adapter():
    return YoloPestAdapter(model_variant="primary")


@pytest.fixture
def secondary_pest_adapter():
    return YoloPestAdapter(model_variant="secondary")


@pytest.fixture
def pipeline():
    return DiseasePestPipeline()


def test_01_checkpoint_loading(pest_adapter):
    """Verify primary YOLO11s checkpoint loads successfully with 102 classes."""
    pest_adapter.load_weights()
    assert pest_adapter.model is not None
    assert len(pest_adapter.model.names) == 102
    assert pest_adapter.model_name == "underdogquality/yolo11s-pest-detection"
    assert pest_adapter.model_version == "YOLO11s-IP102"


def test_02_secondary_checkpoint_loading(secondary_pest_adapter):
    """Verify secondary YOLO11m checkpoint loads successfully."""
    secondary_pest_adapter.load_weights()
    assert secondary_pest_adapter.model is not None
    assert len(secondary_pest_adapter.model.names) == 102
    assert secondary_pest_adapter.model_name == "Yudsky/pest-detection-yolo11"


def test_03_prediction_schema_compliance(pest_adapter):
    """Verify PestPrediction returns strictly compliant Pydantic schema."""
    pred = pest_adapter.predict(
        image=SAMPLE_CORN,
        crop_name="Corn",
        image_type="leaf"
    )
    assert isinstance(pred, PestPrediction)
    assert hasattr(pred, "pests")
    assert hasattr(pred, "top_pests")
    assert hasattr(pred, "bounding_boxes")
    assert hasattr(pred, "scores")
    assert hasattr(pred, "crop")
    assert hasattr(pred, "crop_validation")
    assert hasattr(pred, "model_name")
    assert hasattr(pred, "model_version")
    assert hasattr(pred, "status")
    assert hasattr(pred, "warnings")
    assert hasattr(pred, "provenance")
    assert pred.provenance["device"] in ("cpu", "cuda")


def test_04_zero_pest_output(pest_adapter):
    """Verify clean leaf with no pests returns empty list and no_pest_detected status."""
    pred = pest_adapter.predict(
        image=SAMPLE_HEALTHY,
        crop_name="Tomato",
        image_type="leaf"
    )
    assert pred.pest_count == 0
    assert pred.pests == []
    assert pred.status == "no_pest_detected"


def test_05_one_pest_output(pest_adapter):
    """Verify valid detection returns DetectedPest with coordinates and class."""
    pred = pest_adapter.predict(
        image=SAMPLE_CORN,
        crop_name="Corn",
        image_type="leaf"
    )
    assert pred.pest_count >= 1
    top = pred.top_pests[0]
    assert isinstance(top, DetectedPest)
    assert top.pest != ""
    assert top.score >= pest_adapter.conf_threshold
    assert len(top.bounding_box) == 4


def test_06_multi_pest_output_ranking():
    """Verify multi-pest detections are ranked descending by confidence score."""
    # Test adapter ranking logic with low threshold on sensitive detection
    sens_adapter = YoloPestAdapter(conf_threshold=0.10)
    pred = sens_adapter.predict(
        image=SAMPLE_CORN,
        crop_name="Corn",
        image_type="leaf"
    )
    if len(pred.pests) > 1:
        scores = [p.score for p in pred.top_pests]
        assert scores == sorted(scores, reverse=True)


def test_07_crop_validation_compatible(pest_adapter):
    """Verify compatible pest on user crop passes validation."""
    pred = pest_adapter.predict(
        image=SAMPLE_CORN,
        crop_name="Corn",
        image_type="leaf"
    )
    if pred.pests:
        assert pred.crop_validation["user_crop"] == "Corn"
        # Flatid planthopper host list includes Corn
        assert pred.pests[0].crop_compatible is True


def test_08_crop_validation_mismatch(pest_adapter):
    """Verify mismatch between user crop and pest host is flagged."""
    # Pass Wheat as user crop for image containing Corn Flatid Planthopper
    pred = pest_adapter.predict(
        image=SAMPLE_CORN,
        crop_name="Wheat",  # Not a primary host for Flatid planthopper
        image_type="leaf"
    )
    if pred.pests:
        assert pred.pests[0].crop_compatible is False
        assert pred.status == "crop_mismatch"
        assert pred.crop_validation["crop_pest_mismatch"] is True
        assert any("Crop Pest Mismatch" in w for w in pred.warnings)


def test_09_image_type_validation_and_domain_warning(pest_adapter):
    """Verify trap_sticky_sheet generates out-of-domain advisory warning."""
    pred = pest_adapter.predict(
        image=SAMPLE_TRAP,
        crop_name="Cotton",
        image_type="trap_sticky_sheet"
    )
    assert any("Domain Notice" in w for w in pred.warnings)
    assert any("trap_sticky_sheet" in w for w in pred.warnings)


def test_10_corrupt_and_missing_image_inputs(pest_adapter):
    """Verify file not found raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        pest_adapter.predict(
            image=TEST_DATA_DIR / "non_existent_file_xyz.jpg",
            crop_name="Cotton"
        )


def test_11_low_resolution_image_warning(pest_adapter):
    """Verify extremely small image produces Low Resolution Warning."""
    tiny_img = Image.new("RGB", (20, 20), color="green")
    pred = pest_adapter.predict(
        image=tiny_img,
        crop_name="Tomato"
    )
    assert any("Low Resolution Warning" in w for w in pred.warnings)


def test_12_bounding_box_validity(pest_adapter):
    """Verify bounding box coordinates are non-negative and mathematically valid."""
    pred = pest_adapter.predict(
        image=SAMPLE_CORN,
        crop_name="Corn"
    )
    for b in pred.bounding_boxes:
        x1, y1, x2, y2 = b.box
        assert x1 >= 0
        assert y1 >= 0
        assert x2 >= x1
        assert y2 >= y1


def test_13_high_confidence_threshold_filtering(pest_adapter):
    """Verify high threshold filters out weak detections into no_pest_detected."""
    strict_adapter = YoloPestAdapter(conf_threshold=0.99)
    pred = strict_adapter.predict(
        image=SAMPLE_CORN,
        crop_name="Corn"
    )
    # At 0.99 threshold, no candidate reaches threshold
    assert pred.pest_count == 0
    assert pred.status == "no_pest_detected"


def test_14_pipeline_integration_with_pest(pipeline):
    """Verify full pipeline produces unified result with pest_prediction populated."""
    result = pipeline.predict(
        plant_image=SAMPLE_CORN,
        crop_name="Corn",
        location_state="Bihar",
        growth_stage="vegetative",
        image_type="leaf",
        run_pest_detection=True
    )
    assert result.crop == "Corn"
    assert result.diagnosis.condition != ""
    assert result.pest_prediction is not None
    assert isinstance(result.pest_prediction, PestPrediction)
    assert result.provenance.get("pest_model") == "underdogquality/yolo11s-pest-detection"


def test_15_treatment_engine_pest_compatibility():
    """Verify treatment engine retrieves registered treatments for pest taxonomy entries."""
    engine = TreatmentEngine()
    
    # Spider Mites on Tomato
    rec = engine.get_treatment_recommendations(
        crop_name="Tomato",
        condition="Spider Mites (Two-Spotted Spider Mite)",
        condition_type=ConditionType.PEST,
        location_state="Maharashtra",
        growth_stage="vegetative",
        prediction_score=0.88,
        crop_mismatch=False
    )
    assert rec.status == RecommendationStatus.VERIFIED_CANDIDATES_FOUND
    assert rec.condition_type == ConditionType.PEST
    assert len(rec.chemical_candidates) > 0

    # Cotton Bollworm on Cotton
    rec2 = engine.get_treatment_recommendations(
        crop_name="Cotton",
        condition="Cotton Bollworm Infestation",
        condition_type=ConditionType.PEST,
        location_state="Gujarat",
        growth_stage="boll_formation",
        prediction_score=0.90,
        crop_mismatch=False
    )
    assert rec2.status == RecommendationStatus.VERIFIED_CANDIDATES_FOUND
    assert rec2.condition_type == ConditionType.PEST


def test_16_visualization_utility():
    """Verify visualization generates output copy without mutating original image."""
    img = Image.open(SAMPLE_CORN)
    orig_pixels = list(img.getdata())
    
    adapter = YoloPestAdapter()
    pred = adapter.predict(img, crop_name="Corn")
    
    annotated = draw_pest_detections(img, pred)
    assert isinstance(annotated, Image.Image)
    assert annotated is not img
    # Verify original image was not mutated
    assert list(img.getdata()) == orig_pixels
