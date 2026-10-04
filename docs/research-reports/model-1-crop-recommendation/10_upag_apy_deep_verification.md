# 10 — UPAg APY Dataset Deep Verification

**Date:** 2026-10-04  
**Task:** Deep verification of the UPAg APY dataset as the primary candidate for the 2005–2020 modeling window.  
**Author:** Antigravity (AI-assisted research)  
**Branch:** `research-reports`  

---

## 1. Source & Acquisition
*   **Official Source:** Directorate of Economics and Statistics (DES), Ministry of Agriculture via Unified Portal for Agricultural Statistics (UPAg) / `data.gov.in`.
*   **Local File:** `C:/KisanResearch/crop_production.csv`
*   **Acquisition Method:** Downloaded via open GitHub mirror (representing the standard Kaggle/Gov extract). 
*   **Note:** The open public extract available for automated download terminates in 2015. The official 2016-2020 extension requires authenticated portal access. Verification was performed on the available 1997-2015 data to project the structure.

---

## 2. Dataset Description & Time Coverage
*   **Description:** Historical panel data tracking crop cultivation area and total production across Indian districts and seasons.
*   **Total Time Coverage (Local File):** 1997–2015. (Official UPAg covers up to 2020).
*   **Total Rows (1997-2015):** 246,091
*   **Total Columns:** 7

---

## 3. 2005–2020 Subset Analysis (Local 2005-2015 Slice)
We isolated the data from 2005 onwards to match the preferred modern modeling window:
*   **Rows:** 138,050
*   **Years Represented:** 2005 to 2015 (11 years)
*   **States:** 33
*   **Districts:** 644
*   **Crops:** 122 unique crops

---

## 4. 20 Priority Crops Verification

Every priority crop was found in the dataset. However, a major structural limitation was discovered regarding horticultural crops:

| KisanCare Crop | Exact Dataset Name | Years Present | States | Records (2005+) |
|---|---|---|---|---|
| Rice | `rice` | 2005-2015 | 33 | 8,704 |
| Wheat | `wheat` | 2005-2015 | 28 | 4,402 |
| Maize | `maize` | 2005-2015 | 31 | 8,191 |
| Soybean | `soyabean` | 2005-2015 | 20 | 1,792 |
| Cotton | `cotton(lint)` | 2005-2014 | 23 | 2,504 |
| Sugarcane | `sugarcane` | 2005-2015 | 31 | 4,451 |
| Chickpea | `gram` | 2005-2014 | 23 | 4,085 |
| Pigeon Pea | `arhar/tur` | 2005-2014 | 26 | 4,229 |
| Groundnut | `groundnut` | 2005-2015 | 26 | 5,047 |
| Sorghum | `jowar` | 2005-2014 | 20 | 3,709 |
| Pearl Millet | `bajra` | 2005-2014 | 19 | 2,837 |
| Green Gram | `moong(green gram)` | 2005-2015 | 25 | 6,365 |
| Black Gram | `urad` | 2005-2015 | 26 | 5,971 |
| Mustard | `rapeseed &mustard` | 2005-2015 | 27 | 4,289 |
| Onion | `onion` | 2005-2014 | 20 | 4,161 |
| Potato | `potato` | 2005-2015 | 25 | 4,116 |
| Banana | `banana` | 2005-2014 | 18 | 1,874 |
| **Tomato** | `tomato` | 2012-2014 | 1 | **78** ⚠️ |
| **Mango** | `mango` | 2010-2014 | 4 | **88** ⚠️ |
| **Grapes** | `grapes` | 2012-2014 | 1 | **12** ⚠️ |

*⚠️ **CRITICAL FINDING**: Field crops are exhaustively tracked. Horticultural crops (Tomato, Mango, Grapes) are severely underrepresented because they are traditionally tracked by the National Horticulture Board, not the standard DES APY pipeline.*

---

## 5. Geographic & Season Coverage
*   **Geographic:** The dataset covers 644 districts. District naming follows pre-2014 state boundaries (e.g., requires mapping for Telangana). The geography is perfectly compatible with a standard State/District UI dropdown.
*   **Seasons:** `Kharif`, `Rabi`, `Summer`, `Whole Year`, `Winter`, `Autumn`. 
    *   *Note:* The string `Kharif     ` contains trailing whitespaces that require trimming.

---

## 6. Variables & Feature Schema
1.  **State_Name:** String
2.  **District_Name:** String
3.  **Crop_Year:** Integer
4.  **Season:** String (Agro-climatic planting season)
5.  **Crop:** String 
6.  **Area:** Float64 (Unit: Hectares). Defines land dedicated to the crop.
7.  **Production:** Float64 (Unit: Tonnes). Defines total harvest.
8.  **Yield:** *Missing.* Must be derived manually as `Production / Area` (Tonnes/Hectare).

---

## 7. Data Quality (2005-2015 Subset)
*   **Total Rows:** 138,050
*   **Duplicate Rows:** 0
*   **Zero Area:** 0
*   **Zero Production:** 3 rows
*   **Missing Production Values:** 2,670 rows (1.9% of the subset). These usually occur when a crop fails entirely or data wasn't reported.

---

## 8. Recommendation Suitability (The Scientific Distinction)

Can this dataset be used for a Crop Recommendation Model? **Yes, but with strict mathematical caveats.**

*   **Production Data:** Raw production is useless for recommendation (large districts produce more than small districts).
*   **Yield Data:** Yield is NOT crop suitability. Sugarcane yields 70 tonnes/ha; Wheat yields 3 tonnes/ha. If the model maximizes raw yield, it will always recommend Sugarcane.
*   **Historical Crop Choice:** Area allocation tells us what farmers *choose* to grow (driven by market, tradition, and climate).
*   **Suitability/Recommendation:** True suitability must be engineered as a composite target label:
    1.  Normalize the yield of Crop X in District Y against the *National Average Yield of Crop X*.
    2.  Combine this with the frequency of Area allocation.
    3.  This creates a "Relative Suitability Index."

---

## 9. Limitations & Exact Remaining Work

1.  **Horticultural Data Gap:** We must acquire supplementary data from the National Horticulture Board to fix the massive deficit in Tomato, Mango, and Grapes data.
2.  **2016-2020 Gap:** We must execute an authenticated download from UPAg to append the final 5 years of the preferred 2005-2020 window.
3.  **Weather/Soil Fusion:** The dataset still lacks environmental features (Rainfall, Temp, Soil Type), which must be joined in Phase 11.
