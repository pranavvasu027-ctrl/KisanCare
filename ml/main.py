from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any, List

app = FastAPI(title="KisanCare ML API", version="1.0.0")

class PredictionRequest(BaseModel):
    data: Dict[str, Any]

@app.post("/predict/crop")
def predict_crop(req: PredictionRequest):
    # Mock ML implementation
    # In reality, this would load a scikit-learn model and predict
    return {
        "prediction": "Soybean",
        "confidence": 0.82,
        "unit": "crop_type",
        "factors": ["Current rainfall conditions are suitable", "Expected production cost is lower"],
        "limitations": ["DEMO DATA - NOT REAL PREDICTION"]
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
    return {"status": "ok"}
