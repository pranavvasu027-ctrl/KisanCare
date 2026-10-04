# Model B Phase 2: Data Acquisition & Source Verification

## 1. Objective
Identify, verify, and evaluate REAL external datasets to support Model B's proposed features (N, P, K, pH, Previous Crop, Historical Temperature, Soil Moisture, Soil Texture). This phase strictly prohibits training, fabricating data, or altering the frozen v2 baseline.

## 2. Existing Data Limitations
Our current baseline relies entirely on district, season, and crop categorical data from historical Area, Production, and Yield (APY) records. It lacks actual field-level soil and weather measurements. We currently do not have India district shapefiles (.shp or .geojson) in the repository to instantly map gridded data.

## 3. Source-Search Methodology
We prioritized authoritative Government of India and global scientific sources (e.g., Soil Health Card, ECMWF Copernicus, ISRIC SoilGrids). We evaluated spatial resolution (can it map to our APY districts?), temporal resolution (can we avoid target leakage?), and overall data availability.

## 4. Source-by-Source Findings & Dataset URLs

### Soil N, P, K, pH
*   **Recommended Source:** Soil Health Card Portal (Gov of India) / CoRE Stack
*   **URL:** https://soilhealth.dac.gov.in/
*   **Findings:** The government provides a dashboard but no direct programmatic API for bulk raw data. Crucially, SHC data collection largely started around 2015. Attempting to use 2015+ soil nutrient data to predict historical APY observations (e.g., 2000-2014) introduces severe target leakage (using future data to predict past events).

### Historical Temperature & Soil Moisture
*   **Recommended Source:** ERA5-Land (ECMWF Copernicus Climate Data Store)
*   **URL:** https://cds.climate.copernicus.eu/cdsapp#!/dataset/reanalysis-era5-land-hourly-data
*   **Findings:** Provides hourly `2m_temperature` and `volumetric_soil_water` at ~9km global grid resolution from 1950-present. This is an excellent source. It requires a spatial GIS pipeline to aggregate the NetCDF grids into Indian district polygons.

### Soil Texture (Sand, Silt, Clay)
*   **Recommended Source:** ISRIC SoilGrids
*   **URL:** https://soilgrids.org/
*   **Findings:** Provides 250m resolution gridded soil texture. Because soil texture is generally static over historical timeframes, temporal leakage is low. Like ERA5, it requires spatial aggregation using district shapefiles.

### Previous Crop
*   **Recommended Source:** None viable for historical pan-India APY.
*   **URL:** N/A
*   **Findings:** APY data is district-level aggregate. To know "Previous Crop," one needs field-level or farm-level longitudinal surveys. Deducing field-level crop rotations from district aggregates is impossible without inventing data.

## 5. Coverage and Missingness
*   **ERA5-Land (Temp/Moisture):** 100% spatial and temporal coverage for India.
*   **SoilGrids (Texture):** 100% spatial coverage. Temporal is static (assumed 100%).
*   **Soil Health Card (N/P/K/pH):** High spatial coverage for recent years, but ~100% missing for historical APY years (<2015).
*   **Previous Crop:** 100% missing (no field-level data).

## 6. Leakage Assessment
| Feature | Leakage Risk | Assessment |
| :--- | :--- | :--- |
| N, P, K, pH | **FAIL** | Using post-2015 SHC measurements for historical APY targets breaks causality. |
| Historical Temperature | **PASS** | We can strictly filter ERA5 for pre-season months only. |
| Soil Moisture | **PASS** | Pre-season ERA5 soil moisture can be used. |
| Soil Texture | **PASS** | Texture is geologically static; low risk. |
| Previous Crop | **FAIL** | Field sequences cannot be derived from aggregates without leakage/assumptions. |

## 7. Feature Readiness Table

| Feature | Dataset | Authority | Spatial Match | Temporal Match | Coverage | Units Clear | Leakage Risk | Usable? | Status |
| ------- | ------- | --------- | ------------- | -------------- | -------- | ----------- | ------------ | ------- | ------ |
| N | Soil Health Card | High | District (Aggr) | FAIL (Post-2015) | Low (Hist) | Yes | FAIL | No | **NOT READY** |
| P | Soil Health Card | High | District (Aggr) | FAIL (Post-2015) | Low (Hist) | Yes | FAIL | No | **NOT READY** |
| K | Soil Health Card | High | District (Aggr) | FAIL (Post-2015) | Low (Hist) | Yes | FAIL | No | **NOT READY** |
| pH | Soil Health Card | High | District (Aggr) | FAIL (Post-2015) | Low (Hist) | Yes | FAIL | No | **NOT READY** |
| Previous Crop | N/A | N/A | FAIL | N/A | 0% | N/A | FAIL | No | **NOT READY** |
| Hist. Temp | ERA5-Land | High | Grid (Needs SHP) | PASS (1950+) | 100% | Yes (K/°C)| PASS | Yes | **CONDITIONAL** |
| Soil Moisture | ERA5-Land | High | Grid (Needs SHP) | PASS (1950+) | 100% | Yes (m3/m3)| PASS | Yes | **CONDITIONAL** |
| Soil Texture | SoilGrids | High | Grid (Needs SHP) | PASS (Static) | 100% | Yes (%) | PASS | Yes | **CONDITIONAL** |

*Note: CONDITIONAL means the data is scientifically valid but requires a GIS spatial aggregation pipeline (and India district shapefiles, which we currently lack) before fusion.*

## 8. Explicit NO-TRAIN Decision
As instructed, **Model B will not be trained** at this time. The frozen v2 model and its API remain completely unaltered. We refuse to fabricate synthetic features or impute 100% missing values for N/P/K/pH or Previous Crop.

## 9. Recommended Next Phase
1.  **Acknowledge Feature Drop:** Formally drop N, P, K, pH, and Previous Crop from the Model B experiment due to historical leakage and lack of field-level data.
2.  **GIS Pipeline (Phase 3):** Acquire authoritative Indian District Shapefiles. Build a spatial aggregation pipeline using `geopandas` and `xarray` to extract district-level pre-season averages from ERA5-Land and SoilGrids.
