from fastapi import APIRouter, HTTPException
from typing import Dict
from .schemas import FarmDigitalTwin
from .adapter import run_model1_for_twin

router = APIRouter()

# In-memory storage placeholder for Phase 5
digital_twins_db: Dict[str, FarmDigitalTwin] = {}

@router.post("/api/v1/digital-twin", response_model=FarmDigitalTwin, status_code=201)
async def create_digital_twin(twin: FarmDigitalTwin):
    if twin.farm_id in digital_twins_db:
        raise HTTPException(status_code=409, detail="Farm Digital Twin already exists.")
    digital_twins_db[twin.farm_id] = twin
    return twin

@router.get("/api/v1/digital-twin/{farm_id}", response_model=FarmDigitalTwin)
async def get_digital_twin(farm_id: str):
    if farm_id not in digital_twins_db:
        raise HTTPException(status_code=404, detail="Farm Digital Twin not found.")
    return digital_twins_db[farm_id]

@router.put("/api/v1/digital-twin/{farm_id}", response_model=FarmDigitalTwin)
async def update_digital_twin(farm_id: str, twin: FarmDigitalTwin):
    if farm_id not in digital_twins_db:
        raise HTTPException(status_code=404, detail="Farm Digital Twin not found.")
    if farm_id != twin.farm_id:
        raise HTTPException(status_code=400, detail="Path farm_id does not match payload farm_id.")
    digital_twins_db[farm_id] = twin
    return twin

@router.post("/api/v1/digital-twin/{farm_id}/predict/model1")
async def predict_model1(farm_id: str):
    if farm_id not in digital_twins_db:
        raise HTTPException(status_code=404, detail="Farm Digital Twin not found.")
    
    twin = digital_twins_db[farm_id]
    result = run_model1_for_twin(twin)
    
    if result["status"] == "insufficient_data":
        raise HTTPException(status_code=422, detail=result)
        
    from datetime import datetime
    prediction_data = result["prediction"]
    prediction_data["timestamp"] = datetime.utcnow().isoformat()
    
    if twin.model_outputs is None:
        twin.model_outputs = {}
    twin.model_outputs["model1"] = prediction_data
    digital_twins_db[farm_id] = twin
    
    return result
