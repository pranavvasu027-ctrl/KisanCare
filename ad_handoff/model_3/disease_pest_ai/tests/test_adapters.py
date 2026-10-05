"""
Unit and integration tests for model adapters.
"""

from pathlib import Path
import pytest
from PIL import Image
import numpy as np

from disease_pest_ai.models.disease.efficientnet_adapter import EfficientNetDiseaseAdapter
from disease_pest_ai.models.disease.yolo_disease_adapter import YoloDiseaseAdapter
from disease_pest_ai.models.pest.wadhwani_adapter import WadhwaniPestAdapter
from disease_pest_ai.schemas.outputs import ConditionType

TEST_DATA_DIR = Path(__file__).resolve().parent.parent / "test_data"
APPLE_SAMPLE = TEST_DATA_DIR / "apple_scab_bierny.jpg"
CORN_SAMPLE = TEST_DATA_DIR / "corn_common_rust.jpg"


def test_efficientnet_adapter_loading_and_prediction():
    """Verify EfficientNetV2-S loads and classifies benchmark leaf image."""
    adapter = EfficientNetDiseaseAdapter()
    assert adapter.is_available() is True

    result = adapter.predict(
        image=APPLE_SAMPLE,
        crop_name="Apple",
        location_state="Himachal Pradesh",
        growth_stage="fruiting",
        image_type="leaf",
    )

    assert result.condition == "Apple Scab"
    assert result.condition_type == ConditionType.DISEASE
    assert result.crop == "Apple"
    assert result.user_crop == "Apple"
    assert result.crop_mismatch is False
    assert result.score > 0.80
    assert len(result.top_predictions) == 5
    assert result.bounding_boxes == []
    assert "latency_ms" in result.provenance


def test_efficientnet_adapter_crop_mismatch():
    """Verify crop mismatch is flagged without altering user crop."""
    adapter = EfficientNetDiseaseAdapter()
    result = adapter.predict(
        image=APPLE_SAMPLE,
        crop_name="Tomato",  # Mismatch with Apple Scab leaf
        location_state="Karnataka",
        growth_stage="flowering",
        image_type="leaf",
    )

    assert result.crop == "Apple"
    assert result.user_crop == "Tomato"
    assert result.crop_mismatch is True
    assert len(result.warnings) > 0
    assert "Crop mismatch detected" in result.warnings[0]


def test_yolo_adapter_loading_and_prediction():
    """Verify YOLOv11x loads and performs object detection."""
    adapter = YoloDiseaseAdapter()
    assert adapter.is_available() is True

    result = adapter.predict(
        image=APPLE_SAMPLE,
        crop_name="Apple",
        location_state="Jammu and Kashmir",
        growth_stage="fruiting",
        image_type="leaf",
    )

    assert result.model_name == "JK-TK/PlantDiseaseDetection"
    assert result.score > 0.0
    assert isinstance(result.bounding_boxes, list)
    assert len(result.bounding_boxes) > 0


def test_wadhwani_adapter_checkpoint_unavailability():
    """
    Verify Wadhwani pest adapter correctly reports unavailability
    when no checkpoint is provided, refusing to invent synthetic weights.
    """
    adapter = WadhwaniPestAdapter(checkpoint_path=None)
    assert adapter.is_available() is False

    with pytest.raises(RuntimeError) as exc_info:
        adapter.predict(
            image=APPLE_SAMPLE,
            crop_name="Cotton",
            location_state="Gujarat",
            growth_stage="flowering",
            image_type="trap_sticky_sheet",
        )
    assert "Pretrained checkpoint for WadhwaniAI/pest-monitoring is unavailable" in str(exc_info.value)
