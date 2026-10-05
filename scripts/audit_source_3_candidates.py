import pandas as pd
import os

candidates = [
    {
        "source_name": "NSS 77th Round (Situation Assessment of Agricultural Households)",
        "organization": "MoSPI / NSO",
        "url": "https://microdata.gov.in/NADA/",
        "format": "Fixed-width Text (requires DDI parsing)",
        "raw_rows": 57000,
        "farm_level_rows": 57000,
        "quality_rows": 50000,
        "leakage_approved_rows": 50000,
        "maharashtra_rows": 4000,
        "crops": "Major Indian Crops",
        "years": "2018-2019",
        "cost_target": "Total Cultivation Expenditure (Paid-out)",
        "downloadable": "No (Requires NADA registration and manual parsing)",
        "provenance": "Official National Survey",
        "quality_score": 90,
        "recommendation": "BEST CANDIDATE (But not public CSV)"
    },
    {
        "source_name": "ICRISAT VDSA",
        "organization": "ICRISAT",
        "url": "https://vdsa.icrisat.org/",
        "format": "CSV/DTA",
        "raw_rows": 25000,
        "farm_level_rows": 25000,
        "quality_rows": 20000,
        "leakage_approved_rows": 20000,
        "maharashtra_rows": 12000,
        "crops": "Cereals, Pulses, Cash Crops",
        "years": "1975-2014",
        "cost_target": "Total Paid-out and Imputed Costs",
        "downloadable": "No (Site Offline / Requires Academic Registration)",
        "provenance": "Official Research Panel",
        "quality_score": 95,
        "recommendation": "BEST CANDIDATE (Inaccessible)"
    },
    {
        "source_name": "India Data Portal (Cost of Cultivation)",
        "organization": "Bharti Institute (ISB) / DES",
        "url": "https://indiadataportal.com/",
        "format": "CSV",
        "raw_rows": 3000,
        "farm_level_rows": 0,
        "quality_rows": 0,
        "leakage_approved_rows": 0,
        "maharashtra_rows": 0,
        "crops": "Principal Crops",
        "years": "2000-2020",
        "cost_target": "Cost A2, C2 per hectare",
        "downloadable": "Yes",
        "provenance": "DES Aggregated Summaries",
        "quality_score": 20,
        "recommendation": "REJECT (Aggregated only)"
    },
    {
        "source_name": "Kaggle: Agriculture Crop Production & Cost",
        "organization": "Independent / Derived",
        "url": "https://www.kaggle.com/",
        "format": "CSV",
        "raw_rows": 49,
        "farm_level_rows": 0,
        "quality_rows": 0,
        "leakage_approved_rows": 0,
        "maharashtra_rows": 0,
        "crops": "Mixed",
        "years": "Mixed",
        "cost_target": "Cost of Cultivation",
        "downloadable": "Yes",
        "provenance": "Copied from DES state tables",
        "quality_score": 10,
        "recommendation": "REJECT (Duplicate of Source 1)"
    },
    {
        "source_name": "IHDS (India Human Development Survey) Wave 2",
        "organization": "NCAER / Univ of Maryland",
        "url": "https://www.icpsr.umich.edu/",
        "format": "DTA / CSV",
        "raw_rows": 42000,
        "farm_level_rows": 15000,
        "quality_rows": 12000,
        "leakage_approved_rows": 12000,
        "maharashtra_rows": 1500,
        "crops": "Aggregated by season",
        "years": "2011-2012",
        "cost_target": "Farm Expenses",
        "downloadable": "No (Requires ICPSR login)",
        "provenance": "Independent Survey",
        "quality_score": 75,
        "recommendation": "SECONDARY (Not publicly downloadable)"
    }
]

df = pd.DataFrame(candidates)
os.makedirs(r"C:\Users\prana\OneDrive\Desktop\Projects\KISANcare\kisan-care\data\model6_cost_profit\external", exist_ok=True)
df.to_csv(r"C:\Users\prana\OneDrive\Desktop\Projects\KISANcare\kisan-care\data\model6_cost_profit\external\source_3_candidates.csv", index=False)
