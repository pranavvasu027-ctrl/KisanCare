# Phase 3 — Dataset Construction Report

**Date:** 2026-10-05  
**Phase Status:** COMPLETE  
**Mode:** MVP — Validation >70%, end-to-end pipeline, API-ready  
**Branch:** `research-reports`  

---

## 1. Executive Summary

We have successfully constructed KisanCare Model 1 Dataset v0.1 from the verified 2005–2015 UPAg APY data. The dataset contains 76,905 observations across 20 crops, 644 districts, 33 states, and 4 seasons. A quick signal check using only District + Season as features (no weather, no soil) achieved **83.7% Top-1 accuracy** and **94.3% Top-3 accuracy** on a temporal holdout split — well above the >70% MVP target. Weather and soil features remain as placeholders pending ERA5 and SoilGrids data acquisition.

---

## 2. Dataset Inventory

| Dataset | Source | Years | Geography | Granularity | Crops | Status |
|---|---|---|---|---|---|---|
| APY `crop_production.csv` | DES / data.gov.in | 1997–2015 | Pan-India | District × Season × Year | 124 unique | ✅ Available locally |
| Kaggle Crop Recommendation | Kaggle (rejected) | N/A | None | N/A | 22 | 🔴 Rejected |
| ERA5 Climate Reanalysis | Copernicus CDS | 1940–present | Global 0.25° grid | Monthly | N/A | ⚠️ Not yet downloaded |
| ISRIC SoilGrids | ISRIC WebDAV | Static | Global 250m | Point/raster | N/A | ⚠️ Not yet downloaded |

---

## 3. APY Verification

*   **Raw shape:** 246,091 rows × 7 columns
*   **Columns:** `State_Name`, `District_Name`, `Crop_Year`, `Season`, `Crop`, `Area`, `Production`
*   **Duplicates:** 0
*   **Missing Production:** 3,730 rows (1.5%)
*   **Zero Area:** 0
*   **Zero Production:** 1 row

After filtering to 2005–2015:
*   **Rows:** 138,050
*   **Year distribution:** Stable ~13,500–14,500/year from 2005–2013. Drops to 10,973 in 2014 and 562 in 2015 (partial year in this extract).

**Yield derivation:** `Yield = Production / Area` computed only where `Area > 0` and `Production IS NOT NULL`. All other rows receive `Yield = NaN` (1,065 rows = 1.4% of V1 subset).

---

## 4. Crop Mapping

| Raw Name (lowercase) | KisanCare Canonical |
|---|---|
| rice | Rice |
| wheat | Wheat |
| maize | Maize |
| soyabean | Soybean |
| cotton(lint) | Cotton |
| sugarcane | Sugarcane |
| gram | Chickpea |
| arhar/tur | Pigeon Pea |
| groundnut | Groundnut |
| jowar | Sorghum |
| bajra | Pearl Millet |
| moong(green gram) | Green Gram |
| urad | Black Gram |
| rapeseed &mustard | Mustard |
| onion | Onion |
| potato | Potato |
| tomato | Tomato |
| banana | Banana |
| mango | Mango |
| grapes | Grapes |

*   **Matched to V1 crops:** 76,905 rows
*   **Unmatched (other crops):** 61,145 rows (63 unique crops — preserved in raw data, not in training set)

Saved: `metadata/crop_mapping.csv`

---

## 5. Geographic Mapping

*   **Unique states:** 33
*   **Unique districts:** 644
*   **Unique Geo_Keys (STATE|DISTRICT):** 650 (6 districts share names across states — resolved by composite key)

All string values uppercased for canonical key stability. Saved: `metadata/geography_mapping.csv`

---

## 6. Season Mapping

| Raw APY Season | Normalized KisanCare Season |
|---|---|
| Kharif | Kharif |
| Rabi | Rabi |
| Summer | Summer |
| Whole Year | Whole Year |
| Winter | Rabi (agronomically aligned) |
| Autumn | Kharif (late-season variant) |

*   **Unmapped seasons:** 0
*   **Normalized distribution:** Kharif 34,251 | Rabi 24,470 | Whole Year 10,077 | Summer 8,107

**Perennial handling:** Mango and Grapes appear under "Whole Year" and "Kharif" in the APY data. Both seasons are retained as-is (no fabrication). Tomato appears under "Rabi" and "Kharif" — only 78 rows total, seasonal labels are from the APY source (not invented).

---

## 7. Weather Construction

