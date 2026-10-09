import datetime
from typing import Dict, Any, List
from ml.schemas.prediction import ModelResult

# Registries
MODEL_REGISTRY = {
    "crop_recommendation": {
        "display_name": "Crop Recommendation",
        "status": "available",
        "dependencies": [],
    },
    "cost_prediction": {
        "display_name": "Cost & Profit Prediction",
        "status": "available",
        "dependencies": ["crop_recommendation"], # E.g., we might rely on crop recommendation if crop is unknown, but if it's known, it's fine. For now, we will mark it independent if the user has a crop selected. Actually let's keep dependencies empty since they can be run in parallel if context provides the crop.
        "dependencies": [],
    },
    "yield_prediction": {"display_name": "Yield Prediction", "status": "unavailable", "dependencies": []},
    "disease_pest_risk": {"display_name": "Disease/Pest Risk", "status": "unavailable", "dependencies": []},
    "irrigation_prediction": {"display_name": "Irrigation Prediction", "status": "unavailable", "dependencies": []},
    "farm_risk": {"display_name": "Farm Risk", "status": "unavailable", "dependencies": []},
    "market_price": {"display_name": "Market Price Forecasting", "status": "unavailable", "dependencies": []},
    "post_harvest_loss": {"display_name": "Post-Harvest Loss", "status": "unavailable", "dependencies": []},
    "npk_prediction": {"display_name": "NPK Prediction", "status": "unavailable", "dependencies": []}
}

