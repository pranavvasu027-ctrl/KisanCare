# Model B Data Audit Report

This report evaluates whether the richer agronomic information proposed for Model B has a real data source, sufficient coverage, and proper alignment without target leakage. Per instructions, we do not fabricate or synthesize values for missing features.

## Proposed Feature Audit

| Feature | Source | Coverage | Spatial level | Time alignment | Missingness | Leakage risk | Status |
| ------- | ------ | -------- | ------------- | -------------- | ----------- | ------------ | ------ |
| N | None found | 0% | N/A | N/A | 100% | N/A | NOT READY |
| P | None found | 0% | N/A | N/A | 100% | N/A | NOT READY |
| K | None found | 0% | N/A | N/A | 100% | N/A | NOT READY |
| pH | None found | 0% | N/A | N/A | 100% | N/A | NOT READY |
| Previous Crop | None found | 0% | N/A | N/A | 100% | N/A | NOT READY |
| Historical Temperature | None found | 0% | N/A | N/A | 100% | N/A | NOT READY |
| Soil Moisture | None found | 0% | N/A | N/A | 100% | N/A | NOT READY |
| Soil Texture | None found | 0% | N/A | N/A | 100% | N/A | NOT READY |

### Detailed Evaluation

*   **N/P/K:** We currently lack measured Soil Health Card values (or equivalent defensible sources) that can be aligned geographically to the District and temporarily to the specific observation periods.
*   **pH:** Similar to N/P/K, no robust measured data source for soil pH is available. The previous dataset used static state-level fallbacks which lack the necessary geographic and temporal alignment.
*   **Previous Crop:** Deriving the previous year's crop without target leakage requires field-level temporal data or precise district-level sequencing data. The current APY data (district-year-season-crop aggregates) cannot reliably provide this without massive assumptions and high leakage risk.
*   **Historical Temperature:** True climatological data properly aligned to historical pre-target seasons without future leakage does not currently exist in the raw data lake. Past iterations used simple fallback averages.
*   **Soil Moisture:** We do not have measured observations, historical climatology, current-season values, or model-derived estimates for soil moisture in the raw dataset.
*   **Soil Texture:** There is no geographic source data or soil map available to provide stable soil texture classification for joining.

## Next Actions

Since the required features are critically missing from our data repositories, training Model B at this moment would involve fabricating synthetic data, which violates the strict data rules for this experiment. 

The immediate next step is to **acquire the actual datasets** (e.g., Soil Health Card data for N/P/K/pH, historical weather APIs or datasets for temperature/moisture, and proper agricultural surveys for previous crops) before proceeding to feature engineering and Model B training.

**Model B remains blocked and v2 remains the official Model 1 MVP.**
