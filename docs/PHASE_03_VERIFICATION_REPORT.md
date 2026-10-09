# Phase 3 Verification Report

## A. Verified Working
1. **Farm API & Authentication:** The FastAPI dependency (`get_current_user_client`) correctly extracts the JWT, verifies it via Supabase Auth, and scopes the PostgREST client to the user.
2. **Context Resolution:** The single PostgREST embedding query (`farms -> fields -> irrigation_records & seasons`) accurately collects all inputs needed for the Crop Recommendation model (`district`, `season_name`, `water_availability`).
3. **Model Inference (Model 1):** The endpoint dynamically calls the real `PredictionPipeline.recommend()` function, passing exact features without fabrication. It correctly returns `insufficient_data` if `water_availability` is missing, and captures the `model_version`.

## B. Mock-Tested Only
1. **Farm API Router Tests (`ml/tests/test_farms_api.py`):** 8/8 Passed.
   - Tests validating Farm/Field creation, unauthorized rejections, missing input detection, and the API response structure use `MagicMock` for the database client.
2. **Database Persistence:** The `model_predictions` insert logic is mock-tested, verifying that the router constructs the correct payload schema before executing the insert.

## C. Live-Tested Successfully
1. **ML Inference Regression (`ml/tests/test_api.py`):** 8/8 Passed.
   - These tests instantiate the real `PredictionPipeline` and run live inference against the actual `crop_recommendation_mvp_v2.pkl` artifact to guarantee deterministic outputs and correct latency.
2. **Schema Integrity:** The static SQL verification confirms all queried columns (e.g., `location`, `water_availability`) and `model_predictions` schema actually exist in the locked migration.

## D. Failed Checks
1. **Legacy Stub Tests (`backend/tests/test_integration.py`):** 2 Failed.
   - Returns 404 for `/api/v1/farms/F001/digital-twin` and `/api/v1/simulate` because these test endpoints from an old prototype backend that were replaced by our new secure `ml/routers/farms.py` implementation.

## E. Blockers
1. **Live JWT Verification:** Full live database tests are **BLOCKED**. The environment lacks a seeded test user credential (email/password) necessary to generate a valid Supabase JWT and execute end-to-end RLS-protected queries against the local DB.
2. **AppLocker DLL Issue (`tests/digital_twin/test_dt_api.py` & `tests/model1/test_api.py`):** 11 Errors.
   - These legacy tests fail to load during collection due to an OS-level Application Control policy blocking `sklearn\utils\sparsefuncs_fast.pyd` when loaded through the legacy `app.model1` module.

## F. Exact Recommended Fixes
1. **Cleanup Legacy Backend:** Delete the deprecated `backend/app` directory and its associated `tests/digital_twin/` tests to unify the project on the new `ml/main.py` entry point.
2. **Seed Test Users:** Update the Supabase configuration or a test fixture to inject a known user via the Admin API so live JWT integration tests can be safely unblocked.
