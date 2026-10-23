"""Agricultural intelligence tool interfaces for KisanCare AI Copilot.
Exposes validated backend ML models and heuristic agronomic engines
as callable tools for Google Gemini.
"""
from __future__ import annotations

import os
from contextvars import ContextVar
from typing import Any, Dict, List, Optional

# Context tracker for model invocations during a single Copilot turn
_current_turn_evidence: List[Dict[str, Any]] = []


def get_turn_evidence() -> List[Dict[str, Any]]:
    global _current_turn_evidence
    return list(_current_turn_evidence)


def reset_turn_evidence():
    global _current_turn_evidence
    _current_turn_evidence = []


def _record_tool_execution(tool_name: str, arguments: Dict[str, Any], result: Dict[str, Any], provenance: str):
    global _current_turn_evidence
    _current_turn_evidence.append({
        "tool_name": tool_name,
        "arguments": arguments,
        "result": result,
        "provenance": provenance
    })


def query_market_price(crop: str, market: str, date: str) -> Dict[str, Any]:
    """Query forecast or historical mandi market prices for a crop at an APMC market using KisanCare's trained XGBoost model.

    Args:
        crop: Crop name (e.g., 'onion', 'tomato', 'potato', 'cotton', 'soybean').
        market: Target APMC mandi (e.g., 'Pune(Pimpri)', 'Pune', 'Mumbai', 'Nashik', 'Nagpur', 'Akot').
        date: Reference date in YYYY-MM-DD format (e.g., '2024-07-29').
    """
    try:
        from ml.market_price.predict import MarketPricePredictor
        models_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "models"))
        mp = MarketPricePredictor(models_dir=models_dir)
        res = mp.predict(crop=crop, market=market, date_str=date)
        _record_tool_execution(
            tool_name="query_market_price",
            arguments={"crop": crop, "market": market, "date": date},
            result=res,
            provenance="TRAINED_XGBOOST"
        )
        return res
    except Exception as exc:
        err = {"status": "error", "message": f"Market price model error: {str(exc)}"}
        _record_tool_execution("query_market_price", {"crop": crop, "market": market, "date": date}, err, "ERROR")
        return err


def get_crop_recommendations(district: str, season: str, water_availability: str, top_k: int = 5) -> Dict[str, Any]:
    """Get scientifically suitable crop recommendations for a district and season using KisanCare's trained Random Forest model.

    Args:
        district: District name in Maharashtra (e.g., 'NASHIK', 'PUNE', 'AKOLA', 'NAGPUR', 'AMRAVATI').
        season: Farming season ('Kharif', 'Rabi', 'Summer', or 'Whole Year').
        water_availability: Water availability level ('Low', 'Medium', or 'High').
        top_k: Number of recommendations to return (1-20, default 5).
    """
    try:
        from ml.crop_recommendation.predict import PredictionPipeline
        p = PredictionPipeline()
        res = p.recommend(
            district=district.strip().upper(),
            season=season.strip(),
            water_availability=water_availability.strip(),
            top_k=min(max(top_k, 1), 10)
        )
        _record_tool_execution(
            tool_name="get_crop_recommendations",
            arguments={"district": district, "season": season, "water_availability": water_availability, "top_k": top_k},
            result=res,
            provenance="TRAINED_RANDOM_FOREST"
        )
        return res
    except Exception as exc:
        err = {"status": "error", "message": f"Crop recommendation model error: {str(exc)}"}
        _record_tool_execution("get_crop_recommendations", {"district": district, "season": season}, err, "ERROR")
        return err


