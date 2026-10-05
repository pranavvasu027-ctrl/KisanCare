import os
import json
import joblib
import pandas as pd

class Model1Service:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.label_encoder = None
        self.metadata = None
        self.is_loaded = False
        self.model_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'models', 'model1')

    def load_artifacts(self):
        try:
            self.model = joblib.load(os.path.join(self.model_dir, 'crop_recommendation_model.pkl'))
            self.scaler = joblib.load(os.path.join(self.model_dir, 'preprocessor.pkl'))
            self.label_encoder = joblib.load(os.path.join(self.model_dir, 'label_encoder.pkl'))
            with open(os.path.join(self.model_dir, 'model_metadata.json'), 'r') as f:
                self.metadata = json.load(f)
            self.is_loaded = True
        except Exception as e:
            self.is_loaded = False
            print(f"Error loading Model 1 artifacts: {e}")
            raise e

    def predict_top5(self, request_data: dict):
        if not self.is_loaded:
            raise RuntimeError("Model artifacts are not loaded.")

        # Ensure exact feature order: N, P, K, temperature, humidity, ph, rainfall
        feature_order = self.metadata.get("feature_names", ['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall'])
        
        # Map input to feature names
        input_mapping = {
            'N': request_data.get('nitrogen'),
            'P': request_data.get('phosphorus'),
            'K': request_data.get('potassium'),
            'temperature': request_data.get('temperature'),
            'humidity': request_data.get('humidity'),
            'ph': request_data.get('ph'),
            'rainfall': request_data.get('rainfall')
        }
        
        # Create DataFrame to match scaler format
        input_df = pd.DataFrame([[input_mapping[col] for col in feature_order]], columns=feature_order)
        
        # Scale
        scaled_features = self.scaler.transform(input_df)
        
        # Predict Probabilities
        probas = self.model.predict_proba(scaled_features)[0]
        
        # Get top 5 indices
        top5_idx = probas.argsort()[-5:][::-1]
        
        recommendations = []
        for i, idx in enumerate(top5_idx):
            crop_name = self.label_encoder.inverse_transform([idx])[0]
            prob = float(probas[idx])
            recommendations.append({
                "rank": i + 1,
                "crop": crop_name,
                "score": round(prob, 4)
            })
            
        return {
            "model": self.metadata.get("model_name", "crop_recommendation"),
            "model_version": self.metadata.get("model_version", "1.0.0"),
            "recommendations": recommendations
        }

model1_service = Model1Service()
