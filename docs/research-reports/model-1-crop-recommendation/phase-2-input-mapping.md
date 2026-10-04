# Phase 2 — KisanCare Model 1 Input Mapping (Final MVP Specification)

**Date:** 2026-10-05  
**Phase Status:** COMPLETE  
**Mode:** MVP — Validation >70%, end-to-end pipeline, API-ready  
**Branch:** `research-reports`  

---

## 1. MVP Scope

KisanCare Model 1 is a **Crop Recommendation** classifier.

*   **Goal:** Given a farmer's location, season, and available context, recommend the most suitable crops ranked by suitability score.
*   **Validation target:** >70% accuracy on held-out validation data.
*   **Crop scope:** 20 priority crops (no silent removals).
*   **Training data:** Verified 2005–2015 UPAg APY dataset (2016–2020 deferred).
*   **Weather source:** ERA5 reanalysis historical climatology.
*   **Soil fallback:** ISRIC SoilGrids (WebDAV/GeoTIFF access; REST API currently paused).
*   **Target label:** RYI is PROVISIONAL. Area Allocation Frequency retained as a comparison baseline.

---

## 2. Farmer Input Specification

The farmer should provide **only what the system cannot reliably derive**.

| Input | Classification | Reason |
|---|---|---|
| **District** | REQUIRED | Anchors geography, climate, soil, and historical production. Without it, no recommendation is possible. |
| **Season** | REQUIRED | Determines the planting window (Kharif/Rabi/Summer/Whole Year). Directly constrains which crops are biologically viable. |
| **Water Availability** | REQUIRED | A high-rainfall district may still lack irrigation. Cannot be derived from climate alone. Simplest form: `Irrigated` / `Rainfed`. |
| **Soil Health Card (N, P, K, pH)** | OPTIONAL | Dramatically improves precision. If absent, system uses estimated regional defaults. |
| **Farm Area** | NOT NEEDED | Irrelevant for biological suitability. Feeds Model 2 (Yield) and Model 4 (Economics) only. |
| **Previous Crop** | NOT NEEDED (V1) | Crop rotation is important but adds cold-start complexity. Deferred to V2/Digital Twin. |
| **Future Rainfall** | NOT COLLECTED | The farmer cannot know future weather. The system derives historical climatology instead. |

---

## 3. Derived Variables

These are computed by the backend from the farmer's District + Season selection.

| Variable | Source | Method |
|---|---|---|
| Historical Rainfall | ERA5 reanalysis | Mean seasonal precipitation over 2005–2015 for the grid cells covering the district. |
| Historical Temperature | ERA5 reanalysis | Mean seasonal 2m-temperature over 2005–2015 for the grid cells covering the district. |
| Regional Soil N | SoilGrids (ISRIC) | District-centroid Total Nitrogen at 0–30cm depth. Flagged as ESTIMATED. |
| Regional Soil pH | SoilGrids (ISRIC) | District-centroid pH(H₂O) at 0–30cm depth. Flagged as ESTIMATED. |
| Regional Soil Clay% | SoilGrids (ISRIC) | District-centroid Clay fraction at 0–30cm. Proxy for texture. Flagged as ESTIMATED. |

---

## 4. External Data Sources

| Source | Data Provided | Access Method | Status |
|---|---|---|---|
| UPAg APY (2005–2015) | Area, Production per District × Crop × Season | Local CSV (already downloaded) | ✅ Available |
| ERA5 Monthly Means | 2m Temperature, Total Precipitation | Copernicus CDS API (free registration) | ✅ Available |
| ISRIC SoilGrids | Total N, pH, SOC, Clay, Sand, Silt, CEC | WebDAV GeoTIFF download (REST API paused) | ✅ Available (WebDAV) |
| India District Shapefile | District polygons for zonal statistics | Census / Survey of India open GeoJSON | ✅ Available |

---

## 5. Final Candidate ML Features

