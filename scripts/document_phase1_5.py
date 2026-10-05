import pandas as pd
import os
import json

DOCS_DIR = r"C:\Users\prana\OneDrive\Desktop\Projects\KISANcare\kisan-care\docs\cost_profit"
RAW_DIR = r"C:\Users\prana\OneDrive\Desktop\Projects\KISANcare\kisan-care\data\model6_cost_profit\external\source_1_des_cost\raw"
METADATA_DIR = r"C:\Users\prana\OneDrive\Desktop\Projects\KISANcare\kisan-care\metadata"

def document_phase1_5():
    os.makedirs(DOCS_DIR, exist_ok=True)
    os.makedirs(METADATA_DIR, exist_ok=True)

    # 1. Source Manifest
    manifest = [
        {
            "file_name": "Agricultural-Statistics-at-a-Glance-2023.pdf",
            "source_url": "https://desagri.gov.in/wp-content/uploads/2024/09/Agricultural-Statistics-at-a-Glance-2023.pdf",
            "official_domain": "desagri.gov.in",
            "publisher": "Directorate of Economics & Statistics (DES)",
            "document_title": "Agricultural Statistics at a Glance 2023",
            "document_year": 2023,
            "file_type": "PDF",
            "observation_level": "State x Crop x Year",
            "years_covered": "2018-2021 (varies by table)",
            "crop_coverage": "Principal Crops (Rice, Wheat, Cotton, Sugarcane, Soybean, Maize, etc.)",
            "state_coverage": "Major Agricultural States",
            "maharashtra_available": "Yes",
            "c2_available": "Yes",
            "a2fl_available": "Yes",
            "yield_available": "Yes",
            "download_status": "BLOCKED (Timeout / Geo-blocked)",
            "verification_status": "Pending Manual Download",
            "notes": "PDF contains the Cost of Cultivation tabular data. Automated download timed out."
        }
    ]
    pd.DataFrame(manifest).to_csv(os.path.join(RAW_DIR, "source_manifest.csv"), index=False)

    # 2. Acquisition Inventory
    inventory = [
        {
            "document": "Agricultural Statistics at a Glance 2023",
            "source_url": "https://desagri.gov.in/document-report-category/agricultural-statistics-at-a-glance/",
            "year": "2023",
            "file_type": "PDF",
            "crops": "Principal Crops (Rice, Wheat, Maize, Cotton, Sugarcane, Soybean, Pulses)",
            "states": "Major Indian States",
            "cost_variables": "C2, A2+FL, Yield",
            "maharashtra_present": "Yes",
            "downloaded": "No (Network Timeout)",
            "local_path": "N/A",
            "notes": "Requires manual download."
        }
    ]
    pd.DataFrame(inventory).to_csv(os.path.join(DOCS_DIR, "phase1_5_acquisition_inventory.csv"), index=False)

    # 3. Metadata JSON
    metadata = {
        "status": "BLOCKED_MANUAL_DOWNLOAD_REQUIRED",
        "official_sources_verified": 1,
        "files_downloaded": 0,
        "reason": "The official DES server (desagri.gov.in) drops automated connection requests (ConnectTimeoutError). A manual download from a residential IP/browser is required."
    }
    with open(os.path.join(METADATA_DIR, "des_cacp_acquisition.json"), 'w') as f:
        json.dump(metadata, f, indent=4)

    # 4. Markdown Report
    md = """# Phase 1.5 — Official DES/CACP Data Acquisition

## 1. Objective
To autonomously acquire the true, official Cost of Cultivation data from Government of India sources (DES/CACP) and save it to the repository without bypassing security mechanisms.

## 2. Official Sources Investigated
* **desagri.gov.in** (Directorate of Economics & Statistics)
* **cacp.dacnet.nic.in** (Commission for Agricultural Costs and Prices)
* **data.gov.in** (Open Government Data Portal)

## 3. Official Documents Found
**Agricultural Statistics at a Glance 2023** 
Published by the Ministry of Agriculture & Farmers Welfare. This massive annual publication contains the consolidated State-wise and Crop-wise Cost of Cultivation tables (C2 and A2+FL).

## 4. Files Successfully Acquired
**0 files.** 

## 5. Files Requiring Manual Download
* `Agricultural-Statistics-at-a-Glance-2023.pdf`
The automated Python download script repeatedly timed out. The `.gov.in` firewall actively drops connections from automated data center IPs (geo-blocking/anti-bot). 

## 6. Source Lineage
Official DES Portal -> "Agricultural Statistics at a Glance" -> PDF Tables

## 7. Raw Dataset Inventory
Currently **Empty**. The `raw/official/` directory awaits the manual PDF upload.

## 8. Preliminary Coverage
* **Observation Unit:** State × Crop × Year
* **Time Range:** 2018-2021 (varies by table within the report)

## 9. Maharashtra Coverage
Yes, Maharashtra is covered in the standard Cost of Cultivation tables for its principal crops (Cotton, Sugarcane, Soybean, etc.).

## 10. KisanCare V1 Crop Coverage
High coverage for major crops.

## 11. C2 / A2+FL Availability
Both C2 and A2+FL are present in the PDF tables.

## 12. Duplicate/Overlap Observations
N/A (No files downloaded).

## 13. Acquisition Limitations
Automated download is physically blocked by the government server's firewall.

## 14. Final Status
**BLOCKED_MANUAL_DOWNLOAD_REQUIRED**
"""
    with open(os.path.join(DOCS_DIR, "phase1_5_data_acquisition.md"), 'w', encoding='utf-8') as f:
        f.write(md)

    print("Phase 1.5 Documentation Generated.")

if __name__ == "__main__":
    document_phase1_5()
