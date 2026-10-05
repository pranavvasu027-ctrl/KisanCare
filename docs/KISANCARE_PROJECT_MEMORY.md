# KISANCARE PROJECT MEMORY

**Date:** 2026-10-05
**Purpose:** Permanent project handoff document capturing the actual real state, architecture, models, decisions, and plans.

---

## 1. PROJECT IDENTITY

**Project Name:** KisanCare
**Project Objective:** A connected Farm Decision Intelligence system built around a Farm Digital Twin.
**Core Value Proposition:** Not just isolated AI predictions, but an integrated pipeline mapping real-world constraints to decisions.
**Hackathon/Demo Objective:** Prove the Observe → Predict → Simulate → Compare → Decide → Learn loop works.
**Current Stage:** Early development. Crop Recommendation model MVP is trained and exposed via FastAPI. Frontend contains basic mocks. Database and most other models are currently planned but not implemented.

**Core Loop:**
Observe → Predict → Simulate → Compare → Decide → Learn

**Overall Architecture Concept:**
Data → Data Fusion → Farm Digital Twin → AI Prediction → Risk → What-If Simulation → Optimization → Explainable Decision → Farmer Action → Actual Outcome → Farm Memory → Digital Twin

---

## 2. FINAL ARCHITECTURE

| Component | Location | Technology | Current Status |
|-----------|----------|------------|----------------|
| **Frontend** | `frontend/` | React, Vite, Tailwind | Partially IMPLEMENTED (Mocking API responses) |
| **Backend API** | `ml/main.py` | FastAPI | Partially IMPLEMENTED (Exposes Crop Rec) |
| **Database** | N/A | Unknown | PLANNED — NOT IMPLEMENTED |
| **Digital Twin** | `digital_twin/` | Concept only | PLANNED — NOT IMPLEMENTED |
| **Decision Engine** | `ml/crop_recommendation/predict.py` | Python Rules | Partially IMPLEMENTED (Basic Crop filtering) |
| **What-If Simulator** | `frontend/src/App.tsx` | Mock only | PLANNED — NOT IMPLEMENTED |
| **AI Copilot** | N/A | Unknown | PLANNED — NOT IMPLEMENTED |

---

## 3. AI MODEL INVENTORY

| Model | Status | Framework | File/Path | Notes |
|-------|--------|-----------|-----------|-------|
| **1. Crop Recommendation** | IMPLEMENTED | XGBoost | `models/crop_recommendation/` | `crop_recommendation_mvp_v2.pkl` |
| **2. Yield Prediction** | PLANNED | UNKNOWN | N/A | Needs implementation |
| **3. Disease/Pest Detection** | PLANNED | UNKNOWN | N/A | Needs implementation |
| **4. Irrigation/Water** | PLANNED | UNKNOWN | N/A | Needs implementation |
| **5. Risk Prediction** | PLANNED | UNKNOWN | N/A | Needs implementation |
| **6. Cost & Profit** | PLANNED | UNKNOWN | N/A | Needs implementation |
| **7. Market Price** | PLANNED | UNKNOWN | N/A | Needs implementation |
| **8. Post-Harvest Loss** | PLANNED | UNKNOWN | N/A | Needs implementation |

### Model Details: Crop Recommendation (MVP V2)
* **Status:** IMPLEMENTED
* **Algorithm:** XGBoostRegressor (Hist) with Candidate Grid Zeroes
* **Dataset/Source:** APY (Agricultural Production Yield) 2005-2015
* **Input Features:** District, Season, Crop
* **Output Target:** `Area_Frequency`
* **Supported Crops:** Dynamic based on categorical levels (currently trained on APY data).
* **Reported Accuracy:** val_top1: ~83.5%, test_top1: ~83.5%
* **API Endpoint:** `/api/v1/crop-recommendation`

---

## 4. CROP RECOMMENDATION MODEL — SPECIAL ATTENTION

**STRATEGY UPDATE:** The project has moved away from the fixed 20-crop strategy and the Kaggle 22-crop Random Forest benchmark.
* The original repository (`djdhairya/Crop-Recommendation`) based on Kaggle data was analyzed but **SUPERSEDED**.
* The implemented model (`mvp_v2`) uses actual historical agricultural data (APY) predicting `Area_Frequency`.
* **Crops are data-driven:** The model evaluates whatever crops exist in the `cat_levels` of the dataset for a given district and season. It is NOT limited to a hardcoded 20-crop list.
* The model output is piped through a `CropDecisionEngine` to filter out crops based on current water availability constraints (e.g. Rice/Sugarcane filtered if water is 'Low').

---

## 5. CROP CATALOGUE

* **Status:** PLANNED — NOT IMPLEMENTED (as a centralized DB).
* **Current Implementation:** Categorical encodings within `models/crop_recommendation/preprocessing_mvp_v2.pkl`.
* **Observation:** Codebase relies on `self.cat_levels['Crop']` from the pickled preprocessing step. No centralized SQL/NoSQL table mapping crop metadata (scientific name, category, etc.) exists yet.

