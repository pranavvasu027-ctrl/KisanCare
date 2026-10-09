from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class FarmBase(BaseModel):
    farm_name: str
    description: Optional[str] = None
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    total_area: Optional[float] = None
    area_unit: Optional[str] = "hectare"

class FarmCreate(FarmBase):
    pass

class FarmResponse(FarmBase):
    id: str
    user_id: str
    status: str
    created_at: datetime
    updated_at: datetime

class FieldBase(BaseModel):
    field_name: str
    area: Optional[float] = None
    area_unit: Optional[str] = "hectare"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    boundary: Optional[Dict[str, Any]] = None

class FieldCreate(FieldBase):
    pass

class FieldResponse(FieldBase):
    id: str
    farm_id: str
    status: str
    created_at: datetime
    updated_at: datetime

class SeasonBase(BaseModel):
    season_name: str
    crop: Optional[str] = None
    crop_variety: Optional[str] = None
    sowing_date: Optional[str] = None
    expected_harvest_date: Optional[str] = None
    actual_harvest_date: Optional[str] = None
    crop_stage: Optional[str] = None
    previous_crop: Optional[str] = None

class SeasonCreate(SeasonBase):
    pass

class SeasonResponse(SeasonBase):
    id: str
    field_id: str
    status: str
    created_at: datetime
    updated_at: datetime

class FieldWithSeasons(FieldResponse):
    seasons: List[SeasonResponse] = []

class FarmContextResponse(FarmResponse):
    fields: List[FieldWithSeasons] = []
