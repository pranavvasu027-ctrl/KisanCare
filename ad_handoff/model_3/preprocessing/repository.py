"""
Repository and query layer for CIB&RC Registered Treatments and IPM Practices.
Loads normalized treatments.json and relational sources.json.
"""

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from disease_pest_ai.knowledge_base.normalization import normalize_condition, normalize_crop
from disease_pest_ai.knowledge_base.schema import KBRecord
from disease_pest_ai.models.base import normalize_crop_name

logger = logging.getLogger(__name__)

DEFAULT_TREATMENTS_PATH = Path(__file__).resolve().parent / "treatments.json"
DEFAULT_SOURCES_PATH = Path(__file__).resolve().parent / "sources.json"


def normalize_condition_name(condition: Optional[str], crop_name: Optional[str] = None) -> str:
    """Normalize condition/pathology name for strict canonical comparison."""
    if not condition:
        return ""
    canon_cond, _, _ = normalize_condition(condition, crop_name)
    clean = re.sub(r"[^\w\s]", " ", canon_cond.lower()).strip()
    clean = re.sub(r"\s+", " ", clean)
    return clean


class KnowledgeBaseRepository:
    """
    In-memory, indexed repository for CIB&RC treatment records and authoritative sources.
    Provides strict dual-key (crop + condition) search and provenance tracking.
    """

    def __init__(
        self,
        db_path: Optional[Path] = None,
        sources_path: Optional[Path] = None,
    ):
        self.db_path = Path(db_path) if db_path else DEFAULT_TREATMENTS_PATH
        if not self.db_path.exists():
            # Fallback to cibrc_database.json if treatments.json not yet created
            alt_path = Path(__file__).resolve().parent / "cibrc_database.json"
            if alt_path.exists():
                self.db_path = alt_path

        self.sources_path = Path(sources_path) if sources_path else DEFAULT_SOURCES_PATH
        self.sources: Dict[str, Dict[str, Any]] = {}
        self.records: List[KBRecord] = []
        self._index: Dict[Tuple[str, str], List[KBRecord]] = {}
        self.database_version: str = "1.0.0-20240331"
        self.source_date: str = "2024-03-31"

        self._load_sources()
        self._load_treatments()

    def _load_sources(self) -> None:
        """Load sources.json into an in-memory lookup dictionary."""
        if self.sources_path.exists():
            with open(self.sources_path, "r", encoding="utf-8") as f:
                src_list = json.load(f)
            for s in src_list:
                self.sources[s["source_id"]] = s
        else:
            logger.warning(f"Sources file not found at: {self.sources_path}")

    def _load_treatments(self) -> None:
        """Load, join with sources, and index treatment records."""
        if not self.db_path.exists():
            raise FileNotFoundError(f"Knowledge Base database file not found at: {self.db_path}")

        with open(self.db_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        self.records = []
        self._index = {}

        for item in raw_data:
            src_id = item.get("source_id", "")
            src_info = self.sources.get(src_id, {})
            
            # Populate joined metadata if not already on the record
            if not item.get("source_title") and src_info:
                item["source_title"] = src_info.get("title")
            if not item.get("source_url") and src_info:
                item["source_url"] = src_info.get("url")

            rec = KBRecord(**item)
            self.records.append(rec)
            
            c_key = normalize_crop_name(rec.crop)
            d_key = normalize_condition_name(rec.condition, rec.crop)
            key = (c_key, d_key)

            if key not in self._index:
                self._index[key] = []
            self._index[key].append(rec)

            if rec.source_date and self.source_date == "unknown":
                self.source_date = rec.source_date

        logger.info(
            f"Loaded {len(self.records)} records across {len(self._index)} crop+condition pairs "
            f"from {self.db_path} (DB Version: {self.database_version})"
        )

    def find_treatments(
        self,
        crop_name: str,
        condition: str,
        location_state: Optional[str] = None,
        growth_stage: Optional[str] = None,
    ) -> List[KBRecord]:
        """
        Search for treatments matching BOTH crop AND target condition.
        
        Strict Validation Rules:
        - Must match canonical crop AND condition.
        - NEVER returns treatments for active ingredients registered only for other crops.
        - Preserves location and growth stage metadata.
        """
        c_key = normalize_crop_name(crop_name)
        d_key = normalize_condition_name(condition, crop_name)
        
        matches = self._index.get((c_key, d_key), [])
        if not matches:
            # Try fuzzy contains on condition if exact key failed
            for (idx_crop, idx_cond), recs in self._index.items():
                if idx_crop == c_key:
                    if idx_cond in d_key or d_key in idx_cond:
                        matches = recs
                        break

        return list(matches)

    def get_source_details(self, source_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve authoritative metadata for a given source_id."""
        return self.sources.get(source_id)

    def get_all_sources(self) -> List[Dict[str, Any]]:
        """Return all authoritative source specifications."""
        return list(self.sources.values())

    def get_supported_crops(self) -> List[str]:
        """Return sorted list of supported unique crops."""
        return sorted(list({rec.crop for rec in self.records}))

    def get_supported_conditions_for_crop(self, crop_name: str) -> List[str]:
        """Return list of supported conditions for a specific crop."""
        c_key = normalize_crop_name(crop_name)
        return sorted(list({rec.condition for rec in self.records if normalize_crop_name(rec.crop) == c_key}))

    def is_crop_supported(self, crop_name: str) -> bool:
        """Check if crop is in the knowledge base."""
        c_key = normalize_crop_name(crop_name)
        return any(normalize_crop_name(rec.crop) == c_key for rec in self.records)

    def is_condition_supported(self, condition: str, crop_name: Optional[str] = None) -> bool:
        """Check if condition is in the knowledge base."""
        d_key = normalize_condition_name(condition, crop_name)
        return any(normalize_condition_name(rec.condition, rec.crop) == d_key for rec in self.records)
