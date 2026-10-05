"""Inference verification test for Model 2: Crop Yield Prediction."""

import pytest
from pathlib import Path
import sys

# Add KisanCare root to sys.path
KISANCARE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(KISANCARE_ROOT))

from ad_handoff.model_2.model.loader import load_crop_yield_model
from ad_handoff.model_2.preprocessing.encoder_utils import validate_and_encode_inputs
from ad_handoff.model_2.inference.predictor import predict_crop_yield, YieldPredictionResult


def test_model_2_full_pipeline_inference():
    """Verify Model 2: Artifact Load -> Preprocessing Load -> Valid Input -> Inference -> Valid Output."""
    # 1. MODEL ARTIFACT LOAD
    artifacts = load_crop_yield_model()
    assert "model" in artifacts
    assert hasattr(artifacts["model"], "predict")

    # 2. PREPROCESSING LOAD
    for enc_key in ["le_state", "le_crop", "le_season", "le_soil"]:
        assert enc_key in artifacts
        assert hasattr(artifacts[enc_key], "classes_")
        assert len(artifacts[enc_key].classes_) > 0

    # 3. VALID INPUT
    state = "Maharashtra"
    crop = "Rice"
    season = "Kharif"
    soil_type = "Clay"
    area = 2.5
    rainfall = 800.0
    temperature = 26.0
    humidity = 75.0
    nitrogen = 90.0
    phosphorus = 42.0
    potassium = 43.0

    # Test encoding step
    encoded = validate_and_encode_inputs(state, crop, season, soil_type, artifacts)
    assert len(encoded) == 4

    # 4. INFERENCE
    result = predict_crop_yield(
        state=state,
        crop=crop,
        season=season,
        soil_type=soil_type,
        area=area,
        rainfall=rainfall,
        temperature=temperature,
        humidity=humidity,
        nitrogen=nitrogen,
        phosphorus=phosphorus,
        potassium=potassium,
    )

    # 5. VALID OUTPUT
    assert isinstance(result, YieldPredictionResult)
    assert isinstance(result.predicted_yield, float)
    assert result.predicted_yield > 0.0
    assert result.unit == "quintal/hectare"
    assert result.estimated_production == pytest.approx(result.predicted_yield * area, rel=1e-5)
    assert result.production_unit == "quintal"
