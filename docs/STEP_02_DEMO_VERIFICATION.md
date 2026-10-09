# STEP 02: DEMO VERIFICATION REPORT

## 1. Backend Startup & Health Check

- **Exact Startup Command:** `.\venv\Scripts\python.exe -m uvicorn ml.main:app --host 127.0.0.1 --port 8000` (executed from project root).
- **Virtual Environment:** Successfully verified. The backend relies on dependencies stored in `venv/`, notably `fastapi`, `supabase`, and `xgboost`.
- **Health Check Result:** 
  ```json
  {
      "status": "healthy",
      "model_version": "crop-recommendation-mvp-v2"
  }
  ```
  *(Status: Passed. The prediction pipeline initializes and loads the `.pkl` artifacts on startup).*

## 2. Crop Recommendation Inference

- **Endpoint Tested:** `POST /api/v1/crop-recommendation`
- **Inference Result:**
  ```json
  {
      "model_version": "crop-recommendation-mvp-v2",
      "district": "NASHIK",
      "season": "Rabi",
      "water_availability": "Medium",
      "status": "SUCCESS",
      "recommendations": [
          {"crop": "Wheat", "predicted_area_frequency": 0.5741, "rank": 1},
          {"crop": "Chickpea", "predicted_area_frequency": 0.3332, "rank": 2},
          {"crop": "Sorghum", "predicted_area_frequency": 0.0638, "rank": 3}
      ],
      "filtered_candidates": [
          {
              "crop": "Mango",
              "model_score": 0.1296,
              "eligible": false,
              "filter_reason": "Mango is constrained to ['Whole Year']"
          }
      ],
      "data_source": "APY_2005_2015"
  }
  ```
- **Verification:** The returned result successfully comes from the `HistGradientBoosting` model and the `CropDecisionEngine`. We verified the post-processing natively intercepts crops like Mango and Grapes, filtering them out dynamically because of the configured seasonal constraint (`'Whole Year'`).

## 3. Cost Prediction Inference

- **Inference Mechanism Tested:** Invoked via the internal python `predict_cost` function located in `models.model6_cost_profit.inference.py` (which powers the Orchestrator).
- **Inference Result:**
  ```json
  {
      "predicted_total_cost_inr": 122493.08,
      "predicted_cost_per_hectare_inr": 61246.54,
      "model_status": "SUCCESS",
      "model_type": "HistGradientBoosting_Prototype"
  }
  ```
- **Verification:** The model predicts strictly **Total Cost** and **Cost per Hectare**. It correctly does **not** fabricate a profit prediction, noting internally: `"Yield and Market Price models are not yet available. Profit and Revenue cannot be calculated at this time."`

## 4. Authenticated Orchestrator

- **Endpoint Tested:** `POST /api/v1/farms/f1/fields/f1/seasons/s1/orchestrate`
- **Result:** Refused with `401 Unauthorized`.
- **Prerequisites for Live Test:** 
  The Orchestrator natively queries the Farm Digital Twin stored in Supabase. It extracts Soil, Weather, and Location records directly from the database to feed the models.
  To execute a live demo of this endpoint, you must:
  1. Have a valid Supabase project.
  2. Populate the `.env` file with `SUPABASE_URL` and `SUPABASE_ANON_KEY`.
  3. Send the request with a valid `Authorization: Bearer <JWT_TOKEN>` belonging to a registered user.
  4. Ensure that the database contains a farm context corresponding to the URL path.
  *(Without these, the Orchestrator correctly blocks the request, preserving database integrity).*

## 5. Weather and Market Data Integrations

- **Weather Data:** Does not query live APIs. The system relies entirely on the Digital Twin (the database state, updated by the user) for weather parameters. 
- **Market Data:** Does not query live APIs. The backend uses a local historical snapshot (`data/mandi_prices.csv`) for Market Price Forecasting (`xgboost` time-series). 

## 6. Demonstration Readiness (Next Steps)

The `VIDEO_SUBMISSION_MODEL_DEMO.md` file correctly reflects this reality and is safe to use for recording. 

**Remaining Blockers for the UI integration:** 
Because the Orchestrator requires Supabase Authentication—and the Flutter App currently has no Authentication implemented—the Flutter App cannot query the Orchestrator directly. If the UI needs to show live predictions, you will either need to implement Auth in Flutter (Phase 3/4) or expose an unauthenticated test endpoint for the dashboard.
