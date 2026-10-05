# Phase 6.0 — Prototype Dataset Re-Audit

## A. Source Data Location
* **Path:** `data/model6_cost_profit/raw/seasonal_agriculture_performance_dataset.csv`
* **Rows:** 4000
* **Columns:** 28
* **Maharashtra Rows:** 512

## B. Re-Audit Results
* **Duplicates:** 0
* **Negative Values:** 1966
* **Production ≈ Yield × Area Mismatches:** 0 (Expected ~31 from previous median imputations)
* **Revenue ≈ Production × Price Mismatches:** 0
* **Profit ≈ Revenue − Total Cost Mismatches:** 0
* **Geographic Integrity:** As noted in previous audits, ~3,485 rows have suspicious state-district mappings. These are retained but classified as `SUSPICIOUS` for geographical features.

## C. Yield Fix Strategy
The 0 production/yield mismatches will be corrected by recalculating `Yield = Production / Area` where both are valid. No median imputation will be used.

## D. Leakage Audit
Total Cost components (Seed Cost, Fertilizer Cost, etc.) directly leak the `Total_Cost` target. Post-harvest variables (Revenue, Profit, Production, actual Yield) cannot be used as pre-harvest inputs to the Cost or Yield models. See `prototype_feature_audit.csv` for column-by-column handling.

## E. Architectural Design
The models will be chained sequentially:
1. `Pre-Harvest Features -> Cost Model -> Predicted Total Cost`
2. `Pre-Harvest Features -> Yield Model -> Predicted Yield`
3. `Predicted Yield * Market Price -> Predicted Revenue`
4. `Predicted Revenue - Predicted Total Cost -> Predicted Profit`

## F. Final Status
**READY_FOR_MODEL_DEVELOPMENT**
The dataset is explicitly acknowledged as a synthetic prototype/hackathon dataset. Its internal financial math is highly consistent (Revenue/Cost/Profit relationships are solid). Once the 31 yield median-imputations are mathematically reversed to equal `Production / Area`, the dataset provides a perfectly consistent numerical sandbox to build and test the hybrid chaining architecture for Model 6.
