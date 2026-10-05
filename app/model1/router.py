from fastapi import APIRouter, HTTPException
import math
from .schemas import CropRecommendationRequest, CropRecommendationResponse
from .service import model1_service

router = APIRouter()

@router.post("/api/v1/model1/crop-recommendation", response_model=CropRecommendationResponse)
async def recommend_crop(request: CropRecommendationRequest):
    # Validate NaN/Infinity
    for field_name, value in request.model_dump().items():
        if math.isnan(value) or math.isinf(value):
            raise HTTPException(status_code=422, detail=f"Invalid numeric value for {field_name}. Cannot be NaN or Infinity.")

    try:
        result = model1_service.predict_top5(request.model_dump())
        return result
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail="Service Unavailable: Model not loaded.")
    except Exception as e:
        # Avoid exposing raw Python stack traces, return a generic safe error
        raise HTTPException(status_code=500, detail="Internal prediction error occurred.")
