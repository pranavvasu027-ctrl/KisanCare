from .schemas import FarmDigitalTwin
from ..model1.service import model1_service

def run_model1_for_twin(twin: FarmDigitalTwin):
    required_soil = ['nitrogen', 'phosphorus', 'potassium', 'ph']
    required_climate = ['temperature', 'humidity', 'rainfall']
    
    missing = []
    
    # Check soil fields
    for field in required_soil:
        if getattr(twin.soil, field) is None:
            missing.append(f"soil.{field}")
            
    # Check climate fields
    for field in required_climate:
        if getattr(twin.climate, field) is None:
            missing.append(f"climate.{field}")
            
    if missing:
        return {
            "status": "insufficient_data",
            "missing_fields": missing,
            "message": "Cannot run Model 1. Required data is missing from the Farm Digital Twin."
        }
        
    # All present, construct payload
    req = {
        "nitrogen": twin.soil.nitrogen,
        "phosphorus": twin.soil.phosphorus,
        "potassium": twin.soil.potassium,
        "ph": twin.soil.ph,
        "temperature": twin.climate.temperature,
        "humidity": twin.climate.humidity,
        "rainfall": twin.climate.rainfall
    }
    
    result = model1_service.predict_top5(req)
    return {
        "status": "success",
        "prediction": result
    }
