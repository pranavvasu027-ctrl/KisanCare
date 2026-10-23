"""
KISANcare Soil Intelligence V1 - Prediction Architecture
=========================================================
Prediction orchestration, safe abstention gateway, uncertainty representation,
and ground-truth validation gates for historical soil intelligence.
"""

from ml.soil_intelligence.model.validation_gate import (
    ModelValidationGate,
    ModelValidationScope,
    ValidationGateDecision
)
from ml.soil_intelligence.model.uncertainty import (
    UncertaintyEngine,
    CalibrationStatus,
    UncertaintySourceType,
    SingleNutrientUncertainty,
    SoilUncertaintyBreakdown
)
from ml.soil_intelligence.model.abstention import (
    AbstentionEngine,
    AbstentionDecision,
    AbstentionReasonCode,
    RetestingUrgency
)
from ml.soil_intelligence.model.predictor import (
    SoilIntelligencePredictor,
    SoilIntelligenceReport,
    MODEL_VERSION
)

__all__ = [
    "ModelValidationGate",
    "ModelValidationScope",
    "ValidationGateDecision",
    "UncertaintyEngine",
    "CalibrationStatus",
    "UncertaintySourceType",
    "SingleNutrientUncertainty",
    "SoilUncertaintyBreakdown",
    "AbstentionEngine",
    "AbstentionDecision",
    "AbstentionReasonCode",
    "RetestingUrgency",
    "SoilIntelligencePredictor",
    "SoilIntelligenceReport",
    "MODEL_VERSION",
]
