# SOURCE 2: Maharashtra Government / DES Agricultural Data

## Source Provenance
* **Official Source Name**: Comprehensive Scheme for Studying the Cost of Cultivation of Principal Crops in India
* **Organization**: Directorate of Economics and Statistics (DES), Ministry of Agriculture & Farmers Welfare / Commission for Agricultural Costs & Prices (CACP)
* **Original URL**: [https://eands.dacnet.nic.in/Cost_of_Cultivation.htm](https://eands.dacnet.nic.in/Cost_of_Cultivation.htm)
* **Download URL**: N/A (Extracted from published PDF/Excel annexures)
* **Publication Year**: Annual (Most recent consolidated data usually trails by 2-3 years)
* **Data Year**: 2018-2020 (Sample provided)
* **License**: Open Government Data
* **File Format**: CSV (Manually compiled from official reports)
* **Number of Records**: ~300 historically available for Maharashtra (Sample contains 10)

## Variables
* `State`: Geographic state (Maharashtra)
* `Crop`: Crop name
* `Year`: Agricultural year (e.g., 2018-19)
* `Cost_A2_FL_per_Hectare`: Paid-out costs + imputed family labour (INR)
* `Cost_C2_per_Hectare`: Comprehensive cost including rent and interest on fixed capital (INR)
* `Cost_C2_per_Quintal`: Comprehensive cost per quintal of production (INR)
* `Yield_Quintal_per_Hectare`: Crop yield (Quintals/Hectare)

## Geographic Coverage
* **Coverage**: Strictly State-level (Maharashtra). 
* **Districts**: NOT available in public datasets. The DES samples specific tehsils/villages to construct the state average, but does not publish district-wise aggregations publicly.

## Crop Coverage
* Available for principal crops: Cotton, Soybean, Sugarcane, Wheat, Maize, Sorghum, Groundnut, Pigeon Pea, Chickpea, Onion, Potato.
* Generally covers 12-15 crops for Maharashtra.

## Cost & Yield Coverage
* **Cost**: Highly detailed official estimates (A2, A2+FL, B1, B2, C1, C2).
* **Yield**: Yes (Quintal per Hectare).

## Limitations
* **Granularity**: The data is heavily aggregated. One row represents the **entire state's average** for a specific crop in a specific year. It completely lacks farm-level variance, district-level variance, and environmental context (soil, rainfall, etc.).
* **Data Availability**: The unit-level "Plot Level Summary Data" (PLSD) exists internally (which contains thousands of rows) but is restricted. Publicly, you only get state averages.

## Data Quality Test
* **Real-world credibility**: 100/100 (Gold standard for Indian agriculture pricing).
* **Geographic accuracy**: 20/100 (Only state-level).
* **Temporal coverage**: 90/100 (Decades of time-series).
* **Crop coverage**: 75/100 (Covers principal crops well, but misses horticulture).
* **Cost coverage**: 100/100 (A2 to C2 definitions are precise).
* **Yield coverage**: 100/100.
* **Completeness**: 100/100 (No missing values in aggregated reports).
* **Consistency**: 100/100.
* **ML suitability**: 5/100 (Aggregated data cannot train a personalized farm-level machine learning model. It only provides a static lookup table).
* **Overall Score**: 69/100 (Excellent for reference, terrible for ML).

## Real/Official/Synthetic
This is **100% official, real administrative statistical data**, aggregated from primary household surveys.
