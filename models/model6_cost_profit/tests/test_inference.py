import pytest
import copy
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from inference import predict_cost, EXPECTED_FEATURES

DEFAULT_FARM = {
    "State": "Maharashtra",
    "Crop": "Soybean",
    "Season": "Kharif",
    "Irrigation_Method": "Drip",
    "Farm_Area_Hectares": 2.0,
    "Rainfall_mm": 600.0,
    "Avg_Temperature_C": 28.0,
    "Humidity_pct": 65.0,
    "Sunlight_Hours_Day": 7.0,
    "Soil_pH": 6.8,
    "Soil_Moisture_pct": 45.0,
    "Nitrogen_kg_ha": 40.0,
    "Phosphorus_kg_ha": 20.0,
    "Potassium_kg_ha": 20.0,
    "Fertilizer_kg_ha": 80.0,
    "Pesticide_Litre_ha": 2.0,
    "Seed_Quality_Score": 8.0,
    "Water_Used_m3": 1500.0,
    "Water_Efficiency_t_per_1000m3": 1.5,
    "Disease_Pest_Risk_pct": 10.0
}

def test_valid_prediction():
    res = predict_cost(copy.deepcopy(DEFAULT_FARM))
    assert res["model_status"] == "SUCCESS"
    assert res["predicted_total_cost_inr"] >= 0
    assert res["predicted_cost_per_hectare_inr"] >= 0

def test_missing_feature():
    f = copy.deepcopy(DEFAULT_FARM)
    del f["Crop"]
    with pytest.raises(ValueError, match="Missing required features"):
        predict_cost(f)

def test_zero_area():
    f = copy.deepcopy(DEFAULT_FARM)
    f["Farm_Area_Hectares"] = 0.0
    with pytest.raises(ValueError, match="Farm_Area_Hectares must be > 0"):
        predict_cost(f)

def test_negative_input():
    f = copy.deepcopy(DEFAULT_FARM)
    f["Rainfall_mm"] = -10.0
    with pytest.raises(ValueError, match="cannot be negative"):
        predict_cost(f)
        
def test_unknown_category():
    f = copy.deepcopy(DEFAULT_FARM)
    f["Crop"] = "UnknownAlienCrop"
    res = predict_cost(f)
    assert res["model_status"] == "SUCCESS" # Should handle unknown smoothly
