"""Knowledge Base manager for crop rotation, nutrient demand, and sequence compatibility."""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union
from crop_recommendation.models import CropKnowledge, RotationCompatibility
from crop_recommendation.config import KNOWLEDGE_BASE_PATH

logger = logging.getLogger(__name__)


class KnowledgeBase:
    """Configurable agronomic knowledge base containing crop nutrient demands,

    legume status, root profiles, and sequence compatibility rules.
    """

    def __init__(self, data_or_path: Optional[Union[str, Path, Dict]] = None):
        self._crops: Dict[str, CropKnowledge] = {}
        self._alias_map: Dict[str, str] = {}
        self.load(data_or_path or KNOWLEDGE_BASE_PATH)

    def load(self, source: Union[str, Path, Dict]) -> None:
        """Load and validate crop knowledge from a file path or raw dictionary."""
        if isinstance(source, (str, Path)):
            path = Path(source)
            if not path.exists():
                raise FileNotFoundError(f"Knowledge base file not found at: {path}")
            with open(path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
        elif isinstance(source, dict):
            raw_data = source
        else:
            raise ValueError(f"Unsupported source type for KnowledgeBase: {type(source)}")

        crops_dict = raw_data.get("crops", raw_data)
        self._crops.clear()
        self._alias_map.clear()

        for key, crop_dict in crops_dict.items():
            if isinstance(crop_dict, dict):
                if "name" not in crop_dict:
                    crop_dict["name"] = key
                crop = CropKnowledge(**crop_dict)
                canonical_name = crop.name.lower()
                self._crops[canonical_name] = crop
                self._alias_map[canonical_name] = canonical_name
                for alias in crop.aliases:
                    self._alias_map[alias.lower()] = canonical_name

        logger.info(f"Loaded {len(self._crops)} crops into knowledge base.")

    def get_crop(self, crop_name: Optional[str]) -> Optional[CropKnowledge]:
        """Lookup crop by canonical name or alias. Returns None if unknown."""
        if not crop_name or not crop_name.strip():
            return None
        clean = crop_name.strip().lower()
        canonical = self._alias_map.get(clean)
        if canonical:
            return self._crops.get(canonical)
        # Direct search fallback
        for crop in self._crops.values():
            if crop.matches(clean):
                return crop
        return None

    def get_or_default(self, crop_name: Optional[str]) -> CropKnowledge:
        """Returns CropKnowledge if known, otherwise constructs a neutral fallback profile."""
        crop = self.get_crop(crop_name)
        if crop:
            return crop
        clean = (crop_name or "unknown").strip().lower()
        return CropKnowledge(
            name=clean,
            aliases=[],
            crop_family="Unknown",
            n_demand="Medium",
            p_demand="Medium",
            k_demand="Medium",
            n_demand_kg_ha=[50.0, 80.0],
            p_demand_kg_ha=[25.0, 50.0],
            k_demand_kg_ha=[30.0, 60.0],
            is_legume=False,
            feeder_type="Moderate Feeder",
            root_depth="Medium",
            rotation_compatibility=RotationCompatibility(
                recommended_successors=[],
                avoid_successors=[],
                min_rotation_interval_seasons=1,
                notes="Generic fallback profile for unlisted crop."
            )
        )

    def is_legume(self, crop_name: Optional[str]) -> bool:
        """Check if crop is a nitrogen-fixing legume."""
        crop = self.get_crop(crop_name)
        return crop.is_legume if crop else False

    def list_crops(self) -> List[str]:
        """List all canonical crop names currently loaded."""
        return sorted(list(self._crops.keys()))

    def check_sequence_compatibility(
        self, prev_crop_name: Optional[str], candidate_crop_name: str
    ) -> Dict[str, bool]:
        """Check if candidate crop is explicitly recommended or avoided after previous crop."""
        prev_crop = self.get_crop(prev_crop_name)
        candidate = self.get_crop(candidate_crop_name)

        cand_name = candidate.name.lower() if candidate else candidate_crop_name.lower()
        cand_family = candidate.crop_family.lower() if candidate else ""

        is_recommended = False
        is_avoided = False

        if prev_crop and prev_crop.rotation_compatibility:
            compat = prev_crop.rotation_compatibility
            # Check recommended
            for rec in compat.recommended_successors:
                clean_rec = rec.lower()
                if clean_rec == cand_name or (cand_family and clean_rec == cand_family):
                    is_recommended = True
                    break
                # Check alias match
                rec_crop = self.get_crop(clean_rec)
                if rec_crop and rec_crop.name.lower() == cand_name:
                    is_recommended = True
                    break

            # Check avoided
            for av in compat.avoid_successors:
                clean_av = av.lower()
                if clean_av == cand_name or (cand_family and clean_av == cand_family):
                    is_avoided = True
                    break
                av_crop = self.get_crop(clean_av)
                if av_crop and av_crop.name.lower() == cand_name:
                    is_avoided = True
                    break

        return {
            "recommended": is_recommended,
            "avoid": is_avoided
        }


# Global default knowledge base singleton
_default_kb: Optional[KnowledgeBase] = None


def get_default_knowledge_base() -> KnowledgeBase:
    """Returns or initializes the global singleton knowledge base."""
    global _default_kb
    if _default_kb is None:
        _default_kb = KnowledgeBase()
    return _default_kb
