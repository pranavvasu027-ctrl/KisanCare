# Phase 1 — Existing Model Audit

## 1. Repository
*   **Structure:** Standard monolithic structure containing `data/`, `model/`, `static/`, `template/`, `app.py`, `crop_recommendation.ipynb`, and `README.md`.
*   **README/Documentation:** Very basic. It provides run instructions but lacks any data dictionary, source provenance for the dataset, or scientific explanation of the agronomic principles used.

## 2. Dataset
*   **Source:** Not explicitly documented in the repo, but matches the widely used Kaggle "Crop Recommendation Dataset".
*   **File:** `data/Crop_recommendation.csv`
*   **Number of samples:** 2,200 rows.
*   **Number of crop classes:** 22.
*   **Exact crop labels/classes:** `rice`, `maize`, `chickpea`, `kidneybeans`, `pigeonpeas`, `mothbeans`, `mungbean`, `blackgram`, `lentil`, `pomegranate`, `banana`, `mango`, `grapes`, `watermelon`, `muskmelon`, `apple`, `orange`, `papaya`, `coconut`, `cotton`, `jute`, `coffee`.
*   **Balance:** Perfectly balanced (100 samples per class).

## 3. Features
Exactly 7 numeric input features:
1. `N` (Nitrogen)
2. `P` (Phosphorus)
3. `K` (Potassium)
4. `temperature`
5. `humidity`
6. `ph`
7. `rainfall`

## 4. Target
*   **Label:** `label` (String representing the crop name).

## 5. Preprocessing
*   **Missing-value handling:** None required in code, as the dataset natively has 0 missing values.
*   **Feature scaling/encoding:** The notebook applies both `MinMaxScaler()` and `StandardScaler()` sequentially to the same features. This is statistically redundant.
*   **Train/test split methodology:** Random split using `train_test_split` (80% train, 20% test, `random_state=42`). No geographic or temporal stratification since the dataset lacks those dimensions.

## 6. Model
*   **ML algorithm/model architecture:** Evaluated 10 baseline algorithms (Logistic Regression, Naive Bayes, SVC, KNN, Decision Tree, Random Forest, Bagging, Gradient Boosting, AdaBoost).
*   **Selected Model:** `RandomForestClassifier`.
*   **Hyperparameters:** Default scikit-learn parameters.

## 7. Evaluation
*   **Model evaluation metrics:** Evaluated using `accuracy_score`. Typically achieves 99%+ accuracy due to the highly synthetic/separable nature of the dataset.

## 8. Prediction Pipeline
*   **Existing pretrained files:** `modelrandclf.pkl`, `standscaler.pkl`, `minmaxscaler.pkl`.
*   **`predict()` implementation:** Inside `app.py`, the model takes a 1x7 numpy array, transforms it using the saved min-max and standard scalers sequentially, and calls `.predict()`.
*   **`predict_proba()` implementation:** NOT implemented in the repository's API. It only returns the top-1 absolute prediction.
*   **How confidence/probability is calculated:** It is not calculated.
*   **API implementation:** A monolithic Flask app (`app.py`) serving HTML directly.
*   **Expected input format:** `x-www-form-urlencoded` POST data from an HTML form.
*   **Expected output format:** A rendered HTML template string containing the result text.

## 9. Supported Crops
The repository supports 22 crops. However, mapping this to the **20 KisanCare priority crops**:
*   **Supported (10):** Rice, Maize, Cotton, Chickpea, Pigeon Pea (Tur), Green Gram (Moong), Black Gram (Urad), Banana, Mango, Grapes.
*   **MISSING (10):** Wheat, Soybean, Sugarcane, Groundnut, Sorghum (Jowar), Pearl Millet (Bajra), Mustard, Onion, Potato, Tomato.

## 10. KisanCare Compatibility
*   **Farmer Inputs:** KisanCare requires Location/District, Land Area, Season, Previous Crop, and Irrigation. **The model supports NONE of these.**
*   **Environmental Data:** The model uses `temperature`, `humidity`, and `rainfall`.
*   **Soil Information:** The model uses `N`, `P`, `K`, and `ph`. It lacks soil depth, SOC, EC, and texture.
*   **Conclusion:** The model's feature space is completely disconnected from the proposed KisanCare user flow (which is heavily geographically/seasonally driven).

## 11. Problems/Risks
1. **Missing Priority Crops:** Fails to support 50% of KisanCare's V1 priority crops (including massive staples like Wheat and Soybean).
2. **Temporal Leakage Risk:** Using exact "rainfall" and "temperature" as inputs implies the farmer knows the exact weather for the upcoming 4-month season at planting time. A real system must use historical averages for the given district and season.
3. **Hardcoded Assumptions:** The Flask API will fail if any of the 7 features are missing. There is no fallback logic (e.g., inferring weather from location).
4. **Agronomic Flaw (The NPK Problem):** The dataset's N, P, and K values mathematically resemble *fertilizer recommendation doses* rather than existing *soil test availability*. If a farmer inputs real Soil Health Card values (where Available N is often >250 kg/ha), the model will fail because its training data bounds N at ~140.

## 12. Reusable Components
*   The general concept of a scikit-learn classification pipeline, though our current `ml/main.py` FastAPI implementation is already superior to the repo's Flask app.

## 13. Components We Must Replace
*   **The Dataset:** Must be entirely replaced with real Indian agricultural data.
*   **The Feature Space:** Must introduce District, Season, and derived historical weather.
*   **The Model:** Must be retrained on the new dataset.

## 14. Recommendation
This repository is a standard toy/academic project. It does not meet the geographic, seasonal, or crop coverage requirements of a production agricultural system. 

## 15. Evidence / File References
*   `C:/KisanResearch/AuditRepo/app.py` (Flask API lacking `predict_proba` and handling 7 hardcoded inputs).
*   `C:/KisanResearch/AuditRepo/crop_recommendation.ipynb` (Train/test split, redundant scaling).
*   `C:/KisanResearch/AuditRepo/data/Crop_recommendation.csv` (Dataset shape and classes).

FOUNDATION:
- REJECT
