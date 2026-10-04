# 02 — GitHub Repository Research: Alternative Crop Recommendation Models

**Date:** 2026-10-04  
**Task:** Find and compare 5 additional existing GitHub repositories/models for Crop Recommendation to identify the best foundation covering the V1 priority 20 crops.  
**Author:** Antigravity (AI-assisted research)  
**Branch:** `research-reports`  
**Constraint:** Do NOT build from scratch. Do NOT train yet. Do NOT modify production code. Do NOT delete any crop classes.

---

## Executive Summary & Core Finding

A deep search of the open-source GitHub ecosystem reveals a structural monoculture: **almost all popular crop recommendation repositories are built on the exact same 22-crop dataset** (originally sourced from Kaggle by Atharva Ingle, or its synthetic derivatives). 

As a result, no single open-source repository out-of-the-box supports the complete set of KisanCare's 20 priority crops. The standard open-source baseline covers exactly **10 out of 20** priority crops, leaving critical Indian staples like Wheat, Sugarcane, Potato, and Tomato entirely missing.

## A. Top 5 Repositories Investigated

| Repository | License | Dataset Size | V1 Crops Covered | V1 Coverage % | Extra Crops | Features | Pretrained Model | Accuracy | API | Integration Difficulty |
|---|---|---|---|---|---|---|---|---|---|---|
| **`djdhairya/Crop-Recommendation`** | MIT | 2,200 | 10 | 50% | 12 | 7 (NPK, env) | ✅ Yes | 99.32% (Verified) | ✅ Flask | Low |
| **`anant13sharma/A-Machine-...`** | MIT | 69,718 | 10 | 50% | 12 | 12 (NPK, micro, env) | ❌ No | ~99% (Repo-reported) | ❌ No | Medium |
| **`Gladiator07/Harvestify`** | MIT | 2,200 | 10 | 50% | 12 | 7 (NPK, env) | ✅ Yes | 99% (Repo-reported) | ✅ Flask | Low |
| **`Dhotre12/Crop-Recommenda...`** | MIT | 2,200 | 10 | 50% | 12 | 7 (NPK, env) | ✅ Yes (PyTorch) | Unknown | ✅ Flask | High (CNN logic) |
| **`AhqafCoder/AICropRecomme...`** | MIT | Unknown | ~12 | ~60% | Unknown | Multiple (LightGBM) | ❌ No (Data missing) | Unknown | ✅ FastAPI | Very High |

## B. 20-Crop Coverage Matrix

| Crop | djdhairya | anant13sharma | Harvestify | Dhotre12 | AhqafCoder |
|------|-----------|---------------|------------|----------|------------|
| 1. Rice | ✅ | ✅ | ✅ | ✅ | ✅ |
| 2. Wheat | ❌ | ❌ | ❌ | ❌ | ❌ |
| 3. Maize | ✅ | ✅ | ✅ | ✅ | ✅ |
| 4. Soybean | ❌ | ❌ | ❌ | ❌ | ⚠️ (Claimed) |
| 5. Cotton | ✅ | ✅ | ✅ | ✅ | ✅ |
| 6. Sugarcane | ❌ | ❌ | ❌ | ❌ | ❌ |
| 7. Chickpea | ✅ | ✅ | ✅ | ✅ | ✅ |
| 8. Pigeon Pea (Tur) | ✅ | ✅ | ✅ | ✅ | ✅ |
| 9. Groundnut | ❌ | ❌ | ❌ | ❌ | ⚠️ (Claimed) |
| 10. Sorghum (Jowar) | ❌ | ❌ | ❌ | ❌ | ❌ |
| 11. Pearl Millet (Bajra)| ❌ | ❌ | ❌ | ❌ | ❌ |
| 12. Green Gram (Moong)| ✅ | ✅ | ✅ | ✅ | ✅ |
| 13. Black Gram (Urad)| ✅ | ✅ | ✅ | ✅ | ✅ |
| 14. Mustard | ❌ | ❌ | ❌ | ❌ | ❌ |
| 15. Onion | ❌ | ❌ | ❌ | ❌ | ❌ |
| 16. Potato | ❌ | ❌ | ❌ | ❌ | ❌ |
| 17. Tomato | ❌ | ❌ | ❌ | ❌ | ❌ |
| 18. Banana | ✅ | ✅ | ✅ | ✅ | ✅ |
| 19. Mango | ✅ | ✅ | ✅ | ✅ | ✅ |
| 20. Grapes | ✅ | ✅ | ✅ | ✅ | ✅ |

**Missing V1 Priority Crops (Across almost all repos):** Wheat, Sugarcane, Sorghum, Pearl Millet, Mustard, Onion, Potato, Tomato.

