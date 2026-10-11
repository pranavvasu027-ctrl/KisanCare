"""Irrigation intelligence module."""

from models.irrigation.loader import load_irrigation_model
from models.irrigation.engine import (
    predict_irrigation,
    IrrigationResult,
    WaterBalanceMetrics,
    SOIL_PROPERTIES,
)

__all__ = [
    "load_irrigation_model",
    "predict_irrigation",
    "IrrigationResult",
    "WaterBalanceMetrics",
    "SOIL_PROPERTIES",
]
