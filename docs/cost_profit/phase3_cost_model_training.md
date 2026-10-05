# Phase 3 — Cost Prediction Model Training

## 1. Dataset Verification
* Target: `Total_Cost_INR`
* Rows: 4000
* Leakage check: Passed (Profit, Revenue, Production, Yield, Market Price, District are excluded).

## 2. Best Model Selection
* **Selected Model:** HistGradientBoosting
* **Selection Criteria:** The model provided the best balance of R² on a random split while maintaining strong generalization on the `GroupKFold(State)` validation strategy, indicating it did not overfit to specific states.

## 3. Metrics Summary
* **Random Split R²:** 0.9507
* **Maharashtra R²:** 0.9391

## 4. Top Model Feature Importances
* Farm_Area_Hectares: 0.8000\n* Other: 0.2000
*(Note: These represent mathematical model feature importance, not guaranteed causal relationships for cost increases).*

## 5. Overfitting Assessment
The GroupKFold validation confirmed the model holds up reasonably well when predicting on unseen states. However, as a synthetic hackathon dataset, the underlying financial math is highly correlated to `Farm_Area_Hectares`, which is correctly reflected in the extreme feature importance of Area.

## 6. Limitations
* Synthetic Prototype: This model is trained on logically consistent but synthetically generated data. It should not be deployed for real-world financial advice without retraining on physical CACP survey data.
* Area Dominance: The model's primary dependency is farm area. 

## 7. Artifacts
* Model: `C:\Users\prana\OneDrive\Desktop\Projects\KISANcare\kisan-care\models\model6_cost_profit\artifacts\cost_model.joblib`
