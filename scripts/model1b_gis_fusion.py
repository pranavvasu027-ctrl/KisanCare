import pandas as pd
import json
import os
import re

def normalize_name(name):
    if not isinstance(name, str):
        return ""
    name = re.sub(r'[^a-zA-Z]', '', name.lower())
    return name

def main():
    print("Starting GIS Spatial Aggregation & Dataset Fusion (Phase 3)...")
    
    # 1. Base data
    grid_path = "data/model1/processed/kisancare_model1_v0.3_candidate_grid.csv"
    df = pd.read_csv(grid_path)
    print(f"Loaded base grid: {df.shape}")
    
    # 2. District Boundaries
    geojson_path = "data/model1/external/raw/boundaries/india_districts.geojson"
    try:
        import geopandas as gpd
        gdf = gpd.read_file(geojson_path)
        boundary_districts = gdf['NAME_2'].dropna().unique() if 'NAME_2' in gdf.columns else []
    except Exception as e:
        print(f"Warning: GeoPandas not available or file issue: {e}")
        # fallback if geopandas fails
        with open(geojson_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        boundary_districts = []
        for feat in data['features']:
            props = feat.get('properties', {})
            name = props.get('NAME_2') or props.get('district') or props.get('dtname')
            if name:
                boundary_districts.append(name)
        boundary_districts = list(set(boundary_districts))
    
    # 3. District Name Reconciliation
    apy_districts = df['District'].dropna().unique()
    
    mapping = []
    normalized_bounds = {normalize_name(d): d for d in boundary_districts}
    
    unmatched_count = 0
    for d in apy_districts:
        d_norm = normalize_name(d)
        if d in boundary_districts:
            mapping.append({'APY_District': d, 'Boundary_District': d, 'State': '', 'Match_Status': 'EXACT', 'Notes': ''})
        elif d_norm in normalized_bounds:
            mapping.append({'APY_District': d, 'Boundary_District': normalized_bounds[d_norm], 'State': '', 'Match_Status': 'NORMALIZED', 'Notes': ''})
        else:
            mapping.append({'APY_District': d, 'Boundary_District': None, 'State': '', 'Match_Status': 'UNMATCHED', 'Notes': 'Not found in geojson'})
            unmatched_count += 1
            
    os.makedirs("data/model1/external/metadata", exist_ok=True)
    mapping_df = pd.DataFrame(mapping)
    mapping_df.to_csv("data/model1/external/metadata/district_mapping.csv", index=False)
    print(f"District Mapping created. Unmatched districts: {unmatched_count}")
    
    # 4-8. Spatial and Temporal Aggregation (Mocking the raster extraction)
    # Since we do not possess the multi-TB ERA5/SoilGrids rasters locally, 
    # we define the schema and populate with NaNs. 
    # In a production environment, this step uses xarray/rasterstats on the district polygons.
    
    # 9. Fusion with APY
    df_fused = df.copy()
    df_fused['Historical_Temperature'] = pd.NA
    df_fused['Soil_Moisture'] = pd.NA
    df_fused['Soil_Texture'] = pd.NA
    
    out_path = "data/model1/processed/kisancare_model1_B_fused_v0.1.csv"
    df_fused.to_csv(out_path, index=False)
    print(f"Fused dataset saved to {out_path} with shape {df_fused.shape}")
    
    # 10. Validation & Metrics
    total_rows = len(df_fused)
    unique_districts = df_fused['District'].nunique()
    unique_years = df_fused['Crop_Year'].nunique() if 'Crop_Year' in df_fused.columns else 0
    unique_seasons = df_fused['Season'].nunique()
    unique_crops = df_fused['Candidate_Crop'].nunique() if 'Candidate_Crop' in df_fused.columns else df_fused['Crop'].nunique()
    
    print("\n--- VALIDATION METRICS ---")
    print(f"Total Rows: {total_rows}")
    print(f"Districts: {unique_districts}")
    print(f"Years: {unique_years}")
    print(f"Seasons: {unique_seasons}")
    print(f"Crops: {unique_crops}")
    
    print("\nFeature Coverage:")
    for feat in ['Historical_Temperature', 'Soil_Moisture', 'Soil_Texture']:
        nulls = df_fused[feat].isna().sum()
        non_nulls = total_rows - nulls
        cov_pct = (non_nulls / total_rows) * 100
        print(f"  {feat}: Non-null: {non_nulls}, Null: {nulls}, Coverage: {cov_pct:.2f}%")
        
    # 13. Provenance
    provenance = [
        {'Feature': 'Historical_Temperature', 'Source': 'ERA5-Land', 'Variable': '2m_temperature', 'Units': 'C', 'Spatial resolution': '0.1 deg', 'Temporal resolution': 'Monthly Climatology', 'Aggregation method': 'Zonal Area-weighted mean', 'Leakage rule': 'Pre-season historical only', 'Coverage': '0% (Rasters missing locally)', 'Status': 'BLOCKED'},
        {'Feature': 'Soil_Moisture', 'Source': 'ERA5-Land', 'Variable': 'volumetric_soil_water_layer_1', 'Units': 'm3/m3', 'Spatial resolution': '0.1 deg', 'Temporal resolution': 'Monthly Climatology', 'Aggregation method': 'Zonal Area-weighted mean', 'Leakage rule': 'Pre-season historical only', 'Coverage': '0% (Rasters missing locally)', 'Status': 'BLOCKED'},
        {'Feature': 'Soil_Texture', 'Source': 'ISRIC SoilGrids', 'Variable': 'sand/silt/clay dominant class', 'Units': 'Categorical', 'Spatial resolution': '250m', 'Temporal resolution': 'Static', 'Aggregation method': 'Dominant class by area', 'Leakage rule': 'Geologically stable', 'Coverage': '0% (Rasters missing locally)', 'Status': 'BLOCKED'}
    ]
    pd.DataFrame(provenance).to_csv("data/model1/external/metadata/modelB_feature_provenance.csv", index=False)
    print("Provenance saved.")

if __name__ == "__main__":
    main()
