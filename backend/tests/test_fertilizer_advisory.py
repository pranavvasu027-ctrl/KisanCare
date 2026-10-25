"""
Comprehensive verification tests for Real ML Fertilizer Advisory & Store Discovery.

Validates:
1. Model loading, revision pinning, and artifact checksums.
2. Real numerical Random Forest multi-output inference (DNgigi/FertiliserApplication).
3. Preprocessing ColumnTransformer and feature column integrity.
4. Input validation and handling of out-of-distribution crops.
5. Commercial formulation stoichiometry (Urea, DAP, MOP, Lime).
6. Strict independence from foliar disease pathology.
7. Store discovery ranking (village > pincode > district) and demo labeling.
8. Amazon.in search link generation and attribution.
9. FastAPI end-to-end endpoint contracts.
"""

import sys
from pathlib import Path
import pytest
from pydantic import ValidationError

# Ensure backend is on sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from backend.app.fertilizer.model_adapter import (
    HF_REPO_ID,
    PINNED_REVISION,
    EXPECTED_CHECKSUMS,
    NUMERICAL_TARGETS,
    SUPPORTED_TRAINING_CROPS,
    fertilizer_model_adapter,
)
from backend.app.fertilizer.schemas import FertilizerInput
from backend.app.fertilizer.service import fertilizer_service
from backend.app.fertilizer.store_service import find_matching_stores, build_amazon_discovery_links
from fastapi.testclient import TestClient
from backend.app.main import app


# 1. MODEL ARTIFACT AND REVISION PINNING
def test_model_artifact_loading_and_revision():
    """Verify DNgigi/FertiliserApplication loads correctly with pinned revision."""
    assert fertilizer_model_adapter.is_available() is True
    assert HF_REPO_ID == "DNgigi/FertiliserApplication"
    assert PINNED_REVISION == "5a38c5eda9989b72fe76cebf884da2e4acdb6971"
    assert "preprocessor.joblib" in EXPECTED_CHECKSUMS
    assert "numerical_model.joblib" in EXPECTED_CHECKSUMS


# 2. REAL ML NUMERICAL INFERENCE ON KNOWN SAMPLE
def test_real_model_inference_known_sample():
    """Verify real numerical multi-output Random Forest inference."""
    result = fertilizer_model_adapter.predict(
        crop_name="maize (corn)",
        target_yield_kg_ha=3600.0,
        field_size_ha=1.0,
        ph=6.1,
        organic_carbon=11.4,
        total_nitrogen=1.1,
        available_phosphorus=1.8,
        exchangeable_potassium=3.0,
    )

    preds = result["predictions"]
    assert isinstance(preds, dict)
    for target in NUMERICAL_TARGETS:
        assert target in preds
        assert isinstance(preds[target], float)
        assert preds[target] >= 0.0

    # Model predicts non-zero nutrient requirements for this deficient soil
    assert preds["Nitrogen (N) Need"] > 50.0
    assert preds["Phosphorus (P2O5) Need"] > 40.0
    assert preds["Organic Matter Need"] > 1000.0


# 3. PREPROCESSOR FEATURE INTEGRITY
def test_preprocessor_column_integrity():
    """Verify ColumnTransformer transformers and expected features."""
    fertilizer_model_adapter._ensure_loaded()
    prep = fertilizer_model_adapter.preprocessor
    num_cols = prep.transformers_[0][2]
    cat_cols = prep.transformers_[1][2]

    assert "Target Yield" in num_cols
    assert "Field Size" in num_cols
    assert "pH (water)" in num_cols
    assert "Organic Carbon" in num_cols
    assert "Total Nitrogen" in num_cols
    assert "Phosphorus (M3)" in num_cols
    assert "Potassium (exch.)" in num_cols
    assert cat_cols == ["Crop Name"]


# 4. DETERMINISTIC PREDICTIONS
def test_deterministic_predictions():
    """Verify that identical inputs produce identical numerical predictions."""
    p1 = fertilizer_model_adapter.predict("potato", 20000.0, 1.0, 6.5, 12.0, 1.4, 2.5, 3.5)
    p2 = fertilizer_model_adapter.predict("potato", 20000.0, 1.0, 6.5, 12.0, 1.4, 2.5, 3.5)
    assert p1["predictions"] == p2["predictions"]


# 5. OUT-OF-DISTRIBUTION CROPS AND ALKALINE SOIL
def test_unsupported_crop_and_alkaline_soil_warnings():
    """Verify out-of-distribution crops and alkaline soils produce warnings."""
    res = fertilizer_model_adapter.predict(
        crop_name="Dragonfruit",
        target_yield_kg_ha=5000.0,
        field_size_ha=2.0,
        ph=8.2,  # Alkaline soil
        organic_carbon=8.0,
        total_nitrogen=0.9,
        available_phosphorus=1.2,
        exchangeable_potassium=2.8,
    )
    assert res["is_in_training_distribution"] is False
    # Check that appropriate warnings were raised
    warns = res["warnings"]
    assert any("not part of the model's 5 core training crops" in w for w in warns)
    assert any("alkaline" in w for w in warns)
    # Regression prediction should still execute safely
    assert res["predictions"]["Nitrogen (N) Need"] >= 0.0


