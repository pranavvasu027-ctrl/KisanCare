"""Configuration settings for Disease & Pest AI Inference API."""

import os
from pathlib import Path
from typing import List

# Base Paths
API_DIR = Path(__file__).resolve().parent
MODULE_DIR = API_DIR.parent
PROJECT_ROOT = MODULE_DIR.parent

# Service Metadata
API_TITLE: str = "Agriculture AI — Disease & Pest Diagnostic Service"
API_DESCRIPTION: str = (
    "Production-grade FastAPI inference backend providing neural plant disease classification "
    "(EfficientNetV2-S), arthropod pest localization (YOLO11s), and statutory CIB&RC "
    "pesticide and non-chemical IPM recommendations."
)
API_VERSION: str = "1.0.0"

# Server Host & Port
API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
API_PORT: int = int(os.getenv("API_PORT", "8002"))

# Security / API Key
API_KEY: str = os.getenv("API_KEY", "kc_disease_pest_sec_key_2026_prod")
API_KEY_NAME: str = "X-API-Key"

# CORS Configuration
DEFAULT_ORIGINS = "http://localhost:3000,http://localhost:5173,http://localhost:8000,http://127.0.0.1:3000,http://127.0.0.1:5173,http://127.0.0.1:8000,*"
raw_origins = os.getenv("ALLOWED_ORIGINS", DEFAULT_ORIGINS)
ALLOWED_ORIGINS: List[str] = [orig.strip() for orig in raw_origins.split(",") if orig.strip()]

# Plant Leaf Image Validation Settings
VALIDATION_PLANT_THRESHOLD: float = float(os.getenv("VALIDATION_PLANT_THRESHOLD", "0.75"))
VALIDATION_LEAF_THRESHOLD: float = float(os.getenv("VALIDATION_LEAF_THRESHOLD", "0.75"))
VALIDATION_BLUR_THRESHOLD: float = float(os.getenv("VALIDATION_BLUR_THRESHOLD", "20.0"))
VALIDATION_MIN_DIMENSION: int = int(os.getenv("VALIDATION_MIN_DIMENSION", "128"))

