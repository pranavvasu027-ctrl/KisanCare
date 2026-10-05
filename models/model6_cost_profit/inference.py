import joblib
import pandas as pd
import os

MODEL_PATH = os.path.join(os.path.dirname(__file__), "artifacts", "cost_model.joblib")

# Strict pre-harvest input schema exactly matching training features
EXPECTED_FEATURES = {
    "State": str,
    "Crop": str,
    "Season": str,
    "Irrigation_Method": str,
    "Farm_Area_Hectares": float,
    "Rainfall_mm": float,
    "Avg_Temperature_C": float,
    "Humidity_pct": float,
    "Sunlight_Hours_Day": float,
    "Soil_pH": float,
    "Soil_Moisture_pct": float,
    "Nitrogen_kg_ha": float,
    "Phosphorus_kg_ha": float,
    "Potassium_kg_ha": float,
    "Fertilizer_kg_ha": float,
    "Pesticide_Litre_ha": float,
    "Seed_Quality_Score": float,
    "Water_Used_m3": float,
    "Water_Efficiency_t_per_1000m3": float,
    "Disease_Pest_Risk_pct": float
}

def validate_inputs(features: dict):
    # Check missing
    missing = [f for f in EXPECTED_FEATURES if f not in features]
    if missing:
        raise ValueError(f"Missing required features: {missing}")
        
    # Check types and logical ranges
    for f, expected_type in EXPECTED_FEATURES.items():
        val = features[f]
        # Allow ints for floats
        if expected_type == float and isinstance(val, int):
            val = float(val)
            features[f] = val
        if not isinstance(val, expected_type):
            raise TypeError(f"Feature {f} should be {expected_type.__name__}, got {type(val).__name__}")
            
    # Domain rules
    if features["Farm_Area_Hectares"] <= 0:
        raise ValueError("Farm_Area_Hectares must be > 0")
    if features["Rainfall_mm"] < 0:
        raise ValueError("Rainfall_mm cannot be negative")
    if features["Soil_pH"] < 0 or features["Soil_pH"] > 14:
        raise ValueError("Soil_pH must be between 0 and 14")
    for neg_check in ["Fertilizer_kg_ha", "Pesticide_Litre_ha", "Water_Used_m3", "Nitrogen_kg_ha", "Phosphorus_kg_ha", "Potassium_kg_ha"]:
        if features[neg_check] < 0:
            raise ValueError(f"{neg_check} cannot be negative")

def predict_cost(input_features: dict) -> dict:
    """
    Predicts the Total Cost and Cost/ha for a given farm profile.
    Returns farmer-facing API schema.
    """
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Model artifact not found at {MODEL_PATH}")
        
    # Validation throws ValueError/TypeError if fails
    validate_inputs(input_features)
    
    model = joblib.load(MODEL_PATH)
    df = pd.DataFrame([input_features])
    
    # Predict
    predicted_cost = model.predict(df)[0]
    predicted_cost = max(0.0, float(predicted_cost))
    
    area = input_features["Farm_Area_Hectares"]
    cost_per_ha = predicted_cost / area if area > 0 else 0.0
    
    return {
        "predicted_total_cost_inr": round(predicted_cost, 2),
        "predicted_cost_per_hectare_inr": round(cost_per_ha, 2),
        "model_status": "SUCCESS",
        "model_type": "HistGradientBoosting_Prototype"
    }
