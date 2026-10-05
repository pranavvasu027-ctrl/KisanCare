# Leakage Audit for Cost Prediction Model

## 1. Goal
We aim to train an ML model to predict `Total_Cost_INR`. We must ensure no post-harvest or perfectly collinear variables are used as features. The formula for Profit is `Profit = Revenue - Cost`, meaning `Profit` and `Revenue` inherently contain the `Cost` inside their calculation (especially since this dataset is mathematically synthetic).

## 2. Feature Analysis

### 🔴 REJECTED FEATURES (Data Leakage / Post-Harvest)
* **`Profit_INR`**: Calculated directly as `Revenue - Cost`. If included, the model will just learn `Cost = Revenue - Profit`.
* **`Revenue_INR`**: Calculated as `Production * Price`. This is a post-harvest outcome and depends on yield and market rates.
* **`Yield_Tonnes_Ha`**: This is the outcome of the season. Cost is incurred *before* and *during* the season to produce this yield.
* **`Production_Tonnes`**: Derived from `Yield * Area`. Post-harvest.
* **`Market_Price_INR_Tonne`**: Future information at the time of planting/cost estimation.
* **`Water_Efficiency_t_per_1000m3`**: Since this relies on production (tonnes), it indirectly leaks the yield, which is post-harvest.
* **`Water_Used_m3`**: While water used correlates with cost, total water used is usually only known perfectly at the *end* of the season. However, expected water use could be a feature. For safety, we will rely on `Irrigation_Method` and weather features instead.
* **`Farm_ID`**: A completely uninformative identifier.

### 🟢 APPROVED FEATURES (Pre-Harvest / Input Variables)
* **`State` & `District`**: Geographic location, fully known.
* **`Crop`**: The crop being planted, fully known.
* **`Season`**: Known before planting.
* **`Farm_Area_Hectares`**: The fundamental multiplier for all costs. Known in advance.
* **`Soil_pH`, `Nitrogen_kg_ha`, `Phosphorus_kg_ha`, `Potassium_kg_ha`, `Soil_Moisture_pct`**: Baseline soil conditions requiring management. Known/measurable.
* **`Rainfall_mm`, `Avg_Temperature_C`, `Humidity_pct`, `Sunlight_Hours_Day`**: Expected environmental conditions.
* **`Irrigation_Method`**: Infrastructure choice (Drip, Flood, etc.), directly impacting capital and operational costs.
* **`Fertilizer_kg_ha`, `Pesticide_Litre_ha`**: Management decisions made during the season. Highly predictive of input costs without leaking the final target (since they are just quantities, not exact INR values).
* **`Seed_Quality_Score`**: Seed tier (influencing seed cost).
* **`Disease_Pest_Risk_pct`**: The forecasted risk, which drives pesticide application costs.

## 3. Conclusion
The target is `Total_Cost_INR`. We will strictly use only the approved pre-harvest variables to ensure the model generalizes to new seasons without relying on hindsight.
