"""
Knowledge Base Record Schema for CIB&RC Registered Pesticides and IPM Practices.
Conforms strictly to schema.json and supports relational source resolution.
"""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field


class KBRecord(BaseModel):
    """
    Standard schema for a single treatment record in the Knowledge Base.
    Conforms strictly to knowledge_base/schema.json.
    """
    id: str = Field(..., description="Unique immutable record identifier (e.g., 'CIBRC-CHM-TOM-EB-001').")
    crop: str = Field(..., description="Canonical crop name (e.g., 'Tomato', 'Apple', 'Corn').")
    condition: str = Field(..., description="Canonical disease, pest, or physiological condition.")
    condition_type: str = Field(..., description="'disease' | 'pest' | 'healthy' | 'unknown'")
    target: str = Field(..., description="Biological target organism or pathology.")
    active_ingredient: Optional[str] = Field(None, description="Generic active chemical substance or biological agent.")
    formulation: Optional[str] = Field(None, description="Registered formulation (e.g., '75% WP', '25% EC').")
    registered_use: str = Field(..., description="Summary of registered use as on official publication.")
    approved_crop: str = Field(..., description="Crop explicitly listed in the official register.")
    approved_target: str = Field(..., description="Target pest/disease explicitly listed in the official register.")
    application_method: Optional[str] = Field(None, description="Foliar spray, seed treatment, etc.")
    dose: Optional[Union[str, float]] = Field(None, description="Exact numerical dose if published; null otherwise.")
    dose_unit: Optional[str] = Field(None, description="Unit of measurement (e.g., 'kg/ha', 'ml/ha').")
    pre_harvest_interval: Optional[Union[int, str]] = Field(None, description="Waiting period (PHI) in days.")
    number_of_applications: Optional[Union[int, str]] = Field(None, description="Max applications per cycle.")
    interval: Optional[str] = Field(None, description="Minimum spray interval in days.")
    region_scope: str = Field("India", description="Geographic jurisdiction ('India' or state).")
    source_id: str = Field(..., description="Foreign key referencing source_id in sources.json.")
    source_date: str = Field(..., description="Official publication date (e.g., '2024-03-31').")
    verification_date: str = Field("2026-10-04", description="Date record was verified.")
    verification_status: str = Field("verified", description="'verified' | 'unverified' | 'guidance_only'")
    notes: Optional[str] = Field(None, description="FRAC/IRAC code, resistance management, or agronomic notes.")
    safety_notes: Optional[str] = Field(None, description="Toxicity class, PPE, waiting period, or pollinator warning.")

    # Joined / dynamically resolved source metadata fields
    source_title: Optional[str] = Field(None, description="Resolved title from sources.json.")
    source_url: Optional[str] = Field(None, description="Resolved URL from sources.json.")
    database_version: str = Field("1.0.0-20240331", description="Database version.")

    @property
    def dose_information(self) -> str:
        """Return formatted dose or authoritative fallback without inventing."""
        if self.dose and self.dose_unit:
            return f"{self.dose} {self.dose_unit}"
        return "Application details unavailable in verified source. Follow the current registered product label."

    @property
    def region(self) -> str:
        """Alias for region_scope."""
        return self.region_scope

    @property
    def stage_specific_guidance(self) -> str:
        """Agronomic growth stage guidance."""
        return "unavailable"

    @property
    def target_category(self) -> str:
        """
        Categorize the treatment into chemical or IPM category based on active ingredient and formulation.
        """
        notes_lower = (self.notes or "").lower()
        if not self.formulation or not self.active_ingredient:
            if "cultural" in notes_lower or "sanitation" in notes_lower or "rotation" in notes_lower or "gap" in notes_lower:
                return "cultural"
            if "mechanical" in notes_lower or "trap" in notes_lower or "pruning" in notes_lower or "rogue" in notes_lower:
                return "mechanical"
            if "biological" in notes_lower or "parasitoid" in notes_lower or "trichoderma" in notes_lower:
                return "biological"
            return "preventive_monitoring"

        if "biological" in notes_lower or "bio-fungicide" in notes_lower or "antagonist" in notes_lower:
            return "biological"

        if self.condition_type == "pest" or "insecticide" in notes_lower:
            return "chemical_insecticide"
        if "acaricide" in notes_lower or "miticide" in notes_lower:
            return "chemical_acaricide"
        if "bactericide" in notes_lower or "antibiotic" in notes_lower:
            return "chemical_bactericide"
        return "chemical_fungicide"

    model_config = ConfigDict(arbitrary_types_allowed=True)
