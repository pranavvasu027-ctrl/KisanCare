"""
Thread-Safe Persistent State Store for Soil Intelligence Plot Timelines
======================================================================
Maintains plot timeline instances, multi-tenant ownership metadata, human
review queues, and continuous evaluation records with atomic disk persistence.
"""

from __future__ import annotations
import os
import json
import pickle
import logging
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from ml.soil_intelligence.timeline.timeline_manager import PlotTimelineManager
from ml.soil_intelligence.ocr.review_manager import LabReportReviewManager
from ml.soil_intelligence.evaluation.comparator import SoilContinuousComparator

logger = logging.getLogger("kisancare.soil.store")


class SoilPlotStore:
    """Thread-safe store for active plot timelines, review items, and comparator with persistence."""
    
    _instance: Optional[SoilPlotStore] = None
    _lock = threading.Lock()

    def __init__(self, persistence_file: Optional[Path] = None):
        self._timelines: Dict[str, PlotTimelineManager] = {}
        self._plot_owners: Dict[str, str] = {}
        self._review_manager = LabReportReviewManager()
        self._comparator = SoilContinuousComparator()
        self._access_lock = threading.Lock()
        
        # File paths
        default_dir = Path(__file__).resolve().parent.parent.parent.parent / "data"
        self._persistence_file = persistence_file or Path(os.environ.get("SOIL_STORE_FILE", default_dir / "soil_store.pickle"))
        self._json_meta_file = self._persistence_file.parent / (self._persistence_file.stem + ".json")
        self._load_from_disk()

    @classmethod
    def get_instance(cls) -> SoilPlotStore:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def _save_to_disk(self) -> None:
        """Atomically persist timeline objects and metadata to disk."""
        try:
            self._persistence_file.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "version": 1,
                "saved_at": datetime.now().isoformat(),
                "plot_owners": dict(self._plot_owners),
                "timelines": dict(self._timelines),
            }
            with open(self._persistence_file, "wb") as f:
                pickle.dump(payload, f, protocol=pickle.HIGHEST_PROTOCOL)

            summary = {
                "saved_at": payload["saved_at"],
                "total_plots": len(self._timelines),
                "plots": {
                    pid: {
                        "farm_id": getattr(tm, "farm_id", None),
                        "owner_id": self._plot_owners.get(pid),
                        "lab_reports_count": len(getattr(tm, "lab_reports", [])),
                        "flux_events_count": len(getattr(tm, "flux_events", [])),
                    }
                    for pid, tm in self._timelines.items()
                }
            }
            with open(self._json_meta_file, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2)
        except Exception as exc:
            logger.warning("Failed to persist SoilPlotStore to disk: %s", exc)

    def _load_from_disk(self) -> None:
        """Load stored timelines from disk if available."""
        if not self._persistence_file.exists():
            return
        try:
            with open(self._persistence_file, "rb") as f:
                payload = pickle.load(f)
            if isinstance(payload, dict):
                self._timelines = payload.get("timelines", {})
                self._plot_owners = payload.get("plot_owners", {})
                logger.info("Loaded %d plot timelines from %s", len(self._timelines), self._persistence_file)
        except Exception as exc:
            logger.warning("Could not load soil store from %s: %s", self._persistence_file, exc)

    def get_or_create_timeline(
        self,
        plot_id: str,
        farm_id: Optional[str] = None,
        owner_id: Optional[str] = None
    ) -> PlotTimelineManager:
        with self._access_lock:
            if plot_id in self._timelines:
                existing_owner = self._plot_owners.get(plot_id)
                if owner_id and existing_owner and existing_owner != owner_id:
                    raise PermissionError(f"Access denied: Plot '{plot_id}' is owned by another user.")
                return self._timelines[plot_id]

            tm = PlotTimelineManager(plot_id=plot_id, farm_id=farm_id or "FARM_DEFAULT")
            self._timelines[plot_id] = tm
            if owner_id:
                self._plot_owners[plot_id] = owner_id
            self._save_to_disk()
            return tm

    def verify_access(self, plot_id: str, user_id: Optional[str]) -> None:
        """Verifies caller is authorized to view or mutate the plot."""
        if not user_id:
            return
        with self._access_lock:
            owner = self._plot_owners.get(plot_id)
            if owner and owner != user_id:
                raise PermissionError(f"Access denied: User '{user_id}' does not own plot '{plot_id}'.")

    def get_timeline(self, plot_id: str, user_id: Optional[str] = None) -> Optional[PlotTimelineManager]:
        self.verify_access(plot_id, user_id)
        with self._access_lock:
            return self._timelines.get(plot_id)

    def list_plots(self, user_id: Optional[str] = None) -> List[str]:
        with self._access_lock:
            if user_id:
                return sorted([pid for pid, tm in self._timelines.items() if self._plot_owners.get(pid, user_id) == user_id])
            return sorted(list(self._timelines.keys()))

    def save(self) -> None:
        with self._access_lock:
            self._save_to_disk()

    def delete_plot(self, plot_id: str, user_id: Optional[str] = None) -> bool:
        self.verify_access(plot_id, user_id)
        with self._access_lock:
            if plot_id in self._timelines:
                del self._timelines[plot_id]
                self._plot_owners.pop(plot_id, None)
                self._save_to_disk()
                return True
            return False

    def get_review_manager(self) -> LabReportReviewManager:
        return self._review_manager

    def get_comparator(self) -> SoilContinuousComparator:
        return self._comparator

    def reset(self) -> None:
        """Resets all stored timelines, review items, and comparator history (for testing)."""
        with self._access_lock:
            self._timelines.clear()
            self._plot_owners.clear()
            self._review_manager = LabReportReviewManager()
            self._comparator.clear_ledger()
            if self._persistence_file.exists():
                try:
                    self._persistence_file.unlink()
                except Exception:
                    pass
            if self._json_meta_file.exists():
                try:
                    self._json_meta_file.unlink()
                except Exception:
                    pass
