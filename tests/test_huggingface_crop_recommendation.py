"""Comprehensive tests for the Hugging Face Crop Recommendation Pipeline.

Validates:
- Artifact loading, initialization, and pinned revision.
- Exact feature order.
- Numerical boundary validation.
- Categorical handling (districts, aliases, seasons).
- Regional score lookup against 26-year historical records.
- Ranking, score decomposition, and suitability label derivation.
- Transparent water availability constraints.
- Error handling on missing artifacts and network failures (no silent fallback to fake predictions).
- API request/response compatibility across endpoints (/api/v1/crop-recommendation, /api/v1/recommend, /predict/crop).
"""

from __future__ import annotations

import os
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

from api.main import app as main_app
from ml.main import app as ml_app
from ml.crop_recommendation.huggingface_pipeline import (
    FEATURE_NAMES,
    PINNED_REVISION,
    SUPPORTED_DISTRICTS,
    SUPPORTED_SEASONS,
    CropRecommendationInput,
    CropRecommendationPipeline,
    InputValidationError,
    ModelUnavailableError,
    get_pipeline,
)
from ml.crop_recommendation.predict import (
    predict_crop_from_dict,
    predict_crop_recommendation,
)

main_client = TestClient(main_app)
ml_client = TestClient(ml_app)


class TestHuggingFacePipeline:
    """Core pipeline unit tests."""

    @pytest.fixture(autouse=True)
    def setup_pipeline(self):
        self.pipeline = get_pipeline()
        assert self.pipeline.is_ready, "Pipeline failed to initialize"

    def test_artifact_loading_and_initialization(self):
        """Verify model artifacts (model1_npk.pkl, model1_label_encoder.pkl, model2_full_scored.csv) are loaded."""
        assert self.pipeline.model1 is not None
        assert self.pipeline.label_enc1 is not None
        assert self.pipeline.model2_df is not None

        # Check revision
        assert self.pipeline.revision == PINNED_REVISION
        assert self.pipeline.revision == "f24d6e1666bb9efa530de8f4aec0124cd83c8cfd"

        # Check Model 1 classes
        assert len(self.pipeline.model1_classes) == 22
        assert "rice" in self.pipeline.model1_classes
        assert "cotton" in self.pipeline.model1_classes
        assert "maize" in self.pipeline.model1_classes

        # Check Model 2 regional dataset
        assert len(self.pipeline.model2_df) == 1603
        assert len(self.pipeline.model2_df["District"].unique()) == 35

    def test_correct_feature_order(self):
        """Verify the exact feature order expected by Model 1 Random Forest classifier."""
        expected_order = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]
        assert FEATURE_NAMES == expected_order

        # Verify Random Forest internal feature_names_in_ matches exactly
        if hasattr(self.pipeline.model1, "feature_names_in_"):
            actual_features = list(self.pipeline.model1.feature_names_in_)
            assert actual_features == expected_order

    def test_invalid_numerical_values(self):
        """Verify that out-of-range numerical values raise InputValidationError."""
        # Nitrogen out of bounds (< 0 or > 300)
        with pytest.raises(InputValidationError, match="Feature 'N'"):
            self.pipeline.validate_inputs(
                CropRecommendationInput(N=-5.0, P=40.0, K=40.0, temperature=25.0, humidity=70.0, ph=6.5, rainfall=700.0)
            )

        with pytest.raises(InputValidationError, match="Feature 'N'"):
            self.pipeline.validate_inputs(
                CropRecommendationInput(N=350.0, P=40.0, K=40.0, temperature=25.0, humidity=70.0, ph=6.5, rainfall=700.0)
            )

        # pH out of bounds (< 3.5 or > 9.5)
        with pytest.raises(InputValidationError, match="Feature 'ph'"):
            self.pipeline.validate_inputs(
                CropRecommendationInput(N=50.0, P=40.0, K=40.0, temperature=25.0, humidity=70.0, ph=2.0, rainfall=700.0)
            )

        with pytest.raises(InputValidationError, match="Feature 'ph'"):
            self.pipeline.validate_inputs(
                CropRecommendationInput(N=50.0, P=40.0, K=40.0, temperature=25.0, humidity=70.0, ph=11.5, rainfall=700.0)
            )

        # Temperature out of bounds (< 5 or > 50)
        with pytest.raises(InputValidationError, match="Feature 'temperature'"):
            self.pipeline.validate_inputs(
                CropRecommendationInput(N=50.0, P=40.0, K=40.0, temperature=55.0, humidity=70.0, ph=6.5, rainfall=700.0)
            )

        # Non-finite values (NaN / Inf)
        with pytest.raises(InputValidationError, match="must be a valid finite number"):
            self.pipeline.validate_inputs(
                CropRecommendationInput(N=float("nan"), P=40.0, K=40.0, temperature=25.0, humidity=70.0, ph=6.5, rainfall=700.0)
            )

    def test_unsupported_districts_and_seasons(self):
        """Verify handling of unsupported districts, seasons, and canonical aliases."""
        # Unsupported district outside Maharashtra generates advisory warning and defaults safely
        inp_unknown_dist = CropRecommendationInput(
            N=80.0, P=40.0, K=40.0, temperature=25.0, humidity=70.0, ph=6.5, rainfall=700.0,
            district="LondonDistrict"
        )
        resolved_dist, _, warnings_list = self.pipeline.validate_inputs(inp_unknown_dist)
        assert resolved_dist == "Nashik"
        assert any("LondonDistrict" in w for w in warnings_list)

        # Supported district aliases
        inp_alias = CropRecommendationInput(
            N=80.0, P=40.0, K=40.0, temperature=25.0, humidity=70.0, ph=6.5, rainfall=700.0,
            district="Aurangabad"
        )
        resolved_alias, _, _ = self.pipeline.validate_inputs(inp_alias)
        assert resolved_alias == "Chhatrapati Sambhajinagar"

        # Season alias (Zaid -> Summer)
        inp_season = CropRecommendationInput(
            N=80.0, P=40.0, K=40.0, temperature=25.0, humidity=70.0, ph=6.5, rainfall=700.0,
            season="Zaid"
        )
        _, resolved_season, _ = self.pipeline.validate_inputs(inp_season)
        assert resolved_season == "Summer"

    def test_regional_score_lookup(self):
        """Verify regional suitability score lookup matches historical census records."""
        result = self.pipeline.predict(
            CropRecommendationInput(
                N=90.0, P=42.0, K=43.0, temperature=26.0, humidity=70.0, ph=6.5, rainfall=720.0,
                district="Nashik", season="Kharif", top_k=10
            )
        )

        assert result.prediction is not None
        recs_by_crop = {r.crop.lower(): r for r in result.recommendations}

        # Nashik Kharif known high suitability crops
        assert "rice" in recs_by_crop or "maize" in recs_by_crop or "bajra" in recs_by_crop
        if "rice" in recs_by_crop:
            rice_rec = recs_by_crop["rice"]
            assert rice_rec.region_score > 0.65
            assert "Suitable" in rice_rec.region_suitability

    def test_ranking_and_score_interpretation(self):
        """Verify candidates are sorted descending by combined score and ranks are 1-based sequential."""
        result = self.pipeline.predict(
            CropRecommendationInput(
                N=100.0, P=50.0, K=50.0, temperature=28.0, humidity=65.0, ph=6.8, rainfall=600.0,
                district="Pune", season="Rabi", top_k=5
            )
        )

        assert len(result.recommendations) == 5
        scores = [r.combined_score for r in result.recommendations]
        assert scores == sorted(scores, reverse=True), "Recommendations must be sorted descending"

        # Check sequential ranks
        for idx, rec in enumerate(result.recommendations):
            assert rec.rank == idx + 1
            assert 0.0 <= rec.npk_score <= 1.0
            assert 0.0 <= rec.region_score <= 1.0
            assert 0.0 <= rec.combined_score <= 1.0
            # Ensure npk_score and region_score are distinct fields
            assert hasattr(rec, "npk_score")
            assert hasattr(rec, "region_score")

    def test_water_availability_constraint(self):
        """Verify transparent decision constraint for high-water crops in rainfed conditions."""
        # Sugarcane / Rice planted in strictly rainfed setting with low rainfall
        result = self.pipeline.predict(
            CropRecommendationInput(
                N=90.0, P=42.0, K=43.0, temperature=26.0, humidity=70.0, ph=6.5, rainfall=450.0,
                district="Solapur", season="Kharif", water_access="Strictly Rainfed (Dryland)", top_k=10
            )
        )

        constrained = [r for r in result.recommendations if r.water_constrained]
        # Any high water demand crop returned must have water_constrained flag
        for r in result.recommendations:
            if r.crop.lower() in ("sugarcane", "rice", "banana"):
                assert r.water_constrained is True
                assert "Water Advisory" in r.reason

    def test_missing_artifacts_and_network_failures(self):
        """Verify that failure to load model artifacts raises ModelUnavailableError without fake predictions."""
        with pytest.raises(ModelUnavailableError):
            CropRecommendationPipeline(
                repo_id="Sheshank2609/non-existent-repo-12345",
                revision="main",
                force_reload=True,
            )

    def test_no_silent_fallback_to_fabricated_predictions(self):
        """Verify that invalid inputs raise errors instead of returning fabricated predictions."""
        with pytest.raises(InputValidationError):
            predict_crop_from_dict({"N": -999, "P": 40, "K": 40})


