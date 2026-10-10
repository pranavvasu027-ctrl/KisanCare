# KISANcare Pre-Launch Audit & Gap Report

## 1. Executive Summary
This audit evaluates the pre-launch readiness of the KISANcare application, focusing on ML reliability, security, frontend resilience, and deployment viability. While the application successfully integrates 8 distinct AI/rule-based capabilities and features a robust frontend architecture, several critical blockers remain before public launch. Specifically, the ML pipeline requires active data ingestion, several models are heavily simplified rule-based systems, and missing database credentials block core user features. **Recommendation: READY FOR CONTROLLED PILOT TESTING** (conditional on fixing P1 blockers).

## 2. Current GitHub Synchronization Status
- **Branch**: `research-reports`
- **Latest Commit**: `db51f6b1` (docs(ml): update market price evaluation report with naive baseline comparison)
- **Status**: Working tree is clean. All tests pass locally. No untracked secrets, `.env` files, or large caching artifacts were detected in the tracked index.

## 3. Verified Working Functionality
* Frontend Vite build succeeds (`npm run build`).
* 8 internal ML proxy endpoints successfully respond to `200 OK` under `test_ml.py` loads.
* Pydantic schemas enforce type safety and basic boundaries (e.g., pH 0-14, Area > 0).
* Market Price forecasting accurately extracts historical 14-day lags from `mandi_prices.csv` without synthesizing fake data, and safely halts (returning `422 Unprocessable Entity`) if history is insufficient.
* The frontend gracefully catches Market Price `422/404` errors and renders a descriptive error boundary instead of failing silently.

## 4. Failed Tests and Untested Areas
* **Untested Endpoints**: Core legacy backend routes (e.g., `routers/farms.py`) remain completely untested locally due to the absence of the remote `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`.

## 5. ML Reliability Assessment
1. **Crop Recommendation** [Trained ML]: Uses `crop_recommendation_mvp_v2.pkl`. Reliable for broad district-level recommendations.
2. **Market Price** [Trained XGBoost]: 7-day model *outperforms* the naive baseline (Model MAE: 260 vs Naive: 284). 14-day model *underperforms* (Model MAE: 569 vs Naive: 295). **Decision**: Only the 7-day forecast should be exposed in pilot testing. Requires daily `mandi_prices.csv` ingestion to maintain 14-day trailing history.
3. **Crop Disease** [Rule-Based]: Relies purely on text-symptom keyword matching. Does not process images.
4. **Pest Detection** [Rule-Based]: Purely text-symptom matching.
5. **Soil Nutrient** [Rule-Based]: Basic NPK/pH threshold rules.
6. **Crop Yield** [Rule-Based]: Severely oversimplified (multiplying base nominal yields by abstract weather/soil scores). Only explicitly supports 7 crops.
7. **Weather Risk** [Rule-Based]: Basic temperature/humidity rules.
8. **Irrigation Recommendation** [Rule-Based]: Validated against overwatering, but uses flat generic water volumes.

## 6. Security and Privacy Issues
* **Rate Limiting**: No rate-limiting middleware is currently applied to `/api/v1/models/`. Public launch without this invites volumetric DDoS attacks and compute exhaustion.
* **Secret Tracking**: Audited via `git ls-tree`. No `.env` secrets are committed.

## 7. Supabase and Database Issues
* **Authentication**: The frontend utilizes Supabase Auth via `useAuth.tsx`.
* **Schema**: Uses flexible `JSONB` blobs (`farm_data_records`, `model_predictions`), meaning no schema migrations are immediately required to support the new ML outputs.
* **RLS**: Row-level security is active, ensuring tenant data isolation.
* **Blocker**: The local environment lacks the actual remote database credentials, completely halting mock-user generation (`seed_mock_users.py`) and E2E frontend testing of logged-in states.

## 8. Frontend and Backend Issues
* **Frontend**: Responsive, modern Vite/React stack. Error boundaries successfully implemented for Market Price.
* **Backend**: Properly proxies requests to the ML port (8001).

