# Model 1.B Dataset Audit: ~240,000 Row Dataset

## 1. Identify the dataset
*   **Exact file name:** NOT FOUND LOCALLY
*   **Exact path:** NOT FOUND LOCALLY (Searched `C:\Users\prana\OneDrive\Desktop\Projects\KISANcare\kisan-care` and surrounding directories)
*   **Row count:** Unknown (described as ~240,000)
*   **Column count:** Unknown
*   **Dataset origin:** Based on the row count, this strongly resembles the well-known "Crop Production in India" dataset (APY dataset from data.gov.in, hosted on Kaggle with 246,091 rows). 
*   **Status:** The physical file is missing from the workspace.

## 2. Show the schema
Cannot execute programmatically on a missing file. If this is the standard 246k-row APY dataset, the schema is:
`State_Name`, `District_Name`, `Crop_Year`, `Season`, `Crop`, `Area`, `Production`.

## 3. Determine whether it contains Model B variables
Assuming the standard 246k APY dataset:
*   District / location: **PRESENT**
*   Year: **PRESENT**
*   Season: **PRESENT**
*   Crop: **PRESENT**
*   N: **ABSENT**
*   P: **ABSENT**
*   K: **ABSENT**
*   pH: **ABSENT**
*   Historical Temperature: **ABSENT**
*   Soil Moisture: **ABSENT**
*   Soil Texture: **ABSENT**
*   Previous Crop: **ABSENT**
*   Area / Production / Yield: **PRESENT** (Area, Production present; Yield derivable)

*(CRITICAL WARNING: If the dataset you are referring to DOES contain N/P/K and weather, it is highly likely a synthetic Kaggle dataset created by cross-joining the APY data with a tiny 2,200-row crop recommendation dataset, which duplicates fake soil values hundreds of thousands of times. This violates Model 1.B rules.)*

## 4. Check whether rows are real observations
Assuming the 246k dataset: ONE ROW represents **one district-year-season-crop aggregate**. It does NOT represent one farm, one field, or one soil sample. It is a regional administrative statistic, not an independent farm observation.

## 5. Check source authenticity
The original 246,091 row dataset comes from the Directorate of Economics and Statistics (DES), Ministry of Agriculture, Government of India. 

## 6. Check geographic compatibility
*   India coverage: Yes
*   Maharashtra coverage: Yes
*   District-level coverage: Yes
*   Coordinate/grid coverage: No

## 7. Check temporal coverage
Assuming APY: Typically covers 1997 to 2015, which perfectly matches our Model 1 target timeframe.

## 8. Check crop coverage
Assuming APY: Contains over 100 crops, encompassing our locked 20-crop scope.

## 9. Check target compatibility
It can support the `Area_Frequency` target because it contains Area, District, Year, and Season.

## 10. Leakage audit
Area and Production are post-harvest variables. They cannot be used as predictive features (100% leakage). If synthetic NPK values are present, they are fabricated and cause massive leakage and overfitting.

## 11. Duplicate / synthetic audit
Without the file, a programmatic Pandas duplicate check cannot be run. 

## 12. Missingness
Cannot be calculated on a missing file.

## 13. Final verdict
**D — REJECT**

**Reason:** The dataset file is physically missing from the workspace. Furthermore, if it is the standard 246k-row APY dataset, we already use a heavily cleaned version of it for Model 1 v2. If it is a 240k-row dataset that claims to have NPK and weather, it is a known synthetic Kaggle fabrication that violates our strict rule against using fabricated data.

## 14. Recommendation
Do not merge any external "240k row" dataset into the Model 1.B pipeline. We must stick strictly to the real, verified Phase 2 data sources (ERA5-Land and SoilGrids) mapped accurately to our existing baseline.
