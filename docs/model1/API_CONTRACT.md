# Model 1: Crop Recommendation — API Contract

## Overview
This API provides baseline crop recommendations based on soil nutrients and climatic parameters using the trained Model 1 (Random Forest).

## Limitation Notice
**This is a baseline crop recommendation model trained on a benchmark dataset. Its benchmark performance should not be interpreted as validated real-world agricultural accuracy.**

---

## 1. Predict Crop Recommendations

**Endpoint:** `/api/v1/model1/crop-recommendation`
**Method:** `POST`
**Content-Type:** `application/json`

### Request Schema
All fields are required and must be valid numeric values (float/integer). `NaN` and `Infinity` are strictly rejected.

| Field | Type | Description | Example |
| :--- | :--- | :--- | :--- |
| `nitrogen` | float | Nitrogen content in soil (mg/kg) | 90 |
| `phosphorus` | float | Phosphorus content in soil (mg/kg) | 42 |
| `potassium` | float | Potassium content in soil (mg/kg) | 43 |
| `temperature` | float | Temperature in Celsius | 25.5 |
| `humidity` | float | Relative humidity in percentage | 80 |
| `ph` | float | Soil pH value | 6.5 |
| `rainfall` | float | Rainfall in mm | 200 |

### Example Request
```json
{
    "nitrogen": 90,
    "phosphorus": 42,
    "potassium": 43,
    "temperature": 25.5,
    "humidity": 80,
    "ph": 6.5,
    "rainfall": 200
}
```

### Response Schema
Returns the exact top 5 recommended crops ranked by the model's computed probability score.

### Example Response (200 OK)
```json
{
    "model": "Random_Forest_Baseline",
    "model_version": "1.0.0",
    "recommendations": [
        {
            "rank": 1,
            "crop": "rice",
            "score": 0.56
        },
        {
            "rank": 2,
            "crop": "jute",
            "score": 0.42
        },
        {
            "rank": 3,
            "crop": "papaya",
            "score": 0.01
        },
        {
            "rank": 4,
            "crop": "watermelon",
            "score": 0.01
        },
        {
            "rank": 5,
            "crop": "pigeonpeas",
            "score": 0.0
        }
    ]
}
```

### Error Responses

**422 Unprocessable Entity**
Returned when payload is missing required fields, or fields contain non-numeric types, `NaN`, or `Infinity`.
```json
{
  "detail": "Invalid numeric value for nitrogen. Cannot be NaN or Infinity."
}
```

**503 Service Unavailable**
Returned if the underlying ML model fails to load into memory on application startup.
```json
{
  "detail": "Service Unavailable: Model not loaded."
}
```

---

## 2. Health Check

**Endpoint:** `/health`
**Method:** `GET`

### Example Response (200 OK)
```json
{
    "status": "ok",
    "model": "crop_recommendation",
    "model_loaded": true
}
```
