"""
Soil Intelligence Evaluation, Continuous Comparator & Model Release Gate
========================================================================
Exports comparator and evaluation engines for pairwise comparison of predictions
against ground truth and leakage-safe holdout validation.
"""

from ml.soil_intelligence.evaluation.comparator import SoilContinuousComparator
from ml.soil_intelligence.evaluation.evaluator import SoilIntelligenceEvaluator

__all__ = [
    "SoilContinuousComparator",
    "SoilIntelligenceEvaluator",
]
