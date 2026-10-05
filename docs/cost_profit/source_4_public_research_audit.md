# SOURCE 4 — PUBLIC RESEARCH DATA

### CANDIDATES FOUND
1. **Kaggle** (Agriculture Crop Production in India) - *State aggregates copied from DES*
2. **Mendeley Data / ResearchGate** - *Fragmented thesis surveys (usually <500 rows)*
3. **India Data Portal** - *State aggregates hosted by ISB*
4. **Harvard Dataverse / CGIAR** - *Focused regional field surveys (e.g., Bihar/Haryana rice-wheat systems, ~1,500 rows)*
5. **Zenodo / Figshare / Dryad** - *No 10k+ row farm-level datasets for Indian crop cultivation costs found.*

### BEST DOWNLOADABLE DATASET
**Name:** Various CGIAR Climate-Smart Agriculture Surveys (Combined)
**Organization:** CGIAR / Harvard Dataverse
**Original source:** Primary institutional field surveys
**Download URL:** Multiple fragmented DOIs on Harvard Dataverse
**Format:** CSV / Stata (`.dta`)
**Observation unit:** `Farmer × Plot × Season`

### ACTUAL DATA SIZE
**Raw:** ~1,500 rows (per typical dataset)
**Farm-level:** ~1,500 rows
**Quality-approved:** ~1,000 rows
**Leakage-approved:** ~1,000 rows

### GEOGRAPHY
Mostly Northern/Eastern India (Bihar, Haryana, Punjab). **0 Maharashtra rows.**

### YEARS
2015–2018

### CROPS
Rice, Wheat, Maize

### MODEL 6 INPUTS
Area, Crop, Season, Fertilizer Quantity, Irrigation Source.

### MODEL 6 TARGET
Total expenditure on inputs (often missing family labour imputation).

### DATA QUALITY
**Missing:** High (surveys often skip full ledger accounting).
**Duplicates:** 0.
**Geography:** Exact villages.
**Time:** Cross-sectional.
**Financial consistency:** Medium (often lacks comprehensive C2 tracking).

### LEAKAGE
Same as before: Components (Seed cost, Fertilizer cost, Labour cost) cannot be used to predict Total Cost beforehand.

### 10,000+ TEST
**FAIL**

### CAN WE TRAIN MODEL 6?
**NO**

### IF NO
**Usable count:** 0 (No single downloaded dataset provides a comprehensive, nationwide or Maharashtra-specific farm-level training set).
**Remaining shortfall:** 10,000 observations.
*Explanation:* The open-data ecosystem simply does not host 10,000+ row farm-level cultivation cost CSVs. Massive datasets (like NSS or ICRISAT) are securely gated. Downloadable public datasets on Kaggle/IDP are strictly aggregated (state-level averages). Downloadable research datasets on Dataverse/Mendeley are too small (a few hundred to a thousand rows) and geographically fragmented. 

### FINAL DECISION
**SEARCH REQUIRED** (Search failed to find a valid dataset)
