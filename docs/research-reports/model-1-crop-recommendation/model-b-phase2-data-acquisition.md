# Model B Phase 2: Data Acquisition & Source Verification

## 1. Objective
Identify, verify, and collect REAL external datasets to support Model B's proposed features. This phase strictly prohibits model training, fabricating data, generating synthetic data, or altering the frozen v2 baseline. **Explicit NO-TRAIN decision**: NO MODEL TRAINING IN THIS PHASE.

## 2. Sources Searched
We searched for authoritative Government of India and global scientific sources:
*   Soil Health Card Portal (N, P, K, pH)
*   ECMWF Copernicus Climate Data Store / ERA5 / ERA5-Land (Temperature, Moisture)
*   Open-Meteo Historical Archive (Temperature, Moisture - wraps ERA5-Land)
*   ISRIC SoilGrids (Texture)
*   UPAg, ICRISAT, AgriFieldNet (Previous Crop sequences)

## 3. Sources Obtained
We successfully identified and verified access to:
*   **ERA5-Land via Open-Meteo:** For historical temperature and soil moisture.
*   **ISRIC SoilGrids REST API:** For soil texture.

## 4. Actual Downloaded Files
Small reproducible JSON samples were downloaded using their respective APIs to verify accessibility, schema, and units. They are saved in `data/model1/external/raw/`:
*   `era5_land/sample_nagpur_2010.json` (Temp/Moisture)
*   `soil/sample_texture_nagpur.json` (Texture)

## 5. Variable Definitions
*   **ERA5-Land Temp:** `temperature_2m_mean` (°C). Measured at 2m above ground.
*   **ERA5-Land Moisture:** `soil_moisture_0_to_7cm` (m³/m³). Volumetric water content in layer 1.
*   **SoilGrids Texture:** `sand`, `silt`, `clay` proportions (g/kg, converted to % via d_factor). Depth: 0-5cm.

## 6. Coverage & Missingness
*   **ERA5-Land (Temp/Moisture):** 100% spatial and historical temporal coverage for India. Missingness is 0%.
*   **SoilGrids (Texture):** 100% spatial coverage. Missingness is 0%.
*   **Soil Health Card (N/P/K/pH):** Near 0% coverage for historical APY years (<2015). Missingness is ~100% for the target historical period.
*   **Previous Crop:** 0% field-level sequence coverage. Missingness is 100%.

## 7. Spatial Alignment
*   **Grid to Polygon:** ERA5-Land (0.1° ~9km) and SoilGrids (250m) are continuous gridded products. They require a GIS pipeline (e.g., Zonal Statistics) using District shapefiles to aggregate cell values into single district averages.

## 8. Temporal Alignment & Leakage Analysis
| Feature | Leakage Assessment | Reason |
| :--- | :--- | :--- |
| N, P, K, pH | **FAIL** | SHC data is post-2015. Using it for historical APY targets breaks causality. |
| Historical Temperature | **PASS** | Can strictly filter for pre-season climatology. |
| Soil Moisture | **PASS** | Can strictly filter for pre-season conditions. |
| Soil Texture | **PASS** | Texture is geologically static; low leakage risk. |
| Previous Crop | **FAIL** | Cannot derive sequences from district aggregates without inventing data. |

## 9. Measurement/Model Status
*   **ERA5-Land:** Modeled/Reanalysis (Physical climate model constrained by historical observations).
*   **SoilGrids:** Modeled (Machine learning predictions based on global point observations and covariates).
*   *(Note: Neither are direct "farm measurements," but both are scientifically defensible authoritative proxies).*

## 10. Feature Readiness

| Feature | Status |
| ------- | ------ |
| N | **NOT READY** |
| P | **NOT READY** |
| K | **NOT READY** |
| pH | **NOT READY** |
| Previous Crop | **NOT READY** |
| Hist. Temp | **CONDITIONAL** (Needs Spatial Aggregation) |
| Soil Moisture | **CONDITIONAL** (Needs Spatial Aggregation) |
| Soil Texture | **CONDITIONAL** (Needs Spatial Aggregation) |

## 11. Recommended Next Fusion Steps
1.  **Drop Failed Features:** Permanently exclude N, P, K, pH, and Previous Crop from Model 1.B due to 100% historical missingness and severe target leakage.
2.  **Acquire Shapefiles:** Obtain definitive Indian District boundary shapefiles matching the APY dataset definitions.
3.  **Build GIS Pipeline:** Use `geopandas` to perform spatial joins and aggregate the ERA5-Land and SoilGrids data into District-level features suitable for XGBoost.
