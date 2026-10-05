# KisanCare Model 1 — PHASE 1 AUDIT REPORT

## 1. Problem Definition
**Objective:** Given a farm's soil, climate, location, season and available farming constraints, rank the most suitable crops for that farm.
**Constraint:** Do NOT permanently lock to 20 or 22 crops. The system must support adding new crops dynamically through retraining and catalogue updates. The model acts as the starting point of the Farm Digital Twin loop (predict → simulate → decide).

## 2. Repository Audit

### Primary: Sheshank2609/crop-recommendation-system
* **Type:** Gradio web application.
* **Architecture:** Combines a traditional ML model (NPK + Climate) with a Statistical Regional Scoring model.
* **Files:** `app.py`, `model1_npk.pkl` (RF Model), `model2_full_scored.csv` (Regional Data).
* **Finding:** It does not train a single massive ML model. It uses the standard Kaggle dataset for Model 1, and a custom statistical CSV for Model 2. 

### Secondary: anant13sharma/A-Machine-Learning-Based-Crop-Recommendation-System
* **Type:** Jupyter Notebook analysis.
* **Architecture:** Random Forest / Decision Tree.
* **Finding:** Claims 69,718 rows. However, an audit reveals it is merely a synthetically exploded version of the Kaggle dataset.

### Backup: KRUTHIKTR/Crop-Recommendation-System-Using-Machine-Learning
* **Type:** Standard Kaggle implementation.
* **Finding:** Uses the canonical 2,200 sample dataset.

## 3. Dataset Audit & Data Quality

### Dataset A: Anant (69K)
* **Rows:** 69,718 | **Cols:** 14
* **Distribution:** Exactly 3,169 samples for every single one of the 22 crops. Perfectly balanced (Imbalance Ratio = 1.0).
* **Quality:** `temperature`, `humidity`, `rainfall` have nearly 69,718 unique floating-point values, while base ranges exactly match the Kruthik dataset. 
* **Verdict:** 100% synthetically generated (likely SMOTE/interpolation) from the base 2,200 dataset. Massive data leakage.

### Dataset B: Kruthik (2.2K)
* **Rows:** 2,200 | **Cols:** 8
* **Distribution:** Exactly 100 samples per crop for 22 crops.
* **Quality:** No missing values. Ranges: N(0-140), pH(3.5-9.9). Widely known to be a synthetic/curated Kaggle dataset, not raw field data.

### Dataset C: Sheshank Regional (Model 2 CSV)
* **Rows:** 1,603 | **Cols:** 15
* **Distribution:** Highly imbalanced (e.g., Maize=96, Tobacco=2). Ratio = 48.0.
* **Features:** Lacks N, P, K, pH entirely. Only contains categorical historical data (Yield, Frequency).
* **Verdict:** Real historical frequency data. 

## 4. Leakage Audit
* **Anant:** Extreme leakage. The synthetic generation created tightly clustered duplicated feature spaces. A random train/test split on this dataset guarantees test leakage.
* **Kruthik:** The 99% accuracy is a result of perfectly balanced, distinct synthetic classes. 

## 5. Sheshank Regional Layer Audit
* **Mechanism:** It is NOT a machine learning model. It is a hardcoded weighted statistical formula.
* **Formula:** `0.35 * Frequency + 0.25 * Historical + 0.20 * Yield + 0.10 * Dominance + 0.10 * Recency`
* **Integration:** `app.py` computes `Final = w1 * M1_prob + w2 * M2_score` (default 60/40 split). 
* **Verdict:** Clever heuristic, but limits ML feature interaction. 

## 6. Repository Comparison

| Component | Sheshank | 69K Repo (Anant) | KRUTHIKTR |
| :--- | :--- | :--- | :--- |
| **Dataset size** | 1,603 (Regional) + 2.2K | 69,718 | 2,200 |
| **Crops** | 33 (Regional), 22 (ML) | 22 | 22 |
| **Features** | 15 (Regional), 7 (ML) | 13 | 7 |
| **Soil data** | None (in regional) | N,P,K,pH,Fe,Mn,Mg,S,C | N,P,K,pH |
| **Climate data** | None (in regional) | Temp, Hum, Rain | Temp, Hum, Rain |
| **Maharashtra data**| YES | NO | NO |
| **Model** | Ensembled Gradio | RF / DT | RF |
| **Data quality** | Real (Regional) | Synthetic explosion | Synthetic |
| **Leakage risk** | Low | EXTREME | High |

## 7. FINAL DECISIONS

* **Primary ML Model (Kaggle RF):** **REJECT** for production (too synthetic), **KEEP** only as baseline.
* **Anant 69K Dataset:** **REJECT** (Severe data leakage and synthetic noise).
* **Kruthik 2.2K Dataset:** **MODIFY** (Use for basic pipeline testing only).
* **Sheshank Regional Layer:** **MODIFY** (The district/season logic is highly useful, but should be converted into a true ML feature rather than a separate statistical formula).
* **Deployment Code:** **REJECT/MODIFY** (Gradio is for prototyping; we need FastAPI).

## 8. KisanCare Crop Strategy
* **Initial baseline:** 22 crops.
* **Architecture Rule:** Support data-driven crops. New crop data → Standardize → Add crop_id → Retrain/fine-tune → Validate new crop → Regression test existing crops → Model version → Deploy.

## 9. Required Input Schema
* **Existing/Usable:** N, P, K, pH, temperature, humidity, rainfall, district, season.
* **Useful/Unavailable:** organic carbon, soil type, moisture.
* **Future:** irrigation, area, previous crop.

## 10. Proposed Phase 1 Architecture
Farm Data → Data Validation → Soil + Climate Feature Processing → **Crop Recommendation ML** (re-trained on merged/real data) → **Agronomic Constraints** (Decision Engine) → Crop Suitability Ranking → Top-N Recommendations.

## 11. Risks
1. Over-reliance on the 2,200 synthetic Kaggle dataset for soil features.
2. The 99% accuracy is a mirage caused by dataset synthesis; real-world accuracy will be much lower.

## 12. Phase 2 Prerequisites
1. Discard the Anant 69K dataset entirely.
2. Acquire real APY (Agricultural Production Yield) data to replace the statistical regional CSV with a true regressor model.

## 13. Final Phase 1 Verdict
**COMPLETE.** We understand exactly what the three repositories contain. We will not use the 69K dataset. We will pivot to using real APY data combined with district/season features for Phase 2.