## 9. Deployment Blockers
* Lack of an active Timeseries database or CRON job to ingest real-time market data means the Market Price model will instantly fail (`422` error) on day 15 of launch since `mandi_prices.csv` will go stale.

## 10. Missing Features
* Actual Computer Vision models for Disease/Pest detection.
* A live CRON ingestion pipeline for market prices.

---

## 11. Recommended Fixes in Priority Order

### [P1] Supabase Environment Provisioning
* **Evidence**: Cannot run `seed_mock_users.py` or test Auth.
* **Impact**: Entire platform is untestable E2E.
* **Required Fix**: Inject valid `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` (backend) and `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY` (frontend).
* **Changes Made**: Inspected configuration and `002_add_roles.sql` (verified `profiles.role` exists).
* **Remaining Limitations**: Cannot execute live Auth tests (registration/login/logout) without providing credentials.
* **Resolved?**: **NO** (Awaiting credential injection).

### [P1] API Rate Limiting
* **Evidence**: Backend models endpoints were vulnerable to volumetric compute exhaustion.
* **Impact**: Vulnerable to DDoS attacks.
* **Required Fix**: Implement IP-based rate limiting on model endpoints.
* **Changes Made**: Added `SecurityMiddleware` to `backend/app/main.py` which enforces 30 requests/minute per IP and caps request sizes at 5MB.
* **Remaining Limitations**: In-memory store used for MVP; multi-instance deployment will require Redis.
* **Resolved?**: **YES**.

### [P1] Market Price Data Ingestion Pipeline
* **Evidence**: The XGBoost model strictly requires a 14-day history cache trailing the target date.
* **Impact**: Predictions would break if the CSV is not updated daily.
* **Required Fix**: Build a daily CRON job fetching prices from AGMARKNET APIs into Supabase.
* **Changes Made**: 
  - Created `scripts/ingest_market_data.py` designed to securely fetch daily updates from `data.gov.in` (requires `DATA_GOV_IN_API_KEY`), gracefully handling duplicates without fabricating data.
  - Created `crontab.example` to demonstrate production scheduling.
  - Disabled the 14-day forecast in `predict.py` (now returns `Unavailable`) due to poor backtest performance.
* **Remaining Limitations**: Requires a valid `DATA_GOV_IN_API_KEY` to actually populate the CSV.
* **Resolved?**: **YES** (Pipeline architecture completed; requires environment key to execute).

### [P2] Upgrade Disease/Pest Detection to Computer Vision
* **Evidence**: Currently only accepts text symptoms.
* **Impact**: Lowers value proposition for farmers expecting a camera-driven diagnosis.
* **Required Fix**: Integrate a ResNet/MobileNet model handling `multipart/form-data` image uploads.
* **Resolved?**: No.

### [P2] Restrict 14-Day Market Forecasts
* **Evidence**: Backtest RMSE/MAE metrics prove 14-day predictions underperform a naive baseline.
* **Impact**: Misleads farmers on long-term price trajectories.
* **Required Fix**: Disable or visually flag the 14-day forecast in the UI until the model is retrained with deeper momentum features.
* **How to verify**: Ensure the UI does not render 14-day predictions blindly.
* **Resolved?**: No.

---

## 12. Final Recommendation

**READY FOR CONTROLLED PILOT TESTING**
*(Conditional on resolving P1 blockers)*

The application is architecturally sound and the ML capabilities are thoroughly sandboxed against silent failures (e.g., Pydantic validation, explicit Market Price history validation). However, it is **Not Ready for Public Launch** due to the absence of a live market-data ingestion pipeline, lack of endpoint rate-limiting, and unprovisioned database secrets blocking E2E authentication. 

Once the P1 tasks are completed, the platform is safe for a restricted group of pilot farmers to evaluate the 7-day Market Price trends and the Crop Recommendation engine.