---

## 6. DATA SOURCES

### ACTUALLY USED DATA
* **APY (Agricultural Production Yield):** Used for training the MVP Crop Recommendation model (Years 2005-2015).

### POSSIBLE FUTURE DATA SOURCES
* UPAg, SoilGrids, ERA5, APMC Market Data (None are currently integrated into the prediction pipelines).

---

## 7. MODEL INPUT/OUTPUT CONTRACTS

### Actual Implementation: Crop Recommendation (`/api/v1/crop-recommendation`)
**Input JSON:**
```json
{
  "district": "NASHIK",
  "season": "Kharif",
  "water_availability": "Medium",
  "top_k": 5
}
```

**Output JSON:**
```json
{
  "model_version": "crop-recommendation-mvp-v2",
  "district": "NASHIK",
  "status": "SUCCESS",
  "recommendations": [
    { "crop": "Maize", "predicted_area_frequency": 0.85, "rank": 1 }
  ],
  "filtered_candidates": [],
  "score_interpretation": "Predicted historical area-allocation suitability score"
}
```
*(Note: Differs from older `docs/ml-contract.md` which incorrectly lists soil type and weather as inputs. The `ml/main.py` implementation is the source of truth.)*

---

## 8. DIGITAL TWIN

* **Status:** Concept defined in `digital_twin/README.md`.
* **Database Tables:** PLANNED — NOT IMPLEMENTED.
* **API Endpoints:** Frontend calls `/api/v1/farms/F001/digital-twin`, but backend does not implement it (frontend is mocking data).

---

## 9. DECISION ENGINE

* **Status:** Partially IMPLEMENTED for Crop Recommendation.
* **Current Logic:** Found in `ml/crop_recommendation/predict.py`. Excludes high-water crops (Sugarcane, Rice, Banana) if water availability is 'Low'. Applies strict season rules.
* **Future:** Needs integration with economics, risk, and yield predictions.

---

## 10. WHAT-IF / COUNTERFACTUAL ENGINE

* **Status:** PLANNED — NOT IMPLEMENTED.
* Frontend has a mock UI button simulating a -20% rainfall change and showing mocked Yield/Profit/Risk changes. No backend logic exists yet.

---

## 11. CONFIDENCE SYSTEM

* **Status:** PLANNED — NOT IMPLEMENTED.
* Currently, the crop model returns a raw regression score (`predicted_area_frequency`), but no holistic data-confidence metric is generated based on data quality/sparsity.

---

## 12. INCOMPLETE DATA HANDLING

* **Current Behavior:** Strict FastAPI Validation. If `district` or `season` is missing or unrecognized, the API throws a 422 Validation Error.
* **Expected Behavior (Future):** Degrade gracefully, decrease confidence score, and infer missing values based on region/history.

---

## 13. API INVENTORY

| Endpoint | Method | Status | Frontend Consumer | Purpose |
|----------|--------|--------|-------------------|---------|
| `/health` | GET | IMPLEMENTED | N/A | System check |
| `/api/v1/crop-recommendation/meta` | GET | IMPLEMENTED | N/A | Fetch model metadata |
| `/api/v1/crop-recommendation` | POST | IMPLEMENTED | N/A | Predict suitable crops |
| `/api/v1/farms/{id}/digital-twin` | GET | PLANNED (Mocked in UI) | Dashboard | Fetch farm state |
| `/api/v1/simulate` | POST | PLANNED (Mocked in UI) | Simulator UI | Run what-if scenario |

---

## 14. FRONTEND INVENTORY

| Component | Path | Status | Connected API |
|-----------|------|--------|---------------|
| **Dashboard** | `frontend/src/App.tsx` | IMPLEMENTED | Mocked |
| **Digital Twin Display** | `frontend/src/App.tsx` | IMPLEMENTED | Mocked (`/digital-twin`) |
| **What-If Simulator** | `frontend/src/App.tsx` | IMPLEMENTED | Mocked (`/simulate`) |

---

## 15. DATABASE

* **Status:** PLANNED — NOT IMPLEMENTED. No ORM, no migrations, no relational schema exists in code. Data resides in pickled model objects and JSON metadata.

---

## 16. REPOSITORY STRUCTURE

```text
kisan-care/
├── digital_twin/      # Documentation for Digital Twin concept
├── docs/              # Research reports, architecture specs, old contracts
├── frontend/          # React/Vite UI application
├── ml/                # ML API (FastAPI) and Crop Recommendation training/prediction code
├── models/            # Serialized model artifacts (.pkl, .json)
└── scripts/           # Data preprocessing and fusion scripts
```

---

## 17. ENVIRONMENT & SETUP