| # | Feature | Definition | Unit | Source | Type | Status |
|---|---|---|---|---|---|---|
| 1 | `District` | Administrative district | Categorical (encoded) | Farmer | Farmer Input | 🟢 KEEP |
| 2 | `Season` | Planting season | Categorical (Kharif/Rabi/Summer/Whole Year) | Farmer | Farmer Input | 🟢 KEEP |
| 3 | `Hist_Rainfall` | Mean seasonal rainfall (2005–2015) | mm | ERA5 | Derived | 🟢 KEEP |
| 4 | `Hist_Temperature` | Mean seasonal temperature (2005–2015) | °C | ERA5 | Derived | 🟢 KEEP |
| 5 | `Soil_N` | Available Nitrogen (measured or estimated) | g/kg (SoilGrids) or kg/ha (SHC) | SHC / SoilGrids | Both | 🟡 PROVISIONAL |
| 6 | `Soil_pH` | Soil acidity (measured or estimated) | pH units | SHC / SoilGrids | Both | 🟡 PROVISIONAL |

**Features investigated and deferred or rejected for MVP:**

| Feature | Status | Reason |
|---|---|---|
| `Soil_P` (Phosphorus) | 🟡 PROVISIONAL | SoilGrids does NOT provide Available P directly. Requires SHC or separate ICAR source. If unavailable for estimation, defer. |
| `Soil_K` (Potassium) | 🟡 PROVISIONAL | Same limitation as P. SoilGrids provides CEC but not Available K. Defer if no reliable default. |
| `Soil_SOC` | 🟡 PROVISIONAL | SoilGrids provides SOC. Useful soil health indicator, but adds complexity for MVP. |
| `Soil_Texture (Clay%)` | 🟡 PROVISIONAL | SoilGrids provides Clay/Sand/Silt. Useful for water retention proxy. |
| `State` | 🟡 PROVISIONAL | Useful as hierarchical fallback if District encoding is too sparse. May be redundant if District is properly encoded. |
| `Rainfall_CV` | 🟡 PROVISIONAL | Coefficient of variation captures risk but adds complexity. Defer unless it materially improves >70%. |
| `Lat/Lon` | 🔴 REJECT | Our target data is district-level. Sub-district precision causes overfitting. |
| `Exact_Rainfall` | 🔴 REJECT | Temporal leakage. Farmer cannot know future season's exact rainfall. |
| `Exact_Temperature` | 🔴 REJECT | Temporal leakage. Same reasoning. |
| `Kaggle_NPK` | 🔴 REJECT | Fertilizer doses, not soil state. Proven invalid in Phase 05. |
| `Previous_Yield` | 🔴 REJECT | High missing-data risk. Cold-start problem for new users. |
| `Previous_Crop` | 🔴 REJECT (V1) | Deferred to V2/Digital Twin. |
| `Raw_Yield` | 🔴 REJECT | The Yield Fallacy — biases toward inherently heavy-tonnage crops. |

**MVP Recommended Minimum Feature Set:**

> `District`, `Season`, `Hist_Rainfall`, `Hist_Temperature`, `Soil_N`, `Soil_pH`

This is 6 features: 2 categorical (farmer-entered) + 2 climate (derived) + 2 soil (measured or estimated). This is the smallest set likely to produce >70% validation while remaining scientifically defensible. If soil estimation proves unreliable during Phase 3 data assembly, we can drop soil features and run a 4-feature baseline (District + Season + Rain + Temp).

---

## 6. Leakage Analysis

### Model 1 Leakage Checklist

This checklist MUST be passed before any training begins.

| Check | Risk | Status |
|---|---|---|
| ❌ No realized future rainfall used as input | Farmer cannot know exact future rain | PASS (using historical avg) |
| ❌ No realized future temperature used as input | Same reasoning | PASS (using historical avg) |
| ❌ No post-harvest variables in features | Yield, production, revenue are outcomes | PASS (not in feature set) |
| ❌ No target-derived variables fed as features | RYI/suitability label must not leak into X | MUST VERIFY during Phase 3 |
| ❌ No fertilizer application data treated as soil state | Kaggle NPK flaw | PASS (Kaggle rejected) |
| ❌ Train/test split respects temporal or geographic structure | Random split on panel data can leak | MUST ENFORCE during Phase 3 |

---

## 7. Missing-Data Strategy

| Situation | Fallback | Confidence Flag |
|---|---|---|
| **No Soil Health Card** | Use SoilGrids district-centroid estimates for N and pH | `ESTIMATED` |
| **No irrigation info** | Default to `Rainfed` (pessimistic safe assumption) | Documented |
| **No previous crop** | Ignored for V1 | N/A |
| **No District selected** | Hard failure — recommendation cannot proceed | Error returned |
| **SoilGrids unavailable for a location** | Use State-level median from SoilGrids | `ESTIMATED` |
| **ERA5 data gap for a district** | Use nearest-neighbor grid cell or State-level climate | `ESTIMATED` |

