import pandas as pd
import joblib
import json

def recommend_crops(district: str, season: str, top_k: int = 5):
    """
    KisanCare MVP Prediction Function
    """
    model_dir = 'C:/Users/prana/OneDrive/Desktop/Projects/KISANcare/kisan-care/models/crop_recommendation'
    
    # Load model and preprocessing categories
    try:
        model = joblib.load(f'{model_dir}/crop_recommendation_mvp_v1.pkl')
        cat_levels = joblib.load(f'{model_dir}/preprocessing_mvp.pkl')
        with open(f'{model_dir}/metadata_mvp.json', 'r') as f:
            metadata = json.load(f)
    except FileNotFoundError:
        return {"error": "Model artifacts not found."}
        
    all_crops = cat_levels['Crop']
    
    # Generate 20 candidate rows
    candidates = pd.DataFrame({
        'District': [district] * len(all_crops),
        'Season': [season] * len(all_crops),
        'Crop': all_crops
    })
    
    # Cast to category using exactly the training levels
    for col in ['District', 'Season', 'Crop']:
        candidates[col] = pd.Categorical(candidates[col], categories=cat_levels[col])
        
    # Predict Area Frequency
    candidates['predicted_area_frequency'] = model.predict(candidates[['District', 'Season', 'Crop']])
    
    # Handle negative predictions (possible with tree regression)
    candidates['predicted_area_frequency'] = candidates['predicted_area_frequency'].clip(lower=0)
    
    # Rank
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
        "data_quality": "APY_2005_2015_Verified",
        "confidence": None,
        "recommendations": recommendations
    }

if __name__ == "__main__":
    # Quick test
    import sys
    dist = sys.argv[1] if len(sys.argv) > 1 else 'NASHIK'
    szn = sys.argv[2] if len(sys.argv) > 2 else 'Rabi'
    
    res = recommend_crops(dist, szn)
    print(json.dumps(res, indent=2))
