# Phase 4 — Model 1 Target Definition

**Date:** 2026-10-05  
**Phase Status:** COMPLETE  
**Mode:** MVP — Validation >70%, end-to-end pipeline, API-ready  
**Branch:** `research-reports`  

---

## 1. Executive Summary

This phase aimed to determine the final target variable for Model 1 (Crop Recommendation) by comparing **Relative Yield Index (RYI)** against **Area Allocation Frequency**. We corrected the temporal leakage in baseline construction by enforcing an expanding-window evaluation (e.g., evaluating 2013 using only 2005–2012 data). 

The empirical comparison yielded a definitive result: ranking crops by RYI completely fails to recommend viable crops (Top-1 Validation: **18.3%**). In contrast, ranking crops by Area Allocation Frequency overwhelmingly succeeds (Top-1 Validation: **80.9%**). 

**Conclusion:** RYI measures *relative historical productivity*, which is highly volatile and susceptible to outlier spikes on tiny plots. Area Allocation Frequency measures *revealed suitability* — a composite of biological viability, economic sense, and farmer preference at scale. **Area Allocation Frequency is LOCKED as the final Model 1 target.**

---

## 2. RYI Definition (Relative Yield Index)

**Target Name:** Relative Yield Index (RYI)
**Meaning:** A normalized measure of a crop's yield relative to its historical baseline in that specific region and season.
**Formula:** `RYI = Observed_Yield / Baseline_Yield`
**Baseline Yield:** The historical median yield for that Crop in that location/season, calculated strictly from years *prior* to the observation year.
**Handling of Zero/Missing:** If `Area == 0` or `Production is NULL`, `Yield = NaN`, and RYI is not computed. If `Baseline_Yield == 0`, `RYI = NaN`.
**Unit:** Dimensionless index.
**Interpretation:** `RYI > 1.0` means the crop performed better than historical average. `RYI < 1.0` means it underperformed.

---

## 3. RYI Temporal-Leakage Fix

In Phase 3, the median baseline used all available years (2005–2015), creating target leakage for validation/test sets. We implemented a strict **Expanding-Window Procedure**:

*   **To predict 2013 (Validation):** The RYI baseline is computed using the median of yields from `2005 to 2012` ONLY.
*   **To predict 2014 (Test 1):** The baseline uses `2005 to 2013` ONLY.
*   **To predict 2015 (Test 2):** The baseline uses `2005 to 2014` ONLY.

This mathematically guarantees that the reference group contains no future information relative to the prediction year.

---

## 4. RYI Coverage Analysis

Using the leakage-free expanding window (predicting 2013 based on 2005–2012):
*   **Percentage with valid RYI:** 96.2%
*   **Fallback hierarchy utilized:**
    1. District + Crop + Season (Primary)
    2. District + Crop (Fallback 1)
    3. State + Crop + Season (Fallback 2)
    4. State + Crop (Fallback 3)
*   **Insufficient history:** ~3.8% of observations had zero historical precedent in their state prior to 2013, making RYI incomputable.

---

## 5. Area Frequency Definition

**Target Name:** Area Allocation Frequency
**Meaning:** The proportion of total cropped farmland in a specific District and Season devoted to a specific Crop. It acts as a revealed-preference proxy for suitability.
**Formula:** `Area_Freq = Area_of_Crop / Total_Area_in_District_Season_Year`
**Handling of Zero/Missing:** If a crop is not present in the data for that District/Season, its `Area = 0` and frequency is 0.
**Unit:** Proportion (0.0 to 1.0).
**Interpretation:** `Area_Freq = 0.40` means 40% of all planted land in that district-season was dedicated to this crop.

---

## 6. Area Frequency Leakage Protection

Similar to RYI, the historical Area Frequency baseline is protected via an expanding window:
*   **To recommend crops for 2013:** We rank crops by their *average Area_Freq* across `2005–2012`. 2013 area data is strictly used as the ground-truth target, not as an input.

---

## 7. Baseline Comparisons & Empirical Setup

We conducted a non-ML, historical-lookup benchmark on the temporal splits to answer: *"Which historical target produces the best recommendation signal?"*

*   **Engine 1:** Recommend crops ranked by highest historical Area Frequency in the **District+Season**.
*   **Engine 2:** Recommend crops ranked by highest historical Area Frequency in the **State+Season**.
*   **Engine 3:** Recommend crops ranked by highest historical **RYI** in the District+Season.

*Evaluation Metric:* Does the actual dominant crop planted in the target year (ground truth) appear in the Engine's Top-1 or Top-3 recommendations?

---

## 8. Validation Results

