"""
Input Contract Schemas for Disease & Pest AI Module.

Standardized required user inputs:
- plant_image: Image path, bytes, base64 string, or PIL Image object
- crop_name: User-declared crop (e.g., 'Tomato', 'Corn', 'Apple')
- location_state: Indian state / region (e.g., 'Maharashtra', 'Punjab')
- growth_stage: Crop phenological stage (e.g., 'vegetative', 'flowering', 'fruiting')
- image_type: Modality of image capture (e.g., 'leaf', 'field_leaf', 'trap_sticky_sheet')

Contextual Field Usage Matrix:
-----------------------------------------------------------------------------------------
Field           Tensor Input?   Usage Role                  Purpose
-----------------------------------------------------------------------------------------
plant_image     YES             Model Input                 Processed into numerical tensor
crop_name       NO              Prediction Validation       Cross-checks prediction for mismatch;
                                                            enables class filtering
location_state  NO              Treatment Lookup            Feeds regulatory & agronomic rules
                                                            (CIBRC pesticide recommendations)
growth_stage    NO              Prediction Validation &     Validates disease phenology
                                Treatment Lookup            (e.g., damping-off vs late blight)
image_type      NO              Model Dispatch & Validation Routes between leaf vs trap models;
                                                            guards against modal mismatches
-----------------------------------------------------------------------------------------
"""

from enum import Enum
from pathlib import Path
from typing import Any, Optional, Union
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ImageType(str, Enum):
    LEAF = "leaf"
    FIELD_LEAF = "field_leaf"
    FRUIT = "fruit"
    STEM = "stem"
    WHOLE_PLANT = "whole_plant"
    FIELD_CROP = "field_crop"
    TRAP_STICKY_SHEET = "trap_sticky_sheet"
    OTHER = "other"


class GrowthStage(str, Enum):
    SEEDLING = "seedling"
    VEGETATIVE = "vegetative"
    FLOWERING = "flowering"
    FRUITING = "fruiting"
    MATURITY_HARVEST = "maturity_harvest"
    POST_HARVEST = "post_harvest"
    UNKNOWN = "unknown"


class DiseasePestInput(BaseModel):
    """
    Standardized input payload for Disease and Pest AI inference.
    All five fields are strictly required by the input contract.
    """
    plant_image: Union[str, Path, bytes, Any] = Field(
        ...,
        description="Path to image file, raw bytes, or PIL Image instance."
    )
    crop_name: str = Field(
        ...,
        min_length=1,
        description="User-specified crop name (e.g. 'Tomato', 'Corn', 'Cotton')."
    )
    location_state: str = Field(
        ...,
        min_length=1,
        description="State or geographic region in India (e.g. 'Maharashtra', 'Karnataka')."
    )
    growth_stage: Union[GrowthStage, str] = Field(
        ...,
        description="Crop growth stage (e.g. 'vegetative', 'flowering', 'fruiting')."
    )
    image_type: Union[ImageType, str] = Field(
        ...,
        description="Type of image captured (e.g. 'leaf', 'trap_sticky_sheet')."
    )

    @field_validator("crop_name", "location_state")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        if isinstance(v, str):
            v_strip = v.strip()
            if not v_strip:
                raise ValueError("Field cannot be empty or purely whitespace.")
            return v_strip
        return v

    model_config = ConfigDict(arbitrary_types_allowed=True)
