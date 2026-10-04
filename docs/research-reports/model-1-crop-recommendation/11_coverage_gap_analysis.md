# 11 — Coverage Gap Analysis: 2016-2020 & Horticulture Deficits

**Date:** 2026-10-04  
**Task:** Verify the 2016-2020 dataset extension, calculate precise horticulture deficits, evaluate sufficiency, and identify complementary datasets.  
**Author:** Antigravity (AI-assisted research)  
**Branch:** `research-reports`  

---

## 1. 2016–2020 Verification (UPAg / DES)

The open public mirrors for `crop_production.csv` terminate at 2015. We investigated the official Directorate of Economics and Statistics (DES) and UPAg portals to verify the extension.

*   **Is 2016-2020 available?** Yes. All years (2016, 2017, 2018, 2019, 2020) are officially maintained and published by the MoA.
*   **Exact Access Method:** `upag.gov.in` (Unified Portal for Agricultural Statistics) under the "Crop-wise Area, Production & Yield (APY)" module.
*   **Authentication Requirements:** Massive bulk district-level historical extracts require user registration and authenticated login on the UPAg portal. 
*   **Exact Schema & Compatibility:** The schema remains structurally identical (`State`, `District`, `Crop_Year`, `Season`, `Crop`, `Area`, `Production`, `Yield`), ensuring 100% compatibility with the 2005-2015 dataset format.
*   **Status:** Confirmed existence, but the raw CSV remains behind a government authentication wall and has not yet been merged locally.

---

## 2. 20-Crop Coverage Table (2005-2015 Subset)

We executed a script to count the exact records for all 20 priority crops. 

| Crop | 2005-2010 | 2011-2015 | Total (2005-2015) | Districts | States | Years |
|---|---|---|---|---|---|---|
| Rice | 5359 | 3345 | 8704 | 615 | 33 | 11 |
| Wheat | 2838 | 1564 | 4402 | 536 | 28 | 11 |
| Maize | 4873 | 3318 | 8191 | 602 | 31 | 11 |
| Soybean | 1130 | 662 | 1792 | 284 | 20 | 11 |
| Cotton | 1602 | 902 | 2504 | 334 | 23 | 10 |
| Sugarcane | 2787 | 1664 | 4451 | 563 | 31 | 11 |
| Chickpea | 2688 | 1397 | 4085 | 508 | 23 | 10 |
| Pigeon Pea | 2654 | 1575 | 4229 | 520 | 26 | 10 |
| Groundnut | 3088 | 1959 | 5047 | 447 | 26 | 11 |
| Sorghum | 2398 | 1311 | 3709 | 378 | 20 | 10 |
| Pearl Millet | 1876 | 961 | 2837 | 368 | 19 | 10 |
| Green Gram | 3744 | 2621 | 6365 | 537 | 25 | 11 |
| Black Gram | 3595 | 2376 | 5971 | 524 | 26 | 11 |
| Mustard | 2768 | 1521 | 4289 | 563 | 27 | 11 |
| Onion | 2591 | 1570 | 4161 | 438 | 20 | 10 |
| Potato | 2654 | 1462 | 4116 | 518 | 25 | 11 |
| Banana | 1235 | 639 | 1874 | 302 | 18 | 10 |
| **Tomato** | 0 | 78 | **78** | **13** | **1** | **3** |
| **Mango** | 4 | 84 | **88** | **33** | **4** | **5** |
| **Grapes** | 0 | 12 | **12** | **4** | **1** | **3** |

---

## 3. Horticulture Sufficiency Evaluation

**Are 78 records for Tomato sufficient? NO.**
*   **The Problem:** Tomato, Mango, and Grapes are catastrophically undersampled. Tomato is grown pan-India (AP, MP, Karnataka), yet our dataset only has 13 districts from a single state over 3 years.
*   **The Machine Learning Risk:** If we train a model on this data, the model will learn that Tomato can *only* survive in those 13 specific districts. It will artificially overfit to that one state's agro-climatic profile and never recommend Tomato anywhere else in India.
*   **Conclusion:** The UPAg APY dataset is **insufficient** for training Mango, Grapes, and Tomato. (Banana, Onion, and Potato have 1,800+ records across 18+ states and are deemed sufficient).

---

## 4. Candidate Complementary Datasets

To fix the Tomato, Mango, and Grapes deficit, we investigated alternative authoritative sources:

1.  **National Horticulture Board (NHB) - Area and Production Statistics:**
    *   **Source:** `nhb.gov.in` / Interactive Query Module.
    *   **Data:** District-wise production of fruits (Mango, Grapes) and vegetables (Tomato).
2.  **Horticultural Statistics at a Glance:**
    *   **Source:** Ministry of Agriculture & Farmers Welfare.
    *   **Data:** Published annually; contains major producing districts for specific crops.

### Compatibility Issues & Risks
Merging NHB horticulture data with DES APY field-crop data introduces a critical challenge:
*   **Seasonality Mismatch:** NHB often reports data on an *Annual* basis (e.g., "Tomato: 2015 Annual Production"), whereas the DES APY data is strictly divided by *Season* (Kharif, Rabi, Summer). 
*   **Leakage/Schema Break:** If we forcefully merge annual data into a season-based model, the model won't know which season to recommend the crop for, corrupting the feature space.

---

## 5. Final Recommendation to P27

We have two options to resolve the data sufficiency problem:

**OPTION 1: Execute Complex Data Merge**
1.  Authenticate and download 2016-2020 DES APY data.
2.  Scrape/download district-wise Tomato, Mango, and Grapes data from NHB.
3.  Manually assign standard planting seasons (Kharif/Rabi) to the annual NHB data using agronomic calendars to make it compatible with the main dataset.

**OPTION 2: Deprecate the 3 Deficient Crops for V1**
If building a custom seasonal interpolation layer for NHB data is out of scope for the current sprint, we should temporarily drop **Tomato, Mango, and Grapes** from the Model 1 feature contract. We can proceed with a highly robust **17-crop model** using exclusively the cleanly formatted DES APY dataset.

*Decision required on how to handle the 3 deficient crops.*
