# Phase 4: Cost & Profit Model Integration Report

## 1. Overview
The **Cost & Profit Prediction Model (Model 6)** has been successfully integrated into the authenticated Farm Digital Twin. It utilizes the shared `ModelResult` schema and adheres to all economic correctness boundaries (it restricts predictions purely to Cost and Cost/Ha, as revenue and profit cannot be safely projected without the missing Yield and Price models).

## 2. Model Type and Artifact
- **Type:** Histogram Gradient Boosting Prototype (`HistGradientBoosting_Prototype`)
- **Artifact:** `models/model6_cost_profit/artifacts/cost_model.joblib`
- **Inference Script:** `models.model6_cost_profit.inference`

## 3. Files Changed
- `ml/schemas/prediction.py`: Added `CostPredictionRequest` to accept farmer-entered cultivation costs and bridge the Digital Twin schema gap.
- `ml/routers/farms.py`: Implemented `POST /api/v1/farms/{farm_id}/fields/{field_id}/seasons/{season_id}/predict-cost`.
- `ml/tests/test_cost_profit_api.py` (New): Added tests for the new endpoint.

## 4. API Endpoint Contract
**Endpoint:** `POST /api/v1/farms/{farm_id}/fields/{field_id}/seasons/{season_id}/predict-cost`

**Required Identifiers:**
- `farm_id`, `field_id`, `season_id` in path.
- `Authorization: Bearer <token>` in headers.

**Required Inputs (JSON Payload - `CostPredictionRequest`):**
To bridge the strict 20-feature requirement of the model, the user must provide these inputs that are not natively tracked in the database:
- `sunlight_hours_day` (float)
- `fertilizer_kg_ha` (float)
- `pesticide_litre_ha` (float)
- `seed_quality_score` (float)
- `water_efficiency_t_per_1000m3` (float)
- `disease_pest_risk_pct` (float)

**Successful Response (`200 OK` - `status: success`):**
```json
{
  "model_name": "cost_profit_model",
  "model_version": "HistGradientBoosting_Prototype",
  "status": "success",
  "prediction": {
    "predicted_total_cost_inr": 20000.0,
    "predicted_cost_per_hectare_inr": 10000.0
  },
  "unit": "INR",
  "inputs_used": { ... },
  "data_provenance": "digital_twin_and_user_input",
  "timestamp": "2026-10-09T09:20:00.000Z",
  "warnings": [
    "Yield and Market Price models are not yet available. Profit and Revenue cannot be calculated at this time."
  ]
}
```

**Insufficient Data Response (`200 OK` - `status: insufficient_data`):**
Returned if the database records or user payload lack any of the strict 20 features.
```json
{
  "status": "insufficient_data",
  "warnings": ["Missing required inputs: Sunlight_Hours_Day, Fertilizer_kg_ha..."]
}
```

## 5. Feature Mapping
- **Digital Twin Mapping:** `State` (from farm location), `Farm_Area_Hectares`, `Crop`, `Season`, `Soil_pH`, `Nitrogen`, `Phosphorus`, `Potassium`, `Moisture`, `Rainfall`, `Temperature`, `Humidity`.
- **Payload Mapping:** `Sunlight_Hours_Day`, `Fertilizer`, `Pesticide`, `Seed_Quality`, `Water_Efficiency`, `Disease_Risk`, `Water_Used`, `Irrigation_Method`.

## 6. Tests and Results
- **Run:** `$env:PYTHONPATH="."; venv\Scripts\pytest ml\tests\test_cost_profit_api.py -v`
- **Results:** 5 / 5 Passed.
- **Regression:** Crop Recommendation tests (8 / 8) passed. 
- **Mocked vs Live:** The Farm API ownership and context resolution are mocked against the DB. The model inference calls are mocked in specific scenarios (`test_cost_success`, `test_cost_inference_error`) to simulate XGBoost outputs instantly, but `test_cost_live_inference` successfully attempts to load the actual `.joblib` artifact.

## 7. Database Changes
- **None.** The existing `model_predictions` table correctly supports logging these JSON results.

## 8. Remaining Blockers & Known Limitations
- The model enforces 100% strict adherence to 20 inputs. If the user fails to provide the exact subset of missing payload fields, inference is completely blocked.
- Economic limitations: Profit cannot be calculated yet. The endpoint exclusively projects raw cost in INR.
