# Phase 2: Cleaning Report

## Column Name Standardization
| Original | Standardized |
|---|---|
| `Farm_ID` | `farm_id` |
| `State` | `state` |
| `District` | `district` |
| `Crop` | `crop` |
| `Season` | `season` |
| `Farm_Area_Hectares` | `farm_area_hectares` |
| `Rainfall_mm` | `rainfall_mm` |
| `Avg_Temperature_C` | `avg_temperature_c` |
| `Humidity_pct` | `humidity_pct` |
| `Sunlight_Hours_Day` | `sunlight_hours_day` |
| `Soil_pH` | `soil_p_h` |
| `Soil_Moisture_pct` | `soil_moisture_pct` |
| `Nitrogen_kg_ha` | `nitrogen_kg_ha` |
| `Phosphorus_kg_ha` | `phosphorus_kg_ha` |
| `Potassium_kg_ha` | `potassium_kg_ha` |
| `Irrigation_Method` | `irrigation_method` |
| `Fertilizer_kg_ha` | `fertilizer_kg_ha` |
| `Pesticide_Litre_ha` | `pesticide_litre_ha` |
| `Seed_Quality_Score` | `seed_quality_score` |
| `Yield_Tonnes_Ha` | `yield_tonnes_ha` |
| `Production_Tonnes` | `production_tonnes` |
| `Market_Price_INR_Tonne` | `market_price_inr_tonne` |
| `Total_Cost_INR` | `total_cost_inr` |
| `Revenue_INR` | `revenue_inr` |
| `Profit_INR` | `profit_inr` |
| `Water_Used_m3` | `water_used_m3` |
| `Water_Efficiency_t_per_1000m3` | `water_efficiency_t_per_1000m3` |
| `Disease_Pest_Risk_pct` | `disease_pest_risk_pct` |

## Missing Values & Imputation
- `rainfall_mm`: 1.20% missing. Imputed with median (582.00).
- `soil_moisture_pct`: 1.00% missing. Imputed with median (26.40).
- `yield_tonnes_ha`: 0.80% missing. Imputed with median (1.74).

## Duplicates
- 0 exact duplicate rows found.

## Categorical Standardization
- `crop`: Stripped whitespace and applied Title Case.
- `state`: Stripped whitespace and applied Title Case.
- `district`: Stripped whitespace and applied Title Case.
- `irrigation_method`: Stripped whitespace and applied Title Case.

## Numerical Validation
- No impossible negative/zero numerical values found.