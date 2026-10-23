"""
Comprehensive Model Execution & E2E Persistence Verification for KisanCare
Verifies:
1. Every model's actual implementation, execution, response schema, and provenance labeling.
2. Direct insertion into Supabase model_predictions table.
3. Negative and edge-case inputs (validation errors, 422s).
4. RLS isolation between farmer1 and farmer2.
5. Live weather observations and timestamps.
"""
import os
import sys
import uuid
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath("."))
import dotenv

dotenv.load_dotenv()

from fastapi.testclient import TestClient
from backend.app.main import app
from supabase import create_client

client = TestClient(app)
supabase_url = os.environ.get("SUPABASE_URL")
service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
anon_key = os.environ.get("SUPABASE_ANON_KEY")

assert supabase_url and service_key, "Missing Supabase configuration in environment!"

admin_sb = create_client(supabase_url, service_key)

PRANAV_FARM_ID = "52120432-c948-4026-87c4-7e2c481a7bf5"
PRANAV_USER_ID = "9c851059-4259-4cd3-95c7-9ab287f60710"

results = []

def run_check(name, fn):
    try:
        fn()
        results.append((name, "PASS", None))
        print(f"[PASS] {name}")
    except Exception as e:
        results.append((name, "FAIL", str(e)))
        print(f"[FAIL] {name}: {e}")

# Track created test prediction IDs for cleanup
created_prediction_ids = []

# --- 1. MODEL 1: Crop Recommendation (Trained Random Forest) ---
def test_model1_crop_recommendation():
    # Record count before
    resp = client.post("/api/v1/crop-recommendation", json={
        "district": "AKOLA",
        "season": "Kharif",
        "water_availability": "Low",
        "top_k": 3
    })
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    body = resp.json()
    assert body.get("status") == "SUCCESS", f"Unexpected status: {body}"
    recs = body.get("recommendations", [])
    assert len(recs) == 3, f"Expected 3 recommendations, got {len(recs)}"
    assert recs[0]["crop"] == "Cotton", f"Expected Cotton top crop, got {recs[0]['crop']}"
    assert body.get("data_source") == "APY_2005_2015"
    
    # Check persistence in Supabase
    db_res = admin_sb.table("model_predictions").select("*").eq("model_name", "crop_recommendation").order("created_at", desc=True).limit(1).execute()
    assert len(db_res.data) > 0, "No model_prediction persisted in Supabase!"
    pred_row = db_res.data[0]
    assert pred_row["farm_id"] == PRANAV_FARM_ID
    assert pred_row["status"] == "COMPLETED"
    assert pred_row["data_provenance"] == "ESTIMATED"
    assert pred_row["metadata"].get("model_type") == "TRAINED_RANDOM_FOREST"
    created_prediction_ids.append(pred_row["id"])

# --- 2. MODEL 2: Market Price Forecasting (Trained XGBoost) ---
def test_model2_market_price():
    # Valid historical target date
    resp = client.post("/api/v1/market-price", json={
        "crop": "Tomato",
        "market": "Pune (Pimpri)",
        "date": "2025-11-05"
    })
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    body = resp.json()
    assert body.get("status") == "success"
    assert body.get("model_type") == "xgboost_trained"
    assert body.get("forecast_7d") is not None
    
    # Check persistence
    db_res = admin_sb.table("model_predictions").select("*").eq("model_name", "market_price").order("created_at", desc=True).limit(1).execute()
    assert len(db_res.data) > 0, "No market_price prediction persisted!"
    pred_row = db_res.data[0]
    assert pred_row["status"] == "COMPLETED"
    assert pred_row["metadata"].get("model_type") == "TRAINED_XGBOOST"
    created_prediction_ids.append(pred_row["id"])

