"""KisanCare Integrated Inference Service (Irrigation, Crop Yield, Crop Recommendation & Disease Detection).

FastAPI backend exposing precision irrigation scheduling (FAO-56 + ETo LSTM),
Indian crop yield prediction (Random Forest Regressor),
Hugging Face Dual-Model Crop Recommendation,
and Authentic Plant Pathology Disease Detection (EfficientNetV2-S + CIBRC Engine).
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import (
    ALLOWED_ORIGINS,
    API_DESCRIPTION,
    API_TITLE,
    API_VERSION,
)
from api.routes.health import router as health_router
from api.routes.irrigation import router as irrigation_router
from api.routes.yield_route import router as yield_router
from api.routes.crop_route import router as crop_router
from api.routes.disease_route import router as disease_router
from api.services.irrigation_service import irrigation_service
from api.services.yield_service import yield_service
from api.services.crop_service import crop_recommendation_service
from api.services.disease_service import disease_detection_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("kisancare.api")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager: preload models into memory at startup."""
    logger.info("==================================================")
    logger.info("Starting KisanCare Integrated Inference Service")
    logger.info("Allowed CORS Origins: %s", ALLOWED_ORIGINS)
    logger.info("==================================================")

    # 1. Preload Irrigation Model
    try:
        irrigation_service.initialize()
        logger.info("Irrigation Model preloaded successfully.")
    except Exception as exc:
        logger.error("Failed to preload Irrigation Model: %s", str(exc), exc_info=True)

    # 2. Preload Crop Yield Model
    try:
        yield_service.initialize()
        logger.info("Crop Yield Model preloaded successfully.")
    except Exception as exc:
        logger.error("Failed to preload Crop Yield Model: %s", str(exc), exc_info=True)

    # 3. Preload Crop Recommendation Model
    try:
        crop_recommendation_service.initialize()
        logger.info("Crop Recommendation Model preloaded successfully.")
    except Exception as exc:
        logger.error("Failed to preload Crop Recommendation Model: %s", str(exc), exc_info=True)

    # 4. Preload Plant Disease Detection Model
    try:
        disease_detection_service.initialize()
        logger.info("Plant Disease Detection Model preloaded successfully.")
    except Exception as exc:
        logger.error("Failed to preload Plant Disease Detection Model: %s", str(exc), exc_info=True)

    logger.info("All AI services initialized and ready to serve traffic.")
    yield
    logger.info("Shutting down KisanCare Inference Service.")


app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Register routes
app.include_router(health_router)
app.include_router(irrigation_router)
app.include_router(yield_router)
app.include_router(crop_router)
app.include_router(disease_router)

# Also mount core backend endpoints (Digital Twin, Simulator, Economics) so that
# running `uvicorn api.main:app` serves the full unified platform.
try:
    import sys
    from pathlib import Path
    backend_dir = Path(__file__).resolve().parent.parent / "backend"
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))
    from app.api.endpoints import router as backend_endpoints_router
    app.include_router(backend_endpoints_router, prefix="/api/v1")
    app.include_router(backend_endpoints_router, prefix="/api")
    logger.info("Mounted backend endpoints (Digital Twin, Simulator, Economics) into unified API.")
except Exception as exc:
    logger.warning("Backend endpoints not mounted into api/main.py: %s", exc)


@app.get("/", tags=["Root"])
async def root():
    """Root status summary pointing to documentation."""
    return {
        "service": "KisanCare Dual Inference Service",
        "version": API_VERSION,
        "docs": "/docs",
        "endpoints": [
            {"method": "GET", "path": "/health", "desc": "Service and models health status"},
            {"method": "POST", "path": "/api/irrigation/predict", "desc": "Irrigation scheduling & water balance"},
            {"method": "POST", "path": "/api/yield/predict", "desc": "Crop yield & total harvest prediction"},
            {"method": "POST", "path": "/api/crop/recommend", "desc": "Crop recommendation with multi-layer agronomic scoring"},
            {"method": "POST", "path": "/api/v1/recommend", "desc": "AD Handoff crop recommendation endpoint"},
            {"method": "POST", "path": "/api/disease/predict", "desc": "Authentic plant disease foliar prediction (Multipart)"},
            {"method": "POST", "path": "/api/disease/predict/json", "desc": "Authentic plant disease foliar prediction (JSON Base64)"},
            {"method": "POST", "path": "/api/v1/disease-detection", "desc": "Frontend integrated disease detection endpoint"},
            {"method": "GET", "path": "/api/disease/status", "desc": "Disease model readiness & classes"},
        ],
    }


if __name__ == "__main__":
    import uvicorn
    from api.config import API_HOST, API_PORT

    uvicorn.run("api.main:app", host=API_HOST, port=API_PORT, reload=False)
