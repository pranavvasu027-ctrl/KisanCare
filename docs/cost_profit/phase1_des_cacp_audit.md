# Phase 1 — DES/CACP Final Data Audit

## 1. Executive Summary
An exhaustive search of the KISANcare repository revealed a critical discrepancy: **The assumed ~3,000 row DES/CACP aggregate dataset does not exist in the workspace.** The only actual files found containing DES/CACP equivalent data are a 4-row mock file created previously and the 49-row Kaggle dataset.

**Total Actual Rows Found:** 53
**Observation Level:** State × Crop (Aggregated)

## 2. Source Inventory
1. `des_cost_summary_2019.csv` (4 rows, Mock sample)
2. `datafile.csv` (49 rows, Kaggle subset)

## 3. Observation Level
Verified as exactly **State × Crop** (and sometimes Year). There are 0 Farm × Crop × Year observations.

## 4. Dataset Dimensions
* Rows: 53
* Columns: 15
* Unique Crops: 14
* Unique States: 13

## 5. Column/Data-Type Audit
`State` (Object), `Crop` (Object), `Year` (Object), `C2` (Float/Int), `A2+FL` (Float/Int).

## 6. Cost Variable Audit
* **C2:** Available. Unit: ₹/Hectare. Derived aggregate.
* **A2+FL:** Available. Unit: ₹/Hectare. Derived aggregate.

## 7. Year Coverage
* 2019: 4 rows
* Unknown: 49 rows

## 8. Crop Coverage
See `phase1_crop_coverage.csv`. Major crops (Cotton, Sugarcane) are present, but severely limited by the 53-row total.

## 9. State Coverage
See `phase1_state_coverage.csv`. 

## 10. Maharashtra Coverage
* Maharashtra row count: 9
* Crops: Cotton, Soybean, Sugarcane, Jowar, Bajra, Arhar, Moong, Urad, Groundnut.

## 11. Missing Values
None detected in the critical cost columns. The Kaggle dataset is completely missing `Year`.

## 12. Duplicate Analysis
0 exact duplicates.

## 13. Data Quality Flags
The primary quality flag is the **absence of data**. The 3,000-row benchmark dataset is missing from the local filesystem.

## 14. Unit/Definition Verification
* **C2**: Comprehensive cost including imputed rent and interest. (₹/Hectare)
* **A2+FL**: Actual paid out cost plus imputed family labour. (₹/Hectare)

## 15. Data Lineage
The 49-row file is derived from Kaggle (`srinivas1`). The 4-row file is a mock baseline. Neither is a direct download from the DES portal.

## 16. Leakage Risk Audit
`Seed_Cost`, `Fertilizer_Cost`, `Labour_Cost` (present in the mock file) perfectly sum to `A2` and cannot be used as predictive inputs.

## 17. KisanCare V1 Coverage
Only 9 out of 20 V1 crops are supported by this tiny 53-row dataset. 

## 18. Limitations
**FATAL LIMITATION:** The 3,000-row benchmark dataset does not exist locally. We cannot build a national base-rate engine using only 53 rows with unknown years.

## 19. Final Recommendation
**HALT.** The assumption that we possess a 3,000-row official DES/CACP aggregate dataset is false. We only have 53 disjointed rows. To proceed with the Econometric Base-Rate Engine, we MUST physically acquire the full DES/CACP historical dataset, as it is not currently in the repository.