class TestCropRecommendationAPIEndpoints:
    """API contract and integration tests."""

    def test_api_v1_crop_recommendation_endpoint(self):
        """Verify POST /api/v1/crop-recommendation returns expected schema and real scores."""
        payload = {
            "N": 90.0,
            "P": 42.0,
            "K": 43.0,
            "ph": 6.5,
            "temperature": 26.0,
            "humidity": 70.0,
            "rainfall": 720.0,
            "state": "Maharashtra",
            "district": "Nashik",
            "season": "Kharif",
            "top_k": 5,
        }

        response = main_client.post("/api/v1/crop-recommendation", json=payload)
        assert response.status_code == 200, f"Error: {response.text}"
        data = response.json()

        assert data["success"] is True
        assert data["model"] == "crop_recommendation"
        assert isinstance(data["prediction"], str)
        assert 0.0 <= data["final_score"] <= 1.0
        assert data["is_demo"] is False
        assert len(data["recommendations"]) == 5

        top_rec = data["recommendations"][0]
        assert top_rec["rank"] == 1
        assert "npk_score" in top_rec
        assert "region_score" in top_rec
        assert "region_suitability" in top_rec
        assert "grown_pct_of_years" in top_rec

        # Verify NPK status
        assert data["soil_test_npk_status"]["N"] in ("Low", "Medium", "High")
        assert data["soil_test_npk_status"]["P"] in ("Low", "Medium", "High")
        assert data["soil_test_npk_status"]["K"] in ("Low", "Medium", "High")

    def test_api_v1_recommend_backward_compatibility(self):
        """Verify backward compatibility of POST /api/v1/recommend."""
        payload = {
            "N": 80.0,
            "P": 40.0,
            "K": 40.0,
            "ph": 6.5,
            "temperature": 25.0,
            "humidity": 70.0,
            "rainfall": 750.0,
            "state": "Maharashtra",
            "district": "Pune",
            "season": "Rabi",
            "top_k": 3,
        }

        response = main_client.post("/api/v1/recommend", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["recommendations"]) == 3

    def test_ml_microservice_predict_crop_endpoint(self):
        """Verify ML microservice POST /predict/crop and /api/v1/crop-recommendation."""
        req_body = {
            "data": {
                "N": 90.0,
                "P": 42.0,
                "K": 43.0,
                "ph": 6.5,
                "temperature": 26.0,
                "humidity": 70.0,
                "rainfall": 720.0,
                "district": "Nashik",
                "season": "Kharif",
                "top_k": 3,
            }
        }

        response = ml_client.post("/predict/crop", json=req_body)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["is_demo"] is False
        assert len(data["recommendations"]) == 3

        # Test microservice health endpoint
        health_resp = ml_client.get("/health")
        assert health_resp.status_code == 200
        health_data = health_resp.json()
        assert health_data["models"]["crop_recommendation"]["loaded"] is True
        assert "Sheshank2609" in health_data["models"]["crop_recommendation"]["repo_id"]
