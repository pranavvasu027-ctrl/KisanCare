import pandas as pd
import numpy as np
import os
import json

RAW_FILE = r"C:\Users\prana\OneDrive\Desktop\Projects\KISANcare\kisan-care\data\model6_cost_profit\raw\seasonal_agriculture_performance_dataset.csv"
PROCESSED_DIR = r"C:\Users\prana\OneDrive\Desktop\Projects\KISANcare\kisan-care\data\model6_cost_profit\processed"
DOCS_DIR = r"C:\Users\prana\OneDrive\Desktop\Projects\KISANcare\kisan-care\docs\cost_profit"
METADATA_DIR = r"C:\Users\prana\OneDrive\Desktop\Projects\KISANcare\kisan-care\metadata"

def clean():
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    os.makedirs(DOCS_DIR, exist_ok=True)
    os.makedirs(METADATA_DIR, exist_ok=True)
    
    df = pd.read_csv(RAW_FILE)
    original_rows = len(df)
    
    # 1. Fix Yield Issues
    # Yield_Tonnes_Ha = Production_Tonnes / Farm_Area_Hectares
    calc_prod = df['Yield_Tonnes_Ha'] * df['Farm_Area_Hectares']
    mismatches = abs(calc_prod - df['Production_Tonnes']) > 1
    rows_corrected = mismatches.sum()
    
    # Apply fix
    df.loc[mismatches, 'Yield_Tonnes_Ha'] = df.loc[mismatches, 'Production_Tonnes'] / df.loc[mismatches, 'Farm_Area_Hectares']
    
    # Verify
    new_calc_prod = df['Yield_Tonnes_Ha'] * df['Farm_Area_Hectares']
    new_mismatches = abs(new_calc_prod - df['Production_Tonnes']) > 1
    rows_unresolved = new_mismatches.sum()
    max_diff = abs(new_calc_prod - df['Production_Tonnes']).max() if original_rows > 0 else 0
    
    # 2. Geographic Quality Flag
    # District is excluded due to geographic integrity failure (3485 rows suspicious)
    
    # 3. Leakage Audit for Target: Total_Cost_INR
    exclude_features = [
        "Profit_INR", "Revenue_INR", "Production_Tonnes", "Yield_Tonnes_Ha", 
        "Market_Price_INR_Tonne", "District", "Farm_ID"
    ]
    
    for col in df.columns:
        if 'Cost' in col and col != 'Total_Cost_INR':
            exclude_features.append(col)
            
    final_features = [c for c in df.columns if c not in exclude_features and c != 'Total_Cost_INR']
    
    feature_policy = []
    for col in df.columns:
        if col == 'Total_Cost_INR':
            feature_policy.append({"Feature": col, "Action": "TARGET", "Reason": "Primary prediction target."})
        elif col in exclude_features:
            reason = "Post-harvest leakage"
            if col == 'District':
                reason = "Suspicious geographic mapping (3485/4000 invalid)"
            elif col == 'Farm_ID':
                reason = "Identifier"
            feature_policy.append({"Feature": col, "Action": "EXCLUDE", "Reason": reason})
        else:
            feature_policy.append({"Feature": col, "Action": "INCLUDE", "Reason": "Valid pre-harvest input feature."})
            
    pd.DataFrame(feature_policy).to_csv(os.path.join(METADATA_DIR, "model6_prototype_feature_policy.csv"), index=False)
    
    # Save clean dataset
    df.to_csv(os.path.join(PROCESSED_DIR, "prototype_cost_training.csv"), index=False)
    
    # Validation Metrics
    mh_rows = int(df['State'].str.contains('Maharashtra', case=False, na=False).sum())
    v1_crops = ["Rice", "Wheat", "Maize", "Soybean", "Cotton", "Sugarcane", "Chickpea", "Pigeon Pea", "Groundnut", "Sorghum", "Pearl Millet", "Green Gram", "Black Gram", "Mustard", "Onion", "Potato", "Tomato", "Banana", "Mango", "Grapes"]
    available_crops = df['Crop'].unique().tolist()
    covered_v1 = [c for c in v1_crops if c in available_crops]
    
    val_strategy = "GroupKFold by 'State' or 'Crop' to ensure generalization, or TimeSeriesSplit if temporal data exists."
    
    metadata = {
        "status": "CLEAN_DATA_READY",
        "original_rows": original_rows,
        "clean_rows": len(df),
        "rows_corrected": int(rows_corrected),
        "rows_unresolved": int(rows_unresolved),
        "max_absolute_difference": float(max_diff),
        "rows_rejected": 0,
        "final_features": final_features,
        "excluded_features": exclude_features,
        "target": "Total_Cost_INR",
        "maharashtra_rows": mh_rows,
        "v1_crop_coverage": covered_v1,
        "geographic_limitations": "District mappings are highly suspicious; District excluded from predictive features.",
        "recommended_validation_strategy": val_strategy
    }
    with open(os.path.join(METADATA_DIR, "model6_prototype_cleaning_summary.json"), 'w') as f:
        json.dump(metadata, f, indent=4)
        
    md = f"""# Phase 2 — Prototype Dataset Cleaning & Preparation

## 1. Source Dataset
* **Original Rows:** {original_rows}
* **Clean Rows:** {len(df)}

## 2. Yield Recalculation (Phase C Fix)
Exactly {rows_corrected} rows had `Yield × Area != Production` due to previous median-imputation. These were mathematically corrected by recalculating `Yield = Production / Area`.
* **Rows Corrected:** {rows_corrected}
* **Rows Unresolved:** {rows_unresolved}
* **Maximum Absolute Difference Post-Fix:** {max_diff:.4f} (Floating point precision)

## 3. Geographic Limitations
Due to previous audits flagging ~3,485 District mappings as hallucinated/suspicious, `District` has been explicitly **EXCLUDED** from the final predictive features. `State` remains a trusted macroscopic feature.

## 4. Target & Leakage Policy
**Target:** `Total_Cost_INR`
To prevent the model from cheating, all post-harvest metrics (`Profit_INR`, `Revenue_INR`, `Production_Tonnes`, `Yield_Tonnes_Ha`) and post-harvest market indicators (`Market_Price_INR_Tonne`) have been strictly excluded from the Cost Model inputs. See `model6_prototype_feature_policy.csv` for the full breakdown.

## 5. Coverage
* **Maharashtra Rows:** {mh_rows}
* **KISANcare V1 Crops Supported:** {len(covered_v1)} / 20

## 6. Recommended Validation Strategy
Because the data has a hierarchical structure, a **GroupKFold (grouped by State or Crop)** is recommended to test if the model learns generalizable economic rules rather than memorizing specific state-crop combinations.

## 7. Final Status
**CLEAN_DATA_READY**
"""
    with open(os.path.join(DOCS_DIR, "phase2_prototype_cleaning.md"), "w", encoding="utf-8") as f:
        f.write(md)
        
    print("Cleaning Complete.")

if __name__ == "__main__":
    clean()