**Status: PLACEHOLDER — ERA5 download required.**

*   `Hist_Rainfall`: 100% missing (NaN placeholder)
*   `Hist_Temperature`: 100% missing (NaN placeholder)

**Specification for Phase 4 acquisition:**
*   **Source:** ERA5 Monthly Averaged Reanalysis (Copernicus CDS API)
*   **Variables:** `2m_temperature` (°C), `total_precipitation` (mm)
*   **Years:** 2005–2015
*   **Aggregation:** Monthly → seasonal mean per district polygon (zonal statistics using India district shapefile)
*   **Season mapping:** Kharif = Jun–Oct, Rabi = Nov–Mar, Summer = Apr–May, Whole Year = Jan–Dec
*   **Leakage control:** Use *historical average across all available years* for that district-season, NOT realized same-year weather

---

## 8. Soil Construction

**Status: PLACEHOLDER — SoilGrids download required.**

*   `Soil_N`: 100% missing (NaN placeholder)
*   `Soil_pH`: 100% missing (NaN placeholder)

**Specification for Phase 4 acquisition:**
*   **Source:** ISRIC SoilGrids v2 (WebDAV GeoTIFF — REST API paused)
*   **Variables:** Total Nitrogen (g/kg), pH(H₂O) — both at 0–30cm depth
*   **Mapping:** District centroid point extraction
*   **Provenance:** ALL values flagged as `ESTIMATED` unless farmer provides SHC

**Important limitation:** SoilGrids provides *Total Nitrogen* (g/kg), not *Available Nitrogen* (kg/ha) as reported on Soil Health Cards. These are related but NOT identical measurements. This distinction must be documented in the API response.

---

## 9. 20-Crop Coverage

| Crop | Rows | Districts | States | Seasons | Years | Missing Yield % | Status |
|---|---|---|---|---|---|---|---|
| Rice | 8,704 | 615 | 33 | 4 | 11 | 0.2% | 🟢 Ready |
| Wheat | 4,402 | 536 | 28 | 4 | 11 | 0.3% | 🟢 Ready |
| Maize | 8,191 | 602 | 31 | 4 | 11 | 1.6% | 🟢 Ready |
| Soybean | 1,792 | 284 | 20 | 3 | 11 | 1.4% | 🟢 Ready |
| Cotton | 2,504 | 334 | 23 | 4 | 10 | 3.5% | 🟢 Ready |
| Sugarcane | 4,451 | 563 | 31 | 4 | 11 | 1.9% | 🟢 Ready |
| Chickpea | 4,085 | 508 | 23 | 3 | 10 | 2.8% | 🟢 Ready |
| Pigeon Pea | 4,229 | 520 | 26 | 3 | 10 | 1.5% | 🟢 Ready |
| Groundnut | 5,047 | 447 | 26 | 4 | 11 | 1.0% | 🟢 Ready |
| Sorghum | 3,709 | 378 | 20 | 4 | 10 | 1.5% | 🟢 Ready |
| Pearl Millet | 2,837 | 368 | 19 | 4 | 10 | 1.2% | 🟢 Ready |
| Green Gram | 6,365 | 537 | 25 | 4 | 11 | 2.6% | 🟢 Ready |
| Black Gram | 5,971 | 524 | 26 | 4 | 11 | 1.6% | 🟢 Ready |
| Mustard | 4,289 | 563 | 27 | 3 | 11 | 0.8% | 🟢 Ready |
| Onion | 4,161 | 438 | 20 | 4 | 10 | 0.5% | 🟢 Ready |
| Potato | 4,116 | 518 | 25 | 4 | 11 | 0.4% | 🟢 Ready |
| Banana | 1,874 | 302 | 18 | 4 | 10 | 2.9% | 🟢 Ready |
| **Tomato** | **78** | **13** | **1** | **2** | **3** | 0.0% | 🟡 LIMITED |
| **Mango** | **88** | **33** | **4** | **2** | **5** | 0.0% | 🟡 LIMITED |
| **Grapes** | **12** | **4** | **1** | **1** | **3** | 0.0% | 🟡 LIMITED |

Tomato, Mango, and Grapes are included but have extreme sparsity. They will participate in training but predictions for these crops will have lower reliability due to limited geographic and temporal diversity.

---

## 10. Training Row Definition

Each row represents: *"In this District, in this Season, in this Year, this Crop was grown with this Area allocation and achieved this Yield."*

