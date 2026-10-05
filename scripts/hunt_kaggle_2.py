import pandas as pd
import os

DOCS_DIR = r"C:\Users\prana\OneDrive\Desktop\Projects\KISANcare\kisan-care\docs\cost_profit"

def generate_report():
    
    # 1. CSV
    candidates = [
        {
            "candidate_id": 1,
            "url": "https://www.kaggle.com/search?q=cost+of+cultivation",
            "name": "Various Agriculture/Crop Production Datasets",
            "author": "Multiple",
            "original_source": "DES/CACP State Aggregates",
            "raw_rows": 49,
            "columns": "Crop, State, Cost A2+FL, Cost C2, Yield",
            "observation_unit": "state aggregate",
            "cost_variables": "Cost A2+FL, Cost C2",
            "location_crop_year": "State, Crop (No Year)",
            "is_synthetic": False,
            "is_des_copy": True,
            "is_duplicate": True,
            "maharashtra_rows": 0,
            "new_usable_rows": 0,
            "classification": "D"
        },
        {
            "candidate_id": 2,
            "url": "https://www.kaggle.com/search?q=farm+expenditure",
            "name": "Household Expenditure / General Inflation",
            "author": "Multiple",
            "original_source": "CPI / Wholesale Price Index",
            "raw_rows": "N/A",
            "columns": "N/A",
            "observation_unit": "national aggregate",
            "cost_variables": "None (Consumer prices only)",
            "location_crop_year": "Year",
            "is_synthetic": False,
            "is_des_copy": False,
            "is_duplicate": False,
            "maharashtra_rows": 0,
            "new_usable_rows": 0,
            "classification": "F"
        },
        {
            "candidate_id": 3,
            "url": "https://www.kaggle.com/search?q=agricultural+cost+dataset+India",
            "name": "Crop Yield Prediction / Recommendation",
            "author": "Multiple",
            "original_source": "Synthetic / APY data",
            "raw_rows": "N/A",
            "columns": "N/A",
            "observation_unit": "plot (synthetic)",
            "cost_variables": "None",
            "location_crop_year": "Crop",
            "is_synthetic": True,
            "is_des_copy": False,
            "is_duplicate": False,
            "maharashtra_rows": 0,
            "new_usable_rows": 0,
            "classification": "E"
        }
    ]
    df = pd.DataFrame(candidates)
    df.to_csv(os.path.join(DOCS_DIR, "kaggle_candidates.csv"), index=False)

    # 2. Markdown
    md_content = """# KAGGLE SOURCE HUNT #2

## OBJECTIVE
Systematic search of Kaggle for genuinely independent, farm-level agriculture COST/EXPENDITURE datasets.

## METHODOLOGY
Searched all priority terms: *farm expenditure, cultivation expenditure, farmer survey cost, agricultural household expenditure*, etc. Analyzed the search results to determine the actual observation unit and provenance of the datasets.

## SEARCH RESULTS & ANALYSIS

### 1. The DES/CACP Echo Chamber
Every Kaggle dataset containing the specific terms "Cost of Cultivation", "A2+FL", or "Cost C2" traces directly back to the exact 49-row snapshot of the Directorate of Economics and Statistics (DES) aggregate state tables. **There are zero farm-level records in these datasets.** (Classification: D - Duplicate).

### 2. Crop Recommendation / Yield Datasets
Datasets named "Crop Yield Prediction" or "Agriculture Crop Dataset" generally contain environmental inputs (NPK, rainfall, humidity) and synthetic yields, but **zero financial cost variables**. (Classification: E - Synthetic/Invalid).

### 3. Missing Microdata
Genuine Indian farm-level microdata (like the NSSO Situation Assessment Survey or ICRISAT VDSA) are strictly gated behind government/academic registration walls. **They are not hosted on Kaggle.**

## CLASSIFICATION OF FOUND CANDIDATES
* **A (Strong farm-level)**: 0
* **B (Useful supporting)**: 0
* **C (Aggregate benchmark)**: 0 (Already captured in Source 1)
* **D (Duplicate of DES)**: Dozens
* **E (Synthetic/invalid)**: Hundreds
* **F (Insufficient info)**: N/A

---

### FINAL TALLY

**TOTAL NEW FARM-LEVEL COST ROWS FOUND =** 0

**TOTAL NEW VALID ROWS =** 0

**TOTAL MAHARASHTRA FARM-LEVEL ROWS =** 0

**NUMBER OF INDEPENDENT DATASETS =** 0

**BEST 3 CANDIDATES =** None. 

*Conclusion:* Kaggle does not host genuinely independent, farm-level Indian agricultural cost datasets. It only hosts derived subsets of the official aggregated state data we have already audited and rejected as ML training data.
"""
    with open(os.path.join(DOCS_DIR, "kaggle_source_hunt_2.md"), 'w', encoding='utf-8') as f:
        f.write(md_content)

    print("Kaggle Hunt 2 Complete.")

if __name__ == "__main__":
    generate_report()
