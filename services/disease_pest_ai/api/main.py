"""Main FastAPI Application Entry Point for Disease & Pest AI Microservice.

Provides RESTful inference APIs with statutory CIB&RC treatment advisory
and API key authentication.
Configured strictly for Cotton (DenseNet-121) and Soybean (ConvNeXt-Small) models.
"""

from contextlib import asynccontextmanager
import logging
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from disease_pest_ai.api.config import (
    ALLOWED_ORIGINS,
    API_DESCRIPTION,
    API_TITLE,
    API_VERSION,
)
from disease_pest_ai.api.routes.diagnose import router as diagnose_router, set_pipeline
from disease_pest_ai.api.routes.health import router as health_router
from disease_pest_ai.inference.pipeline import DiseasePestPipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("disease_pest_ai.api")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager: preload Cotton and Soybean specialists at startup."""
    logger.info("==================================================")
    logger.info("Starting Agriculture AI Disease & Pest Service")
    logger.info("Allowed CORS Origins: %s", ALLOWED_ORIGINS)
    logger.info("Foliar Disease Scope: Cotton & Soybean Specialists Only")
    logger.info("==================================================")

    try:
        pipeline = DiseasePestPipeline(
            primary_disease_model="specialist",
            primary_pest_model="yolo_pest",
            lazy_load=False,
        )
        set_pipeline(pipeline)
        logger.info("✓ Specialist models (Cotton DenseNet-121 + Soybean ConvNeXt-Small) and CIB&RC KB preloaded successfully.")
    except Exception as exc:
        logger.error("❌ Failed to preload inference models: %s", exc, exc_info=True)

    yield
    logger.info("Shutting down Agriculture AI Disease & Pest Service.")


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
app.include_router(diagnose_router)


@app.get("/", tags=["Root"])
async def root():
    """Root summary pointing to API docs and endpoints."""
    return {
        "service": API_TITLE,
        "version": API_VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
        "supported_crops": ["Cotton", "Soybean"],
        "endpoints": [
            {
                "method": "GET",
                "path": "/health",
                "auth_required": False,
                "description": "Service and models health status",
            },
            {
                "method": "POST",
                "path": "/api/v1/diagnose",
                "auth_required": True,
                "auth_header": "X-API-Key",
                "description": "Multi-modal disease diagnosis (Cotton & Soybean only), pest detection, and statutory CIB&RC treatment advisory",
            },
        ],
    }


if __name__ == "__main__":
    import uvicorn
    from disease_pest_ai.api.config import API_HOST, API_PORT

    uvicorn.run("disease_pest_ai.api.main:app", host=API_HOST, port=API_PORT, reload=False)
