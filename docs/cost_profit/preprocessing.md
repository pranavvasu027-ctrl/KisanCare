# Preprocessing Log

* **Initial Rows**: 4000
* **Missing Values Detected**: {'Rainfall_mm': 48, 'Soil_Moisture_pct': 40, 'Yield_Tonnes_Ha': 32}
* **Imputed**: Column `Rainfall_mm` with median `582.0`
* **Imputed**: Column `Soil_Moisture_pct` with median `26.4`
* **Imputed**: Column `Yield_Tonnes_Ha` with median `1.74`
* **Duplicates Detected**: 0
* **Invalid Area Count**: 0
* **Invalid Cost Count**: 0
* **Outliers Capped**: Column `Farm_Area_Hectares` capped at 1st percentile (0.64) and 99th percentile (14.89)
* **Outliers Capped**: Column `Rainfall_mm` capped at 1st percentile (80.00) and 99th percentile (1203.60)
* **Outliers Capped**: Column `Avg_Temperature_C` capped at 1st percentile (18.60) and 99th percentile (35.10)
* **Outliers Capped**: Column `Humidity_pct` capped at 1st percentile (35.50) and 99th percentile (89.40)
* **Outliers Capped**: Column `Sunlight_Hours_Day` capped at 1st percentile (4.90) and 99th percentile (10.00)
* **Outliers Capped**: Column `Soil_pH` capped at 1st percentile (5.20) and 99th percentile (8.24)
* **Outliers Capped**: Column `Soil_Moisture_pct` capped at 1st percentile (11.40) and 99th percentile (41.00)
* **Outliers Capped**: Column `Nitrogen_kg_ha` capped at 1st percentile (47.59) and 99th percentile (190.60)
* **Outliers Capped**: Column `Phosphorus_kg_ha` capped at 1st percentile (17.30) and 99th percentile (97.10)
* **Outliers Capped**: Column `Potassium_kg_ha` capped at 1st percentile (38.59) and 99th percentile (168.90)
* **Outliers Capped**: Column `Fertilizer_kg_ha` capped at 1st percentile (44.59) and 99th percentile (328.11)
* **Outliers Capped**: Column `Pesticide_Litre_ha` capped at 1st percentile (0.50) and 99th percentile (9.52)
* **Outliers Capped**: Column `Yield_Tonnes_Ha` capped at 1st percentile (0.30) and 99th percentile (70.82)
* **Outliers Capped**: Column `Production_Tonnes` capped at 1st percentile (0.50) and 99th percentile (701.59)
* **Outliers Capped**: Column `Market_Price_INR_Tonne` capped at 1st percentile (3088.96) and 99th percentile (116094.08)
* **Outliers Capped**: Column `Total_Cost_INR` capped at 1st percentile (42634.82) and 99th percentile (1126428.82)
* **Outliers Capped**: Column `Revenue_INR` capped at 1st percentile (21419.28) and 99th percentile (3171876.93)
* **Outliers Capped**: Column `Profit_INR` capped at 1st percentile (-741708.50) and 99th percentile (2341398.91)
* **Outliers Capped**: Column `Water_Used_m3` capped at 1st percentile (271.98) and 99th percentile (26615.76)
* **Outliers Capped**: Column `Water_Efficiency_t_per_1000m3` capped at 1st percentile (0.32) and 99th percentile (50.01)
* **Outliers Capped**: Column `Disease_Pest_Risk_pct` capped at 1st percentile (18.70) and 99th percentile (74.60)
* **Leakage Features Dropped**: ['Farm_ID', 'Profit_INR', 'Revenue_INR', 'Yield_Tonnes_Ha', 'Production_Tonnes', 'Market_Price_INR_Tonne', 'Water_Efficiency_t_per_1000m3', 'Water_Used_m3']
* **Maharashtra Records**: 512
* **Final Rows**: 4000