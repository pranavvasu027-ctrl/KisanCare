# 07 — Dataset Verification: Real Agricultural Data Analysis

**Date:** 2026-10-04  
**Task:** Download, inspect, and verify candidate real agricultural datasets to replace the flawed Kaggle NPK baseline.  
**Author:** Antigravity (AI-assisted research)  
**Branch:** `research-reports`  

---

## 1. Primary Dataset: Government Crop Production Statistics

*   **Dataset Source:** `data.gov.in` ("District-wise, Season-wise Crop Production Statistics")
*   **Access Method:** Downloaded locally via a reliable GitHub mirror representing the standard Kaggle/Gov extract.
*   **Dataset Size:** 246,091 rows
*   **Data Quality Findings:**
    *   Missing Values: 3,730 in `Production`
    *   Duplicates: 0 exact duplicate rows
    *   Inconsistent Strings: The `Season` column contains trailing whitespaces (e.g., `'Kharif     '`).

### Schema & Data Types
1. `State_Name` (string)
2. `District_Name` (string)
3. `Crop_Year` (int64)
4. `Season` (string)
5. `Crop` (string)
6. `Area` (float64) - Hectares
7. `Production` (float64) - Tonnes

### Coverage Statistics
*   **Geographic Coverage:** Pan-India (33 States/UTs, 646 Districts)
*   **Time Coverage:** 19 Years (1997 - 2015)
*   **Season Coverage:** 6 Seasons (Kharif, Rabi, Summer, Whole Year, Autumn, Winter)
*   **Total Crop Classes:** 124

---

## 2. KisanCare 20-Crop Coverage Table

The Government dataset natively covers **100% of our V1 Priority Crops**:

| Crop | Found? | Exact Dataset Name | States/Districts | Years |
|---|---|---|---|---|
| Rice | ✅ | `rice` | Pan-India | 1997-2015 |
| Wheat | ✅ | `wheat` | Pan-India | 1997-2015 |
| Maize | ✅ | `maize` | Pan-India | 1997-2015 |
| Soybean | ✅ | `soyabean` | Pan-India | 1997-2015 |
| Cotton | ✅ | `cotton(lint)` | Pan-India | 1997-2015 |
| Sugarcane | ✅ | `sugarcane` | Pan-India | 1997-2015 |
| Chickpea | ✅ | `gram` | Pan-India | 1997-2015 |
| Pigeon Pea (Tur) | ✅ | `arhar/tur` | Pan-India | 1997-2015 |
| Groundnut | ✅ | `groundnut` | Pan-India | 1997-2015 |
| Sorghum (Jowar) | ✅ | `jowar` | Pan-India | 1997-2015 |
| Pearl Millet (Bajra)| ✅ | `bajra` | Pan-India | 1997-2015 |
| Green Gram (Moong)| ✅ | `moong(green gram)` | Pan-India | 1997-2015 |
| Black Gram (Urad)| ✅ | `urad` | Pan-India | 1997-2015 |
| Mustard | ✅ | `rapeseed &mustard` | Pan-India | 1997-2015 |
| Onion | ✅ | `onion` | Pan-India | 1997-2015 |
| Potato | ✅ | `potato` | Pan-India | 1997-2015 |
| Tomato | ✅ | `tomato` | Pan-India | 1997-2015 |
| Banana | ✅ | `banana` | Pan-India | 1997-2015 |
| Mango | ✅ | `mango` | Pan-India | 1997-2015 |
| Grapes | ✅ | `grapes` | Pan-India | 1997-2015 |

---

## 3. Feature Availability Assessment

| Feature | Status | Notes |
|---|---|---|
| Location | **PRESENT** | State, District available |
| District | **PRESENT** | |
| State | **PRESENT** | |
| Season | **PRESENT** | |
| Year | **PRESENT** | |
| Soil type | **ABSENT** | Needs external join by District |
| N | **ABSENT** | |
| P | **ABSENT** | |
| K | **ABSENT** | |
| pH | **ABSENT** | |
| Temperature | **ABSENT** | Needs external IMD join by District/Season |
| Humidity | **ABSENT** | Needs external IMD join by District/Season |
| Rainfall | **ABSENT** | Needs external IMD join by District/Season |
| Irrigation | **ABSENT** | |
| Water availability | **ABSENT** | |
| Previous crop | **ABSENT** | |
| Yield | **PRESENT** | Can be derived: `Production / Area` |

---

## 4. Nature of the Dataset & Limitations

**Is this a Crop Recommendation Dataset? NO.**

This is explicitly **historical crop production data**. It tells us *what* was grown and *how much* was produced, but it does not natively tell us the environmental conditions (weather, soil) that led to that production. 

To use this for Crop Recommendation (as defined by `ml-contract.md`), we must undertake a **Data Fusion** process:
1. Calculate `Yield` (Production / Area).
2. Spatially join historical weather data (Temp, Rainfall) for that District/Year/Season.
3. Spatially join static Soil Type data for that District.
4. Filter out low-yielding records, keeping only the high-yielding crops for a given environmental profile to serve as "Recommended" labels.

---

## 5. Auxiliary Dataset Check: CropFusion (`Brijesh2005/CropFusion`)

We successfully cloned and inspected the `CropFusion` repository. 
*   **File:** `datasets/data_season.csv` (224 KB)
*   **Size:** 3,158 rows, 12 columns
*   **Features:** Year, Location, Area, Rainfall, Temperature, Soil type, Irrigation, yields, Humidity, Crops, price, Season.
*   **Geographic Scope:** Severely limited. Covers only 11 southern districts (Mangalore, Kodagu, Kasaragodu, etc.).
*   **Crop Coverage:** Covers only 13 crops (blackgram, paddy, ginger, cotton, cardamum, groundnut, tea, arecanut, coffee, coconut, cocoa, cashew, pepper). 
*   **20-Crop Match:** Fails entirely. Misses 17 of our 20 priority crops.
*   **Conclusion:** Technically accessible, but practically useless for KisanCare due to extremely poor geographic and crop coverage.

---

## 6. Recommendation & Exact Next Step

**Conclusion:** The Government of India `crop_production.csv` dataset solves our 20-crop coverage problem beautifully, but lacks the necessary weather and soil features to fulfill the ML Contract out-of-the-box. 

**Exact Next Step:** 
We must design a **Data Fusion Pipeline** to merge external weather (Rainfall, Temperature) and Soil Type datasets into `crop_production.csv` using `District` and `Season` as joining keys, ultimately generating a true Crop Suitability/Recommendation dataset. 

*No model training was performed. Raw datasets will not be committed to GitHub.*
