# Model 1.B External Data Sources

This manifest catalogs the verified raw datasets acquired for Model 1.B's proposed features.

## 1. ERA5-Land (via Open-Meteo Archive)
*   **Source:** Copernicus Climate Change Service / Open-Meteo
*   **Official Link:** https://open-meteo.com/en/docs/historical-weather-api (Underlying: ERA5-Land)
*   **Download Date:** 2026-10-05
*   **Variable:** `temperature_2m_mean`, `soil_moisture_0_to_7cm`
*   **Units:** °C (Celsius) and m³/m³
*   **Spatial resolution:** ~9km (0.1 degree)
*   **Temporal resolution:** Hourly / Daily available (1940-present)
*   **File Name:** `data/model1/external/raw/era5_land/sample_nagpur_2010.json`
*   **Coverage:** 100% historical coverage for India.
*   **Status:** **READY FOR AGGREGATION** (Requires district shapefiles to aggregate grid to district).

## 2. SoilGrids (ISRIC)
*   **Source:** ISRIC - World Soil Information
*   **Official Link:** https://soilgrids.org/ / https://rest.isric.org/
*   **Download Date:** 2026-10-05
*   **Variable:** `sand`, `silt`, `clay` proportions
*   **Units:** g/kg (mass fraction) -> converts to %
*   **Spatial resolution:** 250m
*   **Temporal resolution:** Static / Climatological baseline
*   **File Name:** `data/model1/external/raw/soil/sample_texture_nagpur.json`
*   **Coverage:** 100% spatial coverage.
*   **Status:** **READY FOR AGGREGATION** (Requires district shapefiles).

## 3. Soil Health Card (N, P, K, pH)
*   **Source:** Government of India Soil Health Card Portal
*   **Official Link:** https://soilhealth.dac.gov.in/
*   **Download Date:** N/A (No bulk historical API available without massive leakage)
*   **Variable:** N, P, K (kg/ha or index), pH
*   **Status:** **NOT READY**. (Excluded due to temporal target leakage for pre-2015 historical crops, and lack of reproducible open API download for raw plot data).

## 4. Previous Crop
*   **Source:** N/A
*   **Status:** **NOT READY**. (Cannot be derived reliably from district-level APY aggregate statistics. Farm-level crop sequence data is unavailable at pan-India historical scale).
