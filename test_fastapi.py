from fastapi.testclient import TestClient
import sys
import os

backend_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'backend')
sys.path.insert(0, backend_dir)

from app.main import app
from app.api.endpoints import router as api_router

client = TestClient(app)

def run_tests():
    print("API Router Routes:")
    for route in api_router.routes:
        print(f"Path: {getattr(route, 'path', None)}, Name: {getattr(route, 'name', None)}")
    print("App Routes:")
    for route in app.routes:
        print(f"Path: {getattr(route, 'path', None)}, Name: {getattr(route, 'name', None)}")
    try:
        response = client.get("/api/v1/digital-twin/F001")
        print(f"Digital Twin Response: {response.status_code}")
        assert response.status_code == 200
        
        response = client.post("/api/v1/crop-recommendation", json={"district": "NASHIK", "season": "Kharif", "water_availability": "Medium", "top_k": 3})
        print(f"Crop Rec Response: {response.status_code}")
        assert response.status_code == 200
        
        response = client.post("/api/v1/market-price/", json={"crop": "Soybean"})
        print(f"Market Price Response: {response.status_code}")
        assert response.status_code == 200
        
        print("All backend tests passed!")
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    run_tests()
