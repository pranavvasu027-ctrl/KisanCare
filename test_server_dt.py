import subprocess
import time
import requests
import sys

print("Starting Uvicorn server...")
proc = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8002"])

try:
    time.sleep(10)
    
    print("\n--- Testing Partial Farm Creation ---")
    payload_partial = {
        "farm_id": "F_HTTP_1",
        "farmer_id": "U999"
    }
    r1 = requests.post("http://localhost:8002/api/v1/digital-twin", json=payload_partial)
    print("Create Partial Status:", r1.status_code)
    
    print("\n--- Testing Model 1 with Partial Farm (Should fail) ---")
    r2 = requests.post("http://localhost:8002/api/v1/digital-twin/F_HTTP_1/predict/model1")
    print("Predict Status:", r2.status_code)
    print("Response:", r2.json())
    
    print("\n--- Testing Full Farm Update ---")
    payload_full = {
        "farm_id": "F_HTTP_1",
        "farmer_id": "U999",
        "soil": {
            "nitrogen": 90,
            "phosphorus": 42,
            "potassium": 43,
            "ph": 6.5
        },
        "climate": {
            "temperature": 25.5,
            "humidity": 80,
            "rainfall": 200
        }
    }
    r3 = requests.put("http://localhost:8002/api/v1/digital-twin/F_HTTP_1", json=payload_full)
    print("Update Status:", r3.status_code)
    
    print("\n--- Testing Model 1 with Full Farm (Should succeed) ---")
    r4 = requests.post("http://localhost:8002/api/v1/digital-twin/F_HTTP_1/predict/model1")
    print("Predict Status:", r4.status_code)
    print("Response:", r4.json())

finally:
    print("\nKilling Uvicorn server...")
    proc.terminate()
    proc.wait()
