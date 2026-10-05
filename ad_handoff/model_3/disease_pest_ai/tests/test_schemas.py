"""
Unit tests for Disease & Pest AI schemas.
"""

import pytest
from pydantic import ValidationError

from disease_pest_ai.schemas.inputs import DiseasePestInput, GrowthStage, ImageType
from disease_pest_ai.schemas.outputs import (
    BoundingBox,
    ConditionType,
    PredictionResult,
    TopPrediction,
)


def test_input_contract_all_fields_present():
    """Verify valid input with all 5 required fields passes validation."""
    data = {
        "plant_image": "dummy_path.jpg",
        "crop_name": "Tomato",
        "location_state": "Maharashtra",
        "growth_stage": "vegetative",
        "image_type": "leaf",
    }
    obj = DiseasePestInput(**data)
    assert obj.crop_name == "Tomato"
    assert obj.location_state == "Maharashtra"
    assert obj.growth_stage == "vegetative"
    assert obj.image_type == "leaf"


def test_input_contract_missing_fields_raises_validation_error():
    """Verify that omitting any of the 5 required fields triggers a ValidationError."""
    # Missing crop_name
    with pytest.raises(ValidationError):
        DiseasePestInput(
            plant_image="leaf.jpg",
            location_state="Punjab",
            growth_stage="flowering",
            image_type="leaf",
        )

    # Missing location_state
    with pytest.raises(ValidationError):
        DiseasePestInput(
            plant_image="leaf.jpg",
            crop_name="Corn",
            growth_stage="flowering",
            image_type="leaf",
        )

    # Missing growth_stage
    with pytest.raises(ValidationError):
        DiseasePestInput(
            plant_image="leaf.jpg",
            crop_name="Corn",
            location_state="Punjab",
            image_type="leaf",
        )

    # Missing image_type
    with pytest.raises(ValidationError):
        DiseasePestInput(
            plant_image="leaf.jpg",
            crop_name="Corn",
            location_state="Punjab",
            growth_stage="vegetative",
        )

    # Missing plant_image
    with pytest.raises(ValidationError):
        DiseasePestInput(
            crop_name="Corn",
            location_state="Punjab",
            growth_stage="vegetative",
            image_type="leaf",
        )


def test_input_contract_empty_strings_rejected():
    """Verify that blank whitespace strings are rejected."""
    with pytest.raises(ValidationError):
        DiseasePestInput(
            plant_image="leaf.jpg",
            crop_name="   ",
            location_state="Punjab",
            growth_stage="vegetative",
            image_type="leaf",
        )


def test_prediction_result_schema():
    """Verify standardized PredictionResult fields and methods."""
    res = PredictionResult(
        condition="Apple Scab",
        condition_type=ConditionType.DISEASE,
        score=0.92,
        top_predictions=[
            TopPrediction(
                condition="Apple Scab",
                crop="Apple",
                score=0.92,
                condition_type=ConditionType.DISEASE,
            )
        ],
        bounding_boxes=[],
        crop="Apple",
        user_crop="Apple",
        crop_mismatch=False,
        model_name="BiernyVR/crop-disease-classifier",
        model_version="v1.0",
        warnings=[],
        provenance={"latency_ms": 120.5},
    )
    assert res.condition == "Apple Scab"
    assert res.crop_mismatch is False
    assert len(res.top_predictions) == 1
    assert res.score == 0.92
