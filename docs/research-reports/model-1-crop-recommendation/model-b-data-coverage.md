# Model B Feature Data Coverage

This report outlines the coverage and readiness for the newly proposed Model B features based on the real datasets verified and sampled in Phase 2.

| Feature | Source | Coverage | Spatial Match | Temporal Match | Status |
| ------- | ------ | -------- | ------------- | -------------- | ------ |
| Historical Temperature | ERA5-Land | 100% | Needs Grid-to-Polygon | PASS (Pre-season filtering possible) | **CONDITIONAL** |
| Soil Moisture | ERA5-Land | 100% | Needs Grid-to-Polygon | PASS (Pre-season filtering possible) | **CONDITIONAL** |
| Soil Texture | ISRIC SoilGrids | 100% | Needs Grid-to-Polygon | PASS (Static geological property) | **CONDITIONAL** |
| N (Nitrogen) | Soil Health Card | ~0% for target years | District | FAIL (Only available post-2015) | **NOT READY** |
| P (Phosphorus) | Soil Health Card | ~0% for target years | District | FAIL (Only available post-2015) | **NOT READY** |
| K (Potassium) | Soil Health Card | ~0% for target years | District | FAIL (Only available post-2015) | **NOT READY** |
| pH | Soil Health Card | ~0% for target years | District | FAIL (Only available post-2015) | **NOT READY** |
| Previous Crop | APY / Surveys | 0% | FAIL | FAIL | **NOT READY** |

## Summary
The only features that have valid historical coverage without target leakage are **Historical Temperature, Soil Moisture, and Soil Texture**. However, they remain **CONDITIONAL** because they are high-resolution gridded datasets (.nc, .tif) or coordinate-based point APIs that require spatial aggregation to match our categorical "District" feature using District shapefiles.
