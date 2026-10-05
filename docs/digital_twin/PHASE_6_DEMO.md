# Phase 6 E2E Demo Instructions

You can manually verify the Phase 6 end-to-end integration by executing the API calls below.

## 1. Start the Server
Open a terminal in the project root and start Uvicorn:
```bash
python -m uvicorn app.main:app --port 8000
```

## 2. API Flow

### Step A: Create the Farm Digital Twin
```bash
curl -X POST "http://localhost:8000/api/v1/digital-twin" \
-H "Content-Type: application/json" \
-d '{
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
}'
```

### Step B: Call Model 1 through the Digital Twin Adapter
```bash
curl -X POST "http://localhost:8000/api/v1/digital-twin/demo_farm_001/predict/model1"
```

### Step C: Retrieve the Updated Twin (Verify Persistence)
```bash
curl -X GET "http://localhost:8000/api/v1/digital-twin/demo_farm_001"
```
*Look at the bottom of the response payload. You will see `"model_outputs"` populated with `"model1"` and its top-5 crop recommendations.*

---

## 3. Incomplete Data Test (Fail Gracefully)

### Step A: Create a Partial Farm (Missing potassium, pH, rainfall, humidity)
```bash
curl -X POST "http://localhost:8000/api/v1/digital-twin" \
-H "Content-Type: application/json" \
-d '{
  "farm_id": "demo_farm_incomplete",
  "farmer_id": "MH_FARMER_999",
  "soil": {
    "nitrogen": 85.0,
    "phosphorus": 40.0
  },
  "climate": {
    "temperature": 26.5
  }
}'
```

### Step B: Attempt Model 1 Prediction
```bash
curl -X POST "http://localhost:8000/api/v1/digital-twin/demo_farm_incomplete/predict/model1"
```
*Expected Result: 422 Unprocessable Content. The response will explicitly list the missing attributes required to run Model 1.*
