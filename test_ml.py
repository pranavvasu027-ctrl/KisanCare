from fastapi.testclient import TestClient
import sys
import os

# Add root directory to python path
ml_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'ml')
sys.path.insert(0, ml_dir)

from main import app

client = TestClient(app)

def run_tests():
    try:
        with TestClient(app) as client:
            response = client.get("/health")
            print(f"Health Response: {response.status_code}")
            print(response.json())
            assert response.status_code == 200
            
            # Test crop recommendation
            response = client.post("/api/v1/crop-recommendation", json={"district": "NASHIK", "season": "Kharif", "water_availability": "Medium", "top_k": 3})
            print(f"Crop Rec Response: {response.status_code}")
            print(response.json())
            assert response.status_code == 200
            
            print("All ML backend tests passed!")
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    run_tests()
