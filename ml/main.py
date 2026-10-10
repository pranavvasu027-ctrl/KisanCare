import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware
import time

from ml.crop_recommendation.predict import PredictionPipeline
from ml.routers import farms
from ml.routers import models_api

pipeline_instance = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global pipeline_instance
    try:
        pipeline_instance = PredictionPipeline()
        print("Model 1 Pipeline initialized successfully.")
    except Exception as e:
        print(f"Warning: Failed to initialize Model 1 Pipeline. {e}")
    yield
    pipeline_instance = None

app = FastAPI(title="KisanCare API", version="1.0.0", lifespan=lifespan)
app.include_router(farms.router)
app.include_router(models_api.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CropRequest(BaseModel):
    district: str = Field(..., example="NASHIK")
    season: str = Field(..., example="Kharif")
    water_availability: str = Field(..., example="Medium")
    top_k: int = Field(5, ge=1, le=20, example=5)
    
    @validator('season')
    def validate_season(cls, v):
        valid = ['Kharif', 'Rabi', 'Summer', 'Whole Year']
        if v not in valid:
            raise ValueError(f"Season must be one of: {', '.join(valid)}")
        return v
        
    @validator('water_availability')
    def validate_water(cls, v):
        valid = ['Low', 'Medium', 'High']
        if v not in valid:
            raise ValueError(f"Water availability must be one of: {', '.join(valid)}")
        return v

@app.get("/health")
def health_check():
    if pipeline_instance and pipeline_instance.model:
        return {
            "status": "healthy",
            "model_version": pipeline_instance.metadata.get("model_version", "unknown")
        }
    return {"status": "unhealthy"}

@app.get("/api/v1/crop-recommendation/meta")
def get_metadata():
    if not pipeline_instance or not pipeline_instance.metadata:
        raise HTTPException(status_code=503, detail="Model metadata not available.")
    
    return {
        "model_version": pipeline_instance.metadata.get("model_version"),
        "target": pipeline_instance.metadata.get("target"),
        "supported_crops": len(pipeline_instance.cat_levels.get("Crop", [])),
        "supported_seasons": pipeline_instance.cat_levels.get("Season", []),
        "water_levels": ["Low", "Medium", "High"],
        "data_source": "APY_2005_2015"
    }

@app.post("/api/v1/crop-recommendation")
def recommend_crops_endpoint(req: CropRequest):
    if not pipeline_instance:
        raise HTTPException(status_code=500, detail="Prediction pipeline is not initialized.")
        
    result = pipeline_instance.recommend(
        district=req.district.upper(),
        season=req.season,
        water_availability=req.water_availability,
        top_k=req.top_k
    )
    
    if result.get("status") == "ERROR":
        # Usually validation errors like unknown district
        raise HTTPException(status_code=404 if "Unknown district" in result["reason"] else 422, 
                            detail=result["reason"])
                            
    return result

