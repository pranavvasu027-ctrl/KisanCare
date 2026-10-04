import pandas as pd
import joblib
import json
import warnings

warnings.filterwarnings('ignore')

def recommend_crops(district: str, season: str, top_k: int = 5):
    """
    KisanCare MVP Prediction Function (Phase 7 - Grid Corrected)
    """
    model_dir = 'C:/Users/prana/OneDrive/Desktop/Projects/KISANcare/kisan-care/models/crop_recommendation'
    
    # Load model and preprocessing categories
    try:
        model = joblib.load(f'{model_dir}/crop_recommendation_mvp_v2.pkl')
        cat_levels = joblib.load(f'{model_dir}/preprocessing_mvp_v2.pkl')
        with open(f'{model_dir}/metadata_mvp_v2.json', 'r') as f:
            metadata = json.load(f)
    except FileNotFoundError:
        return {"error": "Model artifacts not found."}
        
    all_crops = cat_levels['Crop']
    
    # Generate candidate rows for all crops
    candidates = pd.DataFrame({
        'District': [district] * len(all_crops),
        'Season': [season] * len(all_crops),
        'Crop': all_crops
    })
    
    # Cast to exactly the training category levels
    for col in ['District', 'Season', 'Crop']:
        candidates[col] = pd.Categorical(candidates[col], categories=cat_levels[col])
        
    # Predict Area Frequency
    candidates['predicted_area_frequency'] = model.predict(candidates[['District', 'Season', 'Crop']])
    
    # Handle any negative predictions
    candidates['predicted_area_frequency'] = candidates['predicted_area_frequency'].clip(lower=0)
    
    # Rank them
    candidates = candidates.sort_values('predicted_area_frequency', ascending=False).reset_index(drop=True)
    
    # Format output
    recommendations = []
    for rank, row in candidates.head(top_k).iterrows():
        recommendations.append({
            "crop": row['Crop'],
            "rank": rank + 1,
            "predicted_area_frequency": round(float(row['predicted_area_frequency']), 4)
        })
        
    return {
        "district": district,
        "season": season,
        "model_version": metadata['model_version'],
        "data_quality": "APY_2005_2015_Verified_Grid_Padded",
        "confidence": None,
        "recommendations": recommendations
    }

if __name__ == "__main__":
    # Test script locally
    import sys
    dist = sys.argv[1] if len(sys.argv) > 1 else 'NASHIK'
    szn = sys.argv[2] if len(sys.argv) > 2 else 'Rabi'
    
    res = recommend_crops(dist, szn)
    print(json.dumps(res, indent=2))
