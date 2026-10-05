# KisanCare Farm Digital Twin — Shared Data Contract

## Overview
The Farm Digital Twin represents the "Observe / Current State" layer in the KisanCare architecture. It serves as the single source of truth for all AI models (Crop Recommendation, Yield, Disease, Water Risk, etc.) ensuring that they all operate on the exact same farm context.

## Shared Data Representation
All models in KisanCare must expect their inputs to be derived from the `FarmDigitalTwin` state object. 

### Core Components
1. **Farm Identity:** `farm_id`, `farmer_id`, `area_acres`
2. **Location State:** `district`, `state`, geo-coordinates.
3. **Soil State:** Core macronutrients (`nitrogen`, `phosphorus`, `potassium`), `ph`, and organic carbon. *(Matches Model 1 API inputs)*
4. **Climate State:** `temperature`, `humidity`, `rainfall`. *(Matches Model 1 API inputs)*
5. **Crop/Season State:** `current_crop`, `season`, `planting_date`.
6. **Water State:** `water_availability`, `irrigation_type`.
7. **Financial State (Placeholder):** `budget`, `expected_revenue`.
8. **Market State (Placeholder):** `nearest_market`, `current_price`.

## JSON Schema Example
```json
{
  "farm_id": "F001",
  "farmer_id": "U123",
  "area_acres": 5.0,
  "location": {
    "state": "Maharashtra",
    "district": "Pune",
    "latitude": 18.5204,
    "longitude": 73.8567
  },
  "soil": {
    "nitrogen": 90.0,
    "phosphorus": 42.0,
    "potassium": 43.0,
    "ph": 6.5,
    "organic_carbon": null
  },
  "climate": {
    "temperature": 25.5,
    "humidity": 80.0,
    "rainfall": 200.0,
    "weather_condition": "Sunny"
  },
  "crop": {
    "current_crop": null,
    "season": "Kharif",
    "planting_date": null
  },
  "water": {
    "water_availability": "Medium",
    "irrigation_type": "Drip"
  },
  "financial": {
    "budget": 50000,
    "expected_revenue": null,
    "placeholder": {}
  },
  "market": {
    "nearest_market": "Pune APMC",
    "current_price": null,
    "placeholder": {}
  }
}
```

## Architecture Usage
1. The Farmer updates their profile via the dashboard.
2. The Dashboard updates the Farm Digital Twin via `PUT /api/v1/digital-twin/{farm_id}`.
3. To get a recommendation, the decision engine fetches the Farm Digital Twin, extracts `soil` and `climate` properties, and feeds them into `Model 1 — Crop Recommendation`.
4. Subsequent models (e.g., Yield Prediction) will fetch the same Digital Twin and append their predictions.
