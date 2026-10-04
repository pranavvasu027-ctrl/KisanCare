# Phase 2 — KisanCare Input Mapping

## PART 1 — DEFINE THE FARMER-FACING INPUTS

To generate a realistic crop recommendation, the farmer should only provide what cannot be reliably derived. 

1. **Location / District:** `REQUIRED`. Absolutely necessary to derive climate, soil baselines, and agro-ecological zones.
2. **Season:** `REQUIRED`. Necessary to determine planting window constraints (Kharif, Rabi, Summer).
3. **Irrigation / Water Availability:** `REQUIRED`. High-impact constraint. A farmer in a high-rainfall district might still lack irrigation infrastructure, and vice-versa.
4. **Soil Information (Soil Health Card):** `OPTIONAL`. If a farmer has a recent soil test (N, P, K, pH, etc.), it vastly improves precision. If absent, the system must fallback to regional defaults.
5. **Farm Area:** `NOT NEEDED (for ML)`. Farm size dictates economics (Model 4) and total yield (Model 2), but does not dictate *biological suitability* (Model 1).
6. **Current/Past Crop:** `OPTIONAL`. Useful for basic rotation logic, but heavily complex for a V1 ML matrix.

## PART 2 — DISTINGUISH THREE LEVELS

| Information | Farmer Input? | Derived? | External Data? | Actual ML Feature? | Reason |
| :--- | :--- | :--- | :--- | :--- | :--- |
| District | Yes | No | No | Yes | Anchors geographic suitability and links to historical APY. |
| Season | Yes | No | No | Yes | Determines climatic alignment (e.g., Kharif vs Rabi). |
| Hist. Rainfall | No | Yes | Yes (IMD) | Yes | Climatic average dictates long-term crop viability. |
| Hist. Temp | No | Yes | Yes (IMD) | Yes | Climatic average dictates thermal limits. |
| Soil N, P, K, pH | Optional | Yes (Fallback) | Yes (ICAR) | Yes | Drives nutrient suitability; can be estimated if missing. |
| Irrigation Status | Yes | No | No | No (Constraint) | Better used as a post-prediction filter to block water-heavy crops. |
| Farm Area | Optional | No | No | No | Irrelevant for biological crop suitability. |

## PART 3 — WEATHER / CLIMATE INPUT DESIGN

**The Temporal Leakage Problem:**
If we train a model using "Realized Seasonal Rainfall" (e.g., exactly 850mm of rain fell in Kharif 2015), the model assumes the farmer knows the exact future weather before planting. This is a classic ML leakage error.

**The Solution: Historical Climatology**
At the moment of recommendation, the only legitimate weather data available is the *historical average*. 
*   **Historical Seasonal Rainfall:** 10-year rolling average rainfall for that specific District + Season.
*   **Temperature Climatology:** 10-year average min/max temperature for the planting window.
*   **Rainfall Variability (CV):** Coefficient of variation (Risk metric).

## PART 4 — LOCATION / GEOGRAPHY

*   **District:** `PROVISIONAL ML FEATURE`. The primary categorical anchor. It maps perfectly to historical APY data.
*   **State:** `PROVISIONAL ML FEATURE`. Useful as a hierarchical fallback if a specific district is undersampled.
*   **Latitude/Longitude:** `REJECTED`. Unnecessary precision that easily causes overfitting since our ground-truth production data (UPAg APY) is only at the District level.
*   **Agro-Climatic Zone:** `INVESTIGATE`. Scientifically robust, but District boundaries often naturally map to these zones.

## PART 5 — SEASON

*   **Kharif, Rabi, Summer:** `REQUIRED ML FEATURES`. Determines the biological cycle.
*   **Should it affect climatology?** Yes. Historical rainfall must be partitioned by season (Kharif rain != Rabi rain).
*   **Filter Constraint:** Yes. If the user selects "Rabi", the ML predicts, but the Decision Engine strictly filters out exclusively Kharif crops.
*   **Perennials (Mango/Grapes):** Perennials span the "Whole Year". If a farmer selects a specific season, perennials should conceptually bypass seasonal filters, as planting time is more flexible, though harvest is fixed.

## PART 6 — SOIL INPUT DESIGN

We reject the Kaggle NPK interpretation (fertilizer doses). KisanCare needs actual soil availability metrics:
*   **N, P, K (kg/ha):** Available macronutrients.
*   **pH:** Acidity/Alkalinity.
*   **SOC (Soil Organic Carbon):** Soil health indicator.
*   **Soil Texture (Clay/Sand/Loam):** Water retention.

**Strategy:**
1.  *Can the farmer provide it?* Yes, via Soil Health Card.
2.  *Can KisanCare derive it?* Yes, using regional district-level ICAR/SoilGrids soil defaults.
3.  *Is SHC required?* No. It is strictly optional.
4.  *ML Feature?* Yes.

*Critical Requirement:* The UI and API must flag whether the data is `MEASURED` (high confidence) or `ESTIMATED` (average confidence).

## PART 7 — WATER / IRRIGATION

*   **Irrigation Type / Water Availability:** `DECISION ENGINE FILTER`.
*   *Analysis:* If a farmer has "LOW" water availability, an ML model might still give Sugarcane a 15% probability. A Decision Engine rule is much safer: `IF Water == LOW, REMOVE Sugarcane`. This ensures deterministic agronomic safety rather than relying on probabilistic ML approximations.

## PART 8 — FARM HISTORY

