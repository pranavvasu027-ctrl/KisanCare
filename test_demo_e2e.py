import subprocess
import time
import requests
import sys
import json

def run_e2e_tests():
    print("Starting FastAPI Server for E2E tests...")
    proc = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8003"])
    
    try:
        time.sleep(10) # Wait for server and models to load
        base_url = "http://localhost:8003"
        
        print("\n==================================================")
        print("1. HEALTH CHECK")
        print("==================================================")
        r_health = requests.get(f"{base_url}/health")
        print("Status:", r_health.status_code)
        
        print("\n==================================================")
        print("2. CREATE DEMO FARM (demo_farm_001)")
        print("==================================================")
        demo_farm = {
            "farm_id": "demo_farm_001",
            "farmer_id": "MH_FARMER_442",
            "area_acres": 12.5,
            "location": {
                "state": "Maharashtra",
                "district": "Pune",
                "latitude": 18.5204,
                "longitude": 73.8567
            },
            "soil": {
                "nitrogen": 85.0,
                "phosphorus": 40.0,
                "potassium": 45.0,
                "ph": 6.8
            },
            "climate": {
                "temperature": 26.5,
                "humidity": 75.0,
                "rainfall": 180.0
            }
        }
        r_create = requests.post(f"{base_url}/api/v1/digital-twin", json=demo_farm)
        print("Create Status:", r_create.status_code)
        
        print("\n==================================================")
        print("3. CALL MODEL 1 THROUGH DIGITAL TWIN ADAPTER")
        print("==================================================")
        r_predict = requests.post(f"{base_url}/api/v1/digital-twin/demo_farm_001/predict/model1")
        print("Predict Status:", r_predict.status_code)
        print("Prediction Result:", json.dumps(r_predict.json(), indent=2))
        
        print("\n==================================================")
        print("4. VERIFY MODEL 1 RESULT PERSISTED IN DIGITAL TWIN")
        print("==================================================")
        r_get = requests.get(f"{base_url}/api/v1/digital-twin/demo_farm_001")
        twin_data = r_get.json()
        model_outputs = twin_data.get("model_outputs", {})
        print("Model Outputs found in Twin:", json.dumps(model_outputs, indent=2))
        if "model1" in model_outputs:
            print("=> PERSISTENCE SUCCESS: Model 1 output exists in Twin!")
        else:
            print("=> PERSISTENCE FAIL: Model 1 output missing!")
            
        print("\n==================================================")
        print("5. CREATE INCOMPLETE DEMO FARM (demo_farm_incomplete)")
        print("==================================================")
        demo_farm_inc = {
            "farm_id": "demo_farm_incomplete",
            "farmer_id": "MH_FARMER_999",
            "soil": {
                "nitrogen": 85.0,
                "phosphorus": 40.0,
                # Missing potassium, ph
            },
            "climate": {
                "temperature": 26.5,
                # Missing humidity, rainfall
            }
        }
        requests.post(f"{base_url}/api/v1/digital-twin", json=demo_farm_inc)
        
        print("\n==================================================")
        print("6. CALL MODEL 1 ON INCOMPLETE FARM (Expect 422)")
        print("==================================================")
        r_pred_inc = requests.post(f"{base_url}/api/v1/digital-twin/demo_farm_incomplete/predict/model1")
        print("Predict Status:", r_pred_inc.status_code)
        print("Response:", json.dumps(r_pred_inc.json(), indent=2))
        if r_pred_inc.status_code == 422 and "insufficient_data" in str(r_pred_inc.content):
            print("=> INCOMPLETE DATA HANDLING SUCCESS!")
            
        print("\n==================================================")
        print("7. DIRECT MODEL 1 REGRESSION TEST")
        print("==================================================")
        legacy_req = {
            "nitrogen": 90,
            "phosphorus": 42,
            "potassium": 43,
            "temperature": 25.5,
            "humidity": 80,
            "ph": 6.5,
            "rainfall": 200
        }
        r_legacy = requests.post(f"{base_url}/api/v1/model1/crop-recommendation", json=legacy_req)
        print("Legacy Predict Status:", r_legacy.status_code)
        if r_legacy.status_code == 200:
            print("=> DIRECT MODEL 1 API REGRESSION SUCCESS!")
            
    finally:
        print("\nShutting down server...")
        proc.terminate()
        proc.wait()

if __name__ == "__main__":
    run_e2e_tests()
