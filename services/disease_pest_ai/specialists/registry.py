"""Specialist Model Registry.

Manages configuration-driven registration, lifecycle, and access to crop-specific
specialist model adapters.
Part of KisanCare Unified Multi-Model Crop Disease Intelligence System.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from disease_pest_ai.specialists.base import BaseSpecialistAdapter
from disease_pest_ai.specialists.cotton.adapter import CottonDenseNetAdapter
from disease_pest_ai.specialists.soybean.adapter import SoybeanConvNeXtAdapter
from disease_pest_ai.specialists.generalist.adapter import GeneralistEfficientNetAdapter
from disease_pest_ai.specialists.yolo.adapter import YoloSpecialistAdapter
from disease_pest_ai.models.pest.yolo_pest_adapter import YoloPestAdapter

logger = logging.getLogger("kisancare.specialists.registry")

CONFIG_PATH = Path(__file__).resolve().parent / "specialists_config.json"


class SpecialistRegistry:
    """Configuration-driven registry for multi-crop specialist models."""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = Path(config_path) if config_path else CONFIG_PATH
        self.config: Dict[str, Any] = {}
        self._adapters: Dict[str, BaseSpecialistAdapter] = {}
        self._load_config()
        self._initialize_registered_adapters()

    def _load_config(self) -> None:
        if not self.config_path.is_file():
            logger.warning("Specialists configuration not found at %s", self.config_path)
            self.config = {"specialists": {}}
            return
        with open(self.config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)

    def _initialize_registered_adapters(self) -> None:
        # 1. Soybean Specialist
        try:
            self._adapters["soybean"] = SoybeanConvNeXtAdapter()
        except Exception as e:
            logger.warning("Failed to initialize SoybeanConvNeXtAdapter: %s", e)

        # 2. Cotton Specialist
        try:
            self._adapters["cotton"] = CottonDenseNetAdapter()
        except Exception as e:
            logger.warning("Failed to initialize CottonDenseNetAdapter: %s", e)

        # 3. Multi-Crop Generalist (Tomato, Potato, Corn, Grape, Apple, etc.)
        try:
            gen_adapter = GeneralistEfficientNetAdapter()
            self._adapters["generalist"] = gen_adapter
            for crop_alias in ["tomato", "potato", "corn", "grape", "apple", "chilli", "pepper"]:
                self._adapters[crop_alias] = gen_adapter
        except Exception as e:
            logger.warning("Failed to initialize GeneralistEfficientNetAdapter: %s", e)

        # 4. Multi-Crop Spatial Lesion Detector (YOLOv11x)
        try:
            yolo_adapter = YoloSpecialistAdapter()
            self._adapters["yolo"] = yolo_adapter
            self._adapters["yolo_multicrop"] = yolo_adapter
        except Exception as e:
            logger.warning("Failed to initialize YoloSpecialistAdapter: %s", e)

        # 5. Primary Pest Object Detector (YOLO11s)
        try:
            self._adapters["yolo_pest"] = YoloPestAdapter(model_variant="primary")
        except Exception as e:
            logger.warning("Failed to initialize YoloPestAdapter: %s", e)

    def get_specialist(self, crop: str) -> Optional[BaseSpecialistAdapter]:
        """Return dedicated specialist adapter for a given crop if available."""
        crop_clean = crop.lower().strip()
        if crop_clean in self._adapters and self._adapters[crop_clean].is_available():
            return self._adapters[crop_clean]
        return None

    def get_eligible_specialists(self, crop: str) -> List[BaseSpecialistAdapter]:
        """Return all active models eligible to diagnose or cross-validate the given crop."""
        crop_clean = crop.lower().strip()
        eligible: List[BaseSpecialistAdapter] = []

        # 1. Dedicated crop specialist
        if crop_clean in self._adapters and self._adapters[crop_clean].is_available():
            adapter = self._adapters[crop_clean]
            if adapter not in eligible:
                eligible.append(adapter)

        # 2. Multi-crop generalist (if crop is supported by EfficientNet)
        generalist_crops = [
            "tomato", "potato", "corn", "maize", "grape", "apple", "peach",
            "pepper", "chilli", "bell pepper", "cherry", "strawberry", "squash", "blueberry", "raspberry"
        ]
        if crop_clean in generalist_crops and "generalist" in self._adapters:
            if self._adapters["generalist"].is_available() and self._adapters["generalist"] not in eligible:
                eligible.append(self._adapters["generalist"])

        # 3. YOLO multi-crop detector (only if crop is supported by YOLO 116-class taxonomy)
        yolo_crops = [
            "corn", "maize", "tomato", "potato", "apple", "grape", "cherry", "peach",
            "cassava", "banana", "citrus", "orange", "rice", "cucumber", "eggplant",
            "bell pepper", "pepper", "chilli", "blueberry", "strawberry", "squash",
            "zucchini", "soybean", "coffee", "celery", "cabbage", "cauliflower",
            "broccoli", "garlic", "ginger", "basil", "lettuce", "bean", "plum", "carrot", "cotton"
        ]
        if crop_clean in yolo_crops and "yolo" in self._adapters:
            if self._adapters["yolo"].is_available() and self._adapters["yolo"] not in eligible:
                eligible.append(self._adapters["yolo"])

        return eligible

    def get_supported_crops(self) -> List[str]:
        """Return all crops supported across active and planned specialists."""
        crops = set()
        for k, spec in self.config.get("specialists", {}).items():
            c = spec.get("crop")
            if c and c != "Multi-Crop" and c != "All":
                crops.add(c)
        return sorted(list(crops))

    def get_registry_status(self) -> Dict[str, Any]:
        """Return status, availability, and metadata for all configured specialists."""
        items: Dict[str, Any] = {}
        for key, spec_cfg in self.config.get("specialists", {}).items():
            adapter = self._adapters.get(key)
            available = adapter.is_available() if adapter else False
            items[key] = {
                "crop": spec_cfg.get("crop"),
                "model_id": spec_cfg.get("model_id"),
                "architecture": spec_cfg.get("architecture"),
                "status": spec_cfg.get("status", "planned"),
                "is_loaded": available,
                "license": spec_cfg.get("license"),
                "metadata": adapter.get_metadata() if (adapter and hasattr(adapter, "get_metadata") and available) else None,
            }
        # Deduplicate active adapters count
        unique_active = len({id(a) for a in self._adapters.values() if a.is_available()})
        return {
            "registry_version": self.config.get("version", "2.0.0"),
            "total_configured": len(self.config.get("specialists", {})),
            "total_active_loaded": unique_active,
            "specialists": items,
        }


# Global singleton registry instance
specialist_registry = SpecialistRegistry()
