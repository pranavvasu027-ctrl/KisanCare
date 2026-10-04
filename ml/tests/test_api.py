from fastapi.testclient import TestClient
import time
from ml.main import app

def run_tests():
    passed = 0
    failed = 0
    
    def run_test(name, func):
        nonlocal passed, failed
        try:
            func()
            print(f"[PASS] {name}")
            passed += 1
        except Exception as e:
            print(f"[FAIL] {name} FAILED: {e}")
            failed += 1

    def test_health():
        with TestClient(app) as client:
            response = client.get("/health")
            assert response.status_code == 200, f"Got {response.status_code}"
            assert response.json()["status"] == "healthy"
            assert "model_version" in response.json()

    def test_meta():
        with TestClient(app) as client:
            response = client.get("/api/v1/crop-recommendation/meta")
            assert response.status_code == 200
            data = response.json()
            assert data["target"] == "Area_Frequency"
            assert data["supported_crops"] == 20

    def test_valid_recommendation():
        with TestClient(app) as client:
            payload = {
                "district": "NASHIK",
                "season": "Rabi",
                "water_availability": "Medium",
                "top_k": 3
            }
            response = client.post("/api/v1/crop-recommendation", json=payload)
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "SUCCESS"
            assert data["district"] == "NASHIK"
            assert data["season"] == "Rabi"
            assert "latency_ms" in data
            assert len(data["recommendations"]) <= 3
            if len(data["recommendations"]) > 0:
                assert data["recommendations"][0]["rank"] == 1
                assert "predicted_area_frequency" in data["recommendations"][0]

    def test_deterministic_recommendation():
        with TestClient(app) as client:
            payload = {
                "district": "PUNE",
                "season": "Kharif",
                "water_availability": "Low",
                "top_k": 5
            }
            res1 = client.post("/api/v1/crop-recommendation", json=payload).json()
            res2 = client.post("/api/v1/crop-recommendation", json=payload).json()
            assert res1["recommendations"] == res2["recommendations"]

    def test_invalid_season():
        with TestClient(app) as client:
            payload = {
                "district": "PUNE",
                "season": "Winter",
                "water_availability": "Medium",
                "top_k": 5
            }
            response = client.post("/api/v1/crop-recommendation", json=payload)
            assert response.status_code == 422
            assert "Season must be one of" in response.text

    def test_invalid_water():
        with TestClient(app) as client:
            payload = {
                "district": "PUNE",
                "season": "Kharif",
                "water_availability": "Very High",
                "top_k": 5
            }
            response = client.post("/api/v1/crop-recommendation", json=payload)
            assert response.status_code == 422
            assert "Water availability must be one of" in response.text

    def test_unknown_district():
        with TestClient(app) as client:
            payload = {
                "district": "GOTHAM",
                "season": "Kharif",
                "water_availability": "Medium",
                "top_k": 5
            }
            response = client.post("/api/v1/crop-recommendation", json=payload)
            assert response.status_code == 404
            assert "Unknown district" in response.text

    def test_latency():
        with TestClient(app) as client:
            payload = {
                "district": "KOLHAPUR",
                "season": "Whole Year",
                "water_availability": "High",
                "top_k": 5
            }
            
            latencies = []
            for _ in range(10):
                t0 = time.time()
                response = client.post("/api/v1/crop-recommendation", json=payload)
                latencies.append((time.time() - t0) * 1000)
                assert response.status_code == 200
                
            avg_latency = sum(latencies) / len(latencies)
            min_latency = min(latencies)
            max_latency = max(latencies)
            
            print(f"\nAPI Latency (TestClient) - Avg: {avg_latency:.2f}ms, Min: {min_latency:.2f}ms, Max: {max_latency:.2f}ms")
            assert avg_latency < 100
            
    print("Running API Integration Tests...\n")
    run_test("Health Endpoint", test_health)
    run_test("Metadata Endpoint", test_meta)
    run_test("Valid Recommendation", test_valid_recommendation)
    run_test("Deterministic Output", test_deterministic_recommendation)
    run_test("Invalid Season", test_invalid_season)
    run_test("Invalid Water", test_invalid_water)
    run_test("Unknown District", test_unknown_district)
    run_test("Latency Test", test_latency)
    
    print(f"\nTotal: {passed + failed} | Passed: {passed} | Failed: {failed}")

if __name__ == "__main__":
    run_tests()