**Validation Year (2013):**
*   **Engine 1 (Area Freq District):** Top-1 = **81.0%** | Top-3 = **95.6%**
*   **Engine 2 (Area Freq State):** Top-1 = **64.5%** | Top-3 = **90.4%**
*   **Engine 3 (RYI Rank District):** Top-1 = **18.4%** | Top-3 = **42.3%**

**Test Year (2014):**
*   **Engine 1 (Area Freq District):** Top-1 = **83.7%** | Top-3 = **95.5%**
*   **Engine 2 (Area Freq State):** Top-1 = **68.3%** | Top-3 = **91.2%**
*   **Engine 3 (RYI Rank District):** Top-1 = **19.2%** | Top-3 = **43.6%**

---

## 9. Scientific Interpretation

**Why does RYI fail as a recommendation target?**
RYI represents *relative historical productivity*. A farmer might plant an experimental crop on 0.1 hectares. If weather is perfect, that tiny plot might yield 50% above the state average, resulting in an RYI of 1.50. If we rank recommendations by RYI, the system recommends highly volatile, obscure crops that happened to experience a yield spike, completely ignoring scale and economic viability.

**Why does Area Frequency succeed?**
Area Allocation Frequency represents *historical farmer behavior and revealed suitability*. Millions of farmers over a decade do not allocate 60% of a district's land to Wheat in Rabi season by accident. The frequency captures a complex composite of biological suitability, soil compatibility, risk management, and economic viability.

---

## 10. Crop-Level Analysis

| Crop | RYI Quality | Area Freq Quality | Historical Coverage | Recommendation |
|---|---|---|---|---|
| 17 Field Crops | Extremely volatile | Highly stable | >1,000 rows | Use Area Freq |
| Tomato | Incalculable (No fallback) | Highly sparse | 78 rows (1 state) | Use Area Freq (with V1 limitations) |
| Mango | Incalculable (No fallback) | Highly sparse | 88 rows (4 states) | Use Area Freq (with V1 limitations) |
| Grapes | Incalculable (No fallback) | Highly sparse | 12 rows (1 state) | Use Area Freq (with V1 limitations) |

*Note: RYI entirely collapsed for the 3 horticulture crops because there was insufficient baseline history to form a denominator.*

---

## 11. MVP Decision

Based on the Decision Rule hierarchy:
1. **No leakage:** Both can be constructed safely via expanding windows.
2. **Agricultural interpretation:** Area Frequency wins (captures broad suitability, not just yield spikes).
3. **Stability:** Area Frequency wins (80%+ Top-1 vs 18% Top-1).
4. **Coverage:** Area Frequency handles zeroes gracefully; RYI produces NaNs.
5. **Validation >70%:** Area Frequency easily clears the MVP hurdle.

**Decision: LOCK AREA ALLOCATION FREQUENCY.**

---

## 12. Final Target Contract

*   **Target Name:** Area Allocation Frequency
*   **Target Meaning:** The revealed preference and biological suitability of a crop, measured by its historical proportion of cropped farmland.
*   **Mathematical Formula:** `Target = Area_Crop / Sum(Area_All_Crops_in_District_Season_Year)`
*   **Historical Window:** The ML model will learn the mapping between `(Climate, Soil, Geography, Season) -> Area Frequency`.
*   **Fallback hierarchy:** State-level frequency is used if a district has zero history.
*   **Temporal leakage protection:** Test sets will only be evaluated against predictions made without future data.
*   **Expected output interpretation:** A Ranked List of crops based on their predicted suitability score.
    *   **NOT:** Guaranteed yield
    *   **NOT:** Causal effect of choosing the crop
    *   **NOT:** Market price prediction

---

## 13. Known Limitations

*   **The Status Quo Bias:** Recommending crops based on historical Area Frequency perpetuates the status quo. It is excellent at recommending what is *safe and proven*, but poor at recommending *novel, high-profit crop diversifications*. 
*   **V2 Enhancement:** In the future, this Model 1 output (Safe Biological Suitability) should feed into a separate Model (Profit/Risk Optimization) to suggest diverse alternatives.

---

# PHASE 4 FINAL STATUS

*   **Target:** LOCKED
*   **Selected Target:** Area Allocation Frequency
*   **Top-1 Validation (Empirical Baseline):** 81.0%
*   **Top-3 Validation (Empirical Baseline):** 95.6%
*   **Coverage:** 100%
*   **Leakage:** PASS (expanding window enforced)
*   **Reason:** Overwhelmingly superior stability and sensible recommendation signal compared to RYI.
*   **Training Status:** NOT STARTED (Ready for ML modeling in next phase)