def assess_soil_nutrients(nitrogen: float, phosphorus: float, potassium: float, ph: float) -> Dict[str, Any]:
    """Evaluate soil NPK and pH values using KisanCare's agronomic heuristic decision model.

    Args:
        nitrogen: Soil available Nitrogen (N) in kg/ha or test units.
        phosphorus: Soil available Phosphorus (P) in kg/ha or test units.
        potassium: Soil available Potassium (K) in kg/ha or test units.
        ph: Soil pH measurement (0.0 to 14.0).
    """
    try:
        from ml.rule_based.engine import RuleBasedModels
        res = RuleBasedModels.assess_soil_nutrients(nitrogen, phosphorus, potassium, ph)
        _record_tool_execution(
            tool_name="assess_soil_nutrients",
            arguments={"nitrogen": nitrogen, "phosphorus": phosphorus, "potassium": potassium, "ph": ph},
            result=res,
            provenance="AGRONOMIC_HEURISTIC_SYSTEM"
        )
        return res
    except Exception as exc:
        err = {"status": "error", "message": f"Soil assessment error: {str(exc)}"}
        _record_tool_execution("assess_soil_nutrients", {"ph": ph}, err, "ERROR")
        return err


def diagnose_crop_disease(crop: str, symptoms: List[str]) -> Dict[str, Any]:
    """Diagnose crop disease from farmer-observed visual symptoms using KisanCare's expert rule-based diagnostic engine.

    Args:
        crop: Crop name (e.g., 'Cotton', 'Soybean', 'Wheat', 'Tomato').
        symptoms: List of observed leaf/stem/fruit symptoms (e.g. ['yellow leaves', 'stunted growth', 'white powdery spots', 'black spots']).
    """
    try:
        from ml.rule_based.engine import RuleBasedModels
        res = RuleBasedModels.detect_disease(symptoms=symptoms, crop=crop)
        _record_tool_execution(
            tool_name="diagnose_crop_disease",
            arguments={"crop": crop, "symptoms": symptoms},
            result=res,
            provenance="RULE_BASED_EXPERT_SYSTEM"
        )
        return res
    except Exception as exc:
        err = {"status": "error", "message": f"Disease diagnostic error: {str(exc)}"}
        _record_tool_execution("diagnose_crop_disease", {"crop": crop, "symptoms": symptoms}, err, "ERROR")
        return err


def diagnose_crop_pest(crop: str, symptoms: List[str]) -> Dict[str, Any]:
    """Diagnose crop pests from damage symptoms using KisanCare's expert pest diagnostic engine.

    Args:
        crop: Crop name (e.g., 'Cotton', 'Soybean', 'Wheat').
        symptoms: Observed damage symptoms (e.g. ['holes in leaves', 'sticky residue', 'curled leaves']).
    """
    try:
        from ml.rule_based.engine import RuleBasedModels
        res = RuleBasedModels.detect_pest(symptoms=symptoms, crop=crop)
        _record_tool_execution(
            tool_name="diagnose_crop_pest",
            arguments={"crop": crop, "symptoms": symptoms},
            result=res,
            provenance="RULE_BASED_EXPERT_SYSTEM"
        )
        return res
    except Exception as exc:
        err = {"status": "error", "message": f"Pest diagnostic error: {str(exc)}"}
        _record_tool_execution("diagnose_crop_pest", {"crop": crop, "symptoms": symptoms}, err, "ERROR")
        return err


def recommend_irrigation(crop: str, soil_moisture_percent: float, days_since_rain: int) -> Dict[str, Any]:
    """Determine irrigation requirement and volume based on crop type, soil moisture %, and days since rain.

    Args:
        crop: Crop name (e.g., 'Cotton', 'Wheat', 'Rice', 'Soybean').
        soil_moisture_percent: Measured soil moisture percentage (0.0 to 100.0).
        days_since_rain: Number of days elapsed since the last measurable rainfall.
    """
    try:
        from ml.rule_based.engine import RuleBasedModels
        res = RuleBasedModels.recommend_irrigation(
            crop=crop,
            soil_moisture=soil_moisture_percent,
            days_since_rain=days_since_rain
        )
        _record_tool_execution(
            tool_name="recommend_irrigation",
            arguments={"crop": crop, "soil_moisture_percent": soil_moisture_percent, "days_since_rain": days_since_rain},
            result=res,
            provenance="AGRO_CLIMATIC_HEURISTIC"
        )
        return res
    except Exception as exc:
        err = {"status": "error", "message": f"Irrigation recommendation error: {str(exc)}"}
        _record_tool_execution("recommend_irrigation", {"crop": crop}, err, "ERROR")
        return err


