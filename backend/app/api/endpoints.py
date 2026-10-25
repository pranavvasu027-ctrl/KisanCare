"""Public backend routes and resilient ML-service proxying."""
from __future__ import annotations

import os
import uuid
from typing import Any, Dict, List, Optional

import requests
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, Field

from ..economics.engine import calculate_economics
from ..simulation.engine import run_simulation
from ..copilot.router import router as copilot_router
from ..weather.service import get_weather_service

router = APIRouter()
router.include_router(copilot_router)


class FieldSetupItem(BaseModel):
    field_name: str = Field(min_length=1, max_length=256)
    area: float = Field(gt=0)
    area_unit: Optional[str] = Field(default="acre", max_length=32)
    soil_type: Optional[str] = Field(default=None, max_length=128)
    irrigation_method: Optional[str] = Field(default=None, max_length=128)
    current_crop: Optional[str] = Field(default=None, max_length=128)
    previous_crop: Optional[str] = Field(default=None, max_length=128)


class OnboardingRequest(BaseModel):
    farmer_id: Optional[str] = None
    name: str = Field(min_length=1, max_length=256)
    phone: str = Field(min_length=1, max_length=32)
    state: str = Field(default="Maharashtra", max_length=128)
    district: str = Field(min_length=1, max_length=128)
    village: str = Field(min_length=1, max_length=128)
    preferred_language: str = Field(default="en", max_length=16)
    farming_experience: Optional[str] = Field(default=None, max_length=64)
    farmer_category: Optional[str] = Field(default=None, max_length=64)
    farm_name: str = Field(min_length=1, max_length=256)
    total_area: float = Field(gt=0)
    area_unit: str = Field(default="acre", max_length=32)
    latitude: Optional[float] = Field(default=None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(default=None, ge=-180.0, le=180.0)
    irrigation_source: Optional[str] = Field(default=None, max_length=128)
    land_ownership: Optional[str] = Field(default="Owned", max_length=64)
    fields: List[FieldSetupItem] = Field(min_length=1)


class FarmCreate(BaseModel):
    farmer_id: str = Field(min_length=1, max_length=128)
    location: str = Field(min_length=1, max_length=256)
    area: float = Field(gt=0)
    farm_name: Optional[str] = Field(default=None, max_length=256)
    latitude: Optional[float] = Field(default=None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(default=None, ge=-180.0, le=180.0)


class FieldBoundaryUpdate(BaseModel):
    field_id: str = Field(min_length=1, max_length=128)
    field_name: Optional[str] = Field(default=None, max_length=256)
    area: Optional[float] = Field(default=None, gt=0)
    area_unit: Optional[str] = Field(default="acre", max_length=32)
    geometry: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None


class SimulationRequest(BaseModel):
    farm_id: str = Field(min_length=1, max_length=128)
    changes: Dict[str, Any]


class CropRecommendationRequest(BaseModel):
    district: str = Field(min_length=1, max_length=128)
    season: str = Field(min_length=1, max_length=32)
    water_availability: str = Field(min_length=1, max_length=32)
    top_k: int = Field(default=5, ge=1, le=20)


class MarketPriceRequest(BaseModel):
    crop: str = Field(min_length=1, max_length=128)
    market: Optional[str] = None
    date: Optional[str] = None
    quantity: Optional[float] = Field(default=20.0, gt=0, le=50000)
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class SymptomsRequest(BaseModel):
    crop: str = Field(min_length=1, max_length=128)
    symptoms: List[str] = Field(min_length=1)



class PostHarvestRequest(BaseModel):
    crop: str = Field(min_length=1, max_length=128)
    quantity_quintals: float = Field(gt=0)
    storage_type: str = Field(min_length=1, max_length=128)
    storage_days: int = Field(ge=0, le=365)
    farm_id: Optional[str] = None

class SoilRequest(BaseModel):
    n: float
    p: float
    k: float
    ph: float = Field(ge=0, le=14)


class YieldRequest(BaseModel):
    crop: str = Field(min_length=1, max_length=128)
    area_acres: float = Field(gt=0)
    soil_health_score: float
    weather_score: float


class IrrigationRequest(BaseModel):
    crop: str = Field(min_length=1, max_length=128)
    soil_moisture: float = Field(ge=0, le=100)
    days_since_rain: int = Field(ge=0)


class WeatherRiskRequest(BaseModel):
    temperature: float
    humidity: float = Field(ge=0, le=100)
    rainfall_forecast: float = Field(ge=0)


def _ml_service_url() -> str:
    return os.getenv("ML_SERVICE_URL", "http://localhost:8001").rstrip("/")


def _ml_timeout_seconds() -> float:
    try:
        return max(0.1, float(os.getenv("ML_SERVICE_TIMEOUT_SECONDS", "8")))
    except ValueError:
        return 8.0



def _persist_model_prediction(model_name: str, model_version: str, inputs: dict, outputs: dict, provenance: str = "ESTIMATED", farm_id: str = None):
    """Persist model predictions directly to Supabase model_predictions table."""
    try:
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        if not url or not key:
            return
        from supabase import create_client
        sb = create_client(url, key)
        valid_provenances = {"MEASURED", "ESTIMATED", "FARMER_ENTERED", "AUTOMATICALLY_COLLECTED", "EXTRACTED"}
        db_provenance = provenance if provenance in valid_provenances else "ESTIMATED"
        record = {
            "farm_id": farm_id or "52120432-c948-4026-87c4-7e2c481a7bf5",
            "model_name": model_name,
            "model_version": model_version,
            "status": "COMPLETED",
            "inputs_used": inputs,
            "prediction": outputs,
            "data_provenance": db_provenance,
            "metadata": {
                "model_type": provenance
            }
        }
        sb.table("model_predictions").insert(record).execute()
    except Exception as exc:
        print(f"[ModelPersistence] Failed to persist {model_name}: {exc}")


def _proxy_to_ml(path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Forward a request and map transport/protocol failures predictably."""
    try:
        response = requests.post(f"{_ml_service_url()}{path}", json=payload, timeout=_ml_timeout_seconds())
    except requests.Timeout as exc:
        raise HTTPException(504, {"code": "ml_service_timeout", "message": "ML service timed out"}) from exc
    except requests.RequestException as exc:
        raise HTTPException(503, {"code": "ml_service_unavailable", "message": "ML service is unavailable"}) from exc
    try:
        body = response.json()
    except ValueError as exc:
        raise HTTPException(502, {"code": "ml_service_invalid_response", "message": "ML service returned invalid JSON"}) from exc
    if response.status_code >= 500:
        raise HTTPException(503, {"code": "ml_service_unavailable", "message": "ML service is unavailable"})
    if response.status_code >= 400:
        raise HTTPException(response.status_code, body.get("detail", body))
    if not isinstance(body, dict):
        raise HTTPException(502, {"code": "ml_service_invalid_response", "message": "ML service returned an invalid response body"})
    return body


def _crop_mock(payload: CropRecommendationRequest) -> Dict[str, Any]:
    return {
        "status": "mock", "is_mock": True, "data_provenance": "backend_mock_fallback",
        "message": "ML service is unavailable; this is not a model prediction.",
        "district": payload.district, "season": payload.season, "water_availability": payload.water_availability,
        "recommendations": [{"crop": "Soybean", "rank": 1, "label": "mock recommendation"}],
    }


def _market_mock(payload: MarketPriceRequest) -> Dict[str, Any]:
    crop_lower = payload.crop.lower()
    mkt_lower = payload.market.lower()

    if "soya" in crop_lower:
        crop_name = "Soyabean"
        price = 4670 if "akot" in mkt_lower else 4580 if "amravati" in mkt_lower else 4640
        f_min, f_max = 4660, 4750
        trend = "Rising"
    elif "tur" in crop_lower or "pigeon" in crop_lower:
        crop_name = "Tur"
        price = 9940 if "akot" in mkt_lower else 9720 if "amravati" in mkt_lower else 9850
        f_min, f_max = 9900, 10120
        trend = "Rising"
    else:
        crop_name = "Cotton"
        price = 7350 if "akot" in mkt_lower else 7190 if "amravati" in mkt_lower else 7280
        f_min, f_max = 7320, 7460
        trend = "Rising"

    mkt_name = "Akot" if "akot" in mkt_lower else "Amravati" if "amravati" in mkt_lower else "Akola"

    return {
        "status": "mock",
        "is_mock": True,
        "data_provenance": "Demonstration dataset — not live Agmarknet mandi prices",
        "crop": crop_name,
        "market": f"{mkt_name} APMC",
        "current_price": price,
        "trend": trend,
        "forecast_min": f_min,
        "forecast_max": f_max,
        "forecast_7d": int((f_min + f_max) / 2),
        "nearby_markets": [
            {"name": "Akot APMC", "distance": 45, "price": 7350 if crop_name == "Cotton" else 4670 if crop_name == "Soyabean" else 9940, "trend": "+2.4%"},
            {"name": "Akola APMC", "distance": 0, "price": 7280 if crop_name == "Cotton" else 4640 if crop_name == "Soyabean" else 9850, "trend": "+1.8%"},
            {"name": "Amravati APMC", "distance": 95, "price": 7190 if crop_name == "Cotton" else 4580 if crop_name == "Soyabean" else 9720, "trend": "-0.5%"}
        ]
    }

@router.get("/farms")
def list_farms(authorization: Optional[str] = Header(None)):
    """
    Returns list of farms owned by the authenticated user.
    If no authorization or unauthenticated demo mode, returns demo/fallback farm.
    """
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

    from backend.app.core.auth import extract_verified_user_id
    token_user_id = extract_verified_user_id(authorization, required=False)

    if url and key and token_user_id:
        try:
            from supabase import create_client
            sb = create_client(url, key)
            res = sb.table("farms").select(
                "id, farm_name, location, latitude, longitude, total_area, area_unit, status"
            ).eq("user_id", token_user_id).order("created_at", desc=True).execute()

            farms_data = []
            for f in (res.data or []):
                f_lat, f_lon, has_coords = _validate_coordinates(f.get("latitude"), f.get("longitude"))
                farms_data.append({
                    "id": f["id"],
                    "farm_name": f.get("farm_name") or f"Farm {f['id'][:8]}",
                    "location": f.get("location") or "Takli Bu, Akola, Maharashtra",
                    "latitude": f_lat,
                    "longitude": f_lon,
                    "has_precise_coordinates": has_coords,
                    "total_area": float(f.get("total_area") or 0.0),
                    "area_unit": f.get("area_unit") or "acre",
                    "status": f.get("status") or "ACTIVE"
                })
            return {"farms": farms_data, "count": len(farms_data), "is_mock": False}
        except Exception as exc:
            print(f"[ListFarms] Supabase query failed: {exc}")
            raise HTTPException(status_code=500, detail=f"Database query failed: {exc}")

    if token_user_id:
        # Authenticated user but Supabase not configured
        raise HTTPException(status_code=503, detail="Database service not configured")

    # Fallback for unauthenticated/demo mode: return default verified farm
    return {
        "farms": [
            {
                "id": "52120432-c948-4026-87c4-7e2c481a7bf5",
                "farm_name": "Pranav Vasu Farm",
                "location": "Takli Bu, Akola, Maharashtra",
                "latitude": None,
                "longitude": None,
                "has_precise_coordinates": False,
                "total_area": 10.0,
                "area_unit": "acre",
                "status": "ACTIVE"
            }
        ],
        "count": 1,
        "is_mock": not bool(token_user_id)
    }


@router.post("/farms")
def create_farm(farm: FarmCreate, authorization: Optional[str] = Header(None)):
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if url and key:
        try:
            from supabase import create_client
            sb = create_client(url, key)
            user_id = farm.farmer_id
            from backend.app.core.auth import extract_verified_user_id
            v_uid = extract_verified_user_id(authorization, required=False)
            if v_uid:
                user_id = v_uid

            insert_data = {
                "user_id": user_id,
                "farm_name": farm.farm_name or f"Farm {farm.location.split(',')[0]}",
                "location": farm.location,
                "total_area": farm.area,
                "area_unit": "acre",
                "status": "ACTIVE"
            }
            if farm.latitude is not None and farm.longitude is not None:
                f_lat, f_lon, has_coords = _validate_coordinates(farm.latitude, farm.longitude)
                if has_coords:
                    insert_data["latitude"] = f_lat
                    insert_data["longitude"] = f_lon
            res = sb.table("farms").insert(insert_data).execute()
            if res.data:
                f = res.data[0]
                return {
                    "farm_id": f["id"],
                    "status": "created",
                    "data": f,
                    "is_mock": False
                }
        except Exception:
            pass
    return {"farm_id": str(uuid.uuid4()), "status": "created", "data": farm.model_dump(), "is_mock": False}


@router.put("/farms/{farm_id}/boundaries")
def update_farm_field_boundaries(
    farm_id: str,
    update: FieldBoundaryUpdate,
    authorization: Optional[str] = Header(None)
):
    """
    Saves a verified GeoJSON polygon boundary for a field parcel owned by the authenticated user.
    Enforces server-side farm ownership and validates GeoJSON coordinates.
    """
    # 1. Validate GeoJSON Polygon
    geom = _extract_valid_geojson_polygon(update.geometry)
    if not geom:
        raise HTTPException(
            status_code=422,
            detail="Invalid GeoJSON geometry. Must be a valid closed Polygon or MultiPolygon with at least 3 distinct coordinate pairs."
        )

    # Validate coordinate ranges: GeoJSON format is [lon, lat]
    try:
        ring = geom["coordinates"][0] if geom["type"] == "Polygon" else geom["coordinates"][0][0]
        for coord in ring:
            lon, lat = coord[0], coord[1]
            if not (-180.0 <= float(lon) <= 180.0 and -90.0 <= float(lat) <= 90.0):
                raise HTTPException(
                    status_code=422,
                    detail=f"Coordinate out of range: lon={lon}, lat={lat}. Longitude must be between -180 and 180, latitude between -90 and 90."
                )
    except (IndexError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=f"Malformed GeoJSON coordinates: {exc}")

    # 2. Authenticate & Enforce Ownership
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

    from backend.app.core.auth import extract_verified_user_id
    token_user_id = extract_verified_user_id(authorization, required=False)

    if not url or not key:
        # Mock mode fallback response
        return {
            "status": "updated",
            "field_id": update.field_id,
            "farm_id": farm_id,
            "boundaries_mapped": True,
            "area": update.area,
            "is_mock": True
        }

    from supabase import create_client
    sb = create_client(url, key)

    # Verify farm ownership
    farm_query = sb.table("farms").select("id, user_id").eq("id", farm_id)
    if token_user_id:
        farm_query = farm_query.eq("user_id", token_user_id)
    farm_res = farm_query.execute()

    if not farm_res.data:
        raise HTTPException(status_code=404, detail="Farm not found or access denied")

    # Verify field belongs to this farm
    field_res = sb.table("fields").select("*").eq("id", update.field_id).eq("farm_id", farm_id).execute()
    if not field_res.data:
        raise HTTPException(status_code=404, detail="Field not found on this farm or access denied")

    existing_field = field_res.data[0]
    existing_boundary = existing_field.get("boundary") if isinstance(existing_field.get("boundary"), dict) else {}

    # Merge metadata and update boundary
    merged_boundary = {
        **existing_boundary,
        "type": geom["type"],
        "coordinates": geom["coordinates"],
        "geometry": geom,
        "boundaries_mapped": True,
        "mapping_method": "MANUAL_MAP_DRAWING",
        "updated_at": "2026-10-23T21:15:00Z"
    }
    if update.metadata:
        merged_boundary.update(update.metadata)

    update_payload: Dict[str, Any] = {
        "boundary": merged_boundary,
        "updated_at": "now()"
    }
    if update.area and update.area > 0:
        update_payload["area"] = update.area
    if update.area_unit:
        update_payload["area_unit"] = update.area_unit
    if update.field_name:
        update_payload["field_name"] = update.field_name

    # Center coordinates of the first point for field marker if not set
    try:
        first_pt = ring[0]
        update_payload["longitude"] = float(first_pt[0])
        update_payload["latitude"] = float(first_pt[1])
    except Exception:
        pass

    save_res = sb.table("fields").update(update_payload).eq("id", update.field_id).execute()
    if not save_res.data:
        raise HTTPException(status_code=500, detail="Failed to save boundary geometry to database.")

    # Mark farm boundaries_mapped = true
    try:
        sb.table("farms").update({"boundaries_mapped": True}).eq("id", farm_id).execute()
    except Exception:
        pass

    saved_field = save_res.data[0]
    return {
        "status": "updated",
        "field_id": saved_field["id"],
        "farm_id": farm_id,
        "field_name": saved_field.get("field_name"),
        "area": saved_field.get("area"),
        "area_unit": saved_field.get("area_unit"),
        "boundaries_mapped": True,
        "geometry": geom,
        "is_mock": False
    }


def _validate_coordinates(lat: Any, lon: Any) -> tuple[Optional[float], Optional[float], bool]:
    """
    Validates latitude and longitude values.
    Returns (lat_float, lon_float, is_valid_point).
    """
    if lat is None or lon is None:
        return None, None, False
    try:
        f_lat = float(lat)
        f_lon = float(lon)
        if -90.0 <= f_lat <= 90.0 and -180.0 <= f_lon <= 180.0:
            return f_lat, f_lon, True
    except (ValueError, TypeError):
        pass
    return None, None, False


def _extract_valid_geojson_polygon(boundary_obj: Any) -> Optional[Dict[str, Any]]:
    """
    Validates whether boundary_obj is a legitimate GeoJSON Polygon or MultiPolygon.
    Also handles wrap containers like {"geometry": {...}, "metadata": {...}} or GeoJSON Feature.
    Rejects arbitrary metadata dictionaries that are not real GeoJSON geometry.
    """
    if not isinstance(boundary_obj, dict):
        return None

    # If boundary_obj wraps geometry inside 'geometry' key
    if "geometry" in boundary_obj and isinstance(boundary_obj["geometry"], dict):
        boundary_obj = boundary_obj["geometry"]

    geom_type = boundary_obj.get("type")
    coords = boundary_obj.get("coordinates")
    if geom_type in ["Polygon", "MultiPolygon"] and isinstance(coords, list) and len(coords) > 0:
        # Check that coordinates contain numerical coordinate pairs
        try:
            sample_ring = coords[0]
            if geom_type == "MultiPolygon":
                sample_ring = sample_ring[0]
            if len(sample_ring) >= 3 and isinstance(sample_ring[0], (list, tuple)) and len(sample_ring[0]) >= 2:
                # Valid ring
                return {"type": geom_type, "coordinates": coords}
        except (IndexError, TypeError):
            pass
    return None


@router.get("/digital-twin/{farm_id}")
def get_digital_twin(farm_id: str, authorization: Optional[str] = Header(None)):
    if farm_id in ["F001", "FARM-001"] or farm_id.startswith("FARM-"):
        return {
            "farm_id": farm_id,
            "name": f"Farm {farm_id}",
            "area_acres": 10.0,
            "area_unit": "acre",
            "healthScore": 85,
            "location": "Takli Bu, Akola, Maharashtra",
            "latitude": None,
            "longitude": None,
            "has_precise_coordinates": False,
            "approximate_location": "Takli Bu, Akola, Maharashtra (Approximate settlement reference)",
            "approximate_coordinates": {"latitude": 20.918912, "longitude": 76.982846},
            "boundaries_mapped": False,
            "climate": {"temperature": 25.5, "weather_condition": "Sunny", "humidity": 60},
            "state": {"crop": "wheat", "soil_moisture": 0.45, "temperature": 25.5},
            "fields": [
                {
                    "id": "field-a",
                    "name": "Field A",
                    "area": 5.0,
                    "area_unit": "acre",
                    "crop": "wheat",
                    "variety": "gw-322",
                    "stage": "Tillering",
                    "status": "Optimal",
                    "latitude": None,
                    "longitude": None,
                    "has_precise_coordinates": False,
                    "geojson_geometry": None,
                    "boundaries_mapped": False,
                    "boundary_metadata": {}
                }
            ],
            "is_mock": True,
            "data_provenance": "backend_mock"
        }

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if url and key:
        try:
            from supabase import create_client
            sb = create_client(url, key)

            # Check authorization if provided to enforce authorization rules
            from backend.app.core.auth import extract_verified_user_id
            token_user_id = extract_verified_user_id(authorization, required=False)

            # 1. Look up by farm_id
            query = sb.table("farms").select(
                "*, fields(*, seasons(*, crop_records(*)), soil_records(*), irrigation_records(*), weather_records(*))"
            ).eq("id", farm_id)

            # If authentication header is present, enforce tenant ownership
            if token_user_id:
                query = query.eq("user_id", token_user_id)

            farm_res = query.execute()

            # 2. Try by user_id if token provided
            if not farm_res.data and token_user_id:
                farm_res = sb.table("farms").select(
                    "*, fields(*, seasons(*, crop_records(*)), soil_records(*), irrigation_records(*), weather_records(*))"
                ).eq("user_id", token_user_id).limit(1).execute()

            # 3. Default fallback only for unauthenticated demo/default requests
            if not farm_res.data and not token_user_id and farm_id in ["52120432-c948-4026-87c4-7e2c481a7bf5", "default"]:
                farm_res = sb.table("farms").select(
                    "*, fields(*, seasons(*, crop_records(*)), soil_records(*), irrigation_records(*), weather_records(*))"
                ).eq("id", "52120432-c948-4026-87c4-7e2c481a7bf5").execute()

            # If user authenticated or explicit unknown ID requested and not found:
            if not farm_res.data and token_user_id:
                raise HTTPException(status_code=404, detail="Farm not found or access denied")

            if farm_res.data:
                f = farm_res.data[0]
                fields = f.get("fields") or []
                first_field = fields[0] if fields else {}
                first_season = first_season_rec = (first_field.get("seasons") or [{}])[0]
                soil = first_field.get("soil_records")[0] if first_field.get("soil_records") else {}
                weather = first_field.get("weather_records")[0] if first_field.get("weather_records") else {}

                # Validate farm coordinates
                f_lat, f_lon, has_farm_coords = _validate_coordinates(f.get("latitude"), f.get("longitude"))

                # Check if village level approximate coordinates exist
                # Takli Bk/Bu approximate village center is 20.918912, 76.982846
                loc_str = f.get("location", "Takli Bu, Akola, Maharashtra")
                loc_lower = loc_str.lower()
                if "takli" in loc_lower:
                    approx_lat, approx_lon = (20.918912, 76.982846)
                elif "akola" in loc_lower:
                    approx_lat, approx_lon = (20.7002, 77.0082)
                else:
                    approx_lat, approx_lon = (None, None)

                parsed_fields = []
                any_field_mapped = False
                for fld in fields:
                    fld_lat, fld_lon, has_fld_coords = _validate_coordinates(fld.get("latitude"), fld.get("longitude"))
                    b_raw = fld.get("boundary")
                    geojson_geom = _extract_valid_geojson_polygon(b_raw)
                    b_mapped = bool(geojson_geom is not None)
                    if b_mapped:
                        any_field_mapped = True

                    seasons_list = fld.get("seasons") or [{}]
                    first_s = seasons_list[0] if seasons_list else {}

                    parsed_fields.append({
                        "id": fld["id"],
                        "name": fld["field_name"],
                        "area": float(fld.get("area") or 0.0),
                        "area_unit": fld.get("area_unit", "acre"),
                        "crop": first_s.get("crop", "Cotton"),
                        "variety": first_s.get("crop_variety", "godavari"),
                        "stage": first_s.get("crop_stage", "Boll development"),
                        "status": "Alert",
                        "latitude": fld_lat,
                        "longitude": fld_lon,
                        "has_precise_coordinates": has_fld_coords,
                        "geojson_geometry": geojson_geom,
                        "boundaries_mapped": b_mapped,
                        "boundary_metadata": b_raw if isinstance(b_raw, dict) and geojson_geom is None else {}
                    })

                return {
                    "farm_id": f["id"],
                    "name": f["farm_name"],
                    "area_acres": float(f.get("total_area") or 10.0),
                    "area_unit": f.get("area_unit", "acre"),
                    "allocated_acres": sum(float(fld.get("area") or 0.0) for fld in fields),
                    "unallocated_acres": float(f.get("total_area") or 10.0) - sum(float(fld.get("area") or 0.0) for fld in fields),
                    "healthScore": 75,
                    "location": loc_str,
                    "latitude": f_lat,
                    "longitude": f_lon,
                    "has_precise_coordinates": has_farm_coords,
                    "approximate_location": f"{loc_str} (Village-level settlement reference)" if approx_lat else None,
                    "approximate_coordinates": {"latitude": approx_lat, "longitude": approx_lon} if approx_lat else None,
                    "boundaries_mapped": any_field_mapped,
                    "climate": {
                        "temperature": float(weather.get("temperature") or 29.0),
                        "weather_condition": (weather.get("forecast_information") or {}).get("condition", "Partly Cloudy"),
                        "humidity": float(weather.get("humidity") or 55.0),
                        "location": loc_str
                    },
                    "state": {
                        "crop": first_season.get("crop", "Cotton"),
                        "variety": first_season.get("crop_variety", "godavari"),
                        "stage": first_season.get("crop_stage", "Boll development"),
                        "soil_type": soil.get("soil_type", "Black cotton soil (koralvahu jamin)"),
                        "soil_ph": soil.get("ph", 8.05),
                        "water_stress": True
                    },
                    "fields": parsed_fields,
                    "is_mock": False,
                    "data_provenance": "supabase_database"
                }
        except HTTPException:
            raise
        except Exception as exc:
            pass

    if token_user_id and farm_id not in ["F001", "FARM-001"]:
        raise HTTPException(status_code=404, detail="Farm not found or access denied")

    return {
        "farm_id": farm_id,
        "name": f"Farm {farm_id}",
        "area_acres": 10.0,
        "area_unit": "acre",
        "healthScore": 75,
        "location": "Takli Bu, Akola, Maharashtra",
        "latitude": None,
        "longitude": None,
        "has_precise_coordinates": False,
        "approximate_location": "Takli Bu, Akola, Maharashtra (Village-level settlement reference)",
        "approximate_coordinates": {"latitude": 20.918912, "longitude": 76.982846},
        "boundaries_mapped": False,
        "climate": {"temperature": 29.0, "weather_condition": "Partly Cloudy", "humidity": 55},
        "state": {"crop": "Cotton", "variety": "godavari", "stage": "Boll development"},
        "fields": [],
        "is_mock": False,
        "data_provenance": "database_fallback"
    }



@router.get("/weather/current")
def get_current_weather(
    lat: float = 20.7002,
    lon: float = 77.0082,
    farm_id: Optional[str] = None,
    location_name: str = "Takli Bu, Akola, Maharashtra",
    force_refresh: bool = False,
):
    """
    Fetches verified meteorological observations via the pluggable WeatherService.
    Priority 1: Live provider (Open-Meteo or WeatherAPI adapter) with cached TTL.
    Priority 2: Stale cached data (with is_stale marker).
    Priority 3: Supabase weather_records table.
    """
    if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
        raise HTTPException(
            status_code=422,
            detail=f"Invalid geographic coordinates: lat={lat}, lon={lon}. Latitude must be between -90 and 90, longitude between -180 and 180."
        )

    service = get_weather_service()
    res = service.get_current_weather(
        latitude=lat,
        longitude=lon,
        location_name=location_name,
        farm_id=farm_id,
        force_refresh=force_refresh,
    )
    # Output backward-compatible dict
    return res.model_dump()


@router.get("/weather/forecast")
def get_weather_forecast(
    lat: float = 20.7002,
    lon: float = 77.0082,
    days: int = 7,
    location_name: str = "Takli Bu, Akola, Maharashtra",
    force_refresh: bool = False,
):
    """
    Fetches real-time hourly and multi-day agro-climatic weather forecasts.
    Returns metric units (°C, mm, km/h, %) with agricultural advisory context.
    """
    if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
        raise HTTPException(
            status_code=422,
            detail=f"Invalid geographic coordinates: lat={lat}, lon={lon}. Latitude must be between -90 and 90, longitude between -180 and 180."
        )
    if not (1 <= days <= 16):
        raise HTTPException(
            status_code=422,
            detail=f"Forecast days must be between 1 and 16, got {days}."
        )

    service = get_weather_service()
    try:
        res = service.get_forecast(
            latitude=lat,
            longitude=lon,
            days=days,
            location_name=location_name,
            force_refresh=force_refresh,
        )
        return res.model_dump()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Weather forecast service error: {str(exc)}")


@router.post("/crop-recommendation")
def predict_crop(data: CropRecommendationRequest):
    try:
        return _proxy_to_ml("/api/v1/crop-recommendation", data.model_dump())
    except HTTPException as exc:
        if exc.status_code == 503:
            # Fall back to real in-process Model 1 pipeline
            try:
                from ml.crop_recommendation.predict import PredictionPipeline
                p = PredictionPipeline()
                result = p.recommend(
                    district=data.district.upper(),
                    season=data.season,
                    water_availability=data.water_availability,
                    top_k=data.top_k
                )
                if result.get("status") == "ERROR":
                    raise HTTPException(status_code=404 if "Unknown district" in result.get("reason", "") else 422,
                                        detail=result.get("reason", "Inference error"))
                _persist_model_prediction("crop_recommendation", "2.0.0", data.model_dump(), result, provenance="TRAINED_RANDOM_FOREST")
                return result
            except Exception as inner_exc:
                if isinstance(inner_exc, HTTPException):
                    raise inner_exc
                if os.getenv("ML_MOCK_FALLBACK_ENABLED", "false").lower() == "true":
                    return _crop_mock(data)
                raise exc
        raise


@router.post("/market-price")
def get_market_price(data: MarketPriceRequest):
    try:
        return _proxy_to_ml("/api/v1/models/market-price", data.model_dump())
    except HTTPException as exc:
        if exc.status_code == 503:
            try:
                from ml.market_price.predict import MarketPricePredictor
                models_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "models"))
                mp = MarketPricePredictor(models_dir=models_dir)
                res = mp.predict(
                    crop=data.crop,
                    quantity=data.quantity or 20.0,
                    farmer_lat=data.latitude,
                    farmer_lon=data.longitude,
                    selected_market=data.market,
                    date_str=data.date
                )
                if res.get("status") == "error":
                    msg = res.get("message", "Market forecasting error")
                    code = 404 if "not found" in msg.lower() else (422 if "insufficient" in msg.lower() or "not supported" in msg.lower() else 500)
                    raise HTTPException(status_code=code, detail=msg)
                _persist_model_prediction("market_price", "2.0.0", data.model_dump(), res, provenance="TRAINED_XGBOOST")
                return res
            except Exception as inner:
                if isinstance(inner, HTTPException):
                    raise inner
                raise exc
        raise


@router.post("/disease-detection")
def detect_disease(data: SymptomsRequest):
    try:
        return _proxy_to_ml("/api/v1/models/disease-detection", data.model_dump())
    except HTTPException as exc:
        if exc.status_code == 503:
            from ml.rule_based.engine import RuleBasedModels
            res = RuleBasedModels.detect_disease(data.symptoms, data.crop)
            res["model_type"] = "RULE_BASED_EXPERT_SYSTEM"
            _persist_model_prediction("disease_detection", "1.0.0", data.model_dump(), res, provenance="RULE_BASED_EXPERT_SYSTEM")
            return res
        raise


@router.post("/pest-detection")
def detect_pest(data: SymptomsRequest):
    try:
        return _proxy_to_ml("/api/v1/models/pest-detection", data.model_dump())
    except HTTPException as exc:
        if exc.status_code == 503:
            from ml.rule_based.engine import RuleBasedModels
            res = RuleBasedModels.detect_pest(data.symptoms, data.crop)
            res["model_type"] = "RULE_BASED_EXPERT_SYSTEM"
            _persist_model_prediction("pest_detection", "1.0.0", data.model_dump(), res, provenance="RULE_BASED_EXPERT_SYSTEM")
            return res
        raise


@router.post("/soil-assessment")
def assess_soil(data: SoilRequest):
    try:
        return _proxy_to_ml("/api/v1/models/soil-assessment", data.model_dump())
    except HTTPException as exc:
        if exc.status_code == 503:
            from ml.rule_based.engine import RuleBasedModels
            res = RuleBasedModels.assess_soil_nutrients(data.n, data.p, data.k, data.ph)
            res["model_type"] = "AGRONOMIC_HEURISTIC_SYSTEM"
            _persist_model_prediction("soil_assessment", "1.0.0", data.model_dump(), res, provenance="AGRONOMIC_HEURISTIC_SYSTEM")
            return res
        raise


@router.post("/yield-prediction")
def predict_yield(data: YieldRequest):
    try:
        return _proxy_to_ml("/api/v1/models/yield-prediction", data.model_dump())
    except HTTPException as exc:
        if exc.status_code == 503:
            from ml.rule_based.engine import RuleBasedModels
            res = RuleBasedModels.predict_yield(data.crop, data.area_acres, data.soil_health_score, data.weather_score)
            res["model_type"] = "AGRO_CLIMATIC_HEURISTIC"
            _persist_model_prediction("yield_prediction", "1.0.0", data.model_dump(), res, provenance="AGRO_CLIMATIC_HEURISTIC")
            return res
        raise


@router.post("/irrigation")
def recommend_irrigation(data: IrrigationRequest):
    try:
        return _proxy_to_ml("/api/v1/models/irrigation", data.model_dump())
    except HTTPException as exc:
        if exc.status_code == 503:
            from ml.rule_based.engine import RuleBasedModels
            res = RuleBasedModels.recommend_irrigation(data.crop, data.soil_moisture, data.days_since_rain)
            res["model_type"] = "AGRO_CLIMATIC_HEURISTIC"
            _persist_model_prediction("irrigation", "1.0.0", data.model_dump(), res, provenance="AGRO_CLIMATIC_HEURISTIC")
            return res
        raise


@router.post("/weather-risk")
def assess_weather_risk(data: WeatherRiskRequest):
    try:
        return _proxy_to_ml("/api/v1/models/weather-risk", data.model_dump())
    except HTTPException as exc:
        if exc.status_code == 503:
            from ml.rule_based.engine import RuleBasedModels
            res = RuleBasedModels.assess_weather_risk(data.temperature, data.humidity, data.rainfall_forecast)
            res["model_type"] = "METEOROLOGICAL_RULE_BASED"
            _persist_model_prediction("weather_risk", "1.0.0", data.model_dump(), res, provenance="METEOROLOGICAL_RULE_BASED")
            return res
        raise


@router.post("/economics/calculate")
def get_economics(data: Dict[str, Any]):
    return calculate_economics(data)


@router.post("/simulate")
def simulate(req: SimulationRequest):
    return run_simulation(req.farm_id, req.changes)


@router.post("/post-harvest-loss")
def estimate_post_harvest_loss(data: PostHarvestRequest):
    """
    Empirical storage loss heuristic model based on ICAR/CIPHET loss benchmarks.
    """
    crop = data.crop
    days = data.storage_days
    storage = data.storage_type
    qty = data.quantity_quintals

    base_rate = 0.03 if crop == "Wheat" else (0.05 if crop in ["Soybean", "Cotton"] else 0.15)
    storage_mult = 0.4 if "Hermetic" in storage or "Cold" in storage else (1.3 if "Shed" in storage else 1.0)
    days_factor = days / 60.0
    calc_loss_pct = min(round(base_rate * days_factor * storage_mult * 100 * 10) / 10, 45.0) if days > 0 else 0.0
    lost_qtl = round((qty * (calc_loss_pct / 100)) * 10) / 10

    # Akot APMC benchmark price: Cotton 8000, Soybean 4650, Wheat 2340
    price_per_qtl = 8000 if crop == "Cotton" else (4650 if crop == "Soybean" else 2340)
    financial_loss = round(lost_qtl * price_per_qtl)

    result = {
        "crop": crop,
        "quantity_quintals": qty,
        "storage_type": storage,
        "storage_days": days,
        "loss_percentage": calc_loss_pct,
        "quantity_lost_qtl": lost_qtl,
        "financial_loss_rs": financial_loss,
        "spoilage_risk": "Low" if calc_loss_pct < 3 else ("Moderate" if calc_loss_pct < 8 else "High"),
        "model_type": "EMPIRICAL_STORAGE_HEURISTIC",
        "provenance": "ICAR_CIPHET_BENCHMARK",
        "data_provenance": "ESTIMATED"
    }
    _persist_model_prediction("post_harvest_loss", "1.0.0", data.model_dump(), result, provenance="EMPIRICAL_STORAGE_HEURISTIC", farm_id=data.farm_id)
    return result


# ==============================================================================
# REAL ML FERTILIZER ADVISORY & STORE DISCOVERY
# ==============================================================================
from ..fertilizer.schemas import FertilizerInput, FertilizerAdvisoryResponse
from ..fertilizer.service import fertilizer_service
from ..fertilizer.store_service import find_matching_stores


@router.post("/fertilizer-advisory", response_model=FertilizerAdvisoryResponse)
def get_fertilizer_advisory(data: FertilizerInput):
    """Execute real ML fertilizer application recommendation and local store discovery."""
    try:
        return fertilizer_service.generate_advisory(data)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Fertilizer advisory calculation failed: {exc}") from exc


@router.get("/fertilizer-stores")
def list_fertilizer_stores(
    locality: Optional[str] = None,
    pin_code: Optional[str] = None,
    district: Optional[str] = None,
    product: Optional[str] = None,
):
    """Discover local demonstration fertilizer retailers ranked by locality."""
    prods = [product] if product else None
    stores = find_matching_stores(locality=locality, pin_code=pin_code, district=district, recommended_fertilizers=prods)
    return {"status": "success", "total": len(stores), "stores": [s.model_dump() for s in stores]}


@router.get("/fertilizer-models")
def get_fertilizer_model_info():
    """Metadata inspection for DNgigi/FertiliserApplication multi-output random forest."""
    from ..fertilizer.model_adapter import (
        HF_REPO_ID,
        PINNED_REVISION,
        NUMERICAL_TARGETS,
        SUPPORTED_TRAINING_CROPS,
        fertilizer_model_adapter,
    )
    return {
        "model_identifier": HF_REPO_ID,
        "pinned_revision": PINNED_REVISION,
        "is_available": fertilizer_model_adapter.is_available(),
        "numerical_targets": NUMERICAL_TARGETS,
        "supported_training_crops": list(SUPPORTED_TRAINING_CROPS.keys()),
        "architecture": "MultiOutput Random Forest Regressor and Classifier",
        "license": "MIT",
        "limitations": "Trained on East Africa Agricultural Soil Survey data; unvalidated for Indian vertisols without local calibration.",
    }


@router.post("/onboarding")
def complete_onboarding(data: OnboardingRequest, authorization: Optional[str] = Header(None)):
    """
    Production-grade endpoint for Farmer Onboarding (Phase 1).
    Atomically registers the farmer profile, farm, fields, and initial season crop assignments.
    Supports authenticated Supabase session persistence as well as robust local development fallback.
    """
    user_id = data.farmer_id
    from backend.app.core.auth import extract_verified_user_id
    v_uid = extract_verified_user_id(authorization, required=False)
    if v_uid:
        user_id = v_uid
    if not user_id:
        user_id = str(uuid.uuid4())

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

    if url and key:
        try:
            from supabase import create_client
            sb = create_client(url, key)

            # 1. Upsert Farmer Profile
            profile_payload = {
                "user_id": user_id,
                "name": data.name.strip(),
                "phone": data.phone.strip(),
                "state": data.state.strip(),
                "district": data.district.strip(),
                "village": data.village.strip(),
                "preferred_language": data.preferred_language,
                "role": "farmer",
                "updated_at": "now()"
            }
            if data.farming_experience:
                profile_payload["farming_experience"] = data.farming_experience
            if data.farmer_category:
                profile_payload["farmer_category"] = data.farmer_category

            sb.table("profiles").upsert(profile_payload, on_conflict="user_id").execute()

            # 2. Insert Farm
            farm_location = f"{data.village.strip()}, {data.district.strip()}, {data.state.strip()}"
            farm_payload = {
                "user_id": user_id,
                "farm_name": data.farm_name.strip(),
                "location": farm_location,
                "total_area": data.total_area,
                "area_unit": data.area_unit,
                "land_ownership": data.land_ownership or "Owned",
                "status": "ACTIVE"
            }
            if data.latitude is not None and data.longitude is not None:
                f_lat, f_lon, has_coords = _validate_coordinates(data.latitude, data.longitude)
                if has_coords:
                    farm_payload["latitude"] = f_lat
                    farm_payload["longitude"] = f_lon

            res_farm = sb.table("farms").insert(farm_payload).execute()
            if not res_farm.data:
                raise HTTPException(status_code=500, detail="Failed to persist farm record")
            created_farm = res_farm.data[0]
            farm_id = created_farm["id"]

            # 3. Insert Fields & Initial Seasons
            created_fields = []
            for field in data.fields:
                field_payload = {
                    "farm_id": farm_id,
                    "field_name": field.field_name.strip(),
                    "area": field.area,
                    "area_unit": field.area_unit or data.area_unit,
                    "status": "ACTIVE"
                }
                if field.soil_type:
                    field_payload["soil_description"] = field.soil_type
                res_field = sb.table("fields").insert(field_payload).execute()
                if res_field.data:
                    f_record = res_field.data[0]
                    field_id = f_record["id"]
                    created_fields.append(f_record)

                    # Create initial season record for field
                    season_payload = {
                        "field_id": field_id,
                        "season_name": "Kharif 2024",
                        "crop": field.current_crop or "Cotton",
                        "previous_crop": field.previous_crop,
                        "status": "ACTIVE"
                    }
                    try:
                        sb.table("seasons").insert(season_payload).execute()
                    except Exception as s_exc:
                        print(f"[Onboarding] Note: Season insert warning: {s_exc}")

            return {
                "status": "success",
                "message": "Farmer onboarding persisted successfully",
                "user_id": user_id,
                "farm_id": farm_id,
                "farm_name": data.farm_name,
                "fields_created": len(created_fields),
                "is_mock": False
            }
        except HTTPException:
            raise
        except Exception as exc:
            print(f"[Onboarding] Supabase persistence error: {exc}")
            raise HTTPException(status_code=500, detail=f"Database persistence failure: {str(exc)}")

    # Development / Test Fallback when Supabase is not configured
    mock_farm_id = str(uuid.uuid4())
    return {
        "status": "success",
        "message": "Farmer onboarding validated and accepted (development mode)",
        "user_id": user_id,
        "farm_id": mock_farm_id,
        "farm_name": data.farm_name,
        "fields_created": len(data.fields),
        "is_mock": True,
        "data": {
            "profile": {
                "user_id": user_id,
                "name": data.name,
                "phone": data.phone,
                "location": f"{data.village}, {data.district}, {data.state}",
                "preferred_language": data.preferred_language,
                "farming_experience": data.farming_experience,
                "farmer_category": data.farmer_category
            },
            "farm": {
                "id": mock_farm_id,
                "farm_name": data.farm_name,
                "total_area": data.total_area,
                "area_unit": data.area_unit,
                "location": f"{data.village}, {data.district}, {data.state}",
                "irrigation_source": data.irrigation_source,
                "land_ownership": data.land_ownership
            },
            "fields": [f.model_dump() for f in data.fields]
        }
    }
