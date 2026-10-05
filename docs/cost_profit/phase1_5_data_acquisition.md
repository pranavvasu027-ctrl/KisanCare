# Phase 1.5 — Official DES/CACP Data Acquisition

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
