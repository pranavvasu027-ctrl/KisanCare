"""KisanCare Dual Inference Service (Irrigation & Crop Yield).

FastAPI backend exposing precision irrigation scheduling (FAO-56 + ETo LSTM)
and Indian crop yield prediction (Random Forest Regressor) for application frontends.
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
from api.services.irrigation_service import irrigation_service
from api.services.yield_service import yield_service

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
    logger.info("Starting KisanCare Dual Inference Service")
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

    logger.info("All AI services initialized and ready to serve traffic.")
    yield
    logger.info("Shutting down KisanCare Dual Inference Service.")


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
        ],
    }


if __name__ == "__main__":
    import uvicorn
    from api.config import API_HOST, API_PORT

    uvicorn.run("api.main:app", host=API_HOST, port=API_PORT, reload=False)
