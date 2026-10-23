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

    def test_empty_regional_results_handling(self):
        """Verify that district/season combinations missing from Model 2 regional table
        (e.g., Mumbai suburban in Kharif) handle gracefully with explicit warnings and no crash."""
        result = self.pipeline.predict(
            CropRecommendationInput(
                N=85.0, P=45.0, K=40.0, temperature=28.0, humidity=75.0, ph=6.2, rainfall=800.0,
                district="Mumbai suburban", season="Kharif", top_k=5
            )
        )
        assert result.prediction is not None
        assert len(result.recommendations) == 5
        assert any("No historical agricultural records found in Model 2 regional table" in w for w in result.warnings)
        # All regional scores should default to 0.0 with explicit label
        for rec in result.recommendations:
            assert rec.region_score == 0.0
            assert "Unverified in" in rec.region_suitability or rec.region_suitability == "No regional data"
            assert rec.npk_score >= 0.0

    def test_ranking_reproducibility(self):
        """Verify that identical inputs produce perfectly reproducible ranks, scores, and recommendations."""
        inp = CropRecommendationInput(
            N=92.0, P=44.0, K=41.0, temperature=27.5, humidity=68.0, ph=6.6, rainfall=690.0,
            district="Nashik", season="Kharif", top_k=5
        )
        run1 = self.pipeline.predict(inp)
        run2 = self.pipeline.predict(inp)

        assert run1.prediction == run2.prediction
        assert [r.crop for r in run1.recommendations] == [r.crop for r in run2.recommendations]
        assert [r.combined_score for r in run1.recommendations] == [r.combined_score for r in run2.recommendations]
        assert [r.npk_score for r in run1.recommendations] == [r.npk_score for r in run2.recommendations]
        assert [r.region_score for r in run1.recommendations] == [r.region_score for r in run2.recommendations]

    def test_score_decomposition_and_formula(self):
        """Verify that combined score is the exact weighted blend of Model 1 RF and Model 2 Regional."""
        w1 = 0.70
        inp = CropRecommendationInput(
            N=90.0, P=40.0, K=40.0, temperature=26.0, humidity=70.0, ph=6.5, rainfall=700.0,
            district="Pune", season="Kharif", w_model1=w1, top_k=5
        )
        result = self.pipeline.predict(inp)
        for rec in result.recommendations:
            expected = round(w1 * rec.npk_score + (1.0 - w1) * rec.region_score, 4)
            assert abs(rec.combined_score - expected) <= 1e-4

    def test_unexpected_model_failure_never_returns_fake_predictions(self):
        """Verify that if model inference raises an unexpected exception, the pipeline fails and never returns fake data."""
        with patch.object(self.pipeline.model1, "predict_proba", side_effect=RuntimeError("Corrupted model memory")):
            with pytest.raises(Exception):
                self.pipeline.predict(
                    CropRecommendationInput(
                        N=90.0, P=42.0, K=43.0, temperature=26.0, humidity=70.0, ph=6.5, rainfall=720.0
                    )
                )

    def test_regional_evidence_safeguard_coffee_suppression(self):
        """Verify that crops lacking regional historical presence (e.g., Coffee in Sangli)
        are categorized as Biophysical Candidates with 50% discount and do not rank #1."""
        inp = CropRecommendationInput(
            N=105.0, P=30.0, K=55.0, temperature=35.0, humidity=68.0, ph=7.0, rainfall=900.0,
            district="Sangli", season="Kharif", top_k=22
        )
        result = self.pipeline.predict(inp)

        # 1. Top prediction must be a regionally proven crop (e.g. Rice), not Coffee
        assert result.prediction != "Coffee"
        assert result.prediction == "Rice"

        # 2. Coffee must be marked unverified with 50% discount
        coffee_rec = next((r for r in result.recommendations if r.crop.lower() == "coffee"), None)
        assert coffee_rec is not None
        assert coffee_rec.is_regionally_supported is False
        assert coffee_rec.evidence_tier == "Biophysical Candidate Only (Unverified in Sangli)"
        assert "Unverified in Sangli (0 Census Records)" in coffee_rec.region_suitability
        assert coffee_rec.rank > 5, f"Coffee rank should be suppressed, got {coffee_rec.rank}"

        # 3. Proven Sangli crops (Rice, Jowar, Bajra) must be ranked above Coffee
        rice_rec = next(r for r in result.recommendations if r.crop.lower() == "rice")
        assert rice_rec.is_regionally_supported is True
        assert rice_rec.rank < coffee_rec.rank

        # 4. Regional safeguard warning must be emitted
        assert any("Regional Evidence Safeguard" in w for w in result.warnings)

    def test_scientific_extrapolation_warnings(self):
        """Verify that inputs exceeding Model 1 training distribution (K > 205, Rainfall > 300) emit clear warnings."""
        inp = CropRecommendationInput(
            N=90.0, P=45.0, K=350.0, temperature=26.0, humidity=70.0, ph=6.5, rainfall=750.0,
            district="Pune", season="Kharif", top_k=5
        )
        result = self.pipeline.predict(inp)
        assert any("Measured soil Potassium (350.0 kg/ha) exceeds Model 1 training maximum" in w for w in result.warnings)
        assert any("Rainfall (750.0 mm) exceeds Model 1 training maximum (298.6 mm)" in w for w in result.warnings)


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

    def test_missing_and_invalid_inputs_rejected_by_api(self):
        """Verify that missing soil or climate measurements are rejected with 422 and never invented."""
        # Missing N
        resp = main_client.post("/api/v1/crop-recommendation", json={
            "P": 42.0, "K": 43.0, "ph": 6.5, "rainfall": 720.0, "temperature": 26.0, "humidity": 70.0
        })
        assert resp.status_code == 422

        # Missing rainfall
        resp = main_client.post("/api/v1/crop-recommendation", json={
            "N": 90.0, "P": 42.0, "K": 43.0, "ph": 6.5, "temperature": 26.0, "humidity": 70.0
        })
        assert resp.status_code == 422

        # Missing temperature
        resp = main_client.post("/api/v1/crop-recommendation", json={
            "N": 90.0, "P": 42.0, "K": 43.0, "ph": 6.5, "rainfall": 720.0, "humidity": 70.0
        })
        assert resp.status_code == 422

        # Missing humidity
        resp = main_client.post("/api/v1/crop-recommendation", json={
            "N": 90.0, "P": 42.0, "K": 43.0, "ph": 6.5, "rainfall": 720.0, "temperature": 26.0
        })
        assert resp.status_code == 422

    def test_service_unavailability_returns_503(self):
        """Verify that when ModelUnavailableError is raised, the API returns a 503 Service Unavailable."""
        with patch("api.services.crop_service.crop_recommendation_service.predict", side_effect=ModelUnavailableError("Model weights corrupted")):
            resp = main_client.post("/api/v1/crop-recommendation", json={
                "N": 90.0, "P": 42.0, "K": 43.0, "ph": 6.5, "rainfall": 720.0, "temperature": 26.0, "humidity": 70.0
            })
            assert resp.status_code == 503
            assert "Model weights corrupted" in resp.json()["detail"]