# --- 3. MODEL 3: Disease Detection (Rule-based Expert System) ---
def test_model3_disease_detection():
    resp = client.post("/api/v1/disease-detection", json={
        "crop": "Cotton",
        "symptoms": ["yellow leaves", "stunted growth"]
    })
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    body = resp.json()
    assert body.get("prediction") == "Nitrogen Deficiency / Root Rot"
    assert body.get("confidence") == 0.75
    assert body.get("model_type") == "RULE_BASED_EXPERT_SYSTEM"
    
    # Check persistence
    db_res = admin_sb.table("model_predictions").select("*").eq("model_name", "disease_detection").order("created_at", desc=True).limit(1).execute()
    assert len(db_res.data) > 0, "No disease_detection prediction persisted!"
    pred_row = db_res.data[0]
    assert pred_row["metadata"].get("model_type") == "RULE_BASED_EXPERT_SYSTEM"
    created_prediction_ids.append(pred_row["id"])

# --- 4. MODEL 4: Pest Detection (Rule-based Expert System) ---
def test_model4_pest_detection():
    resp = client.post("/api/v1/pest-detection", json={
        "crop": "Cotton",
        "symptoms": ["sticky residue", "curled leaves"]
    })
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    body = resp.json()
    assert body.get("prediction") == "Aphids"
    assert body.get("confidence") == 0.85
    assert body.get("model_type") == "RULE_BASED_EXPERT_SYSTEM"
    
    # Check persistence
    db_res = admin_sb.table("model_predictions").select("*").eq("model_name", "pest_detection").order("created_at", desc=True).limit(1).execute()
    assert len(db_res.data) > 0, "No pest_detection prediction persisted!"
    pred_row = db_res.data[0]
    assert pred_row["metadata"].get("model_type") == "RULE_BASED_EXPERT_SYSTEM"
    created_prediction_ids.append(pred_row["id"])

# --- 5. MODEL 5: Soil Assessment (Agronomic Heuristic) ---
def test_model5_soil_assessment():
    resp = client.post("/api/v1/soil-assessment", json={
        "n": 0, "p": 0, "k": 0, "ph": 8.05
    })
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    body = resp.json()
    assert "Alkaline Soil" in body.get("issues", [])
    assert body.get("overall_status") == "Deficient/Imbalanced"
    assert body.get("model_type") == "AGRONOMIC_HEURISTIC_SYSTEM"
    
    # Check persistence
    db_res = admin_sb.table("model_predictions").select("*").eq("model_name", "soil_assessment").order("created_at", desc=True).limit(1).execute()
    assert len(db_res.data) > 0, "No soil_assessment prediction persisted!"
    pred_row = db_res.data[0]
    assert pred_row["metadata"].get("model_type") == "AGRONOMIC_HEURISTIC_SYSTEM"
    created_prediction_ids.append(pred_row["id"])

# --- 6. MODEL 6: Farm Cost & Economics Engine ---
def test_model6_farm_economics():
    resp = client.post("/api/v1/economics/calculate", json={
        "expected_yield": 50, # 50 quintals
        "expected_price": 8000, # Rs 8000/qtl Akot APMC benchmark
        "input_cost": 21010, # seed + pesticide + fertilizer recorded
        "labour_cost": 75000, # labour recorded
        "irrigation_cost": 60000 # drip + diesel recorded
    })
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    body = resp.json()
    assert body["total_cost"] == 156010
    assert body["expected_revenue"] == 400000
    assert body["expected_profit"] == 243990
    assert body["roi_percent"] > 0

# --- 7. MODEL 7: Crop Yield Prediction (Agro-Climatic Heuristic) ---
def test_model7_yield_prediction():
    resp = client.post("/api/v1/yield-prediction", json={
        "crop": "Cotton",
        "area_acres": 5.0,
        "soil_health_score": 60.0,
        "weather_score": 50.0
    })
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    body = resp.json()
    assert body.get("status") == "success"
    assert body.get("crop") == "Cotton"
    assert body.get("predicted_yield_tons") == 1.65 # 0.6 * 5.0 * 0.55 = 1.65 tons
    assert body.get("model_type") == "AGRO_CLIMATIC_HEURISTIC"
    
    # Check persistence
    db_res = admin_sb.table("model_predictions").select("*").eq("model_name", "yield_prediction").order("created_at", desc=True).limit(1).execute()
    assert len(db_res.data) > 0, "No yield_prediction persisted!"
    pred_row = db_res.data[0]
    assert pred_row["metadata"].get("model_type") == "AGRO_CLIMATIC_HEURISTIC"
    created_prediction_ids.append(pred_row["id"])