---

## 8. Water / Season Decision Rules

These are applied **post-prediction** by the Decision Engine, NOT learned by the ML model.

**Water Availability Rules:**
*   `IF Water == Rainfed AND crop IN {Sugarcane, Rice (Summer)} → SUPPRESS from recommendations`
*   Rationale: Deterministic agronomic safety. Sugarcane requires ~2000mm+ water; recommending it to a rainfed farmer is irresponsible regardless of ML probability.

**Season Constraint Rules:**
*   `IF Season == Rabi AND crop is exclusively Kharif → SUPPRESS`
*   `IF Season == Kharif AND crop is exclusively Rabi → SUPPRESS`
*   `IF crop IN {Mango, Grapes} → Always eligible (perennial, "Whole Year")`
*   Rationale: Biologically impossible crop-season combinations must be hard-filtered, not left to probabilistic ML approximation.

---

## 9. 20-Crop Data Reality Check

| Crop | APY Quality | Weather (ERA5) | Soil (SoilGrids) | Target Feasibility | MVP Status |
|---|---|---|---|---|---|
| Rice | 8,704 rows, 33 states | ✅ | ✅ | ✅ | 🟢 Ready |
| Wheat | 4,402 rows, 28 states | ✅ | ✅ | ✅ | 🟢 Ready |
| Maize | 8,191 rows, 31 states | ✅ | ✅ | ✅ | 🟢 Ready |
| Soybean | 1,792 rows, 20 states | ✅ | ✅ | ✅ | 🟢 Ready |
| Cotton | 2,504 rows, 23 states | ✅ | ✅ | ✅ | 🟢 Ready |
| Sugarcane | 4,451 rows, 31 states | ✅ | ✅ | ✅ | 🟢 Ready |
| Chickpea | 4,085 rows, 23 states | ✅ | ✅ | ✅ | 🟢 Ready |
| Pigeon Pea | 4,229 rows, 26 states | ✅ | ✅ | ✅ | 🟢 Ready |
| Groundnut | 5,047 rows, 26 states | ✅ | ✅ | ✅ | 🟢 Ready |
| Sorghum | 3,709 rows, 20 states | ✅ | ✅ | ✅ | 🟢 Ready |
| Pearl Millet | 2,837 rows, 19 states | ✅ | ✅ | ✅ | 🟢 Ready |
| Green Gram | 6,365 rows, 25 states | ✅ | ✅ | ✅ | 🟢 Ready |
| Black Gram | 5,971 rows, 26 states | ✅ | ✅ | ✅ | 🟢 Ready |
| Mustard | 4,289 rows, 27 states | ✅ | ✅ | ✅ | 🟢 Ready |
| Onion | 4,161 rows, 20 states | ✅ | ✅ | ✅ | 🟢 Ready |
| Potato | 4,116 rows, 25 states | ✅ | ✅ | ✅ | 🟢 Ready |
| Banana | 1,874 rows, 18 states | ✅ | ✅ | ✅ | 🟢 Ready |
| **Tomato** | **78 rows, 1 state** | ✅ | ✅ | ⚠️ Sparse | 🟡 Limited — seasonal data incomplete; if annual NHB data is used, season is mapped to "Whole Year" and this limitation is documented |
| **Mango** | **88 rows, 4 states** | ✅ | ✅ | ⚠️ Sparse | 🟡 Limited — perennial, "Whole Year" mapping is agronomically valid |
| **Grapes** | **12 rows, 1 state** | ✅ | ✅ | ⚠️ Sparse | 🟡 Limited — perennial, "Whole Year" mapping is agronomically valid; extreme geographic bias (likely only Maharashtra) |

**Honest limitation:** Tomato, Mango, and Grapes are included in the 20-crop V1 requirement. The model will attempt to learn their patterns, but predictions for these 3 crops will have lower confidence and narrower geographic validity than the 17 field crops. This is documented, not hidden.

---

## 10. Proposed Minimum ML Feature Matrix

For every training observation (one row = one District × Crop × Season × Year combination):

```
X = [District_encoded, Season_encoded, Hist_Rainfall_mm, Hist_Temperature_C, Soil_N, Soil_pH]
y = Crop label (or RYI-derived suitability label — PROVISIONAL)
```

