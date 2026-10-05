# Phase 2: Data Quality & Consistency Report

## Financial Consistency

- **Revenue vs (Production * Price)**: Max Difference = 0.5000 INR. Inconsistent records (>1 INR) = 0.
- **Profit vs (Revenue - Cost)**: Max Difference = 0.0000 INR. Inconsistent records (>1 INR) = 0.
- **Production vs (Yield * Area)**: Max Difference = 508.0004 Tonnes. Inconsistent records (>0.1 Tonnes) = 31.

## Outliers Analysis
| Variable | Min | P1 | Median | P99 | Max | Potential Outliers (<P1 or >P99) |
|---|---|---|---|---|---|---|
| `total_cost_inr` | 26826.00 | 42634.82 | 519082.50 | 1126428.82 | 1349990.00 | 80 |
| `revenue_inr` | 6107.00 | 21419.28 | 456830.50 | 3171876.93 | 5080900.00 | 80 |
| `yield_tonnes_ha` | 0.30 | 0.30 | 1.74 | 70.82 | 101.44 | 40 |

## Crop & Region Coverage
- **Total Records**: 4000
- **Maharashtra Records**: 512
- **Maharashtra Crops**: Maize, Wheat, Groundnut, Pulses, Cotton, Sugarcane, Chilli, Rice
- **Maharashtra Districts**: Nalgonda, Krishna, Ludhiana, Erode, Rajkot, Guntur, Indore, Raichur, Nashik, Warangal

## Crop Distribution
| Crop | Total Records | Maharashtra Records |
|---|---|---|
| Wheat | 614 | 82 |
| Maize | 551 | 78 |
| Pulses | 496 | 54 |
| Rice | 690 | 86 |
| Cotton | 508 | 70 |
| Chilli | 412 | 53 |
| Groundnut | 424 | 53 |
| Sugarcane | 305 | 36 |

## Unit Validation & Uncertainties

- `farm_area_hectares`: Verified (Hectares)
- `yield_tonnes_ha`: Verified (Tonnes/Hectare)
- `production_tonnes`: Verified (Tonnes)
- `market_price_inr_tonne`: Verified (INR/Tonne)
- `total_cost_inr`: Verified (INR)
- `revenue_inr`: Verified (INR)
- `profit_inr`: Verified (INR)
- `rainfall_mm`: Verified (mm)
- `avg_temperature_c`: Verified (°C)
- `humidity_pct`: Verified (%)
- `nitrogen_kg_ha`, `phosphorus_kg_ha`, `potassium_kg_ha`: Verified (kg/ha)
- `soil_p_h`: Unitless scale
- `soil_moisture_pct`: Verified (%)
- All identified units are consistent with column naming and value distributions. No unknown units detected.
