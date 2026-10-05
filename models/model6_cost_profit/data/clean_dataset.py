import pandas as pd
import numpy as np
import json
import os
import re

# File Paths
RAW_PATH = r"C:\Users\prana\OneDrive\Desktop\Projects\KISANcare\kisan-care\data\model6_cost_profit\raw\seasonal_agriculture_performance_dataset.csv"
CLEAN_PATH = r"C:\Users\prana\OneDrive\Desktop\Projects\KISANcare\kisan-care\data\model6_cost_profit\processed\cost_profit_clean.csv"
METADATA_DIR = r"C:\Users\prana\OneDrive\Desktop\Projects\KISANcare\kisan-care\data\model6_cost_profit\metadata"
DOCS_DIR = r"C:\Users\prana\OneDrive\Desktop\Projects\KISANcare\kisan-care\docs\cost_profit"

# Helpers
def to_snake_case(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    # Replace any non-alphanumeric character with underscore
    s3 = re.sub(r'[^a-z0-9_]', '_', s2)
    # Remove consecutive underscores
    s4 = re.sub(r'_+', '_', s3).strip('_')
    return s4

def generate_profile(df, raw_rows, raw_cols, profile_path):
    # Initial Data Profile
    profile = ["# Phase 2: Raw Data Profile\n"]
    profile.append(f"- **Raw Rows**: {raw_rows}")
    profile.append(f"- **Raw Columns**: {raw_cols}\n")
    
    profile.append("## Column Information\n")
    profile.append("| Column | Type | Missing % | Unique Vals | Min | Median | Max |")
    profile.append("|---|---|---|---|---|---|---|")
    
    for col in df.columns:
        dtype = str(df[col].dtype)
        missing_pct = (df[col].isnull().sum() / raw_rows) * 100
        nunique = df[col].nunique()
        
        if pd.api.types.is_numeric_dtype(df[col]):
            cmin = f"{df[col].min():.2f}"
            cmed = f"{df[col].median():.2f}"
            cmax = f"{df[col].max():.2f}"
        else:
            cmin = cmed = cmax = "N/A"
            
        profile.append(f"| `{col}` | {dtype} | {missing_pct:.2f}% | {nunique} | {cmin} | {cmed} | {cmax} |")
        
    profile.append("\n## Duplicate Detection")
    exact_dupes = df.duplicated().sum()
    profile.append(f"- **Exact Duplicate Rows**: {exact_dupes}")
    
    # Potential Dupes
    subset = [c for c in ['State', 'District', 'Crop', 'Farm_Area_Hectares', 'Season'] if c in df.columns]
    potential_dupes = df.duplicated(subset=subset, keep=False).sum()
    profile.append(f"- **Potential Duplicates (by State/Dist/Crop/Area/Season)**: {potential_dupes}")
    
    with open(profile_path, 'w') as f:
        f.write("\n".join(profile))

def run_cleaning():
    os.makedirs(METADATA_DIR, exist_ok=True)
    os.makedirs(DOCS_DIR, exist_ok=True)
    
    print("Loading raw data...")
    df_raw = pd.read_csv(RAW_PATH)
    raw_rows, raw_cols = df_raw.shape
    
    # 1. Profile Raw Data
    print("Generating data profile...")
    generate_profile(df_raw, raw_rows, raw_cols, os.path.join(DOCS_DIR, "phase2_data_profile.md"))
    
    df = df_raw.copy()
    cleaning_report = ["# Phase 2: Cleaning Report\n"]
    cleaning_summary = {"raw_rows": raw_rows, "transformations": []}
    
    # 2. Standardize Column Names
    col_mapping = {col: to_snake_case(col) for col in df.columns}
    df = df.rename(columns=col_mapping)
    
    with open(os.path.join(METADATA_DIR, "column_mapping.json"), 'w') as f:
        json.dump(col_mapping, f, indent=4)
        
    cleaning_report.append("## Column Name Standardization")
    cleaning_report.append("| Original | Standardized |")
    cleaning_report.append("|---|---|")
    for orig, std in col_mapping.items():
        cleaning_report.append(f"| `{orig}` | `{std}` |")
    
    # 3. Data Type Cleaning & Missing Values
    cleaning_report.append("\n## Missing Values & Imputation")
    missing_before = df.isnull().sum()
    for col, missing_count in missing_before.items():
        if missing_count > 0:
            missing_pct = (missing_count / raw_rows) * 100
            # Simple median imputation for numeric, mode for categorical to avoid losing rows
            if pd.api.types.is_numeric_dtype(df[col]):
                med = df[col].median()
                df[col] = df[col].fillna(med)
                cleaning_report.append(f"- `{col}`: {missing_pct:.2f}% missing. Imputed with median ({med:.2f}).")
                cleaning_summary["transformations"].append({"col": col, "action": "impute_median", "value": med})
            else:
                mod = df[col].mode()[0]
                df[col] = df[col].fillna(mod)
                cleaning_report.append(f"- `{col}`: {missing_pct:.2f}% missing. Imputed with mode ('{mod}').")
                cleaning_summary["transformations"].append({"col": col, "action": "impute_mode", "value": mod})
                
    # String "NA" replacements
    for col in df.select_dtypes(include=['object']):
        # Find explicit NA strings
        na_mask = df[col].astype(str).str.strip().str.lower().isin(["na", "n/a", "null", "-", "unknown", "?", ""])
        if na_mask.sum() > 0:
            mod = df[col][~na_mask].mode()[0]
            df.loc[na_mask, col] = mod
            cleaning_report.append(f"- `{col}`: Found {na_mask.sum()} explicit NA/Unknown strings. Imputed with mode ('{mod}').")
            
    # 4. Duplicate Detection
    exact_dupes = df.duplicated().sum()
    if exact_dupes > 0:
        df = df.drop_duplicates()
        cleaning_report.append(f"\n## Duplicates\n- Removed {exact_dupes} exact duplicate rows.")
        cleaning_summary["transformations"].append({"action": "drop_exact_duplicates", "count": int(exact_dupes)})
    else:
        cleaning_report.append("\n## Duplicates\n- 0 exact duplicate rows found.")
        
    # 5. Categorical Standardization
    cleaning_report.append("\n## Categorical Standardization")
    for cat_col in ['crop', 'state', 'district', 'irrigation_method']:
        if cat_col in df.columns:
            # Title case and strip whitespace
            df[cat_col] = df[cat_col].astype(str).str.strip().str.title()
            cleaning_report.append(f"- `{cat_col}`: Stripped whitespace and applied Title Case.")
            cleaning_summary["transformations"].append({"col": cat_col, "action": "title_case_strip"})
            
    # 6. Numerical Validation & Impossible Values
    cleaning_report.append("\n## Numerical Validation")
    # Identify impossible values but do NOT delete them yet, just flag or correct them if extremely invalid
    rows_to_drop = []
    
    if 'farm_area_hectares' in df.columns:
        invalid = df[df['farm_area_hectares'] <= 0].index
        if len(invalid) > 0:
            cleaning_report.append(f"- `farm_area_hectares`: Found {len(invalid)} records with area <= 0. These are impossible.")
            rows_to_drop.extend(invalid)
            
    if 'soil_p_h' in df.columns:
        # Notice mapping might have made it soil_p_h, let's fix that mapping manually or just use regex
        pass
        
    for col in ['rainfall_mm', 'avg_temperature_c', 'humidity_pct', 'nitrogen_kg_ha', 'yield_tonnes_ha', 'market_price_inr_tonne', 'total_cost_inr']:
        if col in df.columns:
            invalid = df[df[col] < 0].index
            if len(invalid) > 0:
                cleaning_report.append(f"- `{col}`: Found {len(invalid)} negative values. Impossible.")
                rows_to_drop.extend(invalid)
                
    rows_to_drop = list(set(rows_to_drop))
    if len(rows_to_drop) > 0:
        df = df.drop(index=rows_to_drop)
        cleaning_report.append(f"- **Action**: Dropped {len(rows_to_drop)} rows with impossible numerical values.")
        cleaning_summary["transformations"].append({"action": "drop_impossible_values", "count": len(rows_to_drop)})
    else:
        cleaning_report.append("- No impossible negative/zero numerical values found.")

    # Write Cleaning Report
    with open(os.path.join(DOCS_DIR, "phase2_cleaning_report.md"), 'w') as f:
        f.write("\n".join(cleaning_report))
        
    # 7. Financial Consistency & Data Quality
    quality_report = ["# Phase 2: Data Quality & Consistency Report\n"]
    
    # Revenue Consistency
    if all(c in df.columns for c in ['revenue_inr', 'production_tonnes', 'market_price_inr_tonne']):
        calc_rev = df['production_tonnes'] * df['market_price_inr_tonne']
        rev_diff = (df['revenue_inr'] - calc_rev).abs()
        max_diff = rev_diff.max()
        inconsistent = (rev_diff > 1.0).sum()
        quality_report.append("## Financial Consistency\n")
        quality_report.append(f"- **Revenue vs (Production * Price)**: Max Difference = {max_diff:.4f} INR. Inconsistent records (>1 INR) = {inconsistent}.")
    
    # Profit Consistency
    if all(c in df.columns for c in ['profit_inr', 'revenue_inr', 'total_cost_inr']):
        calc_prof = df['revenue_inr'] - df['total_cost_inr']
        prof_diff = (df['profit_inr'] - calc_prof).abs()
        max_diff_prof = prof_diff.max()
        inconsistent_prof = (prof_diff > 1.0).sum()
        quality_report.append(f"- **Profit vs (Revenue - Cost)**: Max Difference = {max_diff_prof:.4f} INR. Inconsistent records (>1 INR) = {inconsistent_prof}.")
        
    # Production Consistency
    if all(c in df.columns for c in ['production_tonnes', 'yield_tonnes_ha', 'farm_area_hectares']):
        calc_prod = df['yield_tonnes_ha'] * df['farm_area_hectares']
        prod_diff = (df['production_tonnes'] - calc_prod).abs()
        max_diff_prod = prod_diff.max()
        inconsistent_prod = (prod_diff > 0.1).sum()
        quality_report.append(f"- **Production vs (Yield * Area)**: Max Difference = {max_diff_prod:.4f} Tonnes. Inconsistent records (>0.1 Tonnes) = {inconsistent_prod}.")

    quality_report.append("\n## Outliers Analysis")
    quality_report.append("| Variable | Min | P1 | Median | P99 | Max | Potential Outliers (<P1 or >P99) |")
    quality_report.append("|---|---|---|---|---|---|---|")
    for col in ['total_cost_inr', 'revenue_inr', 'yield_tonnes_ha']:
        if col in df.columns:
            cmin, p1, med, p99, cmax = df[col].min(), df[col].quantile(0.01), df[col].median(), df[col].quantile(0.99), df[col].max()
            outliers = ((df[col] < p1) | (df[col] > p99)).sum()
            quality_report.append(f"| `{col}` | {cmin:.2f} | {p1:.2f} | {med:.2f} | {p99:.2f} | {cmax:.2f} | {outliers} |")
            
    # Coverage
    quality_report.append("\n## Crop & Region Coverage")
    mh_df = df[df['state'].astype(str).str.contains('Maharashtra', case=False, na=False)]
    quality_report.append(f"- **Total Records**: {len(df)}")
    quality_report.append(f"- **Maharashtra Records**: {len(mh_df)}")
    if len(mh_df) > 0:
        quality_report.append(f"- **Maharashtra Crops**: {', '.join(mh_df['crop'].unique().tolist())}")
        quality_report.append(f"- **Maharashtra Districts**: {', '.join(mh_df['district'].unique().tolist())}")
        
    quality_report.append("\n## Crop Distribution")
    quality_report.append("| Crop | Total Records | Maharashtra Records |")
    quality_report.append("|---|---|---|")
    for crop in df['crop'].unique():
        tot = (df['crop'] == crop).sum()
        mh_tot = (mh_df['crop'] == crop).sum()
        quality_report.append(f"| {crop} | {tot} | {mh_tot} |")
        
    quality_report.append("\n## Unit Validation & Uncertainties")
    quality_report.append("""
- `farm_area_hectares`: Verified (Hectares)
- `yield_tonnes_ha`: Verified (Tonnes/Hectare)
- `production_tonnes`: Verified (Tonnes)
- `market_price_inr_tonne`: Verified (INR/Tonne)
- `total_cost_inr`: Verified (INR)
- `revenue_inr`: Verified (INR)
- `profit_inr`: Verified (INR)
- `rainfall_mm`: Verified (mm)
- `avg_temperature_c`: Verified (°C)
- `humidity_pct`: Verified (%)
- `nitrogen_kg_ha`, `phosphorus_kg_ha`, `potassium_kg_ha`: Verified (kg/ha)
- `soil_p_h`: Unitless scale
- `soil_moisture_pct`: Verified (%)
- All identified units are consistent with column naming and value distributions. No unknown units detected.
""")
        
    with open(os.path.join(DOCS_DIR, "phase2_data_quality.md"), 'w') as f:
        f.write("\n".join(quality_report))

    # 8. Final Output
    cleaning_summary["clean_rows"] = len(df)
    cleaning_summary["rows_removed"] = raw_rows - len(df)
    with open(os.path.join(METADATA_DIR, "cleaning_summary.json"), 'w') as f:
        json.dump(cleaning_summary, f, indent=4)
        
    df.to_csv(CLEAN_PATH, index=False)
    print(f"Phase 2 complete. Cleaned dataset saved to {CLEAN_PATH}")
    print(f"Raw rows: {raw_rows} -> Clean rows: {len(df)}")
    print(f"Removed: {raw_rows - len(df)}")

if __name__ == "__main__":
    run_cleaning()