# --- 8. MODEL 8: Irrigation, Weather Risk & Post-Harvest Storage Loss ---
def test_model8_irrigation_weather_storage():
    # 8a: Irrigation
    resp_irrig = client.post("/api/v1/irrigation", json={
        "crop": "Cotton",
        "soil_moisture": 16.0,
        "days_since_rain": 8
    })
    assert resp_irrig.status_code == 200
    assert resp_irrig.json()["irrigation_required"] is True
    assert resp_irrig.json()["model_type"] == "AGRO_CLIMATIC_HEURISTIC"
    
    # 8b: Weather Risk
    resp_risk = client.post("/api/v1/weather-risk", json={
        "temperature": 33.1,
        "humidity": 35.0,
        "rainfall_forecast": 10.0
    })
    assert resp_risk.status_code == 200
    assert resp_risk.json()["overall_risk"] == "Low"
    assert resp_risk.json()["model_type"] == "METEOROLOGICAL_RULE_BASED"
    
    # 8c: Post-Harvest Storage Loss
    resp_storage = client.post("/api/v1/post-harvest-loss", json={
        "crop": "Cotton",
        "quantity_quintals": 50.0,
        "storage_type": "Covered Farm Shed",
        "storage_days": 45,
        "farm_id": PRANAV_FARM_ID
    })
    assert resp_storage.status_code == 200
    body = resp_storage.json()
    assert body["loss_percentage"] > 0
    assert body["quantity_lost_qtl"] > 0
    assert body["financial_loss_rs"] > 0
    assert body["provenance"] == "ICAR_CIPHET_BENCHMARK"
    
    # Check persistence for post-harvest loss
    db_res = admin_sb.table("model_predictions").select("*").eq("model_name", "post_harvest_loss").order("created_at", desc=True).limit(1).execute()
    assert len(db_res.data) > 0
    created_prediction_ids.append(db_res.data[0]["id"])

# --- 9. ERROR HANDLING & VALIDATION CHECKS ---
def test_error_handling_and_validation():
    # 9a: Area <= 0 in yield prediction
    r = client.post("/api/v1/yield-prediction", json={
        "crop": "Cotton", "area_acres": -5.0, "soil_health_score": 60, "weather_score": 50
    })
    assert r.status_code == 422, f"Expected 422 for negative area, got {r.status_code}"
    
    # 9b: Soil pH out of range (< 0)
    r = client.post("/api/v1/soil-assessment", json={"n": 10, "p": 10, "k": 100, "ph": -2.0})
    assert r.status_code == 422, f"Expected 422 for invalid pH, got {r.status_code}"
    
    # 9c: Missing/empty symptoms in disease detection
    r = client.post("/api/v1/disease-detection", json={"crop": "Cotton", "symptoms": []})
    assert r.status_code == 422, f"Expected 422 for empty symptoms, got {r.status_code}"
    
    # 9d: Market price date beyond historical training boundary (2026-10-23)
    r = client.post("/api/v1/market-price", json={"crop": "Tomato", "market": "Pune (Pimpri)", "date": "2026-10-23"})
    assert r.status_code == 422, f"Expected 422 for out-of-boundary date, got {r.status_code}"
    assert "Insufficient recent historical data" in r.text

    # 9e: Copilot returns 503 when GEMINI_API_KEY is not configured
    r = client.post("/api/v1/copilot/chat", json={"message": "How is my cotton crop doing?"})
    assert r.status_code == 503, f"Expected 503 for unconfigured copilot, got {r.status_code}"

