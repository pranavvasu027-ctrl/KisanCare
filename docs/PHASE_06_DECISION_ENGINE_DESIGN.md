# Phase 6: Decision Engine Design

## 1. Architecture Overview
The **KisanCare Decision Engine** acts as the high-level interpretation layer sitting on top of the Model Orchestrator. It translates raw, standardized `ModelResult` structures into farmer-facing, explainable agricultural recommendations.

The architecture ensures that the decision layer **never trusts client-provided predictions**. Instead, the Decision Engine internally invokes the `ModelOrchestrator` directly using the authenticated farm context, guaranteeing untampered provenance.

## 2. Request and Response Contracts
- **Request (`DecisionRequest`):** Defines the `decision_type` (e.g. `crop_selection`), `preferences` (farmer's preferred crops, water conservation toggles), and provides fallback missing inputs if the orchestrated models (like Cost) require them.
- **Response (`DecisionResponse`):** Enforces a transparent structure containing a `status` (ready, blocked, needs_more_data), a single `primary_recommendation`, a list of `alternatives`, and any `missing_information`. Each recommendation (`RecommendationAlternative`) strictly lists warnings, trade-offs, and supporting evidence.

## 3. Rules and Constraints
The engine explicitly separates hard constraints from soft preferences.
- **Hard Constraints:** Agronomic incompatibilities. For instance, if the farmer toggles `water_conservation_priority: true`, water-intensive crops (like Rice and Sugarcane) are flagged with a "Hard Constraint Conflict". Any option carrying a hard constraint warning is immediately stripped from contention for the `primary_recommendation` (though retained in `alternatives` with the explanation so the farmer isn't left guessing).
- **Preferences:** E.g., `preferred_crops`. If a highly probable crop is not in the preferred list, it triggers a "trade-off" warning rather than a block.

## 4. Recommendation Logic & Alternatives
- **Evidence:** Derives entirely from the `crop_recommendation` model probabilities. It avoids inventing arbitrary confidence scores, relying solely on historical probability and ranking.
- **Missing Data:** Cost Prediction is parsed, and if available, the engine notes it. If the Cost model is unavailable or lacks inputs, the engine gracefully continues the decision process, explicitly stating in `missing_information` that recommendations are purely agronomic without financial context. It specifically avoids synthesizing profit without a valid Yield and Price model.
