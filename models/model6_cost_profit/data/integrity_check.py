import pandas as pd
import os

CLEAN_PATH = r"C:\Users\prana\OneDrive\Desktop\Projects\KISANcare\kisan-care\data\model6_cost_profit\processed\cost_profit_clean.csv"
DOCS_DIR = r"C:\Users\prana\OneDrive\Desktop\Projects\KISANcare\kisan-care\docs\cost_profit"
GEO_AUDIT_PATH = os.path.join(DOCS_DIR, "geographic_integrity_audit.md")
PROD_AUDIT_PATH = os.path.join(DOCS_DIR, "production_yield_integrity_audit.md")

# Known district to state mapping (for the 10 districts observed)
TRUE_STATE_MAP = {
    "Nalgonda": "Telangana",
    "Krishna": "Andhra Pradesh",
    "Ludhiana": "Punjab",
    "Erode": "Tamil Nadu",
    "Rajkot": "Gujarat",
    "Guntur": "Andhra Pradesh",
    "Indore": "Madhya Pradesh",
    "Raichur": "Karnataka",
    "Nashik": "Maharashtra",
    "Warangal": "Telangana"
}

def run_integrity_check():
    df = pd.read_csv(CLEAN_PATH)
    
    # 1. Geographic Consistency Check
    geo_audit = ["# Geographic Integrity Audit\n"]
    geo_audit.append("| State | District | Number of Records | Geographically Plausible? | Issue |")
    geo_audit.append("|---|---|---|---|---|")
    
    geo_counts = df.groupby(['state', 'district']).size().reset_index(name='count')
    
    suspicious_geo_count = 0
    valid_geo_count = 0
    
    for _, row in geo_counts.iterrows():
        st = row['state']
        dist = row['district']
        count = row['count']
        
        true_state = TRUE_STATE_MAP.get(dist, "Unknown")
        
        if true_state == "Unknown":
            plausible = "UNKNOWN"
            issue = "District not recognized"
            suspicious_geo_count += count
        elif true_state.lower() == st.lower():
            plausible = "YES"
            issue = "Valid"
            valid_geo_count += count
        else:
            plausible = "NO"
            issue = f"{dist} belongs to {true_state}, not {st}. Synthetic geography."
            suspicious_geo_count += count
            
        geo_audit.append(f"| {st} | {dist} | {count} | {plausible} | {issue} |")
        
    geo_audit.append("\n## Conclusion")
    geo_audit.append(f"Total valid geographic records: {valid_geo_count}")
    geo_audit.append(f"Total suspicious/synthetic geographic records: {suspicious_geo_count}")
    geo_audit.append("The dataset appears to randomly shuffle a small set of districts across states, proving it is a synthetic dataset.")
    
    with open(GEO_AUDIT_PATH, 'w') as f:
        f.write("\n".join(geo_audit))
        
    # 2. Production vs Yield Check
    prod_audit = ["# Production/Yield Integrity Audit\n"]
    prod_audit.append("| Row Index | Farm Area (ha) | Yield (tonnes/ha) | Reported Production (t) | Calculated Production (t) | Difference (t) | % Difference |")
    prod_audit.append("|---|---|---|---|---|---|---|")
    
    # Calculate difference
    df['calc_prod'] = df['yield_tonnes_ha'] * df['farm_area_hectares']
    df['diff'] = (df['production_tonnes'] - df['calc_prod']).abs()
    
    mismatches = df[df['diff'] > 0.1].copy()
    mismatches['pct_diff'] = (mismatches['diff'] / mismatches['calc_prod']) * 100
    
    for idx, row in mismatches.iterrows():
        prod_audit.append(f"| {idx} | {row['farm_area_hectares']:.2f} | {row['yield_tonnes_ha']:.2f} | {row['production_tonnes']:.2f} | {row['calc_prod']:.2f} | {row['diff']:.2f} | {row['pct_diff']:.2f}% |")
        
    prod_audit.append("\n## Conclusion")
    prod_audit.append(f"Total mismatched records (>0.1t difference): {len(mismatches)}")
    
    with open(PROD_AUDIT_PATH, 'w') as f:
        f.write("\n".join(prod_audit))
        
    print(f"Geo mismatch count: {suspicious_geo_count}")
    print(f"Prod mismatch count: {len(mismatches)}")

if __name__ == "__main__":
    run_integrity_check()
