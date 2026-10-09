# Phase 6: Decision Engine Integration Report

## 1. Scope & Implementation
I have successfully implemented the KisanCare Decision Engine in `ml/decision_engine.py` and exposed it via a new authenticated endpoint `POST /api/v1/farms/{farm_id}/fields/{field_id}/seasons/{season_id}/decide` in `ml/routers/farms.py`. It converts native Model Orchestrator outputs into actionable insights.

## 2. Endpoint Contract
**Endpoint:** `POST /api/v1/farms/{farm_id}/fields/{field_id}/seasons/{season_id}/decide`
**Authentication:** Supabase JWT Bearer Token

**Example Request Payload (`DecisionRequest`):**
```json
{
  "decision_type": "crop_selection",
  "preferences": {
    "water_conservation_priority": true,
    "preferred_crops": ["Wheat", "Maize"]
  },
  "cost_prediction_inputs": {
    "sunlight_hours_day": 8.0,
    "fertilizer_kg_ha": 50.0,
    "pesticide_litre_ha": 2.0,
    "seed_quality_score": 5.0,
    "water_efficiency_t_per_1000m3": 1.5,
    "disease_pest_risk_pct": 10.0
  }
}
```

**Example Response Payload (`DecisionResponse`):**
```json
{
  "decision_id": "ab12-34cd",
  "decision_type": "crop_selection",
  "status": "ready",
  "primary_recommendation": {
    "identifier": "REC-1",
    "recommended_action": "Cultivate Wheat",
    "explanation": "Agronomically suitable for your district and season based on historical patterns.",
    "supporting_evidence": { "crop_probability": 0.8, "rank": 2 },
    "trade_offs": [],
    "warnings": []
  },
  "alternatives": [
    {
      "identifier": "REC-0",
      "recommended_action": "Cultivate Rice",
      "explanation": "Agronomically suitable...",
      "supporting_evidence": { "crop_probability": 0.9, "rank": 1 },
      "trade_offs": ["Rice is highly suitable agronomically, but is not in your preferred crops list."],
      "warnings": ["Hard Constraint Conflict: Rice is highly water-intensive, but you prioritized water conservation."]
    }
  ],
  "missing_information": [],
  "model_versions": {
    "crop_recommendation": "1.0",
    "cost_prediction": "HistGradientBoosting_Prototype"
  },
  "timestamp": "2026-10-09T09:30:00Z"
}
```

## 3. Mocked vs Live Verification
- **Testing Script:** `ml/tests/test_decision_engine_api.py`
- **Database:** `MagicMock` was used to simulate the Supabase API to guarantee secure CI/CD testing without real credentials.
- **Model Execution:** `patch()` was used to simulate orchestrated `ModelResult` outputs, isolating the decision engine's rule-processing capabilities.
- **Results:** 5 / 5 tests passed securely. Regression tests for Crop Recommendation (8/8) and Model Orchestrator (5/5) also ran successfully.

## 4. Known Limitations
- The engine currently focuses strictly on `crop_selection`. 
- Due to the absence of the Yield Prediction model, the Decision Engine cannot fully rank alternatives based on Net Profit. Alternative rankings are currently based purely on the agronomic probability output of the Crop Recommendation model.

## 5. Next Recommended Phase
- **Phase 7: What-If Simulator.** The What-If Simulator is perfectly positioned to leverage the exact architecture we've just built. It can execute parallel orchestrated decision requests by artificially modifying context variables (e.g., changing weather inputs or soil metrics) to give farmers foresight into how climate or investment changes might alter their agronomic outcomes.
