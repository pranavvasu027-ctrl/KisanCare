# Phase 4: Cost & Profit Model Audit

## 1. Actual Model Implementation
- **Model Type:** Histogram Gradient Boosting Prototype (`HistGradientBoosting_Prototype`).
- **Artifact Path:** `models/model6_cost_profit/artifacts/cost_model.joblib`
- **Inference Function:** `models.model6_cost_profit.inference.predict_cost(input_features: dict)`
- **Loading Function:** Loads dynamically inside the inference script using `joblib.load(MODEL_PATH)`.
- **Required Inputs (20 strict features):**
  1. `State` (str)
  2. `Crop` (str)
  3. `Season` (str)
  4. `Irrigation_Method` (str)
  5. `Farm_Area_Hectares` (float)
  6. `Rainfall_mm` (float)
  7. `Avg_Temperature_C` (float)
  8. `Humidity_pct` (float)
  9. `Sunlight_Hours_Day` (float)
  10. `Soil_pH` (float)
  11. `Soil_Moisture_pct` (float)
  12. `Nitrogen_kg_ha` (float)
  13. `Phosphorus_kg_ha` (float)
  14. `Potassium_kg_ha` (float)
  15. `Fertilizer_kg_ha` (float)
  16. `Pesticide_Litre_ha` (float)
  17. `Seed_Quality_Score` (float)
  18. `Water_Used_m3` (float)
  19. `Water_Efficiency_t_per_1000m3` (float)
  20. `Disease_Pest_Risk_pct` (float)

## 2. Digital Twin Data Mapping
We can perfectly map the following features from the locked database schema:
- **`State`**: Derived from `farms.location`.
- **`Crop`**: `seasons.crop`
- **`Season`**: `seasons.season_name`
- **`Farm_Area_Hectares`**: `fields.area`
- **`Soil_pH`, `Nitrogen_kg_ha`, `Phosphorus_kg_ha`, `Potassium_kg_ha`, `Soil_Moisture_pct`**: Extracted from the most recent `soil_records`.
- **`Rainfall_mm`, `Avg_Temperature_C`, `Humidity_pct`**: Extracted from the most recent `weather_records`.
- **`Irrigation_Method`, `Water_Used_m3`**: Extracted from the most recent `irrigation_records` (`irrigation_method` and `irrigation_amount`).

### Exact Schema Gap (Missing Inputs)
The Digital Twin schema currently lacks dedicated columns for the following exact required model inputs. They must be provided dynamically by the farmer in the API payload:
1. `Sunlight_Hours_Day` (Could potentially be tucked into `weather_records.forecast_information JSONB`, but not reliably).
2. `Fertilizer_kg_ha`
3. `Pesticide_Litre_ha`
4. `Seed_Quality_Score`
5. `Water_Efficiency_t_per_1000m3`
6. `Disease_Pest_Risk_pct`

## 3. Existing Limitations
- The model enforces absolute strictness on these 20 inputs. Providing `None` or skipping a key throws a `ValueError`.
- `predict_cost.py` inside the `ml/` directory was a prototype from a previous session pointing to an invalid hardcoded path `C:\Users\prana\.gemini\...`. The true logic is in `models/model6_cost_profit/inference.py`.
- Yield Prediction and Market Price models are not yet live, limiting the full Economic Engine's revenue capabilities. We will focus purely on the `cost_model` inference to predict Cost and Cost/Ha as requested.
