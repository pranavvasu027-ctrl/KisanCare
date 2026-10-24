"""Specialist Model Registry.

Manages configuration-driven registration, lifecycle, and access strictly for
the two verified disease specialist model adapters:
1. Cotton: FarmGuard/cotton-densenet121 (DenseNet-121)
2. Soybean: ixrbhii/soybean-disease-convnext (ConvNeXt-Small)

All other crop disease models and generalist fallbacks are removed from the active
disease detection workflow.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from disease_pest_ai.specialists.base import BaseSpecialistAdapter
from disease_pest_ai.specialists.cotton.adapter import CottonDenseNetAdapter
from disease_pest_ai.specialists.soybean.adapter import SoybeanConvNeXtAdapter

logger = logging.getLogger("kisancare.specialists.registry")

CONFIG_PATH = Path(__file__).resolve().parent / "specialists_config.json"


class SpecialistRegistry:
    """Configuration-driven registry for verified Cotton and Soybean specialist models."""

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
        """Initialize exclusively the two active specialist adapters."""
        # 1. Soybean Specialist (ConvNeXt-Small)
        try:
            self._adapters["soybean"] = SoybeanConvNeXtAdapter()
            logger.info("SoybeanConvNeXtAdapter initialized successfully.")
        except Exception as e:
            logger.warning("Failed to initialize SoybeanConvNeXtAdapter: %s", e)

        # 2. Cotton Specialist (DenseNet-121)
        try:
            self._adapters["cotton"] = CottonDenseNetAdapter()
            logger.info("CottonDenseNetAdapter initialized successfully.")
        except Exception as e:
            logger.warning("Failed to initialize CottonDenseNetAdapter: %s", e)

    def get_specialist(self, crop: str) -> Optional[BaseSpecialistAdapter]:
        """Return dedicated specialist adapter for Cotton or Soybean if available."""
        crop_clean = crop.lower().strip()
        if crop_clean in self._adapters and self._adapters[crop_clean].is_available():
            return self._adapters[crop_clean]
        return None

    def get_eligible_specialists(self, crop: str) -> List[BaseSpecialistAdapter]:
        """Return exclusively the single verified model adapter for the declared crop.

        Strictly supports ONLY 'Cotton' and 'Soybean'.
        All other crops receive an empty list to enforce mandatory abstention/rejection
        without any generic or fallback model.
        """
        crop_clean = crop.lower().strip()
        eligible: List[BaseSpecialistAdapter] = []

        if crop_clean == "cotton" and "cotton" in self._adapters:
            adapter = self._adapters["cotton"]
            if adapter.is_available():
                eligible.append(adapter)
        elif crop_clean == "soybean" and "soybean" in self._adapters:
            adapter = self._adapters["soybean"]
            if adapter.is_available():
                eligible.append(adapter)

        return eligible

    def get_supported_crops(self) -> List[str]:
        """Return strictly the supported crops: Cotton and Soybean."""
        return ["Cotton", "Soybean"]

    def get_registry_status(self) -> Dict[str, Any]:
        """Return status, availability, and metadata for Cotton and Soybean specialists."""
        items: Dict[str, Any] = {}
        for key, spec_cfg in self.config.get("specialists", {}).items():
            adapter = self._adapters.get(key)
            available = adapter.is_available() if adapter else False
            items[key] = {
                "crop": spec_cfg.get("crop"),
                "model_id": spec_cfg.get("model_id"),
                "architecture": spec_cfg.get("architecture"),
                "status": spec_cfg.get("status", "active"),
                "is_loaded": available,
                "license": spec_cfg.get("license"),
                "metadata": adapter.get_metadata() if (adapter and hasattr(adapter, "get_metadata") and available) else None,
            }
        unique_active = len({id(a) for a in self._adapters.values() if a.is_available()})
        return {
            "registry_version": self.config.get("version", "2.1.0"),
            "focus": "Cotton & Soybean Specialized Neural Diagnostics",
            "supported_crops": self.get_supported_crops(),
            "total_configured": len(self.config.get("specialists", {})),
            "total_active_loaded": unique_active,
            "specialists": items,
        }


# Global singleton registry instance
specialist_registry = SpecialistRegistry()