**Encoding notes:**
*   `District`: Label-encoded or target-encoded integer. (High cardinality — ~600 districts. Target encoding or frequency encoding preferred over one-hot to avoid matrix explosion.)
*   `Season`: One-hot or ordinal (4 categories).
*   All numeric features: Standardized or min-max scaled.

---

## 11. Data Confidence Strategy

Every prediction response must include a `data_confidence` field:

| Level | Meaning | When Applied |
|---|---|---|
| `MEASURED` | Farmer provided Soil Health Card values | Soil inputs are from SHC |
| `ESTIMATED` | System used regional defaults | No SHC; SoilGrids/defaults used |
| `PARTIAL` | Some inputs measured, some estimated | Mixed provenance |

This is a metadata flag on the API response. It does NOT affect the ML model itself (the model treats all soil values identically). It informs the farmer/UI about how much to trust the result.

---

## 12. Recommended Model 1 Output Structure

```json
{
  "recommendations": [
    {"crop": "Soybean", "rank": 1, "suitability_score": 0.91},
    {"crop": "Maize",   "rank": 2, "suitability_score": 0.84},
    {"crop": "Cotton",  "rank": 3, "suitability_score": 0.72}
  ],
  "data_confidence": "ESTIMATED",
  "season": "Kharif",
  "district": "Nashik",
  "limitations": [
    "Soil values estimated from regional defaults"
  ]
}
```

*   `suitability_score` is NOT a calibrated probability. It is a model-derived ranking score (e.g., `predict_proba` output or normalized RYI). Confidence calibration is a V2 enhancement.
*   Top-K: Return at least **Top-3** recommendations. Top-5 is acceptable.
*   Decision Engine filters are applied before this output is returned (water-intensive crops removed if Rainfed, biologically impossible season-crop combos removed).

---

## 13. Open Issues That MUST Be Resolved Before Training

| Issue | Blocking? | Resolution Path |
|---|---|---|
| RYI formula finalization | Yes | Must define exact RYI computation (median baseline, normalization) during Phase 3 data assembly. Area Allocation Frequency retained as comparison baseline. |
| District encoding strategy | Yes | Must decide between label encoding, target encoding, or frequency encoding for ~600 district categories. |
| ERA5 data download and zonal aggregation | Yes | Must download ERA5 monthly means for India (2005–2015), aggregate to district polygons using zonal statistics. |
| SoilGrids GeoTIFF extraction | Partial | Must download relevant SoilGrids layers (N, pH) and extract district-centroid values. P and K may be deferred if no reliable source found. |
| Train/test split strategy | Yes | Must avoid naive random split on panel data. Geographic or temporal holdout required. |
| Tomato/Mango/Grapes target label | Partial | These crops have <100 observations. Model will include them but predictions will be lower confidence. |

---

# PHASE 2 FINAL RECOMMENDATION

**Farmer Inputs:**
1. District (REQUIRED)
2. Season (REQUIRED)
3. Water Availability: Irrigated / Rainfed (REQUIRED)
4. Soil Health Card: N, pH (OPTIONAL)

**Derived:**
1. Historical Seasonal Rainfall (ERA5 → district zonal mean, 2005–2015)
2. Historical Seasonal Temperature (ERA5 → district zonal mean, 2005–2015)
3. Regional Soil N, pH (SoilGrids → district centroid, when SHC unavailable)

**External:**
1. UPAg APY 2005–2015 (target data)
2. ERA5 monthly reanalysis (climate features)
3. ISRIC SoilGrids v2 (soil features)
4. India district shapefile (spatial join)

**ML Features:**
1. `District` (encoded)
2. `Season` (encoded)
3. `Hist_Rainfall` (mm)
4. `Hist_Temperature` (°C)
5. `Soil_N` (measured or estimated)
6. `Soil_pH` (measured or estimated)

**Decision Rules (post-prediction):**
1. Water constraint: Suppress water-intensive crops for Rainfed farmers.
2. Season constraint: Suppress biologically impossible crop-season combinations.

**Target:**
RYI — PROVISIONAL. Hierarchical fallback (District → State median) proven mathematically feasible. Scientific validation pending Phase 3 experimental comparison against Area Allocation Frequency baseline.

**Expected MVP Goal:**
> 70% validation performance

**Training Status:**
NOT STARTED
