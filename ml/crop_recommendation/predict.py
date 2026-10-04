import pandas as pd
import joblib
import json
import time
import warnings

warnings.filterwarnings('ignore')

class CropDecisionEngine:
    def __init__(self):
        # Established rules (ambiguous crops allowed everywhere)
        self.high_water_crops = {'Sugarcane', 'Rice', 'Banana'}
        self.season_rules = {
            'Wheat': ['Rabi'],
            'Mango': ['Whole Year'],
            'Grapes': ['Whole Year'],
            'Banana': ['Whole Year']
        }
    
    def evaluate_water(self, crop, water_availability):
        if water_availability == 'Low' and crop in self.high_water_crops:
            return False, 'High water requirement crop excluded in Low water condition'
        return True, None
        
    def evaluate_season(self, crop, season):
        if crop in self.season_rules:
            if season not in self.season_rules[crop]:
                return False, f'{crop} is constrained to {self.season_rules[crop]}'
        return True, None

class PredictionPipeline:
    def __init__(self, model_dir='C:/Users/prana/OneDrive/Desktop/Projects/KISANcare/kisan-care/models/crop_recommendation'):
        self.model_dir = model_dir
        self.model = None
        self.cat_levels = None
        self.metadata = None
        self.decision_engine = CropDecisionEngine()
        self.load_model()
        
    def load_model(self):
        try:
            self.model = joblib.load(f'{self.model_dir}/crop_recommendation_mvp_v2.pkl')
            self.cat_levels = joblib.load(f'{self.model_dir}/preprocessing_mvp_v2.pkl')
            with open(f'{self.model_dir}/metadata_mvp_v2.json', 'r') as f:
                self.metadata = json.load(f)
        except FileNotFoundError:
            raise Exception('Model load failure: Artifacts not found')

    def validate_inputs(self, district, season, water, top_k):
        if district not in self.cat_levels['District']:
            return False, f'Validation Error: Unknown district {district}'
        
        valid_seasons = ['Kharif', 'Rabi', 'Summer', 'Whole Year']
        if season not in valid_seasons:
            return False, f'Validation Error: Unknown season {season}. Allowed: {valid_seasons}'
            
        valid_water = ['Low', 'Medium', 'High']
        if water not in valid_water:
            return False, f'Validation Error: Unknown water availability {water}. Allowed: {valid_water}'
            
        if not isinstance(top_k, int) or top_k < 1 or top_k > 20:
            return False, 'Validation Error: top_k must be an integer between 1 and 20'
            
        return True, None

    def recommend(self, district: str, season: str, water_availability: str, top_k: int = 5):
        t_start = time.time()
        
        is_valid, err_msg = self.validate_inputs(district, season, water_availability, top_k)
        if not is_valid:
            return {'status': 'ERROR', 'reason': err_msg}
            
        all_crops = self.cat_levels['Crop']
        
        # 1. Candidate Generation
        candidates = pd.DataFrame({
            'District': [district] * len(all_crops),
            'Season': [season] * len(all_crops),
            'Crop': all_crops
        })
        
        for col in ['District', 'Season', 'Crop']:
            candidates[col] = pd.Categorical(candidates[col], categories=self.cat_levels[col])
            
        # 2. ML Prediction
        candidates['predicted_area_frequency'] = self.model.predict(candidates[['District', 'Season', 'Crop']])
        candidates['predicted_area_frequency'] = candidates['predicted_area_frequency'].clip(lower=0)
        
        # 3. Ranking
        candidates = candidates.sort_values('predicted_area_frequency', ascending=False).reset_index(drop=True)
        
        # 4. Decision Engine Filtering
        recommendations = []
        filtered_out = []
        
        for _, row in candidates.iterrows():
            crop = row['Crop']
            score = float(row['predicted_area_frequency'])
            
            w_eligible, w_reason = self.decision_engine.evaluate_water(crop, water_availability)
            s_eligible, s_reason = self.decision_engine.evaluate_season(crop, season)
            
            if w_eligible and s_eligible:
                recommendations.append({
                    'crop': crop,
                    'predicted_area_frequency': round(score, 4)
                })
            else:
                reason = w_reason if not w_eligible else s_reason
                filtered_out.append({
                    'crop': crop,
                    'model_score': round(score, 4),
                    'eligible': False,
                    'filter_reason': reason
                })
                
        # Top-K
        final_recs = []
        for i, rec in enumerate(recommendations[:top_k]):
            rec['rank'] = i + 1
            final_recs.append(rec)
            
        status = 'SUCCESS'
        if len(final_recs) == 0:
            status = 'NO_ELIGIBLE_CROP'
            
        return {
            'model_version': self.metadata['model_version'],
            'district': district,
            'season': season,
            'water_availability': water_availability,
            'status': status,
            'recommendations': final_recs,
            'filtered_candidates': filtered_out,
            'data_source': 'APY_2005_2015',
            'score_interpretation': 'Predicted historical area-allocation suitability score',
            'latency_ms': round((time.time() - t_start) * 1000, 2)
        }

# Public module function
_pipeline_instance = None

def recommend_crops(district: str, season: str, water_availability: str, top_k: int = 5):
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = PredictionPipeline()
    return _pipeline_instance.recommend(district, season, water_availability, top_k)

if __name__ == "__main__":
    import sys
    dist = sys.argv[1] if len(sys.argv) > 1 else 'NASHIK'
    szn = sys.argv[2] if len(sys.argv) > 2 else 'Rabi'
    wat = sys.argv[3] if len(sys.argv) > 3 else 'Medium'
    
    res = recommend_crops(dist, szn, wat)
    print(json.dumps(res, indent=2))
