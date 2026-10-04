# 04 — Missing-Crop Strategy: Expanding the Baseline

**Date:** 2026-10-04  
**Task:** Define a strategy to support the 10 missing V1 priority crops (Wheat, Soybean, Sugarcane, Groundnut, Sorghum, Pearl Millet, Mustard, Onion, Potato, Tomato) without sacrificing user experience.  
**Author:** Antigravity (AI-assisted research)  
**Branch:** `research-reports`  

---

## 1. Best Data Source for Missing Crops

Our repository screening (Report 03) proved that no single existing Kaggle or GitHub CSV file contains the exact 7 features (`N`, `P`, `K`, `temperature`, `humidity`, `ph`, `rainfall`) for our 10 missing crops combined with the baseline 22 crops. 

Therefore, the most reliable and scientifically sound data source is **Synthetic Data Generation based on Official Agronomic Standards**. 

*   **Primary Source:** **ICAR (Indian Council of Agricultural Research)** publications and **FAO EcoCrop** database.
*   **Why this works:** The baseline dataset (Atharva Ingle's Kaggle dataset) was itself created by taking optimal agronomic ranges for 22 crops and applying a normal distribution (Gaussian noise) to generate 100 samples per crop. By retrieving the official ICAR/FAO ranges for our 10 missing crops, we can use the exact same mathematical methodology to generate perfectly compatible training data.

---

## 2. Coverage Table

| Crop | Current Baseline | Missing / Needed | Data Source Strategy |
|---|---|---|---|
| **Wheat** | ❌ | ✅ | ICAR NPK ratios + FAO climate ranges |
| **Soybean** | ❌ | ✅ | ICAR NPK ratios + FAO climate ranges |
| **Sugarcane** | ❌ | ✅ | ICAR NPK ratios + FAO climate ranges |
| **Groundnut** | ❌ | ✅ | ICAR NPK ratios + FAO climate ranges |
| **Sorghum (Jowar)** | ❌ | ✅ | ICAR NPK ratios + FAO climate ranges |
| **Pearl Millet (Bajra)** | ❌ | ✅ | ICAR NPK ratios + FAO climate ranges |
| **Mustard** | ❌ | ✅ | ICAR NPK ratios + FAO climate ranges |
| **Onion** | ❌ | ✅ | ICAR NPK ratios + FAO climate ranges |
| **Potato** | ❌ | ✅ | ICAR NPK ratios + FAO climate ranges |
| **Tomato** | ❌ | ✅ | ICAR NPK ratios + FAO climate ranges |

---

## 3. Compatibility Analysis

To successfully merge the missing crops into the baseline, the new data must be strictly compatible:

| Feature | Target Unit / Format | Compatibility Action Required |
|---------|----------------------|-------------------------------|
| **N, P, K** | Ratio / Index | ICAR provides optimal NPK in kg/ha (e.g., Wheat 120:60:40). We must mathematically scale these to match the 0-140 index scale used in the Kaggle dataset. |
| **Temperature** | Celsius (°C) | Direct match with FAO data. |
| **Humidity** | Percentage (%) | Direct match with FAO/IMD regional averages. |
| **pH** | 0-14 scale | Direct match. |
| **Rainfall** | mm | Direct match (must use crop-cycle averages). |
| **Sampling** | Distribution | We must use `numpy.random.normal()` to generate 100 rows per crop, matching the variance/standard deviation of the Kaggle dataset to prevent the model from overfitting on the new crops. |

---

## 4. Architecture Options: A vs B vs C

### Option A: Unified Model (Data Expansion)
*Expand the Kaggle dataset from 2,200 rows (22 crops) to 3,200 rows (32 crops) and train a single Random Forest.*
*   **Advantages:** Provides a single, clean artifact. Native `predict_proba()` effortlessly calculates Top-3 rankings across all 32 crops. Zero API integration complexity.
*   **Disadvantages:** Requires writing a python script to synthesize the 1,000 new rows.
*   **Training Requirements:** Minimal. Scikit-learn Random Forest trains on 3,200 rows in < 2 seconds.
*   **Risk of Inconsistency:** None. All classes are evaluated by the same decision trees.
*   **Hackathon Feasibility:** Very High.

### Option B: Orchestration / Ranking Layer
*Use the baseline 22-crop model alongside a new 10-crop model, blending them via a custom API layer.*
*   **Advantages:** Leaves the baseline `.pkl` completely untouched.
*   **Disadvantages:** Comparing confidence scores between two isolated models trained on different datasets is statistically invalid (uncalibrated probabilities). E.g., Model 1 might predict Rice at 80% confidence, and Model 2 predicts Wheat at 90% confidence, but the scales don't mathematically align.
*   **Integration Complexity:** High.
*   **Hackathon Feasibility:** Medium.

### Option C: Baseline + Secondary Model (Fallback)
*Run the baseline model; if confidence is low, run the secondary model.*
*   **Advantages:** Simple IF/ELSE logic in the API.
*   **Disadvantages:** Fatal UX flaw. If the user inputs optimal conditions for Wheat (which Model 1 doesn't know), Model 1 will forcefully misclassify it as a similar crop (e.g., Maize) with high confidence. The fallback will never trigger.
*   **Integration Complexity:** Low.
*   **Hackathon Feasibility:** Medium.

---

## 5. Recommended Architecture

**Option A (Unified Model)** is the definitive recommendation. 

It completely satisfies the requirement for "ONE clean KisanCare Model 1 experience." The API layer remains entirely agnostic to the underlying dataset, simply requesting predictions and returning the Top-3 crops with standard, calibrated confidence scores. 

---

## 6. Exact Data We Should Obtain Next

Before writing the data generation script, we must compile a JSON/Dictionary containing the optimal ranges for the 10 missing crops. 

For each of the 10 crops, we need:
1. `N_mean`, `P_mean`, `K_mean`
2. `temp_mean`, `temp_std_dev`
3. `humidity_mean`, `humidity_std_dev`
4. `ph_mean`, `ph_std_dev`
5. `rainfall_mean`, `rainfall_std_dev`

---

## 7. Next Implementation Phase

**Do NOT start this yet (awaiting authorization):**

1. Define the dictionary of optimal agronomic ranges for the 10 missing crops based on ICAR/FAO.
2. Write `scripts/generate_missing_crops.py` to output a 1,000-row CSV.
3. Merge this with the downloaded `djdhairya` 2,200-row baseline CSV.
4. Run a quick Random Forest training script (`scripts/train_model1.py`) to output the new, unified `crop_recommendation_v1.pkl` and corresponding scalers.
5. Deploy this single unified model into the FastAPI backend.
