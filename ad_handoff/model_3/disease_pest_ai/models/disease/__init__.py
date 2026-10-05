"""
Disease adapters module.
"""

from disease_pest_ai.models.disease.efficientnet_adapter import EfficientNetDiseaseAdapter
from disease_pest_ai.models.disease.yolo_disease_adapter import YoloDiseaseAdapter

__all__ = ["EfficientNetDiseaseAdapter", "YoloDiseaseAdapter"]
