# 08 — Data Fusion Research: Weather, Soil, and Suitability

**Date:** 2026-10-04  
**Task:** Design and verify the data-fusion strategy to combine historical crop production with real weather and soil data.  
**Author:** Antigravity (AI-assisted research)  
**Branch:** `research-reports`  

---

## 1. Problem Definition
The baseline `crop_production.csv` dataset contains purely historical production data (Area, Production) across 646 Indian districts from 1997-2015. It lacks the environmental context (weather, soil) that determines *why* a crop was grown. To create a scientific Crop Recommendation model, we must fuse this dataset with external meteorological and edaphic (soil) datasets without introducing temporal data leakage or cross-crop biological fallacies.

---

## 2. Weather Dataset Candidates

### Candidate A: District-wise Rainfall in India (1901-2015)
*   **Source:** `data.gov.in` (Widely mirrored on Kaggle)
*   **Resolution:** District-level (Geographic) / Monthly (Time)
*   **Variables:** Monthly Rainfall (mm)
*   **Coverage:** 1901-2015. Perfectly spans our crop dataset (1997-2015).
*   **Joinability:** Excellent. CSV format with State/District columns.
*   **Limitations:** Lacks Temperature and Humidity.

### Candidate B: IMD High-Resolution Daily Gridded Data (NetCDF)
*   **Source:** Indian Meteorological Department (IMD) / Pune Data Centre
*   **Resolution:** 0.25° x 0.25° grid / Daily
*   **Variables:** Rainfall, Max/Min Temperature, Relative Humidity.
*   **Coverage:** 1951-2023.
*   **Joinability:** Very High Effort. Requires GIS Zonal Statistics to aggregate grid pixels into district shapefiles boundaries.
*   **Limitations:** High computational overhead to process 20 years of daily NetCDF files.

### Candidate C: ICRISAT District Level Database (VDSA)
*   **Source:** ICRISAT (Village Dynamics in South Asia)
*   **Resolution:** District-level / Annual & Seasonal
*   **Variables:** Rainfall, Temperature (Min/Max), and some Soil parameters.
*   **Joinability:** High. Already aggregated to district administrative boundaries.

---

## 3. Soil Dataset Candidates

### Candidate A: Soil Health Card (SHC) Scheme Data
*   **Source:** Ministry of Agriculture & Farmers Welfare (`soilhealth.dac.gov.in`)
*   **Resolution:** Village/Block/District
*   **Variables:** pH, N, P, K (Actual lab tests), OC, EC.
*   **Coverage:** Cycle 1 (2015-17), Cycle 2 (2017-19).
*   **Limitations:** **Severe Temporal Mismatch.** The SHC program started in 2015. Our crop production dataset ends in 2015. While soil type is static, N/P/K are highly dynamic. We cannot use 2018 NPK measurements to explain 1999 crop yields.

### Candidate B: NBSS&LUP Agro-Ecological Regions & Soil Maps
*   **Source:** National Bureau of Soil Survey and Land Use Planning (ICAR)
*   **Resolution:** District-level Polygons
*   **Variables:** Static Soil Type (e.g., Deep Black, Alluvial, Red Loamy), Depth, Texture.
*   **Coverage:** Static (Geological timescales).
*   **Joinability:** Excellent. Static categorical join by District.

### Candidate C: ISRIC SoilGrids 250m
*   **Source:** ISRIC World Soil Information
*   **Resolution:** 250m Raster
*   **Variables:** pH, Texture, Organic Carbon.
*   **Joinability:** Very High Effort (Requires GIS zonal stats processing).

---

## 4. Dataset Comparison & Recommended Sources

*   **Recommended Weather Source:** **Candidate A (District-wise Rainfall CSV)** combined with a lightweight District-level Temperature climatology CSV. This avoids heavy NetCDF processing while fulfilling the requirement.
*   **Recommended Soil Source:** **Candidate B (NBSS&LUP Static Soil Types)**. It avoids the temporal fallacy of using modern SHC NPK data for historical crop yields. 

---

## 5. Geographic Join Strategy

Joining datasets by District Name is notoriously difficult in India due to:
1.  **Spelling Variations:** e.g., `Pondicherry` vs `Puducherry`, `Orissa` vs `Odisha`, `Bangalore` vs `Bengaluru`.
2.  **District Bifurcations:** Districts continuously split between 1997 and 2015 (e.g., Telangana state creation in 2014, breaking Andhra Pradesh districts).

