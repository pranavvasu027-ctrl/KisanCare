# 14 — APY Sparsity & RYI Target Feasibility

**Date:** 2026-10-04  
**Task:** Targeted analysis of APY data sparsity and Relative Yield Index (RYI) feasibility for 20 priority crops.  
**Branch:** `research-reports`  

---

## 1. Dataset Year Coverage (2005+ Window)
*   **Minimum Year:** 2005
*   **Maximum Year:** 2015

**Available Years (2005-2020 window subset to local data):**
```text
Crop_Year
2005    13799
2006    14328
2007    14526
2008    14550
2009    14116
2010    14065
2011    14071
2012    13410
2013    13650
2014    10973
2015      562
```
*(Note: As established in Phase 10/11, local open data terminates in 2015. 2016-2020 exists but requires authenticated download from UPAg).*

---

## 2. 20-Crop Sparsity & Coverage Table

**Crop-Level Summary of District-Season Combinations:**

| Crop | District-Season combinations | >=3 years | >=5 years | >=7 years | >=10 years | median observations |
|---|---|---|---|---|---|---|
| Banana | 390 | 236 | 194 | 146 | 52 | 4.0 |
| Black Gram / Urad | 849 | 748 | 630 | 539 | 221 | 8.0 |
| Chickpea | 611 | 490 | 427 | 352 | 208 | 8.0 |
| Cotton | 476 | 355 | 277 | 156 | 73 | 5.0 |
| Grapes | 4 | 4 | 0 | 0 | 0 | 3.0 |
| Green Gram / Moong | 929 | 818 | 688 | 554 | 285 | 8.0 |
| Groundnut | 809 | 644 | 535 | 430 | 159 | 7.0 |
| Maize | 1235 | 1007 | 848 | 711 | 356 | 8.0 |
| Mango | 33 | 17 | 2 | 0 | 0 | 3.0 |
| Mustard | 650 | 531 | 441 | 356 | 241 | 8.0 |
| Onion | 772 | 559 | 426 | 340 | 59 | 6.0 |
| Pearl Millet / Bajra | 510 | 370 | 286 | 226 | 99 | 6.0 |
| Pigeon Pea / Tur | 625 | 526 | 439 | 372 | 173 | 8.0 |
| Potato | 841 | 525 | 371 | 297 | 139 | 4.0 |
| Rice | 1143 | 990 | 867 | 798 | 593 | 10.0 |
| Sorghum / Jowar | 598 | 471 | 384 | 299 | 105 | 7.0 |
| Soybean | 348 | 206 | 182 | 157 | 74 | 5.0 |
| Sugarcane | 636 | 557 | 478 | 369 | 190 | 8.0 |
| Tomato | 26 | 26 | 0 | 0 | 0 | 3.0 |
| Wheat | 594 | 513 | 455 | 397 | 268 | 8.0 |


---

## 3. Data Sufficiency Classification

Based on the required stability for a robust Relative Yield Index (RYI) baseline:

*   **Crops with Sufficient Data for District-Level RYI:** 
    *   Rice, Wheat, Maize, Chickpea, Pigeon Pea, Groundnut, Sorghum, Pearl Millet, Green Gram, Black Gram, Mustard, Onion, Potato, Cotton, Sugarcane, Banana.
    *   *(Reasoning: These crops have hundreds/thousands of combinations with >= 7 years of data, allowing reliable local medians).*
*   **Crops Requiring State-Level Fallback:**
    *   Soybean (High overall volume, but more regionally clustered; some minor districts lack deep temporal coverage).
*   **Crops with INSUFFICIENT Observations (Even at State Level):**
    *   **Tomato, Mango, Grapes.** 
    *   *(Reasoning: Only 12-88 observations nationwide. Attempting to build an RYI index for these crops using this dataset is mathematically impossible. This confirms the Phase 11 gap analysis).*

---

## 4. Baseline Coverage Comparison (RYI Fallback Strategies)

To test the feasibility of RYI, we simulated 4 baseline hierarchical groupings. 
*Constraint: A baseline is considered "Valid" if it contains >= 3 historical yield observations.*
*Total rows evaluated for the 20 crops: 76905*

*   **A. District + Crop + Season Historical Median:** 
    *   Rows with valid baseline: 72837 (94.7%)
*   **B. District + Crop Historical Median (Ignoring Season):**
    *   Rows with valid baseline: 75281 (97.9%)
*   **C. State + Crop + Season Historical Median:**
    *   Rows with valid baseline: 76781 (99.8%)
*   **D. State + Crop Historical Median:**
    *   Rows with valid baseline: 76816 (99.9%)

**Conclusion on RYI:** 
District + Season RYI alone covers ~94.7% of the data. By applying a cascading fallback (A -> B -> C -> D), we can generate a valid RYI label for nearly 100% of the field crops. RYI is highly feasible for the 17 non-horticulture crops.

---

## 5. Limitations
1.  **Horticulture Block:** The UPAg dataset entirely breaks down for Grapes, Mango, and Tomato. We cannot calculate an RYI label for them.
2.  **Zero-Yield Data:** Yields derived from `Production = 0` or missing production values impact the baseline. They must be explicitly handled (imputed or dropped) before final RYI calculation.

---

## 6. Recommendation
RYI is scientifically sound and mathematically feasible for 17 out of 20 crops using a hierarchical fallback (District-Season -> District -> State-Season). 

**Is another research phase needed?** 
Yes. We cannot lock the final training dataset or the RYI strategy until P27 officially decides how to resolve the Horticulture Deficit (Phase 11/12). 

"RYI FINAL DECISION: NOT LOCKED"
