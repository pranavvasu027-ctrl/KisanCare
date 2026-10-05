# Feature Mapping (Based on Repo 3: seasonal_agriculture_performance_dataset.csv)

The following mapping shows how the features from our recommended primary dataset integrate into the KisanCare V1 unified Farm structure.

## Mapping Table

| KisanCare Input Structure | Dataset Feature (`seasonal_agriculture_performance_dataset.csv`) | Transformation / Notes |
| :--- | :--- | :--- |
| **Location** | `State`, `District` | Direct string mapping / categorical encoding. |
| **Area** | `Farm_Area_Hectares` | Direct numerical mapping (ensure metric consistency). |
| **Crop** | `Crop` | Categorical encoding (Wheat, Rice, Maize, etc.). |
| **Season** | `Season` | Categorical encoding (Kharif, Rabi, Zaid). |
| **Soil - pH** | `Soil_pH` | Direct mapping. |
| **Soil - NPK** | `Nitrogen_kg_ha`, `Phosphorus_kg_ha`, `Potassium_kg_ha` | Direct mapping. |
| **Soil - Moisture** | `Soil_Moisture_pct` | Direct mapping. |
| **Weather** | `Rainfall_mm`, `Avg_Temperature_C`, `Humidity_pct`, `Sunlight_Hours_Day` | Direct mapping. |
| **Water / Irrigation** | `Irrigation_Method`, `Water_Used_m3` | Categorical encoding for method, numerical for volume. |
| **Yield (Target/Feature)** | `Yield_Tonnes_Ha` | ML prediction target for the Yield model. |
| **Market (Target)** | `Market_Price_INR_Tonne` | ML prediction target for the Market model. |
| **Economics - Cost** | `Total_Cost_INR` | Can be mapped as an ML prediction target or used as baseline reference. |
| **Economics - Revenue** | `Revenue_INR` | Calculated (`Yield * Area * Price`). Do not use ML to predict directly. |
| **Economics - Profit** | `Profit_INR` | Calculated (`Revenue - Cost`). Do not use ML to predict directly. |

## Compatibility Notes
* **Units**: The dataset uses Tonnes and Hectares, which are standard and easily converted to Quintals or Acres if required by other KisanCare modules.
* **Crop Compatibility**: Includes high-priority Indian crops: Wheat, Rice, Maize, Pulses, Cotton, Groundnut, Chilli, Sugarcane.
* **Missing Features**: Does not break down cost into distinct sub-components (Seed, Fertilizer, Labour, etc.). It only provides `Total_Cost_INR`. We can rely on user inputs or average ratios to estimate sub-components if needed in the UI.
