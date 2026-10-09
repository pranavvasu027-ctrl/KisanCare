# VIDEO SUBMISSION DEMO RUNBOOK
## Phase 1: Verify Working ML Model Integration

This runbook outlines how to reliably demonstrate the **actual**, verified ML models currently running in the KisanCare backend, using true API endpoints and artifacts. Fake data and mock overrides have been completely bypassed to show real system performance.

---

### 1. Environment & Setup

**Required Working Directory:**
`C:\Users\prana\OneDrive\Desktop\Projects\KISANcare\kisan-care`

**Python Environment:**
The active virtual environment (`venv`) must be used, as it contains critical dependencies like `fastapi`, `supabase`, and `xgboost`.
Activate it before starting the backend:
```powershell
.\venv\Scripts\Activate.ps1
```

**Database & Auth Requirements:**
The backend relies on Supabase for the Orchestrator. Ensure your `.env` file contains valid credentials:
```env
SUPABASE_URL=<your-supabase-url>
SUPABASE_ANON_KEY=<your-anon-key>
```
*Note: To run the full Orchestrator endpoint (`/orchestrate`), a valid JWT Bearer token from a logged-in Supabase user is required.*

**Backend Startup Command:**
```powershell
uvicorn ml.main:app --reload --host 0.0.0.0 --port 8000
```
*(Note: We use `ml.main:app` as it is the official orchestration API containing the integrated Decision Engine and Supabase authentication, overriding older prototypes).*

---

### 2. Verified Capabilities Status

Out of the 9 planned capabilities, the following is the **actual, verified status** of the ML models on the server:

| Capability | Status | Artifact Exists | Endpoint Verified |
| :--- | :--- | :--- | :--- |
| **1. Crop Recommendation** | ✅ **Working** | Yes (`crop_recommendation_mvp_v2.pkl`) | `POST /api/v1/crop-recommendation` |
| **2. Cost & Profit** | ✅ **Working** | Yes (`cost_model.joblib`) | Via `/orchestrate` |
| 3. Yield Prediction | ❌ Unavailable | No | - |
| 4. Disease/Pest Risk | ❌ Unavailable | No | - |
| 5. Irrigation Prediction | ❌ Unavailable | No | - |
| 6. Farm Risk | ❌ Unavailable | No | - |
| 7. Market Price | ❌ Unavailable | No | - |
| 8. Post-Harvest Loss | ❌ Unavailable | No | - |
| 9. NPK Prediction | ❌ Unavailable | No | - |

*(Any models marked unavailable are correctly reported as such by the Orchestrator, rather than returning fake successful predictions).*

---

### 3. API Demo Scripts

#### A. Crop Recommendation (Independent Endpoint)
This endpoint does not require Supabase authentication, making it the easiest to demonstrate live.

**Command:**
```powershell
curl -X POST "http://localhost:8000/api/v1/crop-recommendation" `
     -H "Content-Type: application/json" `
     -d '{"district": "PUNE", "season": "Rabi", "water_availability": "Medium", "top_k": 3}'
```

**Actual Response Structure (Verified Live):**
```json
{
  "model_version": "crop-recommendation-mvp-v2",
  "district": "PUNE",
  "season": "Rabi",
  "water_availability": "Medium",
  "status": "SUCCESS",
  "recommendations": [
    {
      "crop": "Sorghum",
      "predicted_area_frequency": 0.6106,
      "rank": 1
    },
    {
      "crop": "Wheat",
      "predicted_area_frequency": 0.1851,
      "rank": 2
    },
    {
      "crop": "Tomato",
      "predicted_area_frequency": 0.1586,
      "rank": 3
    }
  ],
  "filtered_candidates": [
    {
      "crop": "Grapes",
      "model_score": 0.126,
      "eligible": false,
      "filter_reason": "Grapes is constrained to ['Whole Year']"
    }
  ],
  "data_source": "APY_2005_2015",
  "score_interpretation": "Predicted historical area-allocation suitability score",
  "latency_ms": 18.7
}
```
*(Notice how the Decision Engine natively filters out Grapes because it violates the "Rabi" season rule, proving the logic works dynamically).*

#### B. The Orchestrator (Integrated Pipeline)
This endpoint proves that the backend can take a digital twin context and route it to multiple models at once. 

**Command:**
```powershell
curl -X POST "http://localhost:8000/api/v1/farms/FARM123/fields/FIELD1/seasons/SEASON1/orchestrate" `
     -H "Content-Type: application/json" `
     -H "Authorization: Bearer <YOUR_SUPABASE_JWT_TOKEN>" `
     -d '{"models": ["crop_recommendation", "cost_prediction"]}'
```

**Expected Behavior:**
If no valid token is provided, the API safely refuses the connection with `401 Not authenticated`. 
When a valid token is provided, the Orchestrator fetches the Farm state from Supabase, passes the parameters to both `PredictionPipeline` and `predict_cost`, and returns a unified JSON output containing both predictions while ignoring unavailable models.

---

### 4. Recommended Sequence for Recording the Demo

1. **Start the server:** Open a terminal, activate `venv`, and run `uvicorn ml.main:app --reload`. Show the terminal output highlighting that `Model 1 Pipeline initialized successfully`.
2. **Show the independent intelligence:** Open Postman (or terminal) and send a request to `/api/v1/crop-recommendation`. Change the `district` to `NASHIK` and show how the top crop changes (e.g., Wheat moves to Rank 1).
3. **Show the Orchestrator Security:** Send a request to `/orchestrate` without a token to prove the API is fully secured behind Supabase RLS policies (it will return `401`).
4. **Show the Flutter App:** Open the Android Emulator and open the KisanCare app to prove the UI foundation is built and structurally ready to consume these real APIs.
