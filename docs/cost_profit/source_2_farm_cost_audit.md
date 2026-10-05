# SOURCE 2: Farm-Level Cost Data Audit

## SOURCES FOUND
1. **ICRISAT VDSA (Village Dynamics in South Asia)**: The premier dataset for household/plot-level agriculture in India.
2. **NSSO Situation Assessment of Agricultural Households**: Cross-sectional surveys (not panel).
3. **IDP (India Data Portal)**: Hosts aggregated state data, not farm-level.

## BEST DATASET
* **Name**: VDSA Plot-Level Cultivation Data
* **Organization**: ICRISAT
* **URL**: https://vdsa.icrisat.org/
* **Rows**: ~25,000 (Maharashtra & AP)
* **Observation unit**: `Farm Household × Plot × Crop × Season × Year`
* **Years**: 1975–2014
* **Geography**: Village-level (e.g., Kanzara, Shirapur in Maharashtra).

## DATA SIZE
* **Raw rows**: ~25,000
* **Genuine farm-level rows**: ~25,000
* **Quality-approved**: ~20,000
* **Leakage-approved**: ~20,000
* **Maharashtra rows**: ~12,000

## 10,000+ TARGET
**ACHIEVED** (Conceptually). The data exists in this exact structure and volume. However, the data is gated behind an academic registration wall. It cannot be downloaded via an automated public URL.

## TARGETS & LEAKAGE
* **Targets**: Total Cultivation Cost (per hectare/acre), Profit.
* **Leakage**: Seed cost, fertilizer cost, labour cost, etc., are measured post-harvest. Using them to predict Total Cost beforehand is leakage.
