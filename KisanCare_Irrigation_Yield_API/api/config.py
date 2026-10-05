"""Configuration settings for the KisanCare Inference API."""

import os
from typing import List

API_TITLE: str = "KisanCare Dual Inference Service (Irrigation & Crop Yield)"
API_DESCRIPTION: str = (
    "Production-grade FastAPI inference backend providing precision irrigation "
    "scheduling (FAO-56 physical water balance + ETo LSTM) and India crop yield "
    "prediction (Random Forest Regressor) for existing application frontends."
)
API_VERSION: str = "1.0.0"

API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
API_PORT: int = int(os.getenv("API_PORT", "8000"))

# Allowed origins for CORS (configurable via comma-separated string)
DEFAULT_ORIGINS = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173"
raw_origins = os.getenv("ALLOWED_ORIGINS", DEFAULT_ORIGINS)
ALLOWED_ORIGINS: List[str] = [orig.strip() for orig in raw_origins.split(",") if orig.strip()]

# Hugging Face Model settings
CROP_YIELD_REPO_ID: str = os.getenv("CROP_YIELD_REPO_ID", "NIHAL670/Crop-yield")
HF_TOKEN: str = os.getenv("HF_TOKEN", "")
