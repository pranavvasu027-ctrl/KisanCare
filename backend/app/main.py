import logging
import os
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Ensure root directory is in sys.path if running from root
root_dir = backend_dir.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

try:
    from app.api import endpoints
except ModuleNotFoundError:
    from backend.app.api import endpoints

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("kisancare.backend")

app = FastAPI(
    title="KisanCare Backend API",
    version="1.0.0",
    description="Unified backend providing Digital Twin state, What-If simulation, economics ledger, and ML model integration."
)

# CORS configuration
DEFAULT_ORIGINS = (
    "http://localhost:3000,http://localhost:5173,http://localhost:5174,"
    "http://127.0.0.1:3000,http://127.0.0.1:5173,http://127.0.0.1:5174"
)
raw_origins = os.getenv("ALLOWED_ORIGINS", DEFAULT_ORIGINS)
origins = [orig.strip() for orig in raw_origins.split(",") if orig.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Core endpoints under both /api/v1 and /api
app.include_router(endpoints.router, prefix="/api/v1")
app.include_router(endpoints.router, prefix="/api")

# Conditionally mount verified ML routers if packages and models are present
try:
    from api.routes.irrigation import router as irrigation_router
    from api.routes.yield_route import router as yield_router
    from api.routes.crop_route import router as crop_router
    from api.services.irrigation_service import irrigation_service
    from api.services.yield_service import yield_service
    from api.services.crop_service import crop_recommendation_service

    app.include_router(irrigation_router)
    app.include_router(yield_router)
    app.include_router(crop_router)
    logger.info("Successfully mounted verified ML models (Irrigation, Yield & Crop Recommendation) directly in backend.")
except ImportError as exc:
    logger.info("Standalone ML models not loaded into backend directly (%s). Running in microservice mode.", exc)


@app.get("/health", tags=["Health"])
@app.get("/api/health", tags=["Health"])
def health_check():
    return {
        "status": "ok",
        "service": "kisancare-backend",
        "version": "1.0.0"
    }
