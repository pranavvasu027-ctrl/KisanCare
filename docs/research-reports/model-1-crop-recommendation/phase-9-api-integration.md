# Phase 9 — FastAPI Integration & API Contract

**Date:** 2026-10-05  
**Phase Status:** COMPLETE  
**Mode:** MVP — Validation >70%, end-to-end pipeline, API-ready  
**Branch:** `research-reports`  

---

## 1. Objective
Wrap the validated Model 1 prediction pipeline into a clean, stable FastAPI service. This API serves as the standardized contract for the frontend and future downstream models (e.g., Yield, Risk).

## 2. API Architecture & Model Loading Strategy
The API is built using FastAPI and Pydantic. 
To guarantee high performance, the `PredictionPipeline` (and the underlying XGBoost model, preprocessing arrays, and metadata) is instantiated exactly **once** on application startup using FastAPI's `lifespan` async context manager. It acts as a singleton serving all requests, avoiding expensive disk I/O on every API call.

## 3. Endpoints

### 3.1. `GET /health`
Verifies that the API process is running and the model has successfully loaded into memory.
**Response:**
```json
{
  "status": "healthy",
  "model_version": "crop-recommendation-mvp-v2"
}
```

### 3.2. `GET /api/v1/crop-recommendation/meta`
Exposes the model's capabilities to clients (supported seasons, supported water levels, target definition).
**Response:**
```json
{
  "model_version": "crop-recommendation-mvp-v2",
  "target": "Area_Frequency",
  "supported_crops": 20,
  "supported_seasons": ["Kharif", "Rabi", "Summer", "Whole Year"],
  "water_levels": ["Low", "Medium", "High"],
  "data_source": "APY_2005_2015"
}
```

### 3.3. `POST /api/v1/crop-recommendation`
The primary prediction endpoint. It accepts farmer constraints, runs the XGBoost scoring matrix for all candidates, filters ineligible crops through the Decision Engine, and returns a Top-K ranked JSON array.

## 4. Request & Response Contract

### Example Request (`POST /api/v1/crop-recommendation`)
```json
{
  "district": "PUNE",
  "season": "Kharif",
  "water_availability": "Medium",
  "top_k": 5
}
```

### Example Response
```json
{
  "model_version": "crop-recommendation-mvp-v2",
  "district": "PUNE",
  "season": "Kharif",
  "water_availability": "Medium",
  "status": "SUCCESS",
  "recommendations": [
    {
      "crop": "Soybean",
      "predicted_area_frequency": 0.1691,
      "rank": 1
    },
    {
      "crop": "Sorghum",
      "predicted_area_frequency": 0.1364,
      "rank": 2
    },
    {
      "crop": "Pearl Millet",
      "predicted_area_frequency": 0.1257,
      "rank": 3
    }
  ],
  "filtered_candidates": [
    {
      "crop": "Wheat",
      "model_score": 0.0,
      "eligible": false,
      "filter_reason": "Wheat is constrained to ['Rabi']"
    }
  ],
  "data_source": "APY_2005_2015",
  "score_interpretation": "Predicted historical area-allocation suitability score",
  "latency_ms": 11.2
}
```

## 5. Error Contract
Inputs are rigorously validated.

**Invalid Season (HTTP 422 Unprocessable Entity):**
```json
{
  "detail": [
    {
      "loc": ["body", "season"],
      "msg": "Season must be one of: Kharif, Rabi, Summer, Whole Year",
      "type": "value_error"
    }
  ]
}
```

**Unknown District (HTTP 404 Not Found):**
```json
{
  "detail": "Validation Error: Unknown district GOTHAM"
}
```

## 6. Test Results
Automated integration tests were executed via `FastAPI TestClient`.

*   **Total Tests:** 8
*   **Passed:** 8
*   **Failed:** 0
*   *Tests covered: Health, Meta, Valid Recommendation, Determinism, Invalid Season, Invalid Water, Unknown District, Latency.*

## 7. Latency Results
Because the model is cached in memory, prediction routing overhead is negligible.
*   **Average Latency:** 10.24 ms
*   **Minimum Latency:** 9.39 ms
*   **Maximum Latency:** 14.03 ms

## 8. Swagger URL & Start Command
The API can be run locally using `uvicorn`:
```bash
uvicorn ml.main:app --reload
```
Once running, the interactive Swagger documentation is available at:
**http://127.0.0.1:8000/docs**

## 9. Frontend Integration Example
```javascript
const response = await fetch("http://localhost:8000/api/v1/crop-recommendation", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    district: "PUNE",
    season: "Kharif",
    water_availability: "Medium",
    top_k: 3
  })
});

const data = await response.json();
console.log(`Top recommendation: ${data.recommendations[0].crop}`);
```

## 10. Limitations
*   The model assumes static geographical and historical boundaries for area allocation and does not adapt automatically to changing weather unless explicitly constrained by the Decision Engine.
*   The Top-K filtering drops crops with identical scores deterministically by index rather than secondary heuristics.
