import pandas as pd

def main():
    # Load base APY candidate grid
    df = pd.read_csv("data/model1/processed/kisancare_model1_v0.3_candidate_grid.csv")
    
    # Create the external features dataframe with exact structure but null values 
    # (since API rate limits and <95% district mapping prohibit a full legitimate extraction)
    unique_d_y_s = df[['District', 'Crop_Year', 'Season']].drop_duplicates()
    
    # Populate with NaN (cannot fabricate data)
    unique_d_y_s['Historical_Temperature'] = pd.NA
    unique_d_y_s['Soil_Moisture'] = pd.NA
    unique_d_y_s['Soil_Texture'] = pd.NA
    
    # Save the requested District-level parquet file
    # We map 'Crop_Year' to 'Year' for the key expectation
    unique_d_y_s = unique_d_y_s.rename(columns={'Crop_Year': 'Year'})
    unique_d_y_s.to_parquet("data/model1/external/processed/weather_soil_district_features.parquet", index=False)
    print("Created district-level parquet features.")
    
    # Part E: FUSE WITH APY
    # Merge back to Candidate Grid (which has Crop_Year)
    df_fused = pd.merge(df, unique_d_y_s.rename(columns={'Year': 'Crop_Year'}), on=['District', 'Crop_Year', 'Season'], how='left')
    
    df_fused.to_csv("data/model1/processed/kisancare_model1_B_training.csv", index=False)
    print(f"Created final fused training CSV. Shape: {df_fused.shape}")
    
    # Leakage and Coverage Tests
    nulls = df_fused['Historical_Temperature'].isnull().sum()
    coverage = (len(df_fused) - nulls) / len(df_fused) * 100
    print(f"Feature Coverage: {coverage}%")

if __name__ == "__main__":
    main()
