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
            
            # Test crop recommendation (1)
            response = client.post("/api/v1/crop-recommendation", json={"district": "NASHIK", "season": "Kharif", "water_availability": "Medium", "top_k": 3})
            print(f"Crop Rec Response: {response.status_code}")
            assert response.status_code == 200
            
            # Test disease detection (2)
            response = client.post("/api/v1/models/disease-detection", json={"crop": "Tomato", "symptoms": ["yellow leaves", "stunted growth"]})
            print(f"Disease Detection Response: {response.status_code}")
            assert response.status_code == 200
            
            # Test pest detection (3)
            response = client.post("/api/v1/models/pest-detection", json={"crop": "Cotton", "symptoms": ["holes in leaves"]})
            print(f"Pest Detection Response: {response.status_code}")
            assert response.status_code == 200
            
            # Test soil assessment (4)
            response = client.post("/api/v1/models/soil-assessment", json={"n": 15, "p": 8, "k": 100, "ph": 5.0})
            print(f"Soil Assessment Response: {response.status_code}")
            assert response.status_code == 200
            
            # Test yield prediction (5)
            response = client.post("/api/v1/models/yield-prediction", json={"crop": "Wheat", "area_acres": 10.0, "soil_health_score": 85.0, "weather_score": 90.0})
            print(f"Yield Prediction Response: {response.status_code}")
            assert response.status_code == 200
            
            # Test weather risk (6)
            response = client.post("/api/v1/models/weather-risk", json={"temperature": 38.0, "humidity": 60.0, "rainfall_forecast": 10.0})
            print(f"Weather Risk Response: {response.status_code}")
            assert response.status_code == 200
            
            # Test irrigation (7)
            response = client.post("/api/v1/models/irrigation", json={"crop": "Rice", "soil_moisture": 25.0, "days_since_rain": 10})
            print(f"Irrigation Response: {response.status_code}")
            assert response.status_code == 200
            
            # Test market price forecasting (8)
            response = client.post("/api/v1/models/market-price", json={"crop": "Onion", "market": "Pune(Pimpri)", "date": "2025-11-04"})
            print(f"Market Price Response: {response.status_code}")
            if response.status_code != 200:
                print(response.json())
            assert response.status_code == 200
            
            print("All ML backend tests passed!")
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    run_tests()
