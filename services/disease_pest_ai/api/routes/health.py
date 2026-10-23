"""Health check and service status routes."""

from fastapi import APIRouter
from disease_pest_ai.api.config import API_VERSION

router = APIRouter(tags=["Health"])


@router.get("/health", summary="Health Check")
async def health_check():
    """Returns runtime health status and model availability."""
    return {
        "status": "healthy",
        "service": "Agriculture AI — Disease & Pest Diagnostic Service",
        "version": API_VERSION,
        "models": {
            "disease_classifier": "EfficientNetV2-S (PlantVillage)",
            "pest_detector": "YOLO11s (IP102)",
            "knowledge_base": "CIB&RC Statutory Register 2024-03-31",
            "explainability": "Grad-CAM + Bounding Box Overlays",
        },
    }