# 6. INPUT VALIDATION VIA PYDANTIC
def test_invalid_soil_inputs_rejected():
    """Verify invalid or extreme soil inputs fail validation."""
    with pytest.raises(ValidationError):
        FertilizerInput(
            crop_name="Corn",
            ph=14.5,  # Exceeds max pH 11.0
            organic_carbon=10.0,
            total_nitrogen=1.0,
            available_phosphorus=2.0,
            exchangeable_potassium=3.0,
        )

    with pytest.raises(ValidationError):
        FertilizerInput(
            crop_name="",  # Empty crop name
            ph=6.5,
            organic_carbon=10.0,
            total_nitrogen=1.0,
            available_phosphorus=2.0,
            exchangeable_potassium=3.0,
        )


# 7. COMMERCIAL FERTILIZER STOICHIOMETRY
def test_commercial_fertilizer_stoichiometry():
    """Verify conversion of N-P-K nutrient needs into commercial products."""
    inp = FertilizerInput(
        crop_name="Corn",
        target_yield=3600.0,
        field_size=1.0,
        ph=6.5,
        organic_carbon=11.4,
        total_nitrogen=1.1,
        available_phosphorus=1.8,
        exchangeable_potassium=3.0,
    )
    advisory = fertilizer_service.generate_advisory(inp)
    assert advisory.status == "success"
    assert len(advisory.commercial_recommendations) >= 2

    # Check that Urea and DAP are prescribed when N and P are needed
    names = [c.fertilizer_name for c in advisory.commercial_recommendations]
    assert any("DAP" in n for n in names)
    assert any("Urea" in n for n in names)
    for c in advisory.commercial_recommendations:
        assert c.dose_kg_ha > 0.0
        assert c.bags_50kg_per_ha > 0.0


# 8. DISEASE CONTEXT SEGREGATION SAFEGUARD
def test_disease_context_segregation():
    """Verify that disease context does not mutate fertilizer into a fungicide."""
    inp = FertilizerInput(
        crop_name="Tomato",
        ph=6.8,
        organic_carbon=12.0,
        total_nitrogen=1.2,
        available_phosphorus=2.0,
        exchangeable_potassium=3.0,
        disease_context="Tomato Early Blight (Foliar Scan)",
    )
    advisory = fertilizer_service.generate_advisory(inp)
    assert advisory.disease_context_notice is not None
    assert "independent" in advisory.disease_context_notice.lower()
    assert "fungal" in advisory.disease_context_notice.lower()
    assert advisory.is_experimental is True


# 9. LOCAL STORE DISCOVERY AND LOCALITY RANKING
def test_local_store_locality_ranking():
    """Verify store ranking: same village > same pincode > same district."""
    # When searching for Takli Bu (Akola)
    stores_akola = find_matching_stores(locality="Takli Bu", district="Akola", pin_code="444001")
    assert len(stores_akola) > 0
    top_store = stores_akola[0]
    assert top_store.locality_match_level == "same_village"
    assert top_store.village == "Takli Bu"
    assert top_store.is_demo_inventory is True
    assert "demo" in top_store.disclaimer.lower()

    # When searching for Pune PIN code
    stores_pune = find_matching_stores(pin_code="411037", district="Pune")
    assert len(stores_pune) > 0
    assert stores_pune[0].locality_match_level in ("same_pincode", "same_village")


# 10. AMAZON PRODUCT DISCOVERY LINKS
def test_amazon_product_discovery_links():
    """Verify Amazon.in search link generation with disclosures and no fake prices."""
    links = build_amazon_discovery_links(["Neem Coated Urea", "Di-Ammonium Phosphate (DAP)"])
    assert len(links) == 2
    for l in links:
        assert "amazon.in/s?k=" in l.amazon_search_url
        assert "Neem+Coated+Urea" in l.amazon_search_url or "Di-Ammonium" in l.amazon_search_url
        assert "Amazon.in" in l.attribution
        assert "vary on Amazon.in" in l.disclaimer


# 11. FASTAPI ENDPOINTS VIA TESTCLIENT
def test_fastapi_fertilizer_endpoints():
    """Verify /fertilizer-models and /fertilizer-advisory via FastAPI TestClient."""
    client = TestClient(app)

    # 1. GET model info
    r_info = client.get("/api/v1/fertilizer-models")
    assert r_info.status_code == 200
    info_data = r_info.json()
    assert info_data["model_identifier"] == "DNgigi/FertiliserApplication"
    assert info_data["is_available"] is True

    # 2. POST advisory
    payload = {
        "crop_name": "Corn",
        "target_yield": 4000.0,
        "field_size": 1.0,
        "ph": 6.8,
        "organic_carbon": 11.0,
        "total_nitrogen": 1.3,
        "available_phosphorus": 2.1,
        "exchangeable_potassium": 3.2,
        "locality": "Takli Bu",
        "district": "Akola",
        "pin_code": "444001",
    }
    r_adv = client.post("/api/v1/fertilizer-advisory", json=payload)
    assert r_adv.status_code == 200
    data = r_adv.json()
    assert data["status"] == "success"
    assert data["crop"] == "Corn"
    assert len(data["nutrient_requirements"]) >= 3
    assert len(data["matching_local_stores"]) >= 1
    assert len(data["amazon_discovery"]) >= 1

    # 3. GET stores endpoint
    r_stores = client.get("/api/v1/fertilizer-stores?district=Akola")
    assert r_stores.status_code == 200
    assert r_stores.json()["total"] >= 1
