# Phase 5: Model Orchestrator Design

## 1. Architecture Overview
The **KisanCare Model Orchestrator** is a centralized execution engine responsible for routing context-aware prediction requests to the correct inference models. It sits behind the authenticated Farm API and ensures that:
- Input data is securely fetched exactly once (single PostgREST join).
- Eligible models run independently (failures in one model do not block others).
- Outputs are standardized to the unified `ModelResult` schema.
- Successful predictions are persisted centrally.

## 2. Central Model Registry
The registry defines the execution contract, status, and dependency graph for all 9 planned models.

| Identifier | Display Name | Status | Dependencies |
| :--- | :--- | :--- | :--- |
| `crop_recommendation` | Crop Recommendation | **Available** | None |
| `cost_prediction` | Cost & Profit Prediction | **Available** | None (Requires API payload) |
| `yield_prediction` | Yield Prediction | Unavailable | None |
| `disease_pest_risk` | Disease/Pest Risk | Unavailable | None |
| `irrigation_prediction`| Irrigation Prediction | Unavailable | None |
| `farm_risk` | Farm Risk | Unavailable | None |
| `market_price` | Market Price Forecasting | Unavailable | None |
| `post_harvest_loss` | Post-Harvest Loss | Unavailable | None |
| `npk_prediction` | NPK Prediction | Unavailable | None |

## 3. Dependency Rules
Currently, `crop_recommendation` and `cost_prediction` operate independently because they draw completely different required feature sets directly from the Farm Context. In the future, if a farmer has an "Unknown" crop, `cost_prediction` could be explicitly orchestrated to wait for `crop_recommendation` to yield a top suggestion before proceeding. For now, they execute in parallel.

## 4. Execution & Persistence
- The orchestrator validates the requested `models` list against the Registry. Unknown or unavailable models immediately return a standardized error/unavailable result without halting execution.
- It sequentially calls isolated execution functions (e.g. `_execute_cost_prediction`) catching all exceptions to prevent cascading failures.
- Only models resulting in `status="success"` are actively written to the Supabase `model_predictions` table. Models throwing `insufficient_data` or `error` bypass persistence but inform the client via response warnings.