def assess_weather_risk(temperature_c: float, humidity_percent: float, rainfall_forecast_mm: float) -> Dict[str, Any]:
    """Evaluate meteorological stress risks (heat, frost, fungal, flooding) for standing crops.

    Args:
        temperature_c: Forecast temperature in degrees Celsius.
        humidity_percent: Forecast relative humidity percentage (0-100).
        rainfall_forecast_mm: Forecast rainfall accumulation in mm.
    """
    try:
        from ml.rule_based.engine import RuleBasedModels
        res = RuleBasedModels.assess_weather_risk(
            temp=temperature_c,
            humidity=humidity_percent,
            rainfall_forecast=rainfall_forecast_mm
        )
        _record_tool_execution(
            tool_name="assess_weather_risk",
            arguments={"temperature_c": temperature_c, "humidity_percent": humidity_percent, "rainfall_forecast_mm": rainfall_forecast_mm},
            result=res,
            provenance="METEOROLOGICAL_RULE_BASED"
        )
        return res
    except Exception as exc:
        err = {"status": "error", "message": f"Weather risk assessment error: {str(exc)}"}
        _record_tool_execution("assess_weather_risk", {"temperature_c": temperature_c}, err, "ERROR")
        return err


def estimate_post_harvest_storage_loss(crop: str, quantity_quintals: float, storage_type: str, storage_days: int) -> Dict[str, Any]:
    """Estimate expected storage loss and monetary impact using ICAR/CIPHET loss benchmarks.

    Args:
        crop: Stored crop ('Wheat', 'Cotton', 'Soybean', etc.).
        quantity_quintals: Stored quantity in quintals.
        storage_type: Storage structure (e.g. 'Hermetic Bag', 'Warehouse', 'Traditional Shed').
        storage_days: Planned duration of storage in days.
    """
    base_rate = 0.03 if crop == "Wheat" else (0.05 if crop in ["Soybean", "Cotton"] else 0.15)
    storage_mult = 0.4 if ("Hermetic" in storage_type or "Cold" in storage_type) else (1.3 if "Shed" in storage_type else 1.0)
    days_factor = storage_days / 60.0
    calc_loss_pct = min(round(base_rate * days_factor * storage_mult * 100 * 10) / 10, 45.0) if storage_days > 0 else 0.0
    lost_qtl = round((quantity_quintals * (calc_loss_pct / 100)) * 10) / 10
    price_per_qtl = 8000 if crop == "Cotton" else (4650 if crop == "Soybean" else 2340)
    financial_loss = round(lost_qtl * price_per_qtl)

    res = {
        "crop": crop,
        "quantity_quintals": quantity_quintals,
        "storage_type": storage_type,
        "storage_days": storage_days,
        "loss_percentage": calc_loss_pct,
        "quantity_lost_qtl": lost_qtl,
        "financial_loss_rs": financial_loss,
        "spoilage_risk": "Low" if calc_loss_pct < 3 else ("Moderate" if calc_loss_pct < 8 else "High")
    }
    _record_tool_execution(
        tool_name="estimate_post_harvest_storage_loss",
        arguments={"crop": crop, "quantity_quintals": quantity_quintals, "storage_type": storage_type, "storage_days": storage_days},
        result=res,
        provenance="ICAR_CIPHET_BENCHMARK"
    )
    return res


AGRICULTURAL_TOOLS = [
    query_market_price,
    get_crop_recommendations,
    assess_soil_nutrients,
    diagnose_crop_disease,
    diagnose_crop_pest,
    recommend_irrigation,
    assess_weather_risk,
    estimate_post_harvest_storage_loss
]
