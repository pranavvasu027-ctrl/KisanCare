# PHASE 4: API INTEGRATION REPORT

## 1. Objective
Build a clean, robust, and standalone FastAPI inference service around the existing Phase 3 Model 1 (Crop Recommendation) artifacts without modifying the underlying model or training pipeline.

## 2. Architecture
The API acts as a thin inference wrapper:
1. **Startup:** Loads `crop_recommendation_model.pkl`, `preprocessor.pkl`, `label_encoder.pkl`, and `model_metadata.json` into a singleton `Model1Service`.
2. **Request:** Receives 7 numeric soil/climate parameters via POST.
3. **Validation:** FastAPI (Pydantic) enforces types. Custom router logic explicitly rejects `NaN` and `Infinity` to prevent downstream C-library crashes.
4. **Inference:** Maps the JSON keys precisely to the feature order defined in `model_metadata.json` (`N`, `P`, `K`, `temperature`, `humidity`, `ph`, `rainfall`), applies the standard scaler, and invokes `predict_proba()`.
5. **Response:** Sorts the 22 probability scores and returns exactly the Top-5 ranked items.

## 3. Project Structure
The API was placed in the root `app/` directory as requested, avoiding coupling with the legacy MVP code in `ml/main.py`.
```
app/
 ├── __init__.py
 ├── main.py
 └── model1/
     ├── __init__.py
     ├── router.py
     ├── schemas.py
     └── service.py
```

## 4. Input Validation & Error Handling
* **Missing Fields:** Automatically rejected by Pydantic with 422.
* **Invalid Datatypes:** Automatically rejected by Pydantic with 422.
* **NaN / Infinity:** Explicitly caught in `router.py` to prevent JSON serialization crashes (returning standard 422).
* **Model Loading Failures:** Handled gracefully via a 503 error, preventing raw Python exceptions from bleeding into the client response.

## 5. Testing
Automated tests were written in `tests/model1/test_api.py` and execute via `pytest`.
* Tested `/health` payload.
* Tested valid recommendations format and sorting.
* Tested missing fields, string inputs, `NaN` and `Infinity`.
* Tested simulated model unloading (503).
All 7 tests passed.

A real HTTP test (`test_server.py`) was also executed via Uvicorn to guarantee actual socket-level compliance.

## 6. How to Run Locally
Ensure you are in the project root.
```bash
# Start the server
python -m uvicorn app.main:app --reload --port 8000

# View Swagger Documentation
# Open browser to: http://localhost:8000/docs
```

## 7. Known Limitations
As extensively documented in the API Contract:
> **This is a baseline crop recommendation model trained on a benchmark dataset. Its benchmark performance should not be interpreted as validated real-world agricultural accuracy.**

The returned `score` is a mathematical probability within the synthetic feature space, not a certified real-world confidence level. No claims of "99.54% accuracy" are exposed to the API consumer.
