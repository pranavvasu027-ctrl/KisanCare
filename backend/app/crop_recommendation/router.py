"""
Crop Recommendation FastAPI Router
==================================
REST endpoints for farmer upload-first crop recommendation pipeline:
- POST /crop-recommendation/recommend-from-report (Soil Health Card upload: PDF, JPG, PNG)
- POST /crop-recommendation/recommend (Direct JSON parameters)
"""

from __future__ import annotations
import os
from typing import Optional
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from .schemas import (
    CropRecommendationReportResponse,
    CropRecommendationJsonRequest,
)
from .service import CropRecommendationService

crop_rec_router = APIRouter(prefix="/crop-recommendation", tags=["Crop Recommendation"])
_service = CropRecommendationService()

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


@crop_rec_router.post(
    "/recommend-from-report",
    response_model=CropRecommendationReportResponse,
    summary="Upload soil test report (PDF, JPG, PNG) to receive top 3 crop recommendations",
)
@crop_rec_router.post(
    "/upload",
    response_model=CropRecommendationReportResponse,
    summary="Upload soil test report (PDF, JPG, PNG) to receive top 3 crop recommendations (alias)",
)
def recommend_from_soil_report(
    file: UploadFile = File(..., description="Soil test report (PDF, JPG, JPEG, PNG)"),
    farm_id: Optional[str] = Form(None, description="Optional parent farm identifier"),
    district: Optional[str] = Form(None, description="Optional override for Maharashtra district"),
    season: Optional[str] = Form(None, description="Optional override for farming season"),
    water_access: Optional[str] = Form(None, description="Optional irrigation access description"),
    ph_override: Optional[float] = Form(None, description="Optional verified pH if lab certificate did not test pH"),
    fallback_ph: Optional[float] = Form(None, description="Optional regional baseline pH used only if report omitted pH"),
):
    """
    Accepts a single soil laboratory report (PDF or image).
    Extracts soil parameters via OCR, retrieves regional historical climate context,
    and returns exactly the top three suitable crops with farmer-friendly reasons and labels.
    """
    filename = file.filename or "unknown"
    ext = os.path.splitext(filename)[1].lower()
    if ext not in [".pdf", ".jpg", ".jpeg", ".png"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Accepted formats are PDF, JPG, JPEG, and PNG.",
        )

    try:
        contents = file.file.read()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read uploaded file: {str(exc)}",
        )

    if len(contents) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is empty (0 bytes). Please upload a valid document.",
        )

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size ({len(contents) / (1024 * 1024):.2f} MB) exceeds the 5MB maximum limit.",
        )

    return _service.process_soil_report_and_recommend(
        file_bytes=contents,
        filename=filename,
        farm_id=farm_id,
        district=district,
        season=season,
        water_access=water_access,
        ph_override=ph_override,
        fallback_ph=fallback_ph,
    )


@crop_rec_router.post(
    "/recommend",
    response_model=CropRecommendationReportResponse,
    summary="Direct crop recommendation from numerical soil & environmental parameters",
)
def recommend_from_parameters(request: CropRecommendationJsonRequest):
    """Generates recommendations from direct JSON input parameters."""
    return _service.recommend_from_json(request)
