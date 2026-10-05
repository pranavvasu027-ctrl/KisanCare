# Phase 2: Raw Data Profile

- **Raw Rows**: 4000
- **Raw Columns**: 28

## Column Information

| Column | Type | Missing % | Unique Vals | Min | Median | Max |
|---|---|---|---|---|---|---|
| `Farm_ID` | str | 0.00% | 4000 | N/A | N/A | N/A |
| `State` | str | 0.00% | 8 | N/A | N/A | N/A |
| `District` | str | 0.00% | 10 | N/A | N/A | N/A |
| `Crop` | str | 0.00% | 8 | N/A | N/A | N/A |
| `Season` | str | 0.00% | 3 | N/A | N/A | N/A |
| `Farm_Area_Hectares` | float64 | 0.00% | 1370 | 0.50 | 7.89 | 15.00 |
| `Rainfall_mm` | float64 | 1.20% | 3256 | 80.00 | 582.00 | 1395.20 |
| `Avg_Temperature_C` | float64 | 0.00% | 204 | 16.20 | 26.90 | 39.70 |
| `Humidity_pct` | float64 | 0.00% | 573 | 25.00 | 63.00 | 95.00 |
| `Sunlight_Hours_Day` | float64 | 0.00% | 71 | 3.50 | 7.30 | 11.00 |
| `Soil_pH` | float64 | 0.00% | 313 | 5.20 | 6.69 | 8.40 |
| `Soil_Moisture_pct` | float64 | 1.00% | 343 | 8.00 | 26.40 | 47.00 |
| `Nitrogen_kg_ha` | float64 | 0.00% | 1229 | 40.00 | 120.10 | 220.00 |
| `Phosphorus_kg_ha` | float64 | 0.00% | 760 | 15.00 | 57.50 | 120.00 |
| `Potassium_kg_ha` | float64 | 0.00% | 1137 | 30.00 | 105.10 | 200.00 |
| `Irrigation_Method` | str | 0.00% | 4 | N/A | N/A | N/A |
| `Fertilizer_kg_ha` | float64 | 0.00% | 1881 | 40.00 | 186.25 | 400.00 |
| `Pesticide_Litre_ha` | float64 | 0.00% | 851 | 0.50 | 5.12 | 12.08 |
| `Seed_Quality_Score` | float64 | 0.00% | 36 | 0.65 | 0.83 | 1.00 |
| `Yield_Tonnes_Ha` | float64 | 0.80% | 738 | 0.30 | 1.74 | 101.44 |
| `Production_Tonnes` | float64 | 0.00% | 2528 | 0.15 | 11.77 | 1424.40 |
| `Market_Price_INR_Tonne` | int64 | 0.00% | 3760 | 2594.00 | 25913.00 | 131240.00 |
| `Total_Cost_INR` | int64 | 0.00% | 3995 | 26826.00 | 519082.50 | 1349990.00 |
| `Revenue_INR` | int64 | 0.00% | 3993 | 6107.00 | 456830.50 | 5080900.00 |
| `Profit_INR` | int64 | 0.00% | 3992 | -1019223.00 | 3673.00 | 4345421.00 |
| `Water_Used_m3` | int64 | 0.00% | 3407 | 128.00 | 4435.00 | 40902.00 |
| `Water_Efficiency_t_per_1000m3` | float64 | 0.00% | 3127 | 0.14 | 2.94 | 79.80 |
| `Disease_Pest_Risk_pct` | float64 | 0.00% | 597 | 5.00 | 46.40 | 88.90 |

## Duplicate Detection
- **Exact Duplicate Rows**: 0
- **Potential Duplicates (by State/Dist/Crop/Area/Season)**: 14