# Project Audit Report: KISANcare

## A. Project Overview

* **Application Purpose**: AI-powered Farm Decision Intelligence web application (Digital Twin, Crop Recommendation, Cost/Profit prediction, etc.).
* **Technology Stack**:
  * Frontend: React, TypeScript, Vite, TailwindCSS.
  * Backend: FastAPI (Python). Separated into a general `backend` service and an `ml` service.
  * Database: PostgreSQL via Supabase (also handles Authentication).
* **Frontend Structure**: React application organized into screens (`src/screens`) and components. Uses a mocked authentication flow and a `DEMO_MODE` for API calls.
* **Backend Structure**:
  * `backend/`: A FastAPI app intended for general endpoints. Currently broken due to a missing `market_price` module.
  * `ml/`: A FastAPI app for ML inferences (`crop_recommendation`, `cost_profit`, etc.) and model orchestration. Integrates directly with Supabase.
* **Database Technology and Schema**: Supabase PostgreSQL. Tables include `profiles`, `farms`, `fields`, `seasons`, `crop_records`, `model_predictions`, etc.
* **Authentication Mechanism**: Supabase Auth intended. Currently, the frontend bypasses it entirely.
* **External Services and Integrations**: Supabase.
* **ML Models**:
  * Crop Recommendation (`crop_recommendation_model.pkl`)
  * Cost/Profit Prediction (`cost_model.joblib`)
  * (Several other prototype models in `models/`)

## B. Feature Status Table

| Feature | Frontend Status | Backend Status | Database Status | Integration Status | Overall Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Authentication** | Missing (Bypassed) | Working (in `ml/`) | Working | Missing | Broken |
| **Digital Twin** | Partial (UI exists) | Partial (Mocked) | Working | Missing | Partial |
| **Crop Recommendation** | Partial (UI exists) | Working (in `ml/`) | N/A | Missing (DEMO_MODE) | Partial |
| **Market Intelligence** | Partial (UI exists) | Missing | N/A | Missing | Broken |
| **Farm Setup** | Partial (UI exists) | Partial | Working | Missing | Partial |
| **Cost/Profit Modeling** | Partial (UI exists) | Working (in `ml/`) | Working | Missing | Partial |

## C. Working Features

* Database schema is defined and structured correctly.
* ML service API (`ml/`) has endpoints for crop recommendation and cost prediction that appear to be properly structured.

## D. Partially Working Features

* **Frontend UI**: Extensive frontend screens are built (Dashboard, Crop Rec, etc.), but they rely on `DEMO_MODE` hardcoded data instead of live backend endpoints.
* **Backend ML Endpoints**: The ML service handles inference and interacts with Supabase, but it is not connected to the frontend.

## E. Broken Features

* **Backend Service**: `backend/app/main.py` fails to start because it imports a non-existent `market_price` router.
* **Authentication Flow**: `Login.tsx` just calls `navigate('/')` without any actual authentication.
* **Frontend-Backend Integration**: The frontend is running in `DEMO_MODE = true` and bypassing the real API.

## F. Missing Features

* Role-based access control (RBAC) in the frontend.
* Full integration of frontend screens with the ML backend.
* Missing `market_price` backend implementation.

## G. Authentication and Security Audit

* **Login/Logout**: Frontend just mocks the login action. No real token management.
* **Session Management**: Missing in frontend.
* **Backend Authorization**: `ml/` service seems to check `get_current_user_client` but frontend does not pass any tokens.
* **Data Leakage**: Since there's no auth in the frontend, data isolation is entirely broken on the client side.

## H. Model Integration Audit

* **Crop Recommendation**: Model exists in `models/crop_recommendation`. The `ml/` service initializes it via `PredictionPipeline`. The frontend mocks the output.
* **Cost/Profit**: Model exists in `models/model6_cost_profit`. The `ml/` service has endpoints for it. Frontend uses mock data.

## I. Prioritized Issue List

* **P0: Fix Backend Startup**: Remove or fix the missing `market_price` router in `backend/app/main.py`.
* **P0: Implement Real Authentication**: Connect frontend to Supabase Auth.
* **P1: Disable DEMO_MODE**: Connect frontend `api.ts` to the actual `ml/` and `backend/` endpoints.
* **P1: Fix Market Price API**: Implement the missing `market_price` endpoint.
* **P2: Database Seeding**: Need to create test users and farms in Supabase.

## J. Development Readiness

* **Verified Working**: 10% (Database schema, basic ML pipeline structures).
* **Partially Working**: 40% (Frontend UI, ML Endpoints).
* **Broken**: 30% (Backend startup, Auth, Integration).
* **Not Implemented**: 20% (Market Price, Role-based routing).

**Critical Blockers**: Backend service crashes on start; no real authentication.
**Recommended Order**:
1. Fix `backend/app/main.py` crash.
2. Implement Supabase Auth (Mock Users + Frontend Login).
3. Connect Frontend API (`api.ts`) to Backend services (disable `DEMO_MODE`).
4. Ensure models run successfully and connect to UI.
