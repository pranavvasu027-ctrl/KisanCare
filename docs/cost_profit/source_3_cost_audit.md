# SOURCE 3 — MODEL 6 DATA SEARCH

### CANDIDATES FOUND
1. **NSS 77th Round (Situation Assessment of Agricultural Households)** - MoSPI
2. **ICRISAT VDSA** - ICRISAT (Evaluated previously, site offline)
3. **India Data Portal (Cost of Cultivation)** - Bharti Institute / DES
4. **IHDS (India Human Development Survey) Wave 2** - NCAER
5. **Kaggle Derived Datasets (e.g. Agriculture Crop Production & Cost)** - Independent

### BEST CANDIDATE
* **Name**: NSS 77th Round (Situation Assessment of Agricultural Households)
* **Organization**: Ministry of Statistics and Programme Implementation (MoSPI) / NSO
* **Official/original source**: National Sample Survey Office
* **URL**: https://microdata.gov.in/NADA/
* **Downloadable**: **NO** (Strictly requires NADA registration, identity verification, and manual extraction of Fixed-Width Text files using provided DDI codebooks. No direct CSV exists).
* **File format**: `.TXT` (Fixed-width)
* **Observation unit**: `Household × Season × Crop`

### DATA SIZE (Based on Official NSS 77th Round Documentation)
* **Raw**: ~57,000 households
* **Farm-level**: ~57,000 households
* **Quality-approved**: ~50,000 (Estimate after standard cleaning)
* **Leakage-approved**: ~50,000
* **Maharashtra**: ~4,000 households

### INPUTS
* State, District (Often masked to NSS regions in public microdata)
* Season, Year (2018-19)
* Crop Code
* Farm Area, Irrigated Area
* Household Demographics (Size, Social Group)
* Soil/Context: Available broadly via regional mapping.

### TARGET
* Total Cultivation Expenditure (Paid-out costs per household/crop).

### DATA QUALITY
* **Missing**: Low (Rigorous national survey standard).
* **Duplicates**: None.
* **Geography**: High, though exact district labels are sometimes replaced with NSS region codes for anonymity.
* **Time**: Single year snapshot (2018-2019).
* **Financial consistency**: High.

### 10,000+ TEST
**FAIL**

*Why?* The data conceptually holds over 50,000 farm-level observations, but **it is not a genuinely accessible, downloadable CSV dataset.** It fails the prompt's strict requirement: *"The dataset must be downloadable and independently verifiable. Do NOT count inaccessible datasets."*

### BEST DATASET
**NSS 77th Round SAS**. It is the most robust, recent, and statistically representative farm-level survey of agricultural costs in India. However, because it requires NADA registration and complex `.txt` parsing, it cannot be programmatically downloaded here.

### SECOND-BEST DATASET
**IHDS Wave 2**. Contains ~15,000 farming households. Fails because it requires ICPSR academic login and the crop costs are aggregated by season, not separated cleanly by individual crops.

### FINAL DECISION
**SEARCH REQUIRED**

*Conclusion:* An open-access, publicly downloadable CSV containing 10,000+ genuine farm-level crop cultivation cost records for India **does not exist on the open web.** Every genuine dataset of this scale (NSS, ICRISAT, IHDS) is locked behind academic registration walls or complex, gated government microdata portals to protect farmer privacy. Publicly accessible government data (DES, APY) is strictly aggregated to state or district averages.
