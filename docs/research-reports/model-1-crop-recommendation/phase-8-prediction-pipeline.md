# Phase 8 — Prediction Pipeline & API Inference Contract

**Date:** 2026-10-05  
**Phase Status:** COMPLETE  
**Mode:** MVP — Validation >70%, end-to-end pipeline, API-ready  
**Branch:** `research-reports`  

---

## 1. Objective

Convert the successfully validated Model 1 (XGBoost v2) into a robust, production-style inference pipeline. The architecture must explicitly separate Machine Learning (which provides historical suitability scores) from the Decision Engine (which filters crops based on farmer-specific and agronomic constraints).

## 2. Model Artifact & Setup

The `predict.py` script cleanly wraps the Phase 7 artifacts:
*   **Model:** `models/crop_recommendation/crop_recommendation_mvp_v2.pkl`
*   **Preprocessing:** `models/crop_recommendation/preprocessing_mvp_v2.pkl`
*   **Metadata:** `models/crop_recommendation/metadata_mvp_v2.json`

## 3. Input Contract & Validation

The official pipeline exposes the function:
```python
def recommend_crops(district: str, season: str, water_availability: str, top_k: int = 5)
```

**Validation Rules:**
*   `District`: Must exist in the model's known vocabulary.
*   `Season`: Must be exactly one of `['Kharif', 'Rabi', 'Summer', 'Whole Year']`.
*   `Water Availability`: Must be exactly one of `['Low', 'Medium', 'High']`.
*   `Top_k`: Must be an integer between 1 and 20.

*Invalid inputs immediately return a clean JSON object with `"status": "ERROR"` and a descriptive reason, preventing fatal tracebacks.*

## 4. Pipeline Architecture (Candidate Generation & Prediction)

1.  **Candidate Generation:** For a given `(District, Season)`, the system generates exactly 20 candidate rows, one for each KisanCare V1 crop.
2.  **ML Inference:** The XGBoost model independently scores each of the 20 candidates, producing a `predicted_area_frequency`.
3.  **Ranking:** The 20 candidates are sorted in descending order by their ML score.

## 5. Decision Engine Filtering

After the ML model ranks the candidates purely by historical suitability, the Decision Engine applies two deterministic filters:

*   **Season Filter:** Hard constraints on crops that cannot grow outside specific seasons (e.g., Wheat is strictly `Rabi`; Mango, Grapes, Banana are strictly `Whole Year`). Ambiguous crops are passed through safely.
*   **Water Filter:** If the user reports `Low` water availability, inherently high-water crops (Sugarcane, Rice, Banana) are forcefully excluded from the final recommendations.

Filtered crops are retained in a separate `filtered_candidates` array in the JSON response to provide transparency and explainability to the downstream UI.

## 6. Output Contract

The API-ready JSON response follows a strict, stable schema:

```json
{
  "model_version": "crop-recommendation-mvp-v2",
  "district": "KOLHAPUR",
  "season": "Whole Year",
  "water_availability": "Low",
  "status": "SUCCESS",
  "recommendations": [
    {
      "crop": "Mango",
      "predicted_area_frequency": 0.2614,
      "rank": 1
    }
  ],
  "filtered_candidates": [
    {
      "crop": "Sugarcane",
      "model_score": 0.9847,
      "eligible": false,
      "filter_reason": "High water requirement crop excluded in Low water condition"
    }
  ],
  "data_source": "APY_2005_2015",
  "score_interpretation": "Predicted historical area-allocation suitability score",
  "latency_ms": 9.01
}
```
*Note: We intentionally do not frame the output score as a "probability". It is accurately labeled as a predicted Area-Allocation Suitability Score.*

## 7. Performance & Latency

A 10-case test suite was run to evaluate software determinism, edge cases, and latency.
*   **Determinism:** Passes. Identical inputs yield strictly identical rankings and scores.
*   **Average Prediction Latency:** **~13.4 ms** per complete pipeline execution.
*   **Scalability:** At <15ms per request, the pipeline is highly suitable for synchronous interactive UI calls.

## 8. Known Limitations & Future Integration

*   The ML model currently relies solely on categorical geography and time. It cannot natively adjust recommendations based on a changing climate.
*   The Decision Engine rules are currently hardcoded in Python. For a larger V2 system, these should be externalized to a rules-engine database.
*   **Model 2 Integration:** The `recommendations` array exposes the string `crop` name and integer `rank`. This output format is fully ready to be pipelined directly into downstream systems (Yield prediction, Risk analysis).

---

# PHASE 8 FINAL STATUS

*   **Prediction Function:** READY
*   **Input Validation:** PASS
*   **Candidate Generation:** PASS
*   **Top-K Ranking:** PASS
*   **Season Filtering:** PASS
*   **Water Filtering:** PASS
*   **Output Contract:** READY
*   **Model 2 Integration:** READY
*   **Determinism:** PASS
*   **Automated Tests:** PASS
*   **Average Latency:** 13.38 ms
*   **Model Version:** crop-recommendation-mvp-v2

**Final Status:** ✅ MODEL 1 INFERENCE PIPELINE READY
