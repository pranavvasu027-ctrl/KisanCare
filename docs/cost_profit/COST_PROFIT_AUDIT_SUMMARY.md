# COST_PROFIT_AUDIT_SUMMARY

PRIMARY DATASET: Repo 3 (Kusuma-97 / Agriculture_DA_VIOS - seasonal_agriculture_performance_dataset.csv)
SECONDARY DATASET: Repo 1 (shreyzo - crop_production.csv) for supplemental yield data only.
CODE REFERENCE: Repo 2 (Samarth-2003-web - app.py) for the Hybrid architecture implementation.
REJECTED DATASETS: Repo 4 (mithil-exe - lacks yield, too small), Repo 1 (datafile.csv - too small, severe leakage).

BEST TARGET: `Yield_Tonnes_Ha`, `Market_Price_INR_Tonne`, `Total_Cost_INR` (Profit must be calculated deterministically).
BEST FEATURES: `Farm_Area_Hectares`, `Rainfall_mm`, `Avg_Temperature_C`, `Soil_pH`, `Nitrogen_kg_ha`, `Phosphorus_kg_ha`, `Potassium_kg_ha`, `Irrigation_Method`.

NUMBER OF ROWS: 4,000 (Repo 3 Primary), 246,091 (Repo 1 Secondary)
NUMBER OF CROPS: 8 major crops (Repo 3)
NUMBER OF STATES: 8 states (Repo 3)
MAHARASHTRA RECORDS: 512 (Repo 3), 12,628 (Repo 1 Secondary)

DATA QUALITY: Excellent mathematical consistency in Repo 3. 
LEAKAGE RISK: High risk if Profit is modeled directly. Repo 1 code contains severe leakage (using costs to predict profit labels mathematically derived from those costs). Repo 3 has zero variance between calculated profit and target profit, meaning a direct model would leak 100%.

RECOMMENDED ARCHITECTURE: Architecture C (Hybrid). Train independent ML models for Yield, Market Price, and Total Cost. Use a deterministic economic engine to calculate Revenue, Profit, and ROI.

NEXT STEP: Review this audit report. Once approved, the exact next step is to copy `seasonal_agriculture_performance_dataset.csv` into the KisanCare project, implement a cleaning/mapping script to align its columns with the KisanCare Farm structure, and build the scaffolding for Architecture C.
