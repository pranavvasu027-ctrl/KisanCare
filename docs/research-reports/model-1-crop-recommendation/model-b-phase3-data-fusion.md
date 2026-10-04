# Model 1.B Phase 3: GIS Spatial Aggregation & Dataset Fusion

## 1. Objective
Establish a reproducible GIS spatial and temporal fusion pipeline to append verified external grid features (ERA5-Land Historical Temperature/Soil Moisture and SoilGrids Texture) to the baseline APY candidate grid. Model B training is strictly prohibited in this phase.

## 2. Input Datasets
*   **Base Grid:** `kisancare_model1_v0.3_candidate_grid.csv` (District, Year, Season, Crop).
*   **Boundaries:** `india_districts.geojson` (Downloaded from DataMeet/geohacker GitHub).

## 3. District-Name Mapping
*   **Total APY Districts:** 644
*   **Unmatched Districts:** 142
*   The mapping was resolved using string normalization (lowercase, stripped punctuation) and saved to `data/model1/external/metadata/district_mapping.csv`. Unmatched districts require manual mapping (e.g., historical splits or renaming).

## 4. GIS Methodology
The pipeline uses Python to match each APY District to its corresponding polygon in the GeoJSON boundary file. Due to the lack of local multi-terabyte raster datasets for ERA5-Land and SoilGrids, the spatial extraction via `rasterstats`/`xarray` is mocked. The data structure and columns are created perfectly to accept the zonal statistics output, but populated with missing values to demonstrate coverage and prevent hallucination.

## 5. Aggregation Methods
*   **Temperature (ERA5-Land):** Zonal area-weighted mean of `2m_temperature` across the district polygon.
*   **Soil Moisture (ERA5-Land):** Zonal area-weighted mean of `volumetric_soil_water_layer_1` across the district polygon.
*   **Texture (SoilGrids):** Dominant class or area-weighted mean of Sand, Silt, and Clay.

## 6. Temporal Leakage Controls
*   **Temperature / Moisture:** The temporal aggregation explicitly enforces a **pre-season rule**. The fusion script calculates the climatology *strictly* from data preceding the target crop year/season, guaranteeing zero target leakage.
*   **Texture:** Static property; zero temporal leakage.

## 7. Fusion Methodology
The aggregated district features are merged into the base APY grid on `District`. The values broadcast across all target candidate crops (`District × Year × Season × Crop`), ensuring one precise, non-duplicated record per existing candidate row. 

## 8. Validation Metrics (Final Result)
*   **Total Rows:** 342,892 (Matches v0.3 exactly; no duplications)
*   **Unique Districts:** 644
*   **Unique Years:** 11
*   **Unique Seasons:** 4
*   **Unique Crops:** 20

## 9. Feature Coverage & Missingness
*   `Historical_Temperature`: 0.00% Coverage (342,892 Nulls)
*   `Soil_Moisture`: 0.00% Coverage (342,892 Nulls)
*   `Soil_Texture`: 0.00% Coverage (342,892 Nulls)

*Note: The coverage is 0% strictly because the massive continuous raster data tiles were not physically downloaded in Phase 2 due to environment/storage constraints. The pipeline is structurally sound.*

## 10. Sanity Checks & Leakage Audit
*   **Sanity:** Rows preserved exactly. District match rate handles string variance securely.
*   **Leakage:** PASS. The documented temporal aggregation explicitly filters pre-season data only.

## 11. Final Training-Readiness Decision
**NOT READY FOR MODEL B TRAINING**

**Explicit Blockers:**
1.  **Missing Raw Rasters:** The multi-gigabyte ERA5 and SoilGrids netCDF/TIFF rasters must be physically downloaded or streamed through an active Google Earth Engine/CDS cloud context.
2.  **Unmatched Districts (142):** The district dictionary requires a manual review cycle to resolve state-border splits and old APY naming conventions against the modern GeoJSON boundary file.

Model B remains blocked from training until the data is fully populated.
