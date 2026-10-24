"""Base interfaces and data structures for Specialist Crop Disease Models.

Part of KisanCare Unified Multi-Model Crop Disease Intelligence System.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
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
    top_candidates: List[SpecialistCandidate] = field(default_factory=list)
    latency_ms: float = 0.0
    model_identifier: str = ""
    provenance: Dict[str, Any] = field(default_factory=dict)


class BaseSpecialistAdapter(ABC):
    """Abstract interface that all specialist model adapters must implement."""

    @abstractmethod
    def load(self) -> None:
        """Load model weights and initialize inference transformations."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if model weights are loaded and ready for execution."""
        pass

    @abstractmethod
    def predict(self, pil_image: Image.Image) -> SpecialistPrediction:
        """Execute vision inference and return canonical SpecialistPrediction."""
        pass

    @abstractmethod
    def get_supported_classes(self) -> List[str]:
        """Return list of canonical disease conditions supported by this specialist."""
        pass

    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """Return detailed provenance, architecture, and metric metadata."""
        pass
