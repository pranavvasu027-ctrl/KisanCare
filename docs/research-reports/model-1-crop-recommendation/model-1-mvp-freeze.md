# Model 1 MVP Freeze Report

## Baseline Configuration

The current validated model is preserved as the official Model 1 MVP baseline. Do not modify or replace the v2 model.

*   **Model:** XGBoost Regressor v2
*   **Target:** Area Allocation Frequency
*   **ML features:**
    *   District
    *   Season
    *   Candidate Crop
*   **Decision constraints:**
    *   Water Availability
    *   Existing season rules
*   **Performance:**
    *   Test Top-1: ~83.5%
    *   Test Top-3: ~92.9%
*   **API:** FastAPI
*   **API tests:** 8/8 passed
*   **API average TestClient latency:** ~10.24 ms

## Future Experiments

**Important:** Model B is experimental until it proves improvement over v2 under the same leakage-safe temporal evaluation. v2 remains the benchmark for all future experiments.
