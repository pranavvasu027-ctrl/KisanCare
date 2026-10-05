# MODEL CARD: KisanCare Crop Recommendation (Baseline)

## 1. Model Details
* **Name:** Random_Forest_Baseline
* **Version:** 1.0.0
* **Date:** 2026-10-05
* **Algorithm:** Random Forest Classifier (Scikit-Learn)
* **Artifacts:** `crop_recommendation_model.pkl`, `preprocessor.pkl`, `label_encoder.pkl`

## 2. Intended Use
* **Primary Use:** A baseline predictive model for identifying optimal crops based strictly on soil nutrients and climatic averages.
* **Context:** Designed as "Model 1" in the KisanCare Farm Digital Twin loop.
* **Out of Scope:** This model does not understand geographic regions, growing seasons, or farmer financial constraints. 

## 3. Training Data
* **Dataset:** Kaggle Crop Recommendation (Atharva Ingle) / Baseline fallback.
* **Size:** 1,760 training samples, 440 test samples.
* **Classes:** 22 crops (perfectly balanced at 100 samples total per crop).

## 4. Evaluation Metrics
* **Accuracy:** 99.54%
* **Macro F1:** 99.54%
* **Top-3 Accuracy:** 100.0%
* **Top-5 Accuracy:** 100.0%

## 5. Required Inputs
* `N` (Nitrogen mg/kg)
* `P` (Phosphorus mg/kg)
* `K` (Potassium mg/kg)
* `temperature` (°C)
* `humidity` (%)
* `ph` (Soil pH)
* `rainfall` (mm)

## 6. Output
* Ranked list of crop labels with associated probabilities.

## 7. Limitations & Ethical Considerations
> **WARNING:** This is a baseline model trained on a benchmark crop recommendation dataset. Its performance should not be interpreted as real-world agricultural accuracy.

* **Synthetic Data Bias:** The training data contains artificially balanced classes and interpolated continuous variables. Real-world precision will be substantially lower.
* **Confidence vs. Probability:** The probability scores returned by `predict_proba` represent the model's mathematical confidence in the synthetic feature space, NOT the real-world agricultural probability of success.
