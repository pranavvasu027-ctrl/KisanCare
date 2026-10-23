# KisanCare API Contract

This document specifies the authoritative REST API contract between the KisanCare Frontend, Backend Decision Engine, and Machine Learning services.

---

## 1. Core Endpoints

### 1.1 Farms & Digital Twin

#### `GET /api/v1/farms/{farm_id}/digital-twin`
Retrieve the synchronized multi-layer telemetry state of a farm.

- **Response (`200 OK`):**
```json
{
  "farm_id": "F001",
  "state": {
    "crop": "wheat",
    "soil_moisture": 0.45,
    "temperature": 25.5,
    "cadastral_parcels": 4,
    "irrigation_source": "Borewell + Drip",
    "health_score": 86,
    "last_synced": "2026-10-22T16:30:00Z"
  }
}
```

#### `POST /api/v1/farms`
Create a new farm profile.

---

### 1.2 Decision Simulation & What-If Engine

#### `POST /api/v1/simulate`
Simulate weather and input shocks against the baseline farm state.

- **Request Body:**
```json
{
  "farm_id": "F001",
  "changes": {
    "rainfall_change_percent": -20,
    "input_cost": 30000
  }
}
```

- **Response (`200 OK`):**
```json
{
  "baseline": {
    "yield": 24,
    "cost": 30000,
    "revenue": 60000,
    "profit": 30000,
    "risk": 0.35
  },
  "scenario": {
    "yield": 20.4,
    "cost": 30000,
    "revenue": 51000,
    "profit": 21000,
    "risk": 0.52
  },
  "differences": {
    "profit_diff": -9000
  },
  "explanation": [
    "Rainfall changed by -20% affecting yield.",
    "This is a mocked simulation for MVP."
  ]
}
```

---

### 1.3 Agronomic Economics Calculator

#### `POST /api/v1/economics/calculate`
Calculate financial returns, cost breakdown, ROI, and break-even points.

- **Request Body:**
```json
{
  "expected_yield": 24,
  "expected_price": 2500,
  "input_cost": 10000,
  "labour_cost": 15000,
  "irrigation_cost": 5000
}
```

- **Response (`200 OK`):**
```json
{
  "total_cost": 30000,
  "expected_revenue": 60000,
  "expected_profit": 30000,
  "roi_percent": 100.0,
  "break_even_price": 1250.0
}
```

---

## 2. Machine Learning & Predictive Endpoints

### 2.1 Precision Irrigation Scheduling (Verified Hybrid)
- **Endpoint:** `POST /api/irrigation/predict`
- **Methodology:** FAO-56 dual crop coefficient physical soil water balance + PyTorch ETo LSTM with Attention.
- **Request Body:**
```json
{
  "crop": "wheat",
  "crop_stage": "mid",
  "soil_type": "loam",
  "soil_moisture": 0.15,
  "rainfall": 0.0,
  "decision_date": "2026-10-22"
}
```
- **Response (`200 OK`):**
```json
{
  "success": true,
  "model": "irrigation",
  "prediction": {
    "irrigation_required": true,
    "irrigation_quantity_mm": 51.53,
    "irrigation_timing": "today",
    "decision_date": "2026-10-22",
    "crop": "wheat",
    "crop_stage": "mid",
    "soil_type": "loam",
    "soil_moisture": 0.15,
    "rainfall_mm": 0.0,
    "water_balance": {
      "soil_water_depletion_mm": 37.5,
      "total_available_water_mm": 225.0,
      "readily_available_water_mm": 112.5,
      "crop_evapotranspiration_mm": 5.8,
      "reference_eto_mm": 5.0,
      "net_irrigation_requirement_mm": 43.3
    },
    "decision_reason_codes": ["ROOT_ZONE_DEPLETION_EXCEEDED_RAW"],
    "warnings": []
  }
}
```

---

### 2.2 Crop Yield Prediction (Verified Supervised ML)
- **Endpoint:** `POST /api/yield/predict`
- **Methodology:** Scikit-Learn `RandomForestRegressor(n_estimators=200)` trained on 20,000+ Indian agro-climatic records.
- **Request Body:**
```json
{
  "state": "Maharashtra",
  "crop": "Soyabean",
  "season": "Kharif",
  "soil_type": "Black",
  "area": 2.5,
  "rainfall": 680.0,
  "temperature": 26.5,
  "humidity": 65.0,
  "nitrogen": 120.0,
  "phosphorus": 45.0,
  "potassium": 35.0
}
```
- **Response (`200 OK`):**
```json
{
  "success": true,
  "model": "crop_yield",
  "prediction": {
    "predicted_yield": 22.8,
    "yield_unit": "quintal/hectare",
    "estimated_production": 57.0,
    "production_unit": "quintal",
    "cultivated_area_hectares": 2.5,
    "confidence_range": {
      "min": 20.5,
      "max": 25.1
    },
    "contributing_factors": [
      { "factor": "State & Agro-climatic Zone", "impact": "Maharashtra" },
      { "factor": "Seasonal Rainfall", "impact": "680.0 mm" }
    ]
  }
}
```

---

### 2.3 Crop Recommendation (Demo / Historical Acreage Patterns)
- **Endpoint:** `POST /api/v1/predict/crop`
- **Schema Resolution:** Forwards `{"data": {...}}` to the ML microservice.
- **Error Handling:** If ML service is unavailable, raises `503 Service Unavailable` by default. If `ENABLE_DEMO_FALLBACK=true`, returns explicitly labeled demo fallback with `is_demo: true` and `confidence: null`.
- **Response Standard:**
```json
{
  "prediction": "Soybean",
  "confidence": null,
  "unit": "crop_type",
  "factors": ["Favorable rainfall conditions"],
  "limitations": ["DEMO DATA - Reflects historical planting patterns only."],
  "is_demo": true
}
```

---

### 2.4 Market Price Forecasting (Unavailable)
- **Endpoint:** `POST /api/v1/predict/price`
- **Status:** Returns `HTTP 501 Not Implemented`. ML forecasting disabled until backtested against Agmarknet historical seasonal baselines.

---

## 3. Health & Diagnostic Endpoints

- `GET /health` and `GET /api/health`
```json
{
  "status": "ok",
  "service": "kisancare-backend",
  "version": "1.0.0"
}
```