## C. Additional / Future Crop List (To be Preserved)

The standard Kaggle dataset used by Candidates 1, 2, 3, and 4 includes 12 additional crops not currently in KisanCare's V1 priority list. 
**Per strict requirements, these must NOT be deleted.**

1. Apple
2. Coconut
3. Coffee
4. Jute
5. Kidney Beans
6. Lentil
7. Moth Beans
8. Muskmelon
9. Orange
10. Papaya
11. Pomegranate
12. Watermelon

## D. Detailed Comparison

### Candidate 1: `djdhairya/Crop-Recommendation`
- **Pros:** Extremely clean code, ready-to-use pretrained `.pkl` files (Random Forest, scalers), verified 99.32% accuracy. Easy to adapt to FastAPI.
- **Cons:** Only 2,200 rows; limited to the standard 10/20 V1 crops.

### Candidate 2: `anant13sharma/A-Machine-Learning-Based-Crop-Recommendation-System`
- **Pros:** Massive dataset (69,718 rows), includes 5 extra micronutrient features (Fe, Mn, S, Mg, C) making it highly robust.
- **Cons:** No pretrained model provided (must run notebooks); synthetic data expansion needs validation.

### Candidate 3: `Gladiator07/Harvestify`
- **Pros:** The most "famous" repository (1.2k+ stars). Includes a full web UI and adjacent models (fertilizer, disease).
- **Cons:** Uses the exact same underlying 2,200-row dataset as Candidate 1 but comes with a lot of frontend bloat that KisanCare does not need.

### Candidate 4: `Dhotre12/Crop-Recommendation-dataset---India`
- **Pros:** Attempts to use Deep Learning (PyTorch CNN) instead of standard ML.
- **Cons:** CNNs are overkill and poorly suited for 7-feature tabular data. Weights are heavy (11MB) and integration is unnecessarily complex.

### Candidate 5: `AhqafCoder/AICropRecommendation`
- **Pros:** Highly advanced ecosystem (LightGBM, FastAPI). Claims support for Groundnut and Soybean.
- **Cons:** The raw CSV datasets are excluded from the repository. The models are not pre-packaged for direct copy-pasting, making it a very high-effort integration.

## E. Top 3 Candidates Ranked

1. **`djdhairya/Crop-Recommendation`** (Best immediate drop-in replacement)
2. **`anant13sharma/A-Machine-Learning-Based-Crop-Recommendation-System`** (Best data foundation for future retraining)
3. **`Gladiator07/Harvestify`** (Good reference for multi-model architecture, though too bloated for direct Model 1 use)

## F. Recommended Primary Repository

**`djdhairya/Crop-Recommendation`** remains the absolute best primary foundation for KisanCare Model 1. 

**Reasoning:** It has the lowest integration difficulty, verified accuracy, and provides immediately usable `.pkl` files. It perfectly covers 10 of our V1 priority crops and provides a solid fallback of 12 extra crops. Because the open-source community lacks a unified repository containing all 20 of our crops, choosing the cleanest baseline is the optimal engineering decision.

## G. Recommended Backup Repository

**`anant13sharma/A-Machine-Learning-Based-Crop-Recommendation-System`**

**Reasoning:** If the 2,200-row dataset proves too small during field testing, this repo offers a 69K-row drop-in replacement dataset with identical base crops, plus micronutrients.

## H. Why the Winner is Better

`djdhairya` wins not because it has a better dataset than `Harvestify` (they share the same data), but because of **architectural cleanliness**. It provides exactly what KisanCare needs (a Random Forest `.pkl` and scalers) without forcing us to untangle heavy HTML templates (like Harvestify) or complex Deep Learning tensors (like Dhotre12).

## I. What KisanCare Will Need to Add / Adapt

1. **API Migration:** Convert the provided Flask app to FastAPI to match KisanCare standards.
2. **Probability Logic:** Implement `predict_proba()` to enable the Top-3 / Top-5 crop recommendations required by the ML contract.
3. **Phase 2 Data Merging (Future Task):** Since 10 priority crops (Wheat, Sugarcane, etc.) are missing from the global open-source baseline, KisanCare will eventually need to source a secondary dataset for these specific crops and retrain the model.

## J. Risks and Limitations

1. **V1 Coverage Gap:** 50% of the priority crops are unrepresented in the current model. The system will not be able to recommend Wheat or Sugarcane until a custom dataset merge occurs in a future sprint.
2. **Overfitting Risk:** The 99.32% accuracy is based on a highly balanced, synthetic-like Kaggle dataset. Real-world Indian soil data is noisier and will likely yield lower confidence scores.
