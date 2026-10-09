from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from ml.schemas.prediction import ModelResult, CostPredictionRequest

class OrchestrationRequest(BaseModel):
    models: List[str] = Field(..., description="List of model identifiers to execute (e.g., ['crop_recommendation', 'cost_prediction'])")
    cost_prediction_inputs: Optional[CostPredictionRequest] = Field(None, description="Additional farmer-entered inputs required for the cost prediction model")

class OrchestrationResponse(BaseModel):
    status: str
    farm_id: str
    field_id: str
    season_id: str
    results: Dict[str, ModelResult]