class ModelOrchestrator:
    def __init__(self, crop_pipeline=None):
        self.crop_pipeline = crop_pipeline
        
    def _execute_crop_recommendation(self, context: Dict[str, Any]) -> ModelResult:
        farm = context.get("farm", {})
        season = context.get("season", {})
        irrig = context.get("irrigation_records", {})
        
        district = farm.get("location")
        season_name = season.get("season_name")
        water = irrig.get("water_availability")
        
        features = {
            "district": district,
            "season": season_name,
            "water_availability": water
        }
        
        if not district or not season_name or not water:
            return ModelResult(
                model_name="crop_recommendation",
                model_version="unknown",
                status="insufficient_data",
                inputs_used=features,
                data_provenance="digital_twin",
                timestamp=datetime.datetime.utcnow(),
                warnings=["Missing required inputs: district, season, or water_availability"]
            )
            
        try:
            if not self.crop_pipeline:
                from ml.main import pipeline_instance
                from ml.crop_recommendation.predict import PredictionPipeline
                self.crop_pipeline = pipeline_instance or PredictionPipeline()
                
            res = self.crop_pipeline.recommend(district, season_name, water)
            return ModelResult(
                model_name="crop_recommendation",
                model_version=res.get("model_version", "unknown"),
                status=res.get("status", "error"),
                prediction={"recommendations": res.get("recommendations", [])},
                unit="probability/rank",
                inputs_used=features,
                data_provenance="digital_twin",
                timestamp=datetime.datetime.utcnow(),
                warnings=[]
            )
        except Exception as e:
            return ModelResult(
                model_name="crop_recommendation",
                model_version="unknown",
                status="error",
                inputs_used=features,
                data_provenance="digital_twin",
                timestamp=datetime.datetime.utcnow(),
                warnings=[str(e)]
            )
            
    def _execute_cost_prediction(self, context: Dict[str, Any], cost_payload: Any) -> ModelResult:
        farm = context.get("farm", {})
        field = context.get("field", {})
        season = context.get("season", {})
        soil = context.get("soil_records", {})
        weather = context.get("weather_records", {})
        irrig = context.get("irrigation_records", {})
        
        payload = cost_payload or {}
        if hasattr(payload, "dict"):
            payload = payload.dict(exclude_unset=True)
            
        features = {
            "State": farm.get("location"),
            "Crop": season.get("crop"),
            "Season": season.get("season_name"),
            "Irrigation_Method": payload.get("irrigation_method", irrig.get("irrigation_method")),
            "Farm_Area_Hectares": field.get("area"),
            "Rainfall_mm": weather.get("rainfall"),
            "Avg_Temperature_C": weather.get("temperature"),
            "Humidity_pct": weather.get("humidity"),
            "Sunlight_Hours_Day": payload.get("sunlight_hours_day"),
            "Soil_pH": soil.get("ph"),
            "Soil_Moisture_pct": soil.get("moisture"),
            "Nitrogen_kg_ha": soil.get("nitrogen"),
            "Phosphorus_kg_ha": soil.get("phosphorus"),
            "Potassium_kg_ha": soil.get("potassium"),
            "Fertilizer_kg_ha": payload.get("fertilizer_kg_ha"),
            "Pesticide_Litre_ha": payload.get("pesticide_litre_ha"),
            "Seed_Quality_Score": payload.get("seed_quality_score"),
            "Water_Used_m3": payload.get("water_used_m3", irrig.get("irrigation_amount")),
            "Water_Efficiency_t_per_1000m3": payload.get("water_efficiency_t_per_1000m3"),
            "Disease_Pest_Risk_pct": payload.get("disease_pest_risk_pct")
        }
        
        missing_keys = [k for k, v in features.items() if v is None]
        if missing_keys:
            return ModelResult(
                model_name="cost_prediction",
                model_version="unknown",
                status="insufficient_data",
                inputs_used=features,
                data_provenance="digital_twin_and_user_input",
                timestamp=datetime.datetime.utcnow(),
                warnings=[f"Missing required inputs: {', '.join(missing_keys)}"]
            )
            
        try:
            from models.model6_cost_profit.inference import predict_cost
            result = predict_cost(features)
            return ModelResult(
                model_name="cost_prediction",
                model_version=result.get("model_type", "unknown"),
                status="success",
                prediction={
                    "predicted_total_cost_inr": result.get("predicted_total_cost_inr"),
                    "predicted_cost_per_hectare_inr": result.get("predicted_cost_per_hectare_inr")
                },
                unit="INR",
                inputs_used=features,
                data_provenance="digital_twin_and_user_input",
                timestamp=datetime.datetime.utcnow(),
                warnings=["Yield and Market Price models are not yet available. Profit and Revenue cannot be calculated at this time."]
            )
        except Exception as e:
            return ModelResult(
                model_name="cost_prediction",
                model_version="unknown",
                status="error",
                inputs_used=features,
                data_provenance="digital_twin_and_user_input",
                timestamp=datetime.datetime.utcnow(),
                warnings=[str(e)]
            )
            
    def orchestrate(self, requested_models: List[str], context: Dict[str, Any], payload: Any = None) -> Dict[str, ModelResult]:
        results = {}
        
        # 1. Validate requested models
        for m in requested_models:
            if m not in MODEL_REGISTRY:
                results[m] = ModelResult(
                    model_name=m,
                    model_version="unknown",
                    status="error",
                    prediction={},
                    inputs_used={},
                    data_provenance="orchestrator",
                    timestamp=datetime.datetime.utcnow(),
                    warnings=[f"Unknown model identifier: {m}"]
                )
            elif MODEL_REGISTRY[m]["status"] == "unavailable":
                results[m] = ModelResult(
                    model_name=m,
                    model_version="unknown",
                    status="unavailable",
                    prediction={},
                    inputs_used={},
                    data_provenance="orchestrator",
                    timestamp=datetime.datetime.utcnow(),
                    warnings=[f"{MODEL_REGISTRY[m]['display_name']} is currently unavailable."]
                )
                
        # 2. Execute available models (independent)
        if "crop_recommendation" in requested_models and "crop_recommendation" not in results:
            results["crop_recommendation"] = self._execute_crop_recommendation(context)
            
        if "cost_prediction" in requested_models and "cost_prediction" not in results:
            results["cost_prediction"] = self._execute_cost_prediction(context, payload.cost_prediction_inputs if payload else None)
            
        return results
