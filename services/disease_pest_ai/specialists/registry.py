"""Specialist Model Registry.

Manages registration, lifecycle, and access to crop-specific specialist model adapters.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from models.disease_detection.specialists.base import BaseSpecialistAdapter
    from models.disease_detection.specialists.cotton.adapter import CottonDenseNetAdapter
    from models.disease_detection.specialists.soybean.adapter import SoybeanConvNeXtAdapter
except ImportError:
    from specialists.base import BaseSpecialistAdapter
    from specialists.cotton.adapter import CottonDenseNetAdapter
    from specialists.soybean.adapter import SoybeanConvNeXtAdapter

logger = logging.getLogger("kisancare.specialists.registry")

CONFIG_PATH = Path(__file__).resolve().parent / "specialists_config.json"


class SpecialistRegistry:
    """Configuration-driven registry for crop specialist models."""

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

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.config = json.load(f)
            logger.info("Loaded specialists config with %d entries.", len(self.config.get("specialists", {})))
        except Exception as exc:
            logger.error("Failed to load specialists config: %s", exc)
            self.config = {"specialists": {}}

    def _initialize_registered_adapters(self) -> None:
        """Instantiate adapters that have active checkpoints present on disk."""
        specs = self.config.get("specialists", {})

        # Cotton specialist
        if "cotton" in specs and specs["cotton"].get("status") == "active":
            try:
                cotton_adapter = CottonDenseNetAdapter()
                if cotton_adapter.is_available():
                    self._adapters["cotton"] = cotton_adapter
                    logger.info("Cotton specialist registered and ready.")
                else:
                    logger.warning("Cotton specialist adapter initialized but weights unavailable.")
            except Exception as exc:
                logger.error("Failed to initialize Cotton specialist adapter: %s", exc)

        # Soybean specialist
        if "soybean" in specs and specs["soybean"].get("status") == "active":
            try:
                soybean_adapter = SoybeanConvNeXtAdapter()
                if soybean_adapter.is_available():
                    self._adapters["soybean"] = soybean_adapter
                    logger.info("Soybean specialist registered and ready.")
                else:
                    logger.warning("Soybean specialist adapter initialized but weights unavailable.")
            except Exception as exc:
                logger.error("Failed to initialize Soybean specialist adapter: %s", exc)

    def register_adapter(self, crop_name: str, adapter: BaseSpecialistAdapter) -> None:
        """Programmatically register or override an adapter for a crop."""
        key = crop_name.strip().lower()
        self._adapters[key] = adapter
        logger.info("Adapter registered for crop: %s", key)

    def get_specialist(self, crop_name: str) -> Optional[BaseSpecialistAdapter]:
        """Lookup active specialist adapter by declared crop name."""
        if not crop_name:
            return None
        key = crop_name.strip().lower()
        return self._adapters.get(key)

    def has_specialist(self, crop_name: str) -> bool:
        """Check if an active specialist exists for the given crop."""
        spec = self.get_specialist(crop_name)
        return spec is not None and spec.is_available()

    def get_supported_crops(self) -> List[str]:
        """Return list of crops with active specialists."""
        return [crop.title() for crop, adapter in self._adapters.items() if adapter.is_available()]

    def get_registry_status(self) -> Dict[str, Any]:
        """Audit status of all registered and planned specialist models."""
        specs = self.config.get("specialists", {})
        status_report = {}

        for crop_key, spec_cfg in specs.items():
            is_active = crop_key in self._adapters and self._adapters[crop_key].is_available()
            metadata = self._adapters[crop_key].get_metadata() if is_active else {}
            status_report[crop_key] = {
                "crop": spec_cfg.get("crop", crop_key.title()),
                "model_id": spec_cfg.get("model_id"),
                "status": "active" if is_active else spec_cfg.get("status", "planned"),
                "architecture": spec_cfg.get("architecture"),
                "framework": spec_cfg.get("framework"),
                "license": spec_cfg.get("license"),
                "is_available": is_active,
                "supported_classes": (
                    self._adapters[crop_key].get_supported_classes()
                    if is_active
                    else [c["canonical_condition"] for c in spec_cfg.get("class_mapping", [])]
                ),
                "metadata": metadata,
            }

        return {
            "active_specialists_count": len(self.get_supported_crops()),
            "active_crops": self.get_supported_crops(),
            "specialists": status_report,
        }


# Singleton registry instance
specialist_registry = SpecialistRegistry()
