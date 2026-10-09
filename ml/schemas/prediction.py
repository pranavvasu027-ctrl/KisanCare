from pydantic import BaseModel
from typing import Any, Dict, Optional, List
from datetime import datetime

class ModelResult(BaseModel):
    model_name: str
    model_version: str
    status: str
    prediction: Any = None
    unit: Optional[str] = None
    confidence: Optional[float] = None
    inputs_used: Dict[str, Any]
    data_provenance: str
    timestamp: datetime
    warnings: List[str] = []
    metadata: Dict[str, Any] = {}

class CostPredictionRequest(BaseModel):
    # Farmer-entered cultivation costs and missing schema metrics
    sunlight_hours_day: Optional[float] = None
    fertilizer_kg_ha: Optional[float] = None
    pesticide_litre_ha: Optional[float] = None
    seed_quality_score: Optional[float] = None
    water_efficiency_t_per_1000m3: Optional[float] = None
    disease_pest_risk_pct: Optional[float] = None
    
    # Overrides for DB values (optional)
    water_used_m3: Optional[float] = None
    irrigation_method: Optional[str] = None