*   **Previous Crop:** `Future Digital Twin Input`.
*   **Previous Yield:** `Future Digital Twin Input`.
*   *Analysis:* While crop rotation is critical in real farming, embedding it as a strict ML feature in V1 complicates the matrix exponentially and limits cold-start recommendations for new farmers. 

## PART 9 — KISANCARE 20-CROP CONSTRAINT

Current V1 List: Rice, Wheat, Maize, Soybean, Cotton, Sugarcane, Chickpea, Pigeon Pea, Groundnut, Sorghum, Pearl Millet, Green Gram, Black Gram, Mustard, Onion, Potato, Tomato, Banana, Mango, Grapes.

**Feature Availability:**
*   **District/Season:** Available for all.
*   **Climatology:** Available for all.
*   **Soil (Regional):** Available for all.
*   **Target (Yield/Area Data):** Available for 17 field crops. (Tomato, Mango, Grapes remain critically sparse, awaiting P27 decision).

## PART 10 — FEATURE CANDIDATES

| Name | Definition | Unit | Source | Frmr/Deriv | Avail. | Leakage | Useful | Missing Risk |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| District | Geo boundary | Str | UI | Farmer | 100% | None | High | Low |
| Season | Plant window | Str | UI | Farmer | 100% | None | High | Low |
| Hist_Rainfall | 10-yr avg rain | mm | IMD | Derived | High | None | High | Low |
| Act_Rainfall | Exact rain | mm | IMD | Derived | High | **High** | High | Low |
| Soil_N | Avail Nitrogen | kg/ha | SHC/ICAR | Both | High | None | High | Med (Impute) |
| Soil_pH | Soil acidity | pH | SHC/ICAR | Both | High | None | High | Med (Impute) |
| Water_Avail | Irrigation | Cat | UI | Farmer | High | None | Med | Low |
| Prev_Yield | Last harvest | t/ha | UI | Farmer | Low | None | Low | High |

## PART 11 — FEATURE ELIMINATION

*   🔴 **Exact future rainfall:** REJECT. Impossible to know at planting. Severe target leakage.
*   🔴 **Exact future temperature:** REJECT. Severe target leakage.
*   🔴 **Raw yield:** REJECT. "Yield Fallacy"—biases model toward inherently heavy crops (Sugarcane).
*   🔴 **Fertilizer doses (Kaggle NPK):** REJECT. Mathematically invalid proxy for soil baseline.
*   🔴 **Previous Yield:** REJECT. High missing-data risk for V1 cold-start users.
*   🟢 **Historical Climatology (Rain, Temp):** KEEP. Scientifically valid pre-planting knowledge.
*   🟢 **Measured/Default Soil (N, P, K, pH):** KEEP. Essential for agronomic limits.
*   🟡 **Soil Texture / SOC:** INVESTIGATE. Useful, but may be too sparse in regional default databases.

---

# KisanCare Model 1 — Input Specification v1

## A. Farmer Inputs
*(Minimum realistic UI payload)*
1. District (Categorical)
2. Season (Kharif, Rabi, Summer, Whole Year)
3. Water Availability (High, Medium, Low/Rainfed)
4. [Optional] Soil Health Card (N, P, K, pH)

## B. Automatically Derived Inputs
*(Backend resolution)*
1. Historical average rainfall for (District + Season)
2. Historical average temperature for (District + Season)
3. Regional soil defaults (if Soil Health Card is missing)

## C. External Data
1. APY Target Baseline (UPAg)
2. Weather Climatology (IMD / ERA5)
3. Soil Grids (ICAR / ISRIC)

## D. Actual ML Features
*(The final feature matrix fed to the Model)*
1. `District`
2. `Season`
3. `Historical_Rainfall`
4. `Historical_Temperature`
5. `Soil_N`
6. `Soil_P`
7. `Soil_K`
8. `Soil_pH`

## E. Decision-Engine Constraints
*(Applied post-prediction)*
1. `Water Availability`: Hard filters high-water crops if set to Low.
2. `Season Constraint`: Hard filters crops that biologically cannot grow in the chosen season (except perennials).

## F. Data Confidence
*   **MEASURED:** Farmer provided exact Soil Health Card values.
*   **ESTIMATED:** System used district-level average soil defaults.

---

## PART 13 — MISSING-DATA STRATEGY

*   **No soil test:** Fallback to District-level soil defaults (ESTIMATED confidence).
*   **No exact location (District):** Hard failure. District is REQUIRED. Recommendation cannot proceed without geography.
*   **No irrigation info:** Default to "Low/Rainfed" (safest pessimistic assumption).
*   **No crop history:** Ignored for V1.

---

## PART 14 — FINAL DECISION TABLE

| Variable | Farmer Input | Derived | External | ML Feature | Decision Engine | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| District | Yes | No | No | Yes | No | PROVISIONAL |
| Season | Yes | No | No | Yes | Yes | PROVISIONAL |
| Exact Rainfall | No | No | No | No | No | REJECTED |
| Hist. Rainfall | No | Yes | Yes | Yes | No | PROVISIONAL |
| Hist. Temp | No | Yes | Yes | Yes | No | PROVISIONAL |
| Soil N, P, K, pH | Optional | Yes | Yes | Yes | No | PROVISIONAL |
| Water Avail. | Yes | No | No | No | Yes | PROVISIONAL |
| Kaggle NPK | No | No | No | No | No | REJECTED |
| Prev. Yield | Optional | No | No | No | No | REJECTED |
