# COST_PROFIT_MODEL_REPORT

## 1. DATASET
- **Dataset Used**: `seasonal_agriculture_performance_dataset.csv` (Repo 3)
- **Initial Rows**: 4000
- **Usable Rows**: 4000
- **Features Used**: State, District, Crop, Season, Farm_Area_Hectares, Rainfall_mm, Avg_Temperature_C, Humidity_pct, Sunlight_Hours_Day, Soil_pH, Soil_Moisture_pct, Nitrogen_kg_ha, Phosphorus_kg_ha, Potassium_kg_ha, Irrigation_Method, Fertilizer_kg_ha, Pesticide_Litre_ha, Seed_Quality_Score, Disease_Pest_Risk_pct
- **Features Removed**: `Farm_ID`, `Profit_INR`, `Revenue_INR`, `Yield_Tonnes_Ha`, `Production_Tonnes`, `Market_Price_INR_Tonne`, `Water_Efficiency_t_per_1000m3`, `Water_Used_m3`
- **Leakage Findings**: Removed all post-harvest metrics that perfectly reconstruct the profit equation. The model is trained purely on pre-harvest environmental and input features.

## 2. METHODOLOGY & METRICS
- **Split**: 80/20 Random Split. A random split is acceptable here as the dataset represents a synthetic/uniform distribution across a cross-section of farms without temporal components.
- **Models Tested**: Linear Regression, Random Forest, Extra Trees, Gradient Boosting.
- **Selected Model**: Gradient Boosting
- **Maharashtra Performance**: MAE = 48522.65, R2 = 0.9358

## 3. CROP COVERAGE
| KisanCare Crop | Dataset Crop Name | Supported? | Total Records | Maharashtra Records |
|---|---|---|---|---|
| Rice | Rice | Yes | 690 | 86 |
| Wheat | Wheat | Yes | 614 | 82 |
| Maize | Maize | Yes | 551 | 78 |
| Soybean | - | No | 0 | 0 |
| Cotton | Cotton | Yes | 508 | 70 |
| Sugarcane | Sugarcane | Yes | 305 | 36 |
| Chickpea | - | No | 0 | 0 |
| Pigeon Pea | - | No | 0 | 0 |
| Groundnut | Groundnut | Yes | 424 | 53 |
| Sorghum | - | No | 0 | 0 |
| Pearl Millet | - | No | 0 | 0 |
| Green Gram | - | No | 0 | 0 |
| Black Gram | - | No | 0 | 0 |
| Mustard | - | No | 0 | 0 |
| Onion | - | No | 0 | 0 |
| Potato | - | No | 0 | 0 |
| Tomato | - | No | 0 | 0 |
| Banana | - | No | 0 | 0 |
| Mango | - | No | 0 | 0 |
| Grapes | - | No | 0 | 0 |


## 4. INTEGRATION
- **Model Saved**: `C:\Users\prana\.gemini\antigravity\brain\c717cd51-3f5e-497a-9b25-ae28bd0f1741\models\model6_cost_profit\artifacts\cost_model.joblib`
- **Prediction Script**: `predict_cost.py` (to be created)
- **Economic Engine**: `economic_engine.py` (to be created)
- **API Status**: Prepared as a stub in `api_stub.py` (to be created)

## 5. LIMITATIONS
- The original dataset uses a deterministic generating function for costs, making R2 artificially high compared to real-world noisy agricultural data.
- Crop coverage is restricted to 8 crops. Major crops like Soybean, Chickpea, and Onion are missing.
- Prices and Yields are needed from external models to calculate Profit.

## 6. RECOMMENDED NEXT STEP
Integrate `predict_cost.py` and `economic_engine.py` into the main KisanCare backend (e.g. FastAPI/Flask app), and connect them to the existing Yield and Market Price microservices.