* **ML/Backend:** Python 3.x, `ml/requirements.txt` (FastAPI, uvicorn, pandas, xgboost, scikit-learn). Run via `main.py` or Docker.
* **Frontend:** Node.js, `frontend/package.json` (React, Vite, Tailwind). Run via `npm run dev`.

---

## 18. MODEL TRAINING WORKFLOW

* **Implemented (Crop Rec):** Scripted in `ml/crop_recommendation/train_mvp.py` and `scripts/`.
* Data fused via `scripts/model1b_gis_fusion.py` -> Candidates generated -> XGBoost regressor trained -> Models saved to `models/crop_recommendation`.

---

## 19. VALIDATION & MODEL AUDIT

* **Crop Recommendation:** 
    * `val_top1`: 0.8358
    * `test_top1`: 0.8353
    * Accuracy independently documented in `metadata_mvp_v2.json`.

---

## 20. LOCKED DECISIONS

1. **Digital Twin Core:** KisanCare is a connected Farm Decision Intelligence system centered on a Digital Twin.
2. **Dynamic Crop List:** The 20/22 fixed crop constraint is removed. Supported crops are entirely data-driven based on categorical levels in the training data.
3. **Regression vs Classification:** We are using an Area-Frequency based XGBoost regression model (scoring candidate crops) rather than a direct multi-class classifier for Model 1.
4. **LLM Orchestration:** Specialized ML models generate predictions; AI Copilot will explain them (not replace them).

---

## 21. SUPERSEDED DECISIONS

1. **Fixed 22-Crop Kaggle Approach:** The initial plan to use the `djdhairya/Crop-Recommendation` Random Forest model on 2,200 Kaggle samples has been explicitly abandoned in favor of the district/season APY dataset model.
2. **Original ML Contract:** `docs/ml-contract.md` specifies inputs like `soil_type` and `weather` for Crop Rec. This is superseded by the actual implementation which takes `district`, `season`, and `water_availability`.

---

## 22. CURRENT TODO

### P0 — Must do
* **Task:** Implement actual Database schema for Digital Twin.
* **Reason:** Without state, the What-If simulation and API integration cannot function.

### P1 — Important
* **Task:** Implement `/api/v1/simulate` backend logic.
* **Reason:** Currently mocked in frontend.
* **Task:** Refactor/update `docs/ml-contract.md` and `docs/architecture.md` to reflect the actual API reality.

### P2 — Nice to have
* **Task:** Centralize the Crop Catalogue.
* **Reason:** Decouple crop metadata from the `preprocessing_mvp_v2.pkl` dictionary.

---

## 23. KNOWN PROBLEMS

* **Documentation Drift:** Existing `docs/ml-contract.md` and `models/crop_recommendation/README.md` describe a different input structure than what `ml/main.py` actually implements.
* **Missing Backend:** Frontend is calling endpoints (`/simulate`, `/digital-twin`) that do not exist in the FastAPI app.

---

## 24. FUTURE EXTENSIBILITY

To add a new crop:
1. Include crop yield/area data in the underlying APY dataset (fusion script).
2. Ensure the crop is recognized in categorical mappings (`cat_levels`).
3. Re-run `train_mvp.py` to produce a new `.pkl`.
4. Update `CropDecisionEngine` in `predict.py` if the new crop has specific season/water constraints.

---

## 25. DEMO-CRITICAL FEATURES

1. **Farm Digital Twin (P0 - Needs Backend DB)**
2. **Crop Recommendation (Done)**
3. **What-If Simulation (P0 - Needs Backend logic)**
4. Yield/Risk/Economics (Currently mocked in frontend, need basic logic or models)

---
*Document automatically generated by Antigravity AI based on codebase reality.*


## Model 1 — Phase 1 Decision

* **Selected Primary Repo:** `Sheshank2609/crop-recommendation-system` (Because it incorporates realistic historical regional frequency/yield data, avoiding the pure synthetic trap of the Kaggle dataset).
* **Secondary Repo:** `anant13sharma` (Rejected due to severe data leakage and synthetic generation of 69K rows).
* **Backup Repo:** `KRUTHIKTR` (Canonical Kaggle dataset, kept only as a structural baseline).
* **Dataset Findings:** The 69K dataset is a synthetically exploded version of the 2.2K dataset. The 2.2K dataset is perfectly balanced and likely synthetic/interpolated. The regional dataset (1,603 rows) is highly imbalanced real data.
* **Known Risks:** 99% accuracy claims are a mirage caused by synthetic data. Lack of real-world soil/climate field datasets.
* **Decisions:** 
  * REJECT Anant 69K dataset.
  * MODIFY Kruthik 2.2K dataset (use only for structural testing).
  * MODIFY Sheshank Regional scoring (pivot it from a statistical formula into a true ML feature/regressor).
* **Next Phase:** Phase 2 will focus on acquiring real APY (Agricultural Production Yield) data and fusing it with district/season features to train a robust regressor, discarding the synthetic classifiers.
