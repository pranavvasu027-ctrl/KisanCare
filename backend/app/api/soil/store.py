"""
In-Memory Thread-Safe State Store for Soil Intelligence Plot Timelines
======================================================================
Maintains plot timeline instances, human review queues, and continuous
evaluation records in memory without altering the existing relational DB.
"""

from __future__ import annotations
import threading
from typing import Dict, List, Optional

from ml.soil_intelligence.timeline.timeline_manager import PlotTimelineManager
from ml.soil_intelligence.ocr.review_manager import LabReportReviewManager
from ml.soil_intelligence.evaluation.comparator import SoilContinuousComparator


class SoilPlotStore:
    """Thread-safe store for active plot timelines, review items, and comparator."""
    
    _instance: Optional[SoilPlotStore] = None
    _lock = threading.Lock()

    def __init__(self):
        self._timelines: Dict[str, PlotTimelineManager] = {}
        self._review_manager = LabReportReviewManager()
        self._comparator = SoilContinuousComparator()
        self._access_lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> SoilPlotStore:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def get_or_create_timeline(self, plot_id: str, farm_id: Optional[str] = None) -> PlotTimelineManager:
        with self._access_lock:
            if plot_id not in self._timelines:
                self._timelines[plot_id] = PlotTimelineManager(plot_id=plot_id, farm_id=farm_id or "FARM_DEFAULT")
            return self._timelines[plot_id]

    def get_timeline(self, plot_id: str) -> Optional[PlotTimelineManager]:
        with self._access_lock:
            return self._timelines.get(plot_id)

    def list_plots(self) -> List[str]:
        with self._access_lock:
            return sorted(list(self._timelines.keys()))

    def delete_plot(self, plot_id: str) -> bool:
        with self._access_lock:
            if plot_id in self._timelines:
                del self._timelines[plot_id]
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
            self._review_manager = LabReportReviewManager()
            self._comparator.clear_ledger()
