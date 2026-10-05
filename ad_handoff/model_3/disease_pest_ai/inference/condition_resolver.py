"""
Condition Resolver for Unified Agriculture AI Diagnostics (Phase 4, Section 8).

Resolves condition names, maps them to canonical scientific/common names,
performs biological crop compatibility checks against pest taxonomy and
pathology registers, and categorizes status into:
- DISEASE: Diagnosed foliar disease
- PEST: Detected insect/pest
- HEALTHY: Healthy leaf/plant tissue
- UNKNOWN: Unrecognized condition
- CROP_MISMATCH: Biologically incompatible with user crop
- UNSUPPORTED: Crop or condition not present in knowledge base
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from disease_pest_ai.knowledge_base.normalization import (
    CANONICAL_CONDITIONS,
    CANONICAL_CROPS,
    clean_text,
    normalize_condition,
    normalize_crop,
)
from disease_pest_ai.models.base import normalize_crop_name
from disease_pest_ai.schemas.outputs import ConditionType

logger = logging.getLogger(__name__)


class ResolvedCondition(BaseModel):
    """Normalized condition resolution output per Section 8."""
    raw_condition: str = Field(..., description="Original input or model label.")
    canonical_condition: str = Field(..., description="Canonical disease/pest name.")
    condition_type: ConditionType = Field(..., description="disease | pest | healthy | unknown")
    status: str = Field(..., description="DISEASE | PEST | HEALTHY | UNKNOWN | CROP_MISMATCH | UNSUPPORTED")
    crop: str = Field(..., description="User crop or canonical crop.")
    is_crop_match: bool = Field(True, description="True if biologically compatible with specified crop.")
    pathogen_scientific_name: Optional[str] = Field(None, description="Scientific pathogen or pest species name.")
    reason: Optional[str] = Field(None, description="Agronomic or diagnostic rationale.")
    warnings: List[str] = Field(default_factory=list, description="Diagnostic warnings or notices.")


class ConditionResolver:
    """
    Deterministically resolves conditions, normalizes taxonomy,
    and validates biological crop compatibility for diseases and pests.
    """

    def __init__(self, pest_taxonomy_path: Optional[Path] = None):
        if pest_taxonomy_path is None:
            pest_taxonomy_path = Path(__file__).resolve().parent.parent / "knowledge_base" / "pest_taxonomy.json"
        
        self.pest_taxonomy_path = pest_taxonomy_path
        self._pest_taxonomy: Dict[str, Any] = {}
        self._pest_by_name: Dict[str, Dict[str, Any]] = {}
        self._load_pest_taxonomy()

    def _load_pest_taxonomy(self) -> None:
        """Load pest taxonomy for cross-referencing."""
        if not self.pest_taxonomy_path.exists():
            logger.warning(f"Pest taxonomy file not found: {self.pest_taxonomy_path}")
            return

        try:
            with open(self.pest_taxonomy_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                taxonomy_list = data if isinstance(data, list) else data.get("taxonomy", [])
                for entry in taxonomy_list:
                    cname = entry.get("canonical_name", "").lower()
                    if cname:
                        self._pest_by_name[cname] = entry
                    # Index aliases
                    for alias in entry.get("aliases", []):
                        self._pest_by_name[alias.lower()] = entry
                    # Index raw label / raw_model_name
                    raw_l = entry.get("raw_model_name", entry.get("raw_label", "")).lower()
                    if raw_l:
                        self._pest_by_name[raw_l] = entry
        except Exception as e:
            logger.error(f"Error loading pest taxonomy from {self.pest_taxonomy_path}: {e}")

    def resolve_disease(
        self,
        raw_condition: str,
        user_crop: str,
        predicted_crop: Optional[str] = None,
    ) -> ResolvedCondition:
        """
        Resolve disease prediction with biological crop validation (Section 8).
        """
        warnings: List[str] = []
        norm_user_crop = normalize_crop_name(user_crop)
        clean_user_crop = CANONICAL_CROPS.get(norm_user_crop, user_crop.title() if user_crop else "Unknown")

        # Check if user crop is supported
        if norm_user_crop not in CANONICAL_CROPS:
            return ResolvedCondition(
                raw_condition=raw_condition,
                canonical_condition=raw_condition,
                condition_type=ConditionType.UNKNOWN,
                status="UNSUPPORTED",
                crop=clean_user_crop,
                is_crop_match=False,
                reason=f"Crop '{user_crop}' is not in the supported agricultural registry.",
                warnings=[f"Unsupported Crop: '{user_crop}' is outside the verified crop database."],
            )

        norm_cond = clean_text(raw_condition)

        # 1. Healthy check
        if norm_cond == "healthy" or "healthy" in norm_cond:
            return ResolvedCondition(
                raw_condition=raw_condition,
                canonical_condition="Healthy",
                condition_type=ConditionType.HEALTHY,
                status="HEALTHY",
                crop=clean_user_crop,
                is_crop_match=True,
                pathogen_scientific_name="Normal Plant Tissue",
                reason="Plant tissue exhibits healthy physiological characteristics without foliar lesions.",
                warnings=[],
            )

        # 2. Check if predicted crop from classifier conflicts with user crop
        if predicted_crop:
            norm_pred_crop = normalize_crop_name(predicted_crop)
            if norm_pred_crop and norm_user_crop != norm_pred_crop:
                warnings.append(
                    f"Crop Mismatch Warning: Model detected disease characteristic of '{predicted_crop}', "
                    f"which does not match user-specified crop '{user_crop}'."
                )
                return ResolvedCondition(
                    raw_condition=raw_condition,
                    canonical_condition=raw_condition.title(),
                    condition_type=ConditionType.DISEASE,
                    status="CROP_MISMATCH",
                    crop=clean_user_crop,
                    is_crop_match=False,
                    reason=f"Disease '{raw_condition}' from '{predicted_crop}' is incompatible with '{user_crop}'.",
                    warnings=warnings,
                )

        # 3. Check canonical condition table for user crop
        canon_tuple = CANONICAL_CONDITIONS.get((norm_user_crop, norm_cond))
        if canon_tuple:
            c_name, pathogen, c_type = canon_tuple
            status_str = "HEALTHY" if c_type == ConditionType.HEALTHY else "DISEASE"
            return ResolvedCondition(
                raw_condition=raw_condition,
                canonical_condition=c_name,
                condition_type=c_type,
                status=status_str,
                crop=clean_user_crop,
                is_crop_match=True,
                pathogen_scientific_name=pathogen,
                reason=f"Verified biological pathogen '{pathogen}' for {clean_user_crop}.",
                warnings=warnings,
            )

        # 4. Check if condition exists under ANY other crop (identifying cross-crop contamination)
        other_crops_with_condition = [
            crop for (crop, cond), val in CANONICAL_CONDITIONS.items() if cond == norm_cond
        ]
        if other_crops_with_condition:
            other_crops_display = [CANONICAL_CROPS.get(c, c.title()) for c in other_crops_with_condition]
            warnings.append(
                f"Crop Mismatch: '{raw_condition}' is registered on {', '.join(other_crops_display)}, not on '{user_crop}'."
            )
            return ResolvedCondition(
                raw_condition=raw_condition,
                canonical_condition=raw_condition.title(),
                condition_type=ConditionType.DISEASE,
                status="CROP_MISMATCH",
                crop=clean_user_crop,
                is_crop_match=False,
                reason=f"Pathology '{raw_condition}' is registered on {', '.join(other_crops_display)}, but not on '{user_crop}'.",
                warnings=warnings,
            )

        # 5. Fallback for unindexed condition on supported crop
        return ResolvedCondition(
            raw_condition=raw_condition,
            canonical_condition=raw_condition.title(),
            condition_type=ConditionType.DISEASE,
            status="DISEASE",
            crop=clean_user_crop,
            is_crop_match=True,
            pathogen_scientific_name=None,
            reason=f"Diagnosed as foliar pathology on '{clean_user_crop}'.",
            warnings=warnings,
        )

    def resolve_pest(
        self,
        raw_pest: str,
        user_crop: str,
        score: float = 1.0,
    ) -> ResolvedCondition:
        """
        Resolve pest detection with biological host crop validation (Section 8).
        """
        warnings: List[str] = []
        norm_user_crop = normalize_crop_name(user_crop)
        clean_user_crop = CANONICAL_CROPS.get(norm_user_crop, user_crop.title() if user_crop else "Unknown")

        norm_pname = raw_pest.lower().strip()
        tax_entry = self._pest_by_name.get(norm_pname)

        if not tax_entry:
            # Try fuzzy match in keys
            for k, v in self._pest_by_name.items():
                if norm_pname in k or k in norm_pname:
                    tax_entry = v
                    break

        if tax_entry:
            canonical_name = tax_entry.get("canonical_name", raw_pest.title())
            scientific_name = tax_entry.get("scientific_name")
            supported_crops = tax_entry.get("supported_crops", [])

            # Crop compatibility
            is_match = True
            if norm_user_crop and supported_crops:
                norm_supported = [normalize_crop_name(c) for c in supported_crops]
                if norm_user_crop not in norm_supported:
                    is_match = False
                    status_str = "CROP_MISMATCH"
                    warnings.append(
                        f"Pest Host Incompatibility: Detected pest '{canonical_name}' typically infests "
                        f"{', '.join(supported_crops)}, not '{user_crop}'."
                    )
                else:
                    status_str = "PEST"
            else:
                status_str = "PEST"

            return ResolvedCondition(
                raw_condition=raw_pest,
                canonical_condition=canonical_name,
                condition_type=ConditionType.PEST,
                status=status_str,
                crop=clean_user_crop,
                is_crop_match=is_match,
                pathogen_scientific_name=scientific_name,
                reason=f"Identified pest: {canonical_name} ({scientific_name or 'Arthropoda'}).",
                warnings=warnings,
            )

        # Unindexed pest
        return ResolvedCondition(
            raw_condition=raw_pest,
            canonical_condition=raw_pest.title(),
            condition_type=ConditionType.PEST,
            status="PEST",
            crop=clean_user_crop,
            is_crop_match=True,
            pathogen_scientific_name=None,
            reason=f"Detected pest organism '{raw_pest}' on {clean_user_crop}.",
            warnings=warnings,
        )
