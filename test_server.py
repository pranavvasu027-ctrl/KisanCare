import subprocess
import time
import requests
import sys

print("Starting Uvicorn server...")
proc = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8001"])

try:
    time.sleep(3)
    
    print("\n--- Testing /health ---")
    r1 = requests.get("http://localhost:8001/health")
    print("Status:", r1.status_code)
    print("Response:", r1.json())
    
    print("\n--- Testing /api/v1/model1/crop-recommendation ---")
    payload = {
        "nitrogen": 90,
        "phosphorus": 42,
        "potassium": 43,
        "temperature": 25.5,
        "humidity": 80,
        "ph": 6.5,
        "rainfall": 200
    }
    r2 = requests.post("http://localhost:8001/api/v1/model1/crop-recommendation", json=payload)
    print("Status:", r2.status_code)
    print("Response:", r2.json())
finally:
    print("\nKilling Uvicorn server...")
    proc.terminate()
    proc.wait()
