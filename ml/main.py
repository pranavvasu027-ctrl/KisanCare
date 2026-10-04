import os
import joblib
import pandas as pd
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List

# Define absolute paths to models so it works no matter where uvicorn is run from
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "..", "models", "crop_recommendation", "crop_recommendation_model.pkl")
ENCODER_PATH = os.path.join(BASE_DIR, "..", "models", "crop_recommendation", "label_encoder.pkl")

ml_artifacts = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    if os.path.exists(MODEL_PATH) and os.path.exists(ENCODER_PATH):
        ml_artifacts["model"] = joblib.load(MODEL_PATH)
        ml_artifacts["encoder"] = joblib.load(ENCODER_PATH)
        print("Loaded crop recommendation models successfully.")
    else:
        print("Warning: Crop recommendation models not found. Prediction will fail.")
    yield
    ml_artifacts.clear()

app = FastAPI(title="KisanCare ML API", version="1.0.0", lifespan=lifespan)

class PredictionRequest(BaseModel):
    data: Dict[str, Any]

@app.post("/predict/crop")
def predict_crop(req: PredictionRequest):
    if "model" not in ml_artifacts or "encoder" not in ml_artifacts:
        raise HTTPException(status_code=503, detail="Models are not loaded.")

    model = ml_artifacts["model"]
    encoder = ml_artifacts["encoder"]

    # Extract data from request
    req_data = req.data
    
    # Check if we have exact features or if we need to mock them from soil_type/weather
    # Expected features: N, P, K, temperature, humidity, ph, rainfall
    feature_order = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]
    
    # Default values for missing features (e.g. if front-end only sends location/soil_type)
    default_values = {
        "N": 90.0, "P": 42.0, "K": 43.0, 
        "temperature": 25.0, "humidity": 80.0, 
        "ph": 6.5, "rainfall": 150.0
    }
    
    # If weather dict is present in data, try to extract temp/humidity
    weather = req_data.get("weather", {})
    if "temperature" in weather:
        default_values["temperature"] = float(weather["temperature"])
    if "humidity" in weather:
        default_values["humidity"] = float(weather["humidity"])
    if "rainfall" in weather:
        default_values["rainfall"] = float(weather["rainfall"])

    # Build the feature row
    row = []
    for col in feature_order:
        val = req_data.get(col, default_values[col])
        try:
            row.append(float(val))
        except (ValueError, TypeError):
            row.append(default_values[col])
            
    input_df = pd.DataFrame([row], columns=feature_order)
    
    try:
        probabilities = model.predict_proba(input_df)[0]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {exc}")

    # Top predictions
    top_3_idx = probabilities.argsort()[::-1][:3]
    top_3_crops = [encoder.classes_[i] for i in top_3_idx]
    best_idx = top_3_idx[0]
    recommended_crop = encoder.classes_[best_idx]
    confidence = float(probabilities[best_idx])
    
    factors = [f"Recommended alternatives: {top_3_crops[1]}, {top_3_crops[2]}"]
    limitations = ["Assuming default NPK values if not provided by soil sensor"]
    
    # Check if actual NPK was provided
    if not all(k in req_data for k in ["N", "P", "K"]):
        limitations.append("N, P, K values were estimated based on region defaults")

    return {
        "prediction": recommended_crop,
        "confidence": round(confidence, 4),
        "unit": "crop_type",
        "factors": factors,
        "limitations": limitations
    }

@app.post("/predict/yield")
def predict_yield(req: PredictionRequest):
    return {
        "prediction": 24,
        "confidence": 0.85,
        "unit": "quintals/hectare",
        "factors": ["Soil moisture", "Historical yield"],
        "limitations": ["DEMO DATA - NOT REAL PREDICTION"]
    }

@app.get("/health")
def health_check():
    status = "ok"
    if "model" in ml_artifacts:
        status = "ok with model loaded"
    return {"status": status}
