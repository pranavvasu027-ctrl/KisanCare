# Phase 3: Model Inventory

## 1. Crop Recommendation (Model 1)
- **Status:** Implemented and operational.
- **Artifacts:** `models/model1/crop_recommendation_model.pkl`, `models/crop_recommendation/crop_recommendation_mvp_v2.pkl`.
- **Inference Function:** `ml.crop_recommendation.predict.PredictionPipeline.recommend()`
- **API Endpoint:** `POST /api/v1/crop-recommendation` (in `ml/main.py`).
- **Inputs:** `district`, `season`, `water_availability`.
- **Outputs:** Recommended crops list, reasoning, and metadata.
- **Availability:** Yes, ready for integration.

## 2. Cost and Profit Prediction (Model 6)
- **Status:** Implemented offline.
- **Artifacts:** `models/model6_cost_profit/artifacts/cost_model.joblib`.
- **Inference Function:** `models.model6_cost_profit.inference.predict_cost()`
- **API Endpoint:** None currently exposed in `ml/main.py`.
- **Availability:** Yes, inference code exists but lacks an integrated API endpoint.

## 3. Market Price Forecasting
- **Status:** Partially implemented (Lookup/Heuristic).
- **Artifacts:** JSON data caches (`models/market/*.json`).
- **Inference Function:** Found in `app/market_price/service.py`.
- **Availability:** Uses static JSON lookup, not a dynamic ML inference pipeline.

## 4. Yield Prediction
- **Status:** Not implemented. Empty stub directories (`ml/yield_prediction/`).

## 5. Disease and Pest Risk Prediction
- **Status:** Not implemented. Empty stub directories.

## 6. Irrigation Prediction
- **Status:** Not implemented. Empty stub directories.

## 7. Farm Risk Prediction
- **Status:** Not implemented. Empty stub directories.

## 8. Post-Harvest Loss Prediction
- **Status:** Not implemented. Empty stub directories.

## 9. NPK Prediction
- **Status:** Not implemented. 

### Selected First Model: Crop Recommendation (Model 1)
**Reason:** It is the most mature model in the repository. It already has a loaded `PredictionPipeline` initialized in `ml/main.py` on startup, and it accepts basic inputs (`district`, `season`, `water_availability`) that map logically to Farm and Season data in the Digital Twin.