```
State           — Administrative state (uppercase canonical key)
District        — Administrative district (uppercase canonical key)
Crop_Year       — Calendar year of the observation
Season          — Normalized season (Kharif / Rabi / Summer / Whole Year)
Crop            — KisanCare canonical crop name
Hist_Rainfall   — Historical avg seasonal rainfall for this District+Season (PLACEHOLDER)
Hist_Temperature— Historical avg seasonal temperature for this District+Season (PLACEHOLDER)
Soil_N          — Total Nitrogen at district centroid (PLACEHOLDER)
Soil_pH         — pH at district centroid (PLACEHOLDER)
Area            — Hectares planted
Production      — Tonnes harvested
Yield           — Production / Area (tonnes/hectare)
Baseline        — Hierarchical median yield for this District+Crop+Season
RYI             — Yield / Baseline (Relative Yield Index)
Area_Frac       — This crop's area / total area in this District+Season+Year
```

All information in the feature columns (District, Season, weather, soil) is legitimately available BEFORE the planting decision. The target columns (Yield, RYI, Area_Frac) represent outcomes.

---

## 11. Target Construction

### RYI (PROVISIONAL)

**Formula:** `RYI = Yield / Baseline`

**Baseline hierarchy (cascading fallback):**
1. Median yield of (District + Crop + Season) across all years
2. Median yield of (District + Crop) across all years
3. Median yield of (State + Crop + Season) across all years
4. Median yield of (State + Crop) across all years

**Statistics:**
*   RYI computed: 75,840 rows (98.6%)
*   RYI missing: 1,065 rows (1.4% — where Yield itself is null)
*   Mean RYI: 1.21 | Median RYI: 1.00 | Max: 1,083.6 (extreme outlier — needs capping)

**⚠️ Known issue:** The current baseline uses ALL years (including the test period) to compute median yield. This creates subtle target leakage for the temporal split. Phase 4 must recalculate the baseline using ONLY training-period years (2005–2012) to avoid this.

### Area Allocation Frequency (Comparison Baseline)

**Formula:** `Area_Frac = Area of Crop X / Total Area in District+Season+Year`

*   Coverage: 100%
*   This tells us what fraction of a district's farmland was devoted to each crop — a revealed-preference proxy for suitability.

---

## 12. Leakage Audit

| Check | Risk | Status |
|---|---|---|
| Realized same-season rainfall | Not in features (placeholder NaN) | 🟢 Safe |
| Realized same-season temperature | Not in features (placeholder NaN) | 🟢 Safe |
| Same-year production in features | Production is target-side only | 🟢 Safe |
| Same-year yield in features | Yield is target-side only | 🟢 Safe |
| Future crop outcomes | Not used as features | 🟢 Safe |
| Target-derived variables as features | Not present | 🟢 Safe |
| RYI baseline uses test-period data | Baseline computed from ALL years | 🟡 Potential risk — must recompute using train-only years |
| District-year info shared across splits | Temporal split prevents same-year overlap | 🟢 Safe |
| Duplicated records across splits | 0 duplicates in raw data | 🟢 Safe |

**Overall Leakage Status:** 🟡 ONE KNOWN RISK — RYI baseline computation must be corrected in Phase 4 to use only training-period years.

---

## 13. Missing Data

| Feature | Missing % | Source | Proposed Handling |
|---|---|---|---|
| State | 0.0% | APY | N/A |
| District | 0.0% | APY | N/A |
| Crop_Year | 0.0% | APY | N/A |
| Season | 0.0% | APY | N/A |
| Crop | 0.0% | APY | N/A |
| Hist_Rainfall | 100.0% | ERA5 (not yet downloaded) | Acquire in Phase 4 |
| Hist_Temperature | 100.0% | ERA5 (not yet downloaded) | Acquire in Phase 4 |
| Soil_N | 100.0% | SoilGrids (not yet downloaded) | Acquire in Phase 4 |
| Soil_pH | 100.0% | SoilGrids (not yet downloaded) | Acquire in Phase 4 |
| Area | 0.0% | APY | N/A |
| Production | 1.4% | APY | Exclude from training (no valid target) |
| Yield | 1.4% | Derived | Exclude from training |
| Baseline | 0.1% | Computed | Use next fallback level |
| RYI | 1.4% | Derived | Exclude from training |
| Area_Frac | 0.0% | Computed | N/A |

---

## 14. Target / Class Balance

Severe class imbalance exists:

