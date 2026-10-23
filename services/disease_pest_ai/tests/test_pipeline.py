"""
Tests for unified DiseasePestPipeline.
"""

from pathlib import Path
import pytest

from disease_pest_ai.inference.pipeline import DiseasePestPipeline
from disease_pest_ai.schemas.outputs import ConditionType

TEST_DATA_DIR = Path(__file__).resolve().parent.parent / "test_data"
APPLE_SAMPLE = TEST_DATA_DIR / "apple_scab_bierny.jpg"
CORN_SAMPLE = TEST_DATA_DIR / "corn_common_rust.jpg"


def test_pipeline_standard_prediction():
    """Verify end-to-end pipeline inference with all 5 required fields."""
    pipeline = DiseasePestPipeline(primary_disease_model="efficientnet")
    
    result = pipeline.predict(
        plant_image=CORN_SAMPLE,
        crop_name="Corn",
        location_state="Bihar",
        growth_stage="vegetative",
        image_type="leaf",
    )

    assert result.condition == "Common Rust"
    assert result.crop == "Corn"
    assert result.user_crop == "Corn"
    assert result.crop_mismatch is False
    assert result.score > 0.85
    assert result.provenance["pipeline"]["location_state"] == "Bihar"


def test_pipeline_missing_fields_validation_error():
    """Verify pipeline rejects incomplete inputs."""
    pipeline = DiseasePestPipeline()

    with pytest.raises(Exception):
        pipeline.predict(
            plant_image=CORN_SAMPLE,
            crop_name="",  # Blank
            location_state="Bihar",
            growth_stage="vegetative",
            image_type="leaf",
        )


def test_pipeline_model_override():
    """Verify override allows switching between adapters."""
    pipeline = DiseasePestPipeline(primary_disease_model="efficientnet")
    
    result_yolo = pipeline.predict(
        plant_image=APPLE_SAMPLE,
        crop_name="Apple",
        location_state="Himachal Pradesh",
        growth_stage="fruiting",
        image_type="leaf",
        model_override="yolo",
    )

    assert result_yolo.model_name == "JK-TK/PlantDiseaseDetection"
