from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
from ml.schemas.prediction import CostPredictionRequest

class FarmerPreferences(BaseModel):
    preferred_crops: Optional[List[str]] = Field(None, description="List of crops the farmer prefers to grow")
    budget_limit_inr: Optional[float] = Field(None, description="Maximum budget for cultivation in INR")
    water_conservation_priority: bool = Field(False, description="Whether minimizing water usage is a high priority")

class DecisionRequest(BaseModel):
    decision_type: str = Field(..., description="Type of decision requested (e.g., 'crop_selection')")
    preferences: Optional[FarmerPreferences] = Field(None, description="Farmer's preferences and constraints")
    # We pass the cost prediction inputs so the orchestrator can run the cost model if needed
    cost_prediction_inputs: Optional[CostPredictionRequest] = Field(None, description="Required inputs if Cost model is requested")

class RecommendationAlternative(BaseModel):
    identifier: str
    recommended_action: str
    explanation: str
    supporting_evidence: Dict[str, Any]
    trade_offs: Optional[List[str]] = None
    warnings: Optional[List[str]] = None

class DecisionResponse(BaseModel):
    decision_id: str
    decision_type: str
    status: str = Field(..., description="ready, needs_more_data, blocked, or review_required")
    primary_recommendation: Optional[RecommendationAlternative] = None
    alternatives: List[RecommendationAlternative] = []
    missing_information: List[str] = []
    model_versions: Dict[str, str] = {}
    timestamp: datetime
