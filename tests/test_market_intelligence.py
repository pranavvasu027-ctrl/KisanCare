import os
import sys

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
backend_dir = os.path.join(repo_root, "backend")

if repo_root not in sys.path:
    sys.path.insert(0, repo_root)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import pytest
from fastapi.testclient import TestClient
from app.main import app
from ml.market_price.predict import MarketPricePredictor, haversine_km, normalize_crop_controlled, VERIFIED_MANDIS

client = TestClient(app)

def test_cotton_prediction_direct():
    predictor = MarketPricePredictor()
    res = predictor.predict(
        crop="Cotton",
        quantity=20.0,
        farmer_lat=20.7002,
        farmer_lon=77.0082
    )
    assert res["status"] == "success"
    assert res["crop"] == "Cotton"
    assert res["quantity_quintals"] == 20.0
    assert "recommended_market" in res
    rec = res["recommended_market"]
    assert rec["current_price"] > 0
    assert rec["net_price_per_qtl"] <= rec["current_price"]
    assert rec["estimated_road_km"] > rec["straight_line_km"]
    assert res["expected_amount"] == round(20.0 * rec["net_price_per_qtl"], 2)
    assert "forecast_7d" in res and res["forecast_7d"]["expected_price"] > 0
    assert "forecast_14d" in res and res["forecast_14d"]["expected_price"] > 0
    assert "forecast_28d" in res and res["forecast_28d"]["expected_price"] > 0
    assert len(res["markets"]) >= 3
    assert res["confidence"] in ["High Confidence", "Medium Confidence", "Baseline / Historical Confidence"]
    assert "price_type" in res and "modal price" in res["price_type"].lower()

def test_tur_prediction_direct():
    predictor = MarketPricePredictor()
    res = predictor.predict(
        crop="Tur",
        quantity=15.0,
        farmer_lat=20.7002,
        farmer_lon=77.0082
    )
    assert res["status"] == "success"
    assert res["crop"] == "Tur"
    assert res["quantity_quintals"] == 15.0
    assert "recommended_market" in res
    rec = res["recommended_market"]
    assert rec["current_price"] > 0
    assert res["expected_amount"] == round(15.0 * rec["net_price_per_qtl"], 2)
    assert "forecast_7d" in res and res["forecast_7d"]["expected_price"] > 0
    assert "forecast_14d" in res and res["forecast_14d"]["expected_price"] > 0
    assert "forecast_28d" in res and res["forecast_28d"]["expected_price"] > 0
    assert len(res["markets"]) >= 3
    assert "Akola APMC" in [m["name"] for m in res["markets"]]

def test_controlled_crop_normalization():
    assert normalize_crop_controlled("Cotton") == "Cotton"
    assert normalize_crop_controlled("cotton") == "Cotton"
    assert normalize_crop_controlled("KAPAS") == "Cotton"
    assert normalize_crop_controlled("कापूस") == "Cotton"
    assert normalize_crop_controlled("Tur") == "Tur"
    assert normalize_crop_controlled("tur") == "Tur"
    assert normalize_crop_controlled("pigeon pea") == "Tur"
    assert normalize_crop_controlled("arhar") == "Tur"
    assert normalize_crop_controlled("तूर") == "Tur"
    
    # Must NOT match partial substrings like turmeric or turnip
    assert normalize_crop_controlled("turmeric") == "Unsupported"
    assert normalize_crop_controlled("turnip") == "Unsupported"
    assert normalize_crop_controlled("Soybean") == "Unsupported"
    assert normalize_crop_controlled("Wheat") == "Unsupported"

def test_fastapi_endpoint_cotton_e2e():
    payload = {
        "crop": "Cotton",
        "quantity": 25.0,
        "latitude": 20.7002,
        "longitude": 77.0082
    }
    response = client.post("/api/v1/market-price", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["crop"] == "Cotton"
    assert data["quantity_quintals"] == 25.0
    assert data["expected_amount"] > 0
    assert "Dhamangaon APMC" in [m["name"] for m in data["markets"]]

def test_fastapi_endpoint_tur_e2e():
    payload = {
        "crop": "Tur",
        "quantity": 10.0,
        "latitude": 20.7002,
        "longitude": 77.0082
    }
    response = client.post("/api/v1/market-price", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["crop"] == "Tur"
    assert data["quantity_quintals"] == 10.0
    assert data["expected_amount"] > 0
    assert "Akola APMC" in [m["name"] for m in data["markets"]]

def test_unsupported_crop_fails_gracefully():
    # Only Cotton and Tur are supported
    payload = {"crop": "Tomato", "quantity": 10.0}
    response = client.post("/api/v1/market-price", json=payload)
    assert response.status_code in (404, 422)
    assert "not supported" in response.text.lower() or "cotton and tur" in response.text.lower()

def test_turmeric_rejected_gracefully():
    payload = {"crop": "turmeric", "quantity": 10.0}
    response = client.post("/api/v1/market-price", json=payload)
    assert response.status_code in (404, 422)

def test_soybean_rejected_gracefully():
    payload = {"crop": "Soybean", "quantity": 10.0}
    response = client.post("/api/v1/market-price", json=payload)
    assert response.status_code in (404, 422)

def test_negative_quantity_rejected_with_422():
    payload = {"crop": "Cotton", "quantity": -5.0}
    response = client.post("/api/v1/market-price", json=payload)
    assert response.status_code == 422

def test_zero_quantity_rejected_with_422():
    payload = {"crop": "Cotton", "quantity": 0.0}
    response = client.post("/api/v1/market-price", json=payload)
    assert response.status_code == 422

def test_exorbitant_quantity_rejected_with_422():
    payload = {"crop": "Cotton", "quantity": 100000.0}
    response = client.post("/api/v1/market-price", json=payload)
    assert response.status_code == 422

def test_missing_location_fallback():
    predictor = MarketPricePredictor()
    res = predictor.predict(crop="Cotton", quantity=20.0, farmer_lat=None, farmer_lon=None)
    assert res["status"] == "success"
    assert res["farmer_location"]["is_fallback"] is True
    assert res["farmer_location"]["latitude"] == 20.7002

def test_haversine_distance():
    dist = haversine_km(20.7002, 77.0082, 20.9374, 77.7796)
    assert 80 <= dist <= 90

def test_transport_deduction_affects_recommendation():
    predictor = MarketPricePredictor()
    res = predictor.predict(crop="Cotton", quantity=20.0, farmer_lat=20.7002, farmer_lon=77.0082)
    rec = res["recommended_market"]
    expected_net = round(max(0.0, rec["current_price"] - rec["transport_cost_per_qtl"]), 2)
    assert round(rec["net_price_per_qtl"], 2) == expected_net

def test_sell_decision_engine_has_explicit_reason():
    predictor = MarketPricePredictor()
    res = predictor.predict(crop="Cotton", quantity=20.0, farmer_lat=20.7002, farmer_lon=77.0082)
    assert "recommended_sell_window" in res
    assert "sell_action" in res
    assert "sell_advice_reason" in res
    assert len(res["sell_advice_reason"]) > 10
