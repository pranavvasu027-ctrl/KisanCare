import pandas as pd
import json
import os

RAW_DATA_PATH = r"C:\Users\prana\.gemini\antigravity\brain\c717cd51-3f5e-497a-9b25-ae28bd0f1741\data\model6_cost_profit\raw\seasonal_agriculture_performance_dataset.csv"
PROCESSED_DATA_PATH = r"C:\Users\prana\.gemini\antigravity\brain\c717cd51-3f5e-497a-9b25-ae28bd0f1741\data\model6_cost_profit\processed\cost_profit_master.csv"
DICT_PATH = r"C:\Users\prana\.gemini\antigravity\brain\c717cd51-3f5e-497a-9b25-ae28bd0f1741\data\model6_cost_profit\metadata\data_dictionary.json"
MD_DICT_PATH = r"C:\Users\prana\.gemini\antigravity\brain\c717cd51-3f5e-497a-9b25-ae28bd0f1741\docs\cost_profit\data_dictionary.md"
PREPROCESSING_MD = r"C:\Users\prana\.gemini\antigravity\brain\c717cd51-3f5e-497a-9b25-ae28bd0f1741\docs\cost_profit\preprocessing.md"

def run_etl():
    df = pd.read_csv(RAW_DATA_PATH)
    initial_rows = len(df)
    
    preprocessing_log = []
    preprocessing_log.append(f"# Preprocessing Log\n\n* **Initial Rows**: {initial_rows}")
    
    # 1. Missing Values
    missing = df.isnull().sum()
    missing_cols = missing[missing > 0]
    preprocessing_log.append(f"* **Missing Values Detected**: {missing_cols.to_dict()}")
    
    # Impute missing continuous variables with median
    for col in missing_cols.index:
        median_val = df[col].median()
        df[col] = df[col].fillna(median_val)
        preprocessing_log.append(f"* **Imputed**: Column `{col}` with median `{median_val}`")
    
    # 2. Duplicates
    dupes = df.duplicated().sum()
    preprocessing_log.append(f"* **Duplicates Detected**: {dupes}")
    if dupes > 0:
        df = df.drop_duplicates()
        preprocessing_log.append("* **Action**: Removed duplicate rows.")
        
    # 3. Impossible Values / Verification
    # Ensure no negative costs or areas
    invalid_area = (df['Farm_Area_Hectares'] <= 0).sum()
    invalid_cost = (df['Total_Cost_INR'] <= 0).sum()
    preprocessing_log.append(f"* **Invalid Area Count**: {invalid_area}")
    preprocessing_log.append(f"* **Invalid Cost Count**: {invalid_cost}")
    
    if invalid_area > 0 or invalid_cost > 0:
        df = df[(df['Farm_Area_Hectares'] > 0) & (df['Total_Cost_INR'] > 0)]
        preprocessing_log.append("* **Action**: Removed rows with zero or negative Area/Cost.")
        
    # 4. Outliers
    # Keep it simple: cap extreme outliers using 1st and 99th percentiles for numerical columns
    num_cols = df.select_dtypes(include=['float64', 'int64']).columns
    for col in num_cols:
        p1 = df[col].quantile(0.01)
        p99 = df[col].quantile(0.99)
        outliers = ((df[col] < p1) | (df[col] > p99)).sum()
        if outliers > 0:
            df[col] = df[col].clip(lower=p1, upper=p99)
            preprocessing_log.append(f"* **Outliers Capped**: Column `{col}` capped at 1st percentile ({p1:.2f}) and 99th percentile ({p99:.2f})")

    # 5. Drop Leakage Features
    leakage_features = [
        'Farm_ID', 
        'Profit_INR', 
        'Revenue_INR', 
        'Yield_Tonnes_Ha', 
        'Production_Tonnes', 
        'Market_Price_INR_Tonne',
        'Water_Efficiency_t_per_1000m3',
        'Water_Used_m3'
    ]
    df = df.drop(columns=leakage_features, errors='ignore')
    preprocessing_log.append(f"* **Leakage Features Dropped**: {leakage_features}")
    
    # Verify MH records and Crops
    mh_records = df[df['State'].str.contains('Maharashtra', case=False, na=False)].shape[0]
    preprocessing_log.append(f"* **Maharashtra Records**: {mh_records}")
    preprocessing_log.append(f"* **Final Rows**: {len(df)}")
    
    # Save Processed
    df.to_csv(PROCESSED_DATA_PATH, index=False)
    
    with open(PREPROCESSING_MD, 'w') as f:
        f.write("\n".join(preprocessing_log))
        
    # Data Dictionary
    data_dict = {
        "columns": [
            {"name": col, "type": str(df[col].dtype), "sample": str(df[col].iloc[0])}
            for col in df.columns
        ]
    }
    with open(DICT_PATH, 'w') as f:
        json.dump(data_dict, f, indent=4)
        
    md_dict = "# Data Dictionary\n\n| Column | Type | Sample |\n|---|---|---|\n"
    for col in data_dict["columns"]:
        md_dict += f"| `{col['name']}` | `{col['type']}` | `{col['sample']}` |\n"
    with open(MD_DICT_PATH, 'w') as f:
        f.write(md_dict)
        
    print("ETL complete. Master dataset generated.")

if __name__ == "__main__":
    run_etl()
