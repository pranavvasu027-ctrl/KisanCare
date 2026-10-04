# 12 — Horticulture Alternative Research

**Date:** 2026-10-04  
**Task:** Research alternative authoritative datasets to resolve the coverage gap for Tomato, Mango, and Grapes without dropping the 20-crop V1 requirement.  
**Author:** Antigravity (AI-assisted research)  
**Branch:** `research-reports`  

---

## 1. The Agronomic Reality of the Target Crops

Before evaluating datasets, we must establish the agronomic nature of the three deficient crops, as this heavily impacts the "Season" feature constraint:

1.  **Mango:** A perennial tree. It does not have a distinct planting season (like Kharif or Rabi) each year. It occupies land year-round.
2.  **Grapes:** A perennial vine. Like Mango, it occupies land year-round, despite having specific harvest windows.
3.  **Tomato:** A highly seasonal crop. It can be grown in Kharif, Rabi, or Summer depending on the region's climate.

**Conclusion on "Annual" Data Constraints:** 
If an alternative dataset only provides *Annual* data:
*   For **Mango and Grapes**, it is perfectly scientifically compatible with the UPAg dataset. We can legitimately assign the season as `"Whole Year"` (a label UPAg already uses for sugarcane and orchards).
*   For **Tomato**, annual data is a **major limitation**. Assigning "Whole Year" to Tomato destroys the model's ability to recommend *when* in the year a farmer should plant it.

---

## 2. Comparison of Viable Options

### Option A: UPAg APY Only
*   **Source:** Ministry of Agriculture (DES).
*   **Crop Coverage:** 17 crops perfectly. Fails on Mango (88 rows), Tomato (78 rows), Grapes (12 rows).
*   **Records/Geography:** Unusable for the 3 target crops.
*   **Season Availability:** Native (Kharif, Rabi, Summer, Whole Year, etc.).
*   **Compatibility & Leakage:** Perfect internal consistency. Zero leakage.
*   **Implementation Complexity:** Zero (Dataset is already standardized).
*   **Verdict:** Mathematically impossible to support the 20-crop requirement.

### Option B: UPAg APY + National Horticulture Board (NHB)
*   **Source:** NHB Interactive Query Module / `data.gov.in` Horticulture Statistics.
*   **Crop Coverage:** Excellent for Mango, Tomato, Grapes.
*   **Records/Geography:** Contains district-wise area and production estimates across all major producing states (e.g., Maharashtra for grapes, AP/UP for mango).
*   **Season Availability:** **Annual Only.** The NHB reports total yearly production per district, rarely breaking it down by Kharif/Rabi.
*   **Compatibility:** High for Mango/Grapes (can safely map to "Whole Year"). **Poor for Tomato** (loses planting season granularity).
*   **Leakage Risk:** Low, provided we align the NHB reporting year with the UPAg crop year.
*   **Geographic Consistency:** High, NHB uses standard government district names.
*   **Implementation Complexity:** High. Requires web scraping or parsing complex NHB PDFs/Excel files, normalizing district strings, and handling the Tomato season deficit.

### Option C: UPAg APY + State-Level Horticulture Directorates
*   **Source:** Individual state open data portals (e.g., MahaAgri, AP Dept of Horticulture, Karnataka KSDA).
*   **Crop Coverage:** Perfect for the crops grown in those specific states.
*   **Records/Geography:** High fidelity district-level data.
*   **Season Availability:** **High.** State departments usually track seasonal planting (e.g., Rabi Tomato vs Kharif Tomato).
*   **Compatibility:** Excellent agronomically.
*   **Leakage Risk:** Low.
*   **Geographic Consistency:** Fragmented. Each state uses different formatting, naming conventions, and languages.
*   **Implementation Complexity:** Extreme. Requires manually hunting, downloading, cleaning, and standardizing 10+ different state-level datasets to build a pseudo-national database for 3 crops.

### Option D: A Pre-Fused Third-Party Dataset (e.g., ICRISAT / Kaggle)
*   **Source:** Academic or community-curated datasets.
*   **Crop Coverage:** ICRISAT DLD heavily favors field crops (cereals/pulses) and lacks comprehensive district-level Tomato/Grapes. Kaggle datasets (like the one used by Harvestify) cover all 20, but rely on flawed synthetic NPK generation rather than real area/production statistics.
*   **Implementation Complexity:** N/A (No scientifically defensible option exists that natively solves the horticulture problem with seasonal granularity).

---

## 3. Presentation to P27 for Decision

The 20-crop requirement remains locked. To fulfill it, we must inject external data for Tomato, Mango, and Grapes. 

Please review the viable paths forward and authorize one:

*   **PATH 1 (Execute Option B):** Use NHB data. Accept the limitation that **Tomato** will be modeled as a `"Whole Year"` crop (like Mango and Grapes), meaning the model will recommend *where* to grow Tomato, but not *which season* to plant it in. (High implementation effort, minor agronomic compromise).
*   **PATH 2 (Execute Option C):** Source data directly from State Horticulture portals to preserve exact planting seasons for Tomato. (Extreme implementation effort, high precision).
*   **PATH 3 (Re-evaluate Requirement):** Acknowledge the extreme complexity of mixing field-crop and horticulture data pipelines, and temporarily reduce V1 to a 17-crop model, pushing horticulture to V2. 

**Awaiting P27 direction on how to proceed.**