# --- 10. ROW LEVEL SECURITY (RLS) ISOLATION ---
def test_rls_cross_user_isolation():
    from supabase import create_client as anon_sb_client
    # Farmer 2 sign in
    client_f2 = anon_sb_client(supabase_url, anon_key)
    auth_resp = client_f2.auth.sign_in_with_password({
        "email": "farmer2@kisancare.test",
        "password": "TestPassword123!"
    })
    assert auth_resp.user is not None, "Farmer 2 login failed"
    f2_uid = auth_resp.user.id
    assert f2_uid != PRANAV_USER_ID, "Farmer 2 must have distinct UID"
    
    # Farmer 2 client attempting to select Pranav Vasu's farm
    pranav_farm = client_f2.table("farms").select("*").eq("id", PRANAV_FARM_ID).execute()
    assert len(pranav_farm.data) == 0, f"SECURITY VIOLATION: Farmer 2 was able to view Pranav Vasu's farm! Data: {pranav_farm.data}"
    
    # Farmer 2 attempting to view Pranav's fields
    pranav_fields = client_f2.table("fields").select("*").eq("farm_id", PRANAV_FARM_ID).execute()
    assert len(pranav_fields.data) == 0, f"SECURITY VIOLATION: Farmer 2 was able to view Pranav Vasu's fields!"

# --- 11. LIVE WEATHER METEOROLOGICAL VERIFICATION ---
def test_live_weather_verification():
    resp = client.get("/api/v1/weather/current?lat=20.7002&lon=77.0082")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    w = resp.json()
    assert w["location"] == "Takli Bu, Akola, Maharashtra"
    assert w["temperature"] != "Unavailable", "Live temperature should be resolved"
    assert "Open-Meteo" in w["data_source"] or "Supabase" in w["data_source"]
    assert w["observed_at"] is not None
    assert w["rainfall_since_sowing"] == "Unavailable (No on-field rain gauge installed)"
    assert w["is_synthetic"] is False


if __name__ == "__main__":
    print("================================================================")
    print("STARTING KISANCARE COMPLETE MODEL & E2E INTEGRATION VERIFICATION")
    print("================================================================")
    
    run_check("Model 1: Crop Recommendation (Trained RF)", test_model1_crop_recommendation)
    run_check("Model 2: Market Price Forecasting (Trained XGBoost)", test_model2_market_price)
    run_check("Model 3: Disease Detection (Rule-Based Expert)", test_model3_disease_detection)
    run_check("Model 4: Pest Detection (Rule-Based Expert)", test_model4_pest_detection)
    run_check("Model 5: Soil Assessment (Agronomic Heuristic)", test_model5_soil_assessment)
    run_check("Model 6: Farm Economics Calculation Engine", test_model6_farm_economics)
    run_check("Model 7: Yield Prediction (Agro-Climatic Heuristic)", test_model7_yield_prediction)
    run_check("Model 8: Irrigation, Weather Risk & Storage Loss", test_model8_irrigation_weather_storage)
    run_check("Validation & Error Scenarios (422, 503)", test_error_handling_and_validation)
    run_check("Row Level Security Cross-User Isolation", test_rls_cross_user_isolation)
    run_check("Live Meteorological Agromet Observation", test_live_weather_verification)
    
    print("\n----------------------------------------------------------------")
    print(f"CLEANING UP {len(created_prediction_ids)} TEST PREDICTION RECORDS...")
    for pid in created_prediction_ids:
        try:
            admin_sb.table("model_predictions").delete().eq("id", pid).execute()
        except Exception:
            pass
    print("CLEANUP COMPLETE.")
    print("----------------------------------------------------------------")
    
    failed = [r for r in results if r[1] == "FAIL"]
    print(f"\nTOTAL CHECKS: {len(results)} | PASSED: {len(results) - len(failed)} | FAILED: {len(failed)}")
    if failed:
        print("\nFAILURES:")
        for name, _, err in failed:
            print(f"- {name}: {err}")
        sys.exit(1)
    else:
        print("\nALL PRODUCTION READINESS CHECKS PASSED PERFECLTY!")
        sys.exit(0)
