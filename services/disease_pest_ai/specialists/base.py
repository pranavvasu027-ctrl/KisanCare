"""Base interfaces and data structures for Multi-Crop Specialist Models.

Part of KisanCare Unified Multi-Model Crop Disease Intelligence System.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
from PIL import Image


@dataclass
class SpecialistCandidate:
    """Individual candidate pathology from specialist inference."""
    raw_condition: str
    canonical_condition: str
    canonical_label: str
    crop: str
    category: str  # 'disease' | 'healthy' | 'pest' | 'deficiency'
    raw_score: float  # Uncalibrated softmax score (0.0 to 1.0)
    calibrated_confidence: float  # Normalized / calibrated score
    percentage: int  # 0 to 100
    scientific_name: Optional[str] = None


@dataclass
class SpecialistPrediction:
    """Standardized prediction output from any specialist model adapter."""
    raw_condition: str
    canonical_condition: str
    canonical_label: str
    crop: str
    category: str  # 'disease' | 'healthy' | 'pest' | 'deficiency'
    raw_score: float
    calibrated_confidence: float
    percentage: int
    scientific_name: Optional[str] = None
    top_candidates: List[SpecialistCandidate] = field(default_factory=list)
    latency_ms: float = 0.0
    model_identifier: str = ""
    weights_hash: str = ""
    is_abstaining: bool = False
    abstention_reason: Optional[str] = None


class BaseSpecialistAdapter(ABC):
    """Abstract base class for all specialist crop disease model adapters."""

    model_identifier: str = "base-specialist"
    crop: str = "General"
    architecture: str = "Unknown"
    license: str = "Proprietary / Unknown"
    abstention_threshold: float = 0.40

    @abstractmethod
    def predict(self, image: Image.Image, requested_crop: Optional[str] = None) -> SpecialistPrediction:
        """Execute inference on a PIL image and return standardized SpecialistPrediction."""
        raise NotImplementedError

    @abstractmethod
    def is_available(self) -> bool:
        """Check whether the model weights and runtime dependencies are available."""
        raise NotImplementedError

    @abstractmethod
    def get_supported_classes(self) -> List[str]:
        """Return list of supported pathology / condition class names."""
        raise NotImplementedError

    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """Return model metadata, license, weights hash, provenance, and operational limits."""
        raise NotImplementedError