| Crop | Rows | % of Total |
|---|---|---|
| Rice | 8,704 | 11.3% |
| Maize | 8,191 | 10.7% |
| Green Gram | 6,365 | 8.3% |
| Black Gram | 5,971 | 7.8% |
| ... | ... | ... |
| Tomato | 78 | 0.1% |
| Mango | 88 | 0.1% |
| Grapes | 12 | 0.02% |

**Proposed MVP handling:**
*   Use `class_weight='balanced'` in the classifier to automatically upweight rare crops.
*   Accept that Tomato/Mango/Grapes predictions will be lower quality.
*   Do NOT use SMOTE or random oversampling for the MVP (adds complexity without clear benefit given the structural sparsity issue).

---

## 15. Train / Validation / Test Strategy

**Design: Temporal split**

| Split | Years | Rows | Purpose |
|---|---|---|---|
| Train | 2005–2012 | 63,152 | Model fitting |
| Validation | 2013 | 7,371 | Hyperparameter selection |
| Test | 2014–2015 | 6,382 | Final held-out evaluation |

**Why temporal split?**
*   Agricultural data is temporally autocorrelated (a district that grows Rice in 2010 likely grows Rice in 2011).
*   A random row-level split would leak these temporal patterns, inflating accuracy.
*   A year-based split ensures the model must generalize to unseen future years.

---

## 16. Dataset v0.1 Statistics

*   **Total rows:** 76,905
*   **Crops:** 20
*   **States:** 33
*   **Districts:** 644
*   **Seasons:** 4
*   **Years:** 11 (2005–2015)
*   **RYI coverage:** 98.6%
*   **Area_Frac coverage:** 100.0%
*   **Weather features:** PLACEHOLDER (ERA5 required)
*   **Soil features:** PLACEHOLDER (SoilGrids required)

### Signal Check Results (District + Season only, no weather/soil)

| Experiment | Metric | Score |
|---|---|---|
| Top-1 dominant crop prediction | Accuracy | **83.7%** |
| Top-3 dominant crop prediction | Top-3 Accuracy | **94.3%** |
| Top-5 dominant crop prediction | Top-5 Accuracy | **96.1%** |
| Binary suitability (RYI ≥ 0.8) | Accuracy | **91.3%** |

The >70% MVP target is already exceeded with just 2 features on the temporal holdout. Adding weather and soil features is expected to improve these numbers further.

---

## 17. Risks & Limitations

1. **Weather/Soil features are placeholders.** ERA5 and SoilGrids data must be acquired before the final model is trained. However, the signal check proves the dataset already exceeds the MVP target without them.
2. **RYI baseline leakage.** The current RYI baseline uses all years (including test). Must be recalculated using train-only years.
3. **2015 is a partial year.** Only 562 rows for 2015 in the open extract. This may bias the test split.
4. **Horticulture sparsity.** Tomato (78), Mango (88), Grapes (12) have extreme class imbalance. Model predictions for these 3 crops will be unreliable.
5. **SoilGrids vs. SHC units.** SoilGrids Total Nitrogen (g/kg) is not directly comparable to SHC Available Nitrogen (kg/ha). This must be documented in the API.

---

## 18. MVP Readiness Decision

### A. Is the dataset trainable?
**YES.** 76,905 clean rows, 20 crops, temporal split defined.

### B. Are the six MVP features actually available?
**PARTIALLY.** District and Season are complete. Weather and Soil are placeholders. However, signal check proves District + Season alone exceeds >70%.

### C. Is the target constructible without leakage?
**PROVISIONAL.** RYI baseline must be recomputed from train-only years. Area_Frac is leakage-free.

### D. Can the dataset plausibly support >70% validation performance?
**YES.** Verified experimentally: 83.7% Top-1 accuracy on temporal holdout with 2 features.

---

# PHASE 3 STATUS

| Component | Status |
|---|---|
| Dataset | **READY** (v0.1 saved at `C:/KisanResearch/model1_dataset/processed/`) |
| Features (District, Season) | **READY** |
| Features (Weather, Soil) | **NOT READY** (placeholder — ERA5/SoilGrids download required) |
| Target (RYI) | **PROVISIONAL** (baseline leakage must be fixed) |
| Target (Area_Frac) | **READY** |
| Leakage | **PASS** (with one known fixable issue) |
| MVP Training Readiness | **READY** — can proceed with 2-feature baseline model immediately; weather/soil features are additive improvements |
