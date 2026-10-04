import pandas as pd
import json
import difflib
import re

def normalize(name):
    if not isinstance(name, str): return ""
    name = name.lower()
    name = re.sub(r'[^a-z]', '', name)
    name = name.replace('purbi', 'east').replace('pashchim', 'west').replace('paschim', 'west')
    return name

def main():
    # Load base APY candidate grid
    df = pd.read_csv("data/model1/processed/kisancare_model1_v0.3_candidate_grid.csv")
    
    with open("data/model1/external/raw/boundaries/india_districts.geojson", 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    boundary_districts = []
    for feat in data['features']:
        props = feat.get('properties', {})
        name = props.get('NAME_2')
        if name:
            boundary_districts.append(name)
    boundary_districts = list(set(boundary_districts))
    norm_bounds = {normalize(b): b for b in boundary_districts}
    
    apy_districts = df['District'].unique()
    
    mapping = []
    for d in apy_districts:
        d_norm = normalize(d)
        if d in boundary_districts:
            mapping.append({'APY_District': d, 'Boundary_District': d, 'State': '', 'Mapping_Method': 'EXACT', 'Confidence': 'HIGH', 'Notes': '', 'Source': ''})
        elif d_norm in norm_bounds:
            mapping.append({'APY_District': d, 'Boundary_District': norm_bounds[d_norm], 'State': '', 'Mapping_Method': 'NORMALIZED', 'Confidence': 'HIGH', 'Notes': '', 'Source': ''})
        else:
            # Fuzzy
            matches = difflib.get_close_matches(d_norm, list(norm_bounds.keys()), n=1, cutoff=0.7)
            if matches:
                mapping.append({'APY_District': d, 'Boundary_District': norm_bounds[matches[0]], 'State': '', 'Mapping_Method': 'FUZZY', 'Confidence': 'MEDIUM', 'Notes': f'Matched to {norm_bounds[matches[0]]}', 'Source': ''})
            else:
                mapping.append({'APY_District': d, 'Boundary_District': None, 'State': '', 'Mapping_Method': 'UNMATCHED', 'Confidence': 'NONE', 'Notes': 'Not found', 'Source': ''})
                
    mapping_df = pd.DataFrame(mapping)
    mapping_df.to_csv("data/model1/external/metadata/district_mapping_final.csv", index=False)
    
    # Calculate coverage
    matched_mapping = mapping_df[mapping_df['Mapping_Method'] != 'UNMATCHED']
    unmatched_districts = mapping_df[mapping_df['Mapping_Method'] == 'UNMATCHED']['APY_District'].tolist()
    
    district_coverage = len(matched_mapping) / len(mapping_df) * 100
    
    matched_rows = df[df['District'].isin(matched_mapping['APY_District'])]
    row_coverage = len(matched_rows) / len(df) * 100
    
    print(f"Total Rows: {len(df)}")
    print(f"Row Coverage: {row_coverage:.2f}%")
    print(f"District Coverage: {district_coverage:.2f}%")
    print(f"Unmatched Districts: {len(unmatched_districts)}")
    
    # Create Parquet with Nulls (since we can't fetch 15 years for 500+ districts locally)
    unique_d_y_s = df[['District', 'Crop_Year', 'Season']].drop_duplicates().copy()
    unique_d_y_s['Historical_Temperature'] = pd.NA
    unique_d_y_s['Soil_Moisture'] = pd.NA
    unique_d_y_s['Soil_Texture'] = pd.NA
    unique_d_y_s = unique_d_y_s.rename(columns={'Crop_Year': 'Year'})
    unique_d_y_s.to_parquet("data/model1/external/processed/weather_soil_district_features.parquet", index=False)
    
    # Final Fusion
    df_fused = pd.merge(df, unique_d_y_s.rename(columns={'Year': 'Crop_Year'}), on=['District', 'Crop_Year', 'Season'], how='left')
    df_fused.to_csv("data/model1/processed/kisancare_model1_B_training.csv", index=False)
    
    # Write Provenance
    provenance = [
        {'Feature': 'Historical_Temperature', 'Source': 'ERA5-Land via CDS/GEE (Blocked)', 'Variable': '2m_temperature', 'Units': 'C', 'Spatial resolution': '0.1 deg', 'Temporal resolution': 'Monthly Climatology', 'Extraction dates': 'Pre-decision', 'Aggregation method': 'Zonal Area-weighted mean', 'Leakage rule': 'Pre-season historical only', 'Coverage': '0%', 'Status': 'BLOCKED'},
        {'Feature': 'Soil_Moisture', 'Source': 'ERA5-Land via CDS/GEE (Blocked)', 'Variable': 'volumetric_soil_water_layer_1', 'Units': 'm3/m3', 'Spatial resolution': '0.1 deg', 'Temporal resolution': 'Monthly Climatology', 'Extraction dates': 'Pre-decision', 'Aggregation method': 'Zonal Area-weighted mean', 'Leakage rule': 'Pre-season historical only', 'Coverage': '0%', 'Status': 'BLOCKED'},
        {'Feature': 'Soil_Texture', 'Source': 'ISRIC SoilGrids (Blocked)', 'Variable': 'sand/silt/clay dominant class', 'Units': 'Categorical', 'Spatial resolution': '250m', 'Temporal resolution': 'Static', 'Extraction dates': 'Static', 'Aggregation method': 'Dominant class by area', 'Leakage rule': 'Geologically stable', 'Coverage': '0%', 'Status': 'BLOCKED'}
    ]
    pd.DataFrame(provenance).to_csv("data/model1/external/metadata/modelB_feature_provenance.csv", index=False)

if __name__ == "__main__":
    main()
