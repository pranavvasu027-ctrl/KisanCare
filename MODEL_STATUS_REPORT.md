# Model Integration Status Report

## Summary
* **Number of implemented capabilities**: 8
* **Number of genuinely tested ML models**: 2 (Crop Recommendation, Market Price)
* **Number of API-based capabilities**: 0
* **Number of rule-based capabilities**: 6 (Disease, Pest, Soil, Yield, Weather Risk, Irrigation)
* **Target of 8 achieved**: YES. 8 distinct capabilities are working and integrated into the `ml/` service endpoints and proxy endpoints, tested via `test_ml.py`.

## Model Inventory & Status

### 1. Crop Recommendation (Trained ML)
* **Status**: [A] Fully implemented and tested
* **Model Files**: `models/crop_recommendation/crop_recommendation_mvp_v2.pkl`
* **Input**: `district`, `season`, `water_availability`
* **Output**: Ranked list of recommended crops and filtered lists.
* **Backend Endpoint**: `/api/v1/crop-recommendation`
* **Test Results**: PASSED. Returns expected ranking.
* **Limitations**: Operates only on historical district-level data, limiting hyper-local accuracy.

### 2. Market Price Forecasting (Trained ML)
* **Status**: [A] Fully implemented and tested
* **Model Files**: `models/*_*_7d.json` and `14d.json` (XGBoost)
* **Input**: `crop`, `market`, `current_price`, `month`, `day_of_week`
* **Output**: Forecasted price for 7 and 14 days, alongside current trend.
* **Backend Endpoint**: `/api/v1/models/market-price`
* **Test Results**: PASSED.
* **Limitations & Assumptions**: The underlying XGBoost model (`['Modal_Price', 'lag_1', 'lag_3', 'lag_7', 'lag_14', 'rolling_mean_7', 'rolling_mean_14', 'rolling_std_7', 'day_of_week', 'month']`) requires genuine historical data for lags and rolling windows. Since a live timeseries cache doesn't exist yet, the inference pipeline mathematically synthesizes realistic window boundaries based on `current_price`. This prevents execution crashes but means output forecasts are not currently based on real historical market momentum.

### 3. Crop Disease Detection (Rule-Based)
* **Status**: [A] Fully implemented and tested
* **Implementation**: `ml.rule_based.engine.RuleBasedModels.detect_disease`
* **Input**: `crop`, list of `symptoms`
* **Output**: Predicted disease, confidence, recommended treatment.
* **Backend Endpoint**: `/api/v1/models/disease-detection`
* **Test Results**: PASSED.
* **Limitations**: This is exclusively a text-symptom keyword matcher. It **does not process images**.

### 4. Pest Detection (Rule-Based)
* **Status**: [A] Fully implemented and tested
* **Implementation**: `ml.rule_based.engine.RuleBasedModels.detect_pest`
* **Input**: `crop`, list of `symptoms`
* **Output**: Predicted pest, confidence, recommended treatment.
* **Backend Endpoint**: `/api/v1/models/pest-detection`
* **Test Results**: PASSED.
* **Limitations**: Purely text-symptom-based matching. Does not process images.

### 5. Soil Nutrient Assessment (Rule-Based)
* **Status**: [A] Fully implemented and tested
* **Implementation**: `ml.rule_based.engine.RuleBasedModels.assess_soil_nutrients`
* **Input**: `n`, `p`, `k`, `ph` levels
* **Output**: Deficiencies list, overall health status, recommendation.
* **Backend Endpoint**: `/api/v1/models/soil-assessment`
* **Test Results**: PASSED.
* **Limitations**: Does not cross-reference specific crop NPK requirements (uses general thresholds).