**Strategy:**
*   Do NOT use standard inner/left joins on raw strings.
*   We must create a **Normalized District Mapping Dictionary** (e.g., standardizing everything to 2011 Census naming conventions). 
*   Use Fuzzy String Matching (Levenshtein distance) via `thefuzz` library in Python to auto-map weather districts to crop districts, with manual overrides for splits.

---

## 6. Temporal Alignment & Data Leakage (CRITICAL)

**The Data Leakage Risk:**
If we train a model to recommend a crop for *Kharif 2005* using the *actual recorded rainfall of Kharif 2005*, we introduce massive data leakage. A farmer asking for a recommendation in May 2026 does not know exactly how much it will rain in August 2026. 

**Temporal Join Strategy:**
*   Weather data must be joined as **Historical Rolling Averages** (Climatological Normals).
*   To predict/recommend for Year $Y$, the model features must be the average Rainfall/Temp of $[Y-10 \text{ to } Y-1]$. 
*   This perfectly simulates the real-world farmer experience: making decisions based on the *climate* of their region, not the *actual future weather*.

---

## 7. Feature Contract

**A. Farmer-Provided Inputs:**
*   `State` & `District` (Determines the agro-climatic zone)
*   `Season` (Kharif, Rabi, Summer, Whole Year)
*   `Irrigation_Available` (Boolean) - *New UI feature to handle water dependency*

**B. Digital Twin (Auto-fetched via Location):**
*   `Historical_Avg_Rainfall_Season` (mm)
*   `Historical_Avg_Temperature_Season` (°C)
*   `Soil_Type` (e.g., Black, Alluvial, Red)

**C. Model Features (X):**
*   `State_Encoded`, `District_Encoded`, `Season_Encoded`, `Soil_Type_Encoded`, `Avg_Rainfall`, `Avg_Temp`, `Irrigation`

**D. Target Label (y):**
*   `Recommended_Crop` (Categorical - 20 Priority Crops)

*(Note: N, P, K, pH are completely removed from the contract as they are dynamic, hard to measure without a lab, and historically unavailable for our 1997-2015 dataset.)*

---

## 8. Target-Label Analysis: Why "Yield" is a Flawed Proxy

**Can `Production / Area = Yield` be used as a proxy for "Suitability"?**  
**NO. This is a severe biological fallacy.**

*   **Weight Discrepancy:** Sugarcane yields ~70 tonnes/hectare. Wheat yields ~3 tonnes/hectare. If we define "Suitability = Max Yield", the model will blindly recommend Sugarcane and Banana everywhere simply because they are biologically heavier crops. Yield is *not* comparable across different crop species.
*   **The Solution: Area Allocation + Success Frequency (RYI).**
    Instead of comparing raw yield, a district is "highly suitable" for a crop if:
    1.  The district repeatedly allocates a large percentage of its arable `Area` to that crop over 19 years (Farmers don't repeatedly plant failing crops).
    2.  The crop's yield in that district is consistently equal to or higher than the *National Average Yield for that specific crop*.

---

## 9. Data Leakage Risks
1.  **Future Weather Leakage:** Addressed in Section 6 by using rolling averages.
2.  **Survivorship Bias:** The `crop_production.csv` dataset only records crops that were actually planted. We don't have negative labels (crops that were planted and failed completely). We will only train on positive associations.

---

## 10. Recommended Data Architecture

1.  **Base:** `crop_production.csv`
2.  **Filter:** Filter out the 100+ non-priority crops, leaving only the 20 KisanCare V1 crops.
3.  **Aggregate:** Group by `District` + `Season` + `Crop` over the 19 years to calculate an `Area_Dominance_Score` and `Relative_Yield_Score`.
4.  **Join Soils:** Map each `District` to a static `Soil_Type` (NBSS&LUP mapping).
5.  **Join Climate:** Map each `District` + `Season` to its 30-year average `Rainfall` and `Temperature` (IMD district climatology).
6.  **Labeling:** For every unique `District` + `Season` + `Soil` + `Weather` combination, label the Top 3 crops based on the highest combined Area/Yield scores.

---

## 11. Remaining Gaps
*   We need a standardized CSV mapping of India's 646 districts to their primary Soil Type (Black, Alluvial, Laterite, etc.).
*   We need a standardized CSV of District-wise historical monthly temperature averages.

---

## 12. Exact Next Step

**Do not write merging code yet.**
The exact next step is to acquire/create the two missing mapping files:
1. `district_soil_mapping.csv`
2. `district_climate_mapping.csv`
We will assemble these mappings manually or via targeted API queries before initiating the final Jupyter notebook merge sequence.
