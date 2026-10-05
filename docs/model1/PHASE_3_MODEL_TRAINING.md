# PHASE 3: MODEL TRAINING & EVALUATION REPORT

## 1. Objective
Build a robust, auditable baseline Crop Recommendation model for KisanCare that accepts `N`, `P`, `K`, `temperature`, `humidity`, `pH`, and `rainfall` and returns ranked crop recommendations.

## 2. Dataset
* **Source:** Kaggle Canonical Dataset (Fallback Baseline)
* **Status:** Cleaned (`Crop_recommendation_cleaned.csv`)
* **Samples:** 2,200
* **Classes:** 22 crops (perfectly balanced at 100 samples each)
* **Missing Values:** 0
* **Duplicates:** 0

## 3. Features
* **Predictors:** `N`, `P`, `K`, `temperature`, `humidity`, `pH`, `rainfall`
* **Target:** `label` (Crop name)

## 4. Preprocessing
* Target labels were encoded using `LabelEncoder`.
* Continuous features were scaled using `StandardScaler`.
* Note: Prior to this script, the raw floating-point features were rounded to 2 decimal places to remove synthetic algorithmic uniqueness.

## 5. Train/Test Methodology
* **Split:** 80% Train (1,760 samples), 20% Test (440 samples).
* **Stratification:** Stratified by crop label to ensure proportional representation.
* **Seed:** Fixed `random_state=42` for reproducibility.
* **Leakage Prevention:** `StandardScaler` was fit ONLY on the training data.

## 6. Models Evaluated
1. Random Forest Classifier
2. Decision Tree Classifier
3. Logistic Regression
4. K-Nearest Neighbors (KNN)
5. XGBoost Classifier

## 7. Metrics & Performance
| Model | Accuracy | Macro F1 | Weighted F1 | Top-3 Acc | Top-5 Acc | Train Time (s) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Random Forest** | **0.9954** | **0.9954** | **0.9954** | **1.000** | **1.000** | 3.20 |
| XGBoost | 0.9886 | 0.9885 | 0.9885 | 1.000 | 1.000 | 1.22 |
| KNN | 0.9795 | 0.9792 | 0.9792 | 0.997 | 1.000 | 0.12 |
| Decision Tree | 0.9795 | 0.9794 | 0.9794 | 0.979 | 0.979 | 1.84 |
| Logistic Reg | 0.9727 | 0.9724 | 0.9724 | 1.000 | 1.000 | 1.49 |

## 8. Cross-Validation Results (5-Fold Stratified on Train Set)
| Model | Mean Macro F1 | Std Dev |
| :--- | :--- | :--- |
| **Random Forest** | **0.9937** | **0.0049** |
| XGBoost | 0.9903 | 0.0034 |
| Decision Tree | 0.9846 | 0.0066 |
| Logistic Reg | 0.9678 | 0.0067 |
| KNN | 0.9655 | 0.0127 |

## 9. Feature Importance (Random Forest)
1. **Rainfall:** 22.86%
2. **Humidity:** 22.42%
3. **K (Potassium):** 17.53%
4. **P (Phosphorus):** 15.11%
5. **N (Nitrogen):** 9.81%
6. **Temperature:** 7.37%
7. **pH:** 4.87%

## 10. Final Model Selection
**Selected Model:** Random Forest Classifier
**Rationale:** It achieved the highest generalization performance across all metrics (99.5% accuracy, 99.3% CV mean), flawless Top-3/Top-5 accuracy (100%), and high stability (std dev 0.004). 

## 11. Ranked Recommendations
The Random Forest model utilizes `predict_proba()` to output class probabilities. This directly supports KisanCare's requirement to output Top-N ranked recommendations with associated model scores.

## 12. Limitations
* **Synthetic Performance:** 99.5% accuracy is a direct result of the perfectly balanced, synthetically interpolated nature of the Kaggle dataset. It will not achieve 99.5% on real field data.
* **Geographic Vacuum:** The model has no concept of state, district, or season.

## 13. Next Improvements
* **Phase 4 Integration:** Route this model's probability output into the `CropDecisionEngine` and Regional Statistical model developed in Phase 1 to ground the synthetic predictions in real-world geographic constraints.
