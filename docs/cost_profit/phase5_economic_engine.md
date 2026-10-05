# Phase 5 — Economic Calculation Engine

## 1. Engine Design
The deterministic calculation layer has been built without fabricating Yield or Market Price. It purely acts as the final equation engine that combines outputs from the disparate models.

## 2. Core Formulas Implemented
* `Production (t) = Yield (t/ha) × Farm Area (ha)`
* `Revenue (₹) = Production (t) × Market Price (₹/t)`
* `Profit (₹) = Revenue (₹) - Predicted Total Cost (₹)`
* `ROI (%) = (Profit / Predicted Total Cost) × 100`
* `Profit Margin (%) = (Profit / Revenue) × 100`
* `Break-Even Price (₹/t) = Predicted Total Cost / Production`
* `Break-Even Yield (t/ha) = Predicted Total Cost / (Area × Price)`

## 3. Unit Validation & Conversions
The engine actively monitors the provided unit arguments. 
* If `quintals/hectare` is passed instead of `tonnes/hectare`, the engine dynamically divides by 10.
* If `INR/quintal` is passed instead of `INR/tonne`, the engine dynamically multiplies by 10.

## 4. Test Results
* **15 deterministic edge-case tests passed**, covering division-by-zero protection (zero area, zero cost, zero production, zero revenue) and typical Maharashtra profiles.
* **Phase 4 Regression Tests passed**, ensuring the Cost Model inference module was not disrupted.

## 5. What-If Support
Because the engine is entirely deterministic and decoupled from the ML pipeline, a What-If scenario (e.g., Yield +10%) can simply pass `predicted_yield_tonnes_per_hectare * 1.10` directly into `calculate_economics()`.

## 6. Output Schema
The exact schema structure specified in the requirements is exported, gracefully allowing `null` values for economic fields if the Yield or Market models return `NOT_CONNECTED`.

## 7. Limitations
This engine assumes static snapshot pricing and does not currently discount for time value of money, loan interest, or dynamic market shifts during the season.

## 8. Final Status
**ECONOMIC_ENGINE_READY**
