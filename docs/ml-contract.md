# ML Contract

## Philosophy
The ML Module is responsible for isolated predictive intelligence.
It should NOT manage database connections or handle user sessions.
It accepts a structured payload and returns a structured prediction.

## Interfaces
All ML services must return the following JSON structure:

```json
{
  "prediction": <any>,
  "confidence": <float_between_0_and_1>,
  "unit": "<string>",
  "factors": ["<list_of_strings>"],
  "limitations": ["<list_of_strings>"]
}
```

### Models

#### 1. Crop Recommendation
**Endpoint:** `/predict/crop`
**Input:** `{"location": "", "soil_type": "", "weather": {}}`
**Output Unit:** `crop_type`

#### 2. Yield Prediction
**Endpoint:** `/predict/yield`
**Input:** `{"crop": "", "area": 0.0, "expected_rainfall": 0.0}`
**Output Unit:** `quintals/hectare`

#### 3. Disease/Pest Prediction
**Endpoint:** `/predict/disease`
**Input:** `{"crop": "", "weather_history": []}`
**Output Unit:** `disease_risk_probability`

#### 4. Risk Prediction
**Endpoint:** `/predict/risk`
**Input:** `{"farm_data": {}}`
**Output Unit:** `risk_score`

#### 5. Price Prediction
**Endpoint:** `/predict/price`
**Input:** `{"crop": "", "month": ""}`
**Output Unit:** `currency_per_quintal`
