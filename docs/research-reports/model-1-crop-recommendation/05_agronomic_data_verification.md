# 05 — Agronomic Data Verification: The Flaw in the Baseline

**Date:** 2026-10-04  
**Task:** Verify official agronomic inputs for the 10 missing priority crops and assess the scientific validity of synthetically generating data to append to the Kaggle baseline.  
**Author:** Antigravity (AI-assisted research)  
**Branch:** `research-reports`  

---

## 1. Verified Agronomic Data Table (Missing 10 Crops)

The following agronomic requirements were compiled for the missing priority crops. 

> **CRITICAL CONTEXT:** The N, P, and K values below represent standard **fertilizer recommendations (kg/ha)** for optimal yield, *not* the existing baseline soil nutrients before planting.

| Crop | N (kg/ha) | P (kg/ha) | K (kg/ha) | Temp (°C) | Rain (mm) | pH |
|---|---|---|---|---|---|---|
| **Wheat (Rabi)** | 120 | 60 | 40 | 15 - 25 | 50 - 100* | 6.0 - 7.0 |
| **Soybean (Kharif)** | 20 | 60 | 40 | 25 - 30 | 600 - 750 | 6.0 - 7.5 |
| **Sugarcane** | 250 | 100 | 100 | 20 - 35 | 1500 - 2500 | 6.5 - 7.5 |
| **Groundnut** | 20 | 50 | 40 | 25 - 30 | 500 - 700 | 6.0 - 7.5 |
| **Sorghum (Jowar)** | 80 | 40 | 40 | 25 - 32 | 400 - 600 | 6.0 - 7.5 |
| **Pearl Millet (Bajra)**| 60 | 30 | 30 | 25 - 35 | 300 - 500 | 6.0 - 8.0 |
| **Mustard (Rabi)** | 80 | 40 | 40 | 15 - 25 | 50 - 100* | 6.0 - 7.5 |
| **Onion** | 100 | 50 | 50 | 15 - 25 | 500 - 700 | 6.0 - 7.0 |
| **Potato (Rabi)** | 150 | 80 | 100 | 15 - 20 | 500 - 700 | 5.0 - 6.5 |
| **Tomato** | 120 | 60 | 60 | 20 - 25 | 600 - 800 | 6.0 - 7.0 |

*\*Rabi crops (Wheat, Mustard) rely heavily on irrigation rather than monsoon rainfall. The Kaggle dataset does not model irrigation, creating a weather mismatch.*

## 2. Source Citations
*   **ICAR (Indian Council of Agricultural Research)**: "Handbook of Agriculture" — Baseline NPK fertilizer requirements and soil pH tolerances.
*   **FAO EcoCrop Database**: Optimal temperature and rainfall thresholds.
*   **Government of India (Farmer Portal)**: Crop-specific cultivation guidelines.

---

## 3. Existing Baseline Feature Distribution Summary

We analyzed the `djdhairya` 2,200-row Kaggle dataset to understand its limits:

**Global Dataset Statistics:**
*   **N**: Min `0`, Max `140`, Mean `50.5`
*   **P**: Min `5`, Max `145`, Mean `53.3`
*   **K**: Min `5`, Max `205`, Mean `48.1`

**Crop-Specific Evidence (The Smoking Gun):**
*   **Chickpea (Legume):** Mean N = `40.0`
*   **Cotton (Cash Crop):** Mean N = `117.7`

---

## 4. Compatibility Assessment

**Is the conversion (fertilizer recommendation -> Kaggle index) scientifically justified?**  
**NO. It is fundamentally and scientifically flawed.**

1. **The Reversed Input Problem:** Analyzing the baseline stats reveals that the Kaggle dataset's NPK values perfectly mirror *fertilizer recommendations*, not *soil test values*. Legumes (chickpea) which fix their own nitrogen have low N (~40) in the dataset. Cotton, which demands heavy nitrogen, has high N (~117) in the dataset. 
2. **Real-World UX Failure:** If KisanCare deploys this, a farmer taking a real Soil Health Card test will input their "Available Soil Nitrogen" (which in India is typically **250 - 500 kg/ha**). The Kaggle model's absolute maximum N is **140**. Real farmer data will fall completely out-of-distribution, yielding garbage predictions. 
3. **Mathematical Boundary Breaking:** Sugarcane requires ~250 kg/ha of Nitrogen. The baseline dataset caps N at 140. Synthesizing Sugarcane would either break the dataset's scale or require arbitrary down-scaling, rendering the output meaningless.

---

## 5. Synthetic-Data Risk Assessment

**Conclusion: Category C — Not defensible with available data.**

Synthetically generating the missing 10 crops would mean doubling down on a fundamentally flawed premise. It would result in a "toy" model that cannot accept real-world soil test inputs. While generating the data is mathematically easy (using Gaussian noise around ICAR ranges), it produces agricultural fiction.

---

## 6. Real-Data Alternatives

Instead of trying to force NPK values into a flawed index, we can utilize **Real Agro-Climatic Data**:

*   **Source:** Government of India Crop Production Statistics (`data.gov.in`).
*   **Features Available:** District/Location, Season (Kharif, Rabi, Zaid), Crop grown, Area, Production/Yield.
*   **Methodology:** We can cross-reference the District and Season with historical IMD weather data (Temp, Rainfall) and NBSS&LUP soil type data (Black, Red, Alluvial). 
*   **Result:** This allows the model to predict the most successful crop based on Geography, Season, Soil Type, and Weather—completely bypassing the flawed NPK requirement while perfectly aligning with the `docs/ml-contract.md` JSON inputs.

---

## 7. Final Recommendation

**Abandon the unified synthetic generation approach for NPK.**

We recommend a **Pivot/Real-Data Strategy**:
1. **Drop N, P, K from the ML Contract:** They are highly misleading in open-source datasets and difficult for farmers to measure without lab tests.
2. **Build a Location-First Model:** We should use historical Indian crop production datasets (which cover all 20 priority crops natively) and train a model mapping `Location + Season + Soil Type + Weather` → `Recommended Crop`.
3. **Discard the Kaggle Baseline:** The baseline is an educational toy dataset. KisanCare is aiming for production-grade agricultural intelligence, which requires moving to real spatial/yield data.

*No data generation scripts were written, and no code was modified during this verification.*
