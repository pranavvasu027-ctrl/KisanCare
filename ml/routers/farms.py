from fastapi import APIRouter, HTTPException, Depends
from typing import List
from ml.schemas.farm import FarmCreate, FarmResponse, FieldCreate, FieldResponse, SeasonCreate, SeasonResponse, FarmContextResponse
from supabase import Client
from ml.auth import get_current_user_client

router = APIRouter(prefix="/api/v1/farms", tags=["Farms"])

@router.post("", response_model=FarmResponse)
def create_farm(farm: FarmCreate, db: Client = Depends(get_current_user_client)):
    data = farm.model_dump(exclude_unset=True)
    data["user_id"] = db.current_user_id
    res = db.table("farms").insert(data).execute()
    if not res.data:
        raise HTTPException(status_code=400, detail="Failed to create farm")
    return res.data[0]

@router.get("", response_model=List[FarmResponse])
def get_farms(db: Client = Depends(get_current_user_client)):
    # RLS ensures user only sees their own farms, but we explicitly filter anyway for safety
    res = db.table("farms").select("*").eq("user_id", db.current_user_id).execute()
    return res.data

@router.get("/{farm_id}", response_model=FarmResponse)
def get_farm(farm_id: str, db: Client = Depends(get_current_user_client)):
    res = db.table("farms").select("*").eq("id", farm_id).eq("user_id", db.current_user_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Farm not found")
    return res.data[0]

@router.put("/{farm_id}", response_model=FarmResponse)
def update_farm(farm_id: str, farm: FarmCreate, db: Client = Depends(get_current_user_client)):
    data = farm.model_dump(exclude_unset=True)
    res = db.table("farms").update(data).eq("id", farm_id).eq("user_id", db.current_user_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Farm not found or update failed")
    return res.data[0]

@router.post("/{farm_id}/fields", response_model=FieldResponse)
def create_field(farm_id: str, field: FieldCreate, db: Client = Depends(get_current_user_client)):
    # Verify farm ownership first
    farm_res = db.table("farms").select("id").eq("id", farm_id).eq("user_id", db.current_user_id).execute()
    if not farm_res.data:
         raise HTTPException(status_code=403, detail="Not authorized to add fields to this farm")
    
    data = field.model_dump(exclude_unset=True)
    data["farm_id"] = farm_id
    res = db.table("fields").insert(data).execute()
    if not res.data:
        raise HTTPException(status_code=400, detail="Failed to create field")
    return res.data[0]

@router.get("/{farm_id}/fields", response_model=List[FieldResponse])
def get_fields(farm_id: str, db: Client = Depends(get_current_user_client)):
    # Verify farm ownership
    farm_res = db.table("farms").select("id").eq("id", farm_id).eq("user_id", db.current_user_id).execute()
    if not farm_res.data:
         raise HTTPException(status_code=403, detail="Not authorized")
         
    res = db.table("fields").select("*").eq("farm_id", farm_id).execute()
    return res.data

@router.put("/fields/{field_id}", response_model=FieldResponse)
def update_field(field_id: str, field: FieldCreate, db: Client = Depends(get_current_user_client)):
    # Verify field ownership through farm
    res_field = db.table("fields").select("id, farms!inner(user_id)").eq("id", field_id).eq("farms.user_id", db.current_user_id).execute()
    if not res_field.data:
        raise HTTPException(status_code=403, detail="Field not found or not authorized")
        
    data = field.model_dump(exclude_unset=True)
    res = db.table("fields").update(data).eq("id", field_id).execute()
    return res.data[0]

@router.post("/fields/{field_id}/seasons", response_model=SeasonResponse)
def create_season(field_id: str, season: SeasonCreate, db: Client = Depends(get_current_user_client)):
    # Verify field ownership
    res_field = db.table("fields").select("id, farms!inner(user_id)").eq("id", field_id).eq("farms.user_id", db.current_user_id).execute()
    if not res_field.data:
        raise HTTPException(status_code=403, detail="Not authorized to add seasons to this field")
        
    data = season.model_dump(exclude_unset=True)
    data["field_id"] = field_id
    res = db.table("seasons").insert(data).execute()
    if not res.data:
        raise HTTPException(status_code=400, detail="Failed to create season")
    return res.data[0]

@router.get("/fields/{field_id}/seasons", response_model=List[SeasonResponse])
def get_seasons(field_id: str, db: Client = Depends(get_current_user_client)):
    # Verify field ownership
    res_field = db.table("fields").select("id, farms!inner(user_id)").eq("id", field_id).eq("farms.user_id", db.current_user_id).execute()
    if not res_field.data:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    res = db.table("seasons").select("*").eq("field_id", field_id).execute()
    return res.data

@router.put("/seasons/{season_id}", response_model=SeasonResponse)
def update_season(season_id: str, season: SeasonCreate, db: Client = Depends(get_current_user_client)):
    # Verify season ownership
    res_season = db.table("seasons").select("id, fields!inner(farms!inner(user_id))").eq("id", season_id).eq("fields.farms.user_id", db.current_user_id).execute()
    if not res_season.data:
        raise HTTPException(status_code=403, detail="Season not found or not authorized")
        
    data = season.model_dump(exclude_unset=True)
    res = db.table("seasons").update(data).eq("id", season_id).execute()
    return res.data[0]

@router.get("/{farm_id}/context", response_model=FarmContextResponse)
def get_farm_context(farm_id: str, db: Client = Depends(get_current_user_client)):
    # Single query to get farm, fields, and seasons using PostgREST embedding
    res = db.table("farms").select("*, fields(*, seasons(*))").eq("id", farm_id).eq("user_id", db.current_user_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Farm context not found")
        
    return res.data[0]

from ml.schemas.prediction import ModelResult
from datetime import datetime

def get_crop_pipeline():
    from ml.main import pipeline_instance
    from ml.crop_recommendation.predict import PredictionPipeline
    return pipeline_instance or PredictionPipeline()

@router.get("/{farm_id}/fields/{field_id}/seasons/{season_id}/recommend-crops", response_model=ModelResult)
def recommend_crops_for_season(farm_id: str, field_id: str, season_id: str, db: Client = Depends(get_current_user_client)):
    # 1. Validate ownership and fetch farm context
    res = db.table("farms").select("location, fields!inner(id, irrigation_records(water_availability), seasons!inner(id, season_name))") \
        .eq("id", farm_id).eq("user_id", db.current_user_id) \
        .eq("fields.id", field_id).eq("fields.seasons.id", season_id).execute()
        
    if not res.data:
        raise HTTPException(status_code=404, detail="Farm context not found or not authorized")
        
    farm_data = res.data[0]
    district = farm_data.get("location")
    
    field_data = farm_data.get("fields", [])[0]
    season_data = field_data.get("seasons", [])[0]
    season = season_data.get("season_name")
    
    irrigation_records = field_data.get("irrigation_records", [])
    water = None
    if irrigation_records:
        water = irrigation_records[-1].get("water_availability")
        
    inputs = {
        "district": district,
        "season": season,
        "water_availability": water
    }
    
    if not district or not season or not water:
        return ModelResult(
            model_name="crop_recommendation",
            model_version="unknown",
            status="insufficient_data",
            inputs_used=inputs,
            data_provenance="database",
            timestamp=datetime.utcnow(),
            warnings=["Missing one of: location (district), season_name, or water_availability"]
        )
        
    pipeline = get_crop_pipeline()
    result = pipeline.recommend(
        district=district.upper(),
        season=season,
        water_availability=water
    )
    
    if result.get("status") == "ERROR":
        return ModelResult(
            model_name="crop_recommendation",
            model_version=result.get("model_version", "unknown"),
            status="error",
            inputs_used=inputs,
            data_provenance="database",
            timestamp=datetime.utcnow(),
            warnings=[result.get("reason")]
        )
        
    top_crop = None
    if result.get("recommendations"):
        top_crop = result["recommendations"][0]["crop"]
        
    model_result = ModelResult(
        model_name="crop_recommendation",
        model_version=result.get("model_version", "unknown"),
        status="success",
        prediction={"top_recommendation": top_crop, "all_recommendations": result.get("recommendations")},
        inputs_used=inputs,
        data_provenance=result.get("data_source", "APY_2005_2015"),
        timestamp=datetime.utcnow()
    )
    
    # 2. Persist prediction
    # Using standard service role database dependency to save internal prediction if needed, or user client.
    # We can just use the user client as it bypasses RLS for insert if RLS allows users to insert their own.
    # The table model_predictions has policy: "Users can access own predictions" but maybe not INSERT?
    # Actually, RLS generally allows INSERT for authenticated users with their own farm_id.
    try:
        db.table("model_predictions").insert({
            "farm_id": farm_id,
            "field_id": field_id,
            "season_id": season_id,
            "model_name": "crop_recommendation",
            "model_version": result.get("model_version", "unknown"),
            "prediction": model_result.prediction,
            "data_provenance": model_result.data_provenance
        }).execute()
    except Exception as e:
        model_result.warnings.append(f"Failed to persist prediction: {str(e)}")
        
    return model_result

from ml.schemas.prediction import CostPredictionRequest

@router.post("/{farm_id}/fields/{field_id}/seasons/{season_id}/predict-cost", response_model=ModelResult)
def predict_cost_for_season(farm_id: str, field_id: str, season_id: str, payload: CostPredictionRequest, db: Client = Depends(get_current_user_client)):
    # 1. Fetch entire farm context
    res = db.table("farms").select(
        "location, fields!inner(id, area, seasons!inner(id, season_name, crop), "
        "soil_records(ph, moisture, nitrogen, phosphorus, potassium), "
        "weather_records(temperature, rainfall, humidity), "
        "irrigation_records(irrigation_method, irrigation_amount))"
    ).eq("id", farm_id).eq("user_id", db.current_user_id) \
     .eq("fields.id", field_id).eq("fields.seasons.id", season_id).execute()
     
    if not res.data:
        raise HTTPException(status_code=404, detail="Farm context not found or not authorized")
        
    farm = res.data[0]
    field = farm.get("fields", [])[0]
    season = field.get("seasons", [])[0]
    
    # Latest records
    soil = field.get("soil_records", [])[-1] if field.get("soil_records") else {}
    weather = field.get("weather_records", [])[-1] if field.get("weather_records") else {}
    irrig = field.get("irrigation_records", [])[-1] if field.get("irrigation_records") else {}
    
    # 2. Map Features
    features = {
        "State": farm.get("location"),  # Using location as proxy for State/District
        "Crop": season.get("crop"),
        "Season": season.get("season_name"),
        "Irrigation_Method": payload.irrigation_method if payload.irrigation_method is not None else irrig.get("irrigation_method"),
        "Farm_Area_Hectares": field.get("area"),
        "Rainfall_mm": weather.get("rainfall"),
        "Avg_Temperature_C": weather.get("temperature"),
        "Humidity_pct": weather.get("humidity"),
        "Sunlight_Hours_Day": payload.sunlight_hours_day,
        "Soil_pH": soil.get("ph"),
        "Soil_Moisture_pct": soil.get("moisture"),
        "Nitrogen_kg_ha": soil.get("nitrogen"),
        "Phosphorus_kg_ha": soil.get("phosphorus"),
        "Potassium_kg_ha": soil.get("potassium"),
        "Fertilizer_kg_ha": payload.fertilizer_kg_ha,
        "Pesticide_Litre_ha": payload.pesticide_litre_ha,
        "Seed_Quality_Score": payload.seed_quality_score,
        "Water_Used_m3": payload.water_used_m3 if payload.water_used_m3 is not None else irrig.get("irrigation_amount"),
        "Water_Efficiency_t_per_1000m3": payload.water_efficiency_t_per_1000m3,
        "Disease_Pest_Risk_pct": payload.disease_pest_risk_pct
    }
    
    # 3. Check for missing data
    missing_keys = [k for k, v in features.items() if v is None]
    if missing_keys:
        return ModelResult(
            model_name="cost_profit_model",
            model_version="unknown",
            status="insufficient_data",
            inputs_used=features,
            data_provenance="digital_twin_and_user_input",
            timestamp=datetime.utcnow(),
            warnings=[f"Missing required inputs: {', '.join(missing_keys)}"]
        )
        
    # 4. Import and run model
    try:
        from models.model6_cost_profit.inference import predict_cost
        result = predict_cost(features)
    except FileNotFoundError as e:
        return ModelResult(
            model_name="cost_profit_model",
            model_version="unknown",
            status="unavailable",
            inputs_used=features,
            data_provenance="digital_twin_and_user_input",
            timestamp=datetime.utcnow(),
            warnings=[str(e)]
        )
    except (ValueError, TypeError) as e:
        return ModelResult(
            model_name="cost_profit_model",
            model_version="unknown",
            status="error",
            inputs_used=features,
            data_provenance="digital_twin_and_user_input",
            timestamp=datetime.utcnow(),
            warnings=[str(e)]
        )
    except Exception as e:
        return ModelResult(
            model_name="cost_profit_model",
            model_version="unknown",
            status="error",
            inputs_used=features,
            data_provenance="digital_twin_and_user_input",
            timestamp=datetime.utcnow(),
            warnings=[f"Inference failed: {str(e)}"]
        )
        
    # 5. Success response mapping
    warnings = []
    warnings.append("Yield and Market Price models are not yet available. Profit and Revenue cannot be calculated at this time.")
    
    model_result = ModelResult(
        model_name="cost_profit_model",
        model_version=result.get("model_type", "HistGradientBoosting_Prototype"),
        status="success",
        prediction={
            "predicted_total_cost_inr": result.get("predicted_total_cost_inr"),
            "predicted_cost_per_hectare_inr": result.get("predicted_cost_per_hectare_inr")
        },
        unit="INR",
        inputs_used=features,
        data_provenance="digital_twin_and_user_input",
        timestamp=datetime.utcnow(),
        warnings=warnings
    )
    
    # 6. Persist to DB
    try:
        db.table("model_predictions").insert({
            "farm_id": farm_id,
            "field_id": field_id,
            "season_id": season_id,
            "model_name": "cost_profit_model",
            "model_version": model_result.model_version,
            "prediction": model_result.prediction,
            "data_provenance": model_result.data_provenance
        }).execute()
    except Exception as e:
        model_result.warnings.append(f"Failed to persist prediction: {str(e)}")
        
    return model_result

from ml.schemas.orchestrator import OrchestrationRequest, OrchestrationResponse
from ml.orchestrator import ModelOrchestrator

@router.post("/{farm_id}/fields/{field_id}/seasons/{season_id}/orchestrate", response_model=OrchestrationResponse)
def orchestrate_models(farm_id: str, field_id: str, season_id: str, payload: OrchestrationRequest, db: Client = Depends(get_current_user_client)):
    # 1. Fetch entire farm context
    res = db.table("farms").select(
        "location, fields!inner(id, area, seasons!inner(id, season_name, crop), "
        "soil_records(ph, moisture, nitrogen, phosphorus, potassium), "
        "weather_records(temperature, rainfall, humidity), "
        "irrigation_records(irrigation_method, irrigation_amount, water_availability))"
    ).eq("id", farm_id).eq("user_id", db.current_user_id) \
     .eq("fields.id", field_id).eq("fields.seasons.id", season_id).execute()
     
    if not res.data:
        raise HTTPException(status_code=404, detail="Farm context not found or not authorized")
        
    farm = res.data[0]
    field = farm.get("fields", [])[0]
    season = field.get("seasons", [])[0]
    
    # Latest records
    soil = field.get("soil_records", [])[-1] if field.get("soil_records") else {}
    weather = field.get("weather_records", [])[-1] if field.get("weather_records") else {}
    irrig = field.get("irrigation_records", [])[-1] if field.get("irrigation_records") else {}
    
    context = {
        "farm": farm,
        "field": field,
        "season": season,
        "soil_records": soil,
        "weather_records": weather,
        "irrigation_records": irrig
    }
    
    # 2. Run Orchestrator
    orchestrator = ModelOrchestrator()
    results = orchestrator.orchestrate(payload.models, context, payload)
    
    # 3. Persist successful ones
    for m_id, m_res in results.items():
        if m_res.status == "success":
            try:
                db.table("model_predictions").insert({
                    "farm_id": farm_id,
                    "field_id": field_id,
                    "season_id": season_id,
                    "model_name": m_res.model_name,
                    "model_version": m_res.model_version,
                    "prediction": m_res.prediction,
                    "data_provenance": m_res.data_provenance
                }).execute()
            except Exception as e:
                m_res.warnings.append(f"Persistence failed: {str(e)}")
                
    # 4. Overall status
    all_success = all(r.status == "success" for r in results.values())
    any_error = any(r.status == "error" for r in results.values())
    overall = "error" if any_error else ("success" if all_success else "partial")
    
    return OrchestrationResponse(
        status=overall,
        farm_id=farm_id,
        field_id=field_id,
        season_id=season_id,
        results=results
    )

from ml.schemas.decision import DecisionRequest, DecisionResponse
from ml.decision_engine import DecisionEngine

@router.post("/{farm_id}/fields/{field_id}/seasons/{season_id}/decide", response_model=DecisionResponse)
def get_decision(farm_id: str, field_id: str, season_id: str, req: DecisionRequest, db: Client = Depends(get_current_user_client)):
    # 1. Fetch entire farm context
    res = db.table("farms").select(
        "location, fields!inner(id, area, seasons!inner(id, season_name, crop), "
        "soil_records(ph, moisture, nitrogen, phosphorus, potassium), "
        "weather_records(temperature, rainfall, humidity), "
        "irrigation_records(irrigation_method, irrigation_amount, water_availability))"
    ).eq("id", farm_id).eq("user_id", db.current_user_id) \
     .eq("fields.id", field_id).eq("fields.seasons.id", season_id).execute()
     
    if not res.data:
        raise HTTPException(status_code=404, detail="Farm context not found or not authorized")
        
    farm = res.data[0]
    field = farm.get("fields", [])[0]
    season = field.get("seasons", [])[0]
    
    # Latest records
    soil = field.get("soil_records", [])[-1] if field.get("soil_records") else {}
    weather = field.get("weather_records", [])[-1] if field.get("weather_records") else {}
    irrig = field.get("irrigation_records", [])[-1] if field.get("irrigation_records") else {}
    
    context = {
        "farm": farm,
        "field": field,
        "season": season,
        "soil_records": soil,
        "weather_records": weather,
        "irrigation_records": irrig
    }
    
    # 2. Run Orchestrator natively to get trusted results
    # We do NOT trust client-submitted predictions. We fetch them live here.
    # We only run the models relevant for the requested decision.
    models_to_run = ["crop_recommendation", "cost_prediction"]
    
    orchestrator = ModelOrchestrator()
    orch_req = OrchestrationRequest(models=models_to_run, cost_prediction_inputs=req.cost_prediction_inputs)
    results = orchestrator.orchestrate(models_to_run, context, orch_req)
    
    # 3. Decision Engine
    engine = DecisionEngine()
    decision = engine.generate_decision(req, results)
    
    # 4. Persistence (optional, if we had a decisions table, we would save it here)
    # We persist the model outputs using the orchestrator's standard flow
    for m_id, m_res in results.items():
        if m_res.status == "success":
            try:
                db.table("model_predictions").insert({
                    "farm_id": farm_id,
                    "field_id": field_id,
                    "season_id": season_id,
                    "model_name": m_res.model_name,
                    "model_version": m_res.model_version,
                    "prediction": m_res.prediction,
                    "data_provenance": "decision_engine"
                }).execute()
            except Exception:
                pass
                
    return decision
