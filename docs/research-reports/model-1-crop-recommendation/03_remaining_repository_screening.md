# 03 — Remaining Repository Screening & Final Hunt Conclusion

**Date:** 2026-10-04  
**Task:** Final screening of remaining promising repositories to determine if any break the 10/20 crop coverage baseline.  
**Author:** Antigravity (AI-assisted research)  
**Branch:** `research-reports`  

---

## Executive Summary & Decision

After deeply inspecting the final remaining GitHub candidates (`Harvestify`, `AgriSens`, `Dhotre12`, `AhqafCoder`, etc.), **the conclusion is definitive: no existing open-source repository offers materially better coverage than the current baseline (10 out of 20 V1 Priority Crops).**

The open-source ecosystem is heavily fragmented across hundreds of repositories, but nearly **all of them are built on the exact same underlying 2,200-row Kaggle dataset** (or synthetically expanded derivatives).

**Decision Reached:** We have hit the ceiling of open-source crop recommendation foundations. Continuing to hunt for repositories is no longer productive. We must accept `djdhairya/Crop-Recommendation` as the baseline Model 1 and move to the **Missing-Crop Strategy** (custom data sourcing and merging) for Phase 2.

---

## Detailed Screening of Remaining Candidates

### 1. `Gladiator07/Harvestify`
- **Dataset:** `Data-processed/crop_recommendation.csv` (2,200 rows)
- **Model:** Random Forest
- **Crop Classes (22):** Identical to the standard Kaggle dataset.
- **Priority V1 Coverage:** 10/20
- **Missing Priority Crops:** Wheat, Soybean, Sugarcane, Groundnut, Sorghum, Pearl Millet, Mustard, Onion, Potato, Tomato.
- **Evaluation:** High-quality code and UI, but offers absolutely no data advantage over `djdhairya`.

### 2. `Dhotre12/Crop-Recommendation-dataset---India`
- **Dataset:** `Crop_recommendation.csv` (2,200 rows)
- **Model:** PyTorch CNN (`best_model_india_CNN.pth`)
- **Crop Classes (22):** Identical to the standard Kaggle dataset.
- **Priority V1 Coverage:** 10/20
- **Evaluation:** Over-engineered (uses a heavy 11MB CNN for simple 7-feature tabular data). Same exact crops. Unusable for lightweight production.

### 3. `ravikant-diwakar/AgriSens`
- **Dataset:** `Datasets/Crop_recommendation.csv` (2,200 rows)
- **Model:** Random Forest
- **Crop Classes (22):** Identical to the standard Kaggle dataset.
- **Priority V1 Coverage:** 10/20
- **Evaluation:** Another clone of the same data foundation. No advantage.

### 4. `AhqafCoder/AICropRecommendation`
- **Dataset:** Not included in the repository / Mock data used.
- **Model:** Claims LightGBM, but the backend implementation (`backend/app.py`) reveals a heavily mocked structure.
- **Crop Classes:** The `/predict` API endpoint returns a hardcoded `"recommended_crop": "rice"`. Other endpoints use dummy lists containing Wheat, Sugarcane, Cotton.
- **Priority V1 Coverage:** 0/20 (No real trained model provided).
- **Evaluation:** It is a front-end/marketplace template, not a functioning ML repository with an exploitable dataset. The cloning issues stem from unoptimized assets, but the ML core is hollow.

### 5. `SiddhiThorat16` & `smaranjitghose` (Smart-Farming-System)
- **Dataset / Crops:** Both utilize the same Kaggle standard.
- **Evaluation:** Confirms the monoculture finding.

---

## Final Comparison Table

| Repository | V1 Crops Covered | Model Approach | Dataset Size | Provenance | Provides Better Data? | Integration Difficulty |
|---|---|---|---|---|---|---|
| `djdhairya` (Current Baseline) | **10** / 20 | Random Forest (.pkl) | 2,200 | Kaggle | **N/A** | Low |
| `Harvestify` | **10** / 20 | Random Forest (.pkl) | 2,200 | Kaggle | ❌ No | Medium (Bloated UI) |
| `Dhotre12` | **10** / 20 | CNN (.pth) | 2,200 | Kaggle | ❌ No | High (Over-engineered) |
| `AgriSens` | **10** / 20 | Random Forest | 2,200 | Kaggle | ❌ No | Medium |
| `AhqafCoder` | **0** / 20 (Mock) | Mock JSON API | N/A | Dummy Data | ❌ No | Very High |

---

## Final Recommendation: Stop Hunting

As strictly defined by the decision rule:
> *"If no repository is materially better → keep djdhairya as the baseline and move to the missing-crop strategy."*

**We recommend halting all repository hunting.**

1. **Phase 1 Action:** Proceed with implementing `djdhairya/Crop-Recommendation` as the foundation for the first release. It cleanly supports 10 priority crops + 12 extra crops.
2. **Phase 2 Action:** To support Wheat, Soybean, Sugarcane, Potato, etc., KisanCare must shift focus from *finding* an existing repository to *building* a custom dataset. This will require merging external agricultural datasets (e.g., FAO, government portals) and re-training the baseline model.

*No production code was modified during this screening.*
