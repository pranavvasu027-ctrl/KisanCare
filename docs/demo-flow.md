# Demo Flow

The initial vertical slice of KisanCare follows this flow:

1. **Onboarding:** User arrives at the KisanCare Dashboard.
2. **Digital Twin View:** The dashboard fetches the current state of Farm F001 via `/api/v1/farms/F001/digital-twin`.
3. **What-If Simulation:** The user wants to see the impact of a 20% reduction in rainfall.
4. **Action:** User clicks "Run Simulation".
5. **Backend Processing:**
   - Frontend calls `POST /api/v1/simulate` with `{"rainfall_change_percent": -20}`.
   - Backend Simulation Engine fetches the baseline economics.
   - Backend calculates the new expected yield based on reduced rainfall (mock sensitivity).
   - Backend calculates the new economics.
6. **Comparison:** The UI displays Baseline vs Scenario side-by-side (Yield, Profit, Risk).