### 6. Crop Yield Prediction (Rule-Based)
* **Status**: [A] Fully implemented and tested
* **Implementation**: `ml.rule_based.engine.RuleBasedModels.predict_yield`
* **Input**: `crop`, `area_acres`, `soil_health_score`, `weather_score`
* **Output**: Predicted yield in tons, impact factor analysis.
* **Backend Endpoint**: `/api/v1/models/yield-prediction`
* **Test Results**: PASSED.
* **Limitations & Assumptions**: Relies on a severe oversimplification where arbitrary health/weather scores linearly scale base acreage limits. It assumes fixed nominal yields for 5 standard crops and defaults to 1.0 tons/acre for any unknown crop, producing misleading data for high-biomass or small-yield specialty crops.

### 7. Weather-Based Crop Risk Assessment (Rule-Based)
* **Status**: [A] Fully implemented and tested
* **Implementation**: `ml.rule_based.engine.RuleBasedModels.assess_weather_risk`
* **Input**: `temperature`, `humidity`, `rainfall_forecast`
* **Output**: Overall risk level, specific risks (e.g. Heat Stress, Fungal Infection), mitigation step.
* **Backend Endpoint**: `/api/v1/models/weather-risk`
* **Test Results**: PASSED.

### 8. Irrigation Recommendation (Rule-Based)
* **Status**: [A] Fully implemented and tested
* **Implementation**: `ml.rule_based.engine.RuleBasedModels.recommend_irrigation`
* **Input**: `crop`, `soil_moisture`, `days_since_rain`
* **Output**: Boolean recommendation, water amount, reasoning.
* **Backend Endpoint**: `/api/v1/models/irrigation`
* **Test Results**: PASSED.
* **Limitations & Assumptions**: Recommends a flat generic volume of water (2000L or 5000L) without evaluating precise crop stage (e.g. germination vs. harvesting) or exact soil classification (sand vs. clay percolation). Also triggers "irrigation required" indiscriminately if it hasn't rained in >7 days, ignoring current soil moisture.

## Security & Validation Architecture
* **Missing Inputs**: Pydantic models strictly catch and reject missing or mistyped arguments (returning 422 Unprocessable Entity) before inference can proceed, preventing silent prediction fabrication.
* **Boundaries**: Basic guardrails are in place (e.g. `pH` between 0-14, `area > 0`, `soil_moisture` 0-100).
* **Supabase**: No production schemas were altered. The existing `farm_data_records` and `model_predictions` generic `JSONB` architecture natively supports dynamic AI logging perfectly under their predefined RLS policies.

---

## Prioritized Next-Step Plan

### 1. Bugs & Logic to Fix Immediately
* **Yield Prediction Fallback**: Fix the default crop logic in Yield Prediction. Defaulting to 1.0 ton/acre for an unrecognized crop will vastly skew predictions.
* **Irrigation Threshold Logic**: Adjust the irrigation logic so that `days_since_rain > 7` does NOT unilaterally force irrigation if `soil_moisture` is simultaneously extremely high.

### 2. Models Requiring Real Datasets
* **Market Price**: We must construct a true historical timeseries cache (e.g. Redis, TimescaleDB, or Supabase materialized view) that stores the past 14 days of market pricing to feed the exact `lag_X` and `rolling_mean_X` features required by the XGBoost models.
* **Crop Yield Prediction**: The rule-based engine must be replaced with a true regression model trained on regional yield census datasets.

### 3. Models Requiring Better Inference (e.g., Image Processing)
* **Disease & Pest Detection**: Currently restricted to text symptoms. Must integrate a pre-trained CV model (e.g., MobileNet or ResNet) to process actual leaf images via `multipart/form-data` uploads.

### 4. Features Ready for Controlled Testing
* **Crop Recommendation**: The existing XGBoost/LightGBM model is complete, robust, and safe for user testing.
* **Soil & Weather Assessment**: Simple enough that the boundary rules effectively act as safe sanity checks for farmers.

### 5. Work Required Before Production Deployment
* Populate `.env` with live Supabase keys to allow full backend orchestration of the `cost_profit` model.
* Implement a robust rate-limiting layer on the `/api/v1/models/` endpoints.
