"""Inference verification test for Model 1: Crop Recommendation."""

import pytest
from pathlib import Path
import sys

# Ensure KisanCare root is on path
KISANCARE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(KISANCARE_ROOT))

# Ensure model_1 package directory is also on path for internal relative imports
M1_DIR = KISANCARE_ROOT / "ad_handoff" / "model_1"
sys.path.insert(0, str(M1_DIR))

from ad_handoff.model_1.model.loader import load_crop_recommendation_model
from ad_handoff.model_1.preprocessing.knowledge_base import get_default_knowledge_base
from ad_handoff.model_1.inference.schemas import SoilClimateData, CropHistoryInput
from ad_handoff.model_1.inference.engine import RecommendationEngine


def test_model_1_full_pipeline_inference():
    """Verify Model 1: Artifact Load -> Preprocessing Load -> Valid Input -> Inference -> Valid Output."""
    # 1. MODEL ARTIFACT LOAD
    model, label_encoder = load_crop_recommendation_model()
    assert model is not None
    assert label_encoder is not None
    assert hasattr(model, "predict_proba")
    assert len(label_encoder.classes_) == 22

    # 2. PREPROCESSING LOAD
    kb = get_default_knowledge_base()
    assert kb is not None
    all_crops = kb.list_crops()
    assert len(all_crops) > 0

    # 3. VALID INPUT
    soil_climate = SoilClimateData(
        N=90.0,
        P=42.0,
        K=43.0,
        temperature=26.0,
        humidity=75.0,
        ph=6.5,
        rainfall=800.0,
        state="Maharashtra",
    )
    history = CropHistoryInput(
        crops_grown=["Cotton", "Soybean"],
        seasons_ago=[1, 2],
        yields=[20.0, 15.0],
    )

    # 4. INFERENCE
    engine = RecommendationEngine(knowledge_base=kb)
    response = engine.recommend(
        soil_climate=soil_climate,
        history=history,
        top_k=3,
    )

    # 5. VALID OUTPUT
    assert response is not None
    assert len(response.recommendations) == 3
    top_rec = response.recommendations[0]
    assert isinstance(top_rec.crop, str)
    assert 0.0 <= top_rec.final_score <= 1.0
    assert 0.0 <= top_rec.soil_climate_score <= 1.0
    assert 0.0 <= top_rec.history_rotation_score <= 1.0
    assert top_rec.crop in label_encoder.classes_ or top_rec.crop in all_crops
