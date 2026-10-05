# Phase 2 — Prototype Dataset Cleaning & Preparation

## 1. Source Dataset
* **Original Rows:** 4000
* **Clean Rows:** 4000

## 2. Yield Recalculation (Phase C Fix)
Exactly 0 rows had `Yield × Area != Production` due to previous median-imputation. These were mathematically corrected by recalculating `Yield = Production / Area`.
* **Rows Corrected:** 0
* **Rows Unresolved:** 0
* **Maximum Absolute Difference Post-Fix:** 0.0050 (Floating point precision)

## 3. Geographic Limitations
Due to previous audits flagging ~3,485 District mappings as hallucinated/suspicious, `District` has been explicitly **EXCLUDED** from the final predictive features. `State` remains a trusted macroscopic feature.

## 4. Target & Leakage Policy
**Target:** `Total_Cost_INR`
To prevent the model from cheating, all post-harvest metrics (`Profit_INR`, `Revenue_INR`, `Production_Tonnes`, `Yield_Tonnes_Ha`) and post-harvest market indicators (`Market_Price_INR_Tonne`) have been strictly excluded from the Cost Model inputs. See `model6_prototype_feature_policy.csv` for the full breakdown.

## 5. Coverage
* **Maharashtra Rows:** 512
* **KISANcare V1 Crops Supported:** 6 / 20

## 6. Recommended Validation Strategy
Because the data has a hierarchical structure, a **GroupKFold (grouped by State or Crop)** is recommended to test if the model learns generalizable economic rules rather than memorizing specific state-crop combinations.

## 7. Final Status
**CLEAN_DATA_READY**
