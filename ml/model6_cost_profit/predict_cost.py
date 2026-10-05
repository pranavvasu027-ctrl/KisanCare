import joblib
import pandas as pd
import os
from economic_engine import calculate_economics

MODEL_PATH = r"C:\Users\prana\.gemini\antigravity\brain\c717cd51-3f5e-497a-9b25-ae28bd0f1741\models\model6_cost_profit\artifacts\cost_model.joblib"

class CostProfitModel:
    def __init__(self):
        if os.path.exists(MODEL_PATH):
            self.model = joblib.load(MODEL_PATH)
        else:
            self.model = None

    def predict_cost(self, input_data: dict):
        if self.model is None:
            return {"error": "Model not loaded"}
            
        # Wrap into dataframe
        df = pd.DataFrame([input_data])
        
        # Standard fallback for missing keys to match training
        expected_cols = [
            'State', 'District', 'Crop', 'Season', 'Farm_Area_Hectares',
            'Rainfall_mm', 'Avg_Temperature_C', 'Humidity_pct', 'Sunlight_Hours_Day',
            'Soil_pH', 'Soil_Moisture_pct', 'Nitrogen_kg_ha', 'Phosphorus_kg_ha',
            'Potassium_kg_ha', 'Irrigation_Method', 'Fertilizer_kg_ha',
            'Pesticide_Litre_ha', 'Seed_Quality_Score', 'Disease_Pest_Risk_pct'
        ]
        
        for c in expected_cols:
            if c not in df.columns:
                if 'area' in c.lower():
                    df[c] = 1.0
                elif c in ['State', 'District', 'Crop', 'Season', 'Irrigation_Method']:
                    df[c] = "Unknown"
                else:
                    df[c] = 0.0
                    
        try:
            pred = self.model.predict(df)[0]
            # Enforce non-negative cost
            pred = max(0.0, float(pred))
            
            return {
                "predicted_cost_inr": round(pred, 2),
                "cost_per_hectare_inr": round(pred / df['Farm_Area_Hectares'].iloc[0], 2) if df['Farm_Area_Hectares'].iloc[0] > 0 else 0.0,
                "model_version": "v1.0-gradient-boosting",
                "coverage_warning": "" if df['Crop'].iloc[0] in ["Wheat", "Rice", "Maize", "Pulses", "Cotton", "Groundnut", "Chilli", "Sugarcane"] else f"Warning: {df['Crop'].iloc[0]} is outside training support.",
                "confidence": "unavailable"
            }
        except Exception as e:
            return {"error": str(e)}

# ---------------------------------------------------------
# API Stub Function (representing POST /profit)
# ---------------------------------------------------------
def api_profit_endpoint(farm_input: dict):
    # 1. Map input to expected feature names
    mapped_input = {
        'Crop': farm_input.get('crop', 'Unknown'),
        'State': farm_input.get('state', 'Unknown'),
        'District': farm_input.get('district', 'Unknown'),
        'Season': farm_input.get('season', 'Kharif'),
        'Farm_Area_Hectares': farm_input.get('area_hectares', 1.0),
        'Soil_pH': farm_input.get('soil_ph', 6.5),
        'Nitrogen_kg_ha': farm_input.get('nitrogen', 0.0),
        'Phosphorus_kg_ha': farm_input.get('phosphorus', 0.0),
        'Potassium_kg_ha': farm_input.get('potassium', 0.0),
        'Rainfall_mm': farm_input.get('rainfall_mm', 0.0),
        'Avg_Temperature_C': farm_input.get('temperature_c', 25.0),
        'Humidity_pct': farm_input.get('humidity_pct', 50.0),
        'Irrigation_Method': farm_input.get('irrigation_method', 'Unknown'),
        # Fill required defaults
        'Sunlight_Hours_Day': 8.0,
        'Soil_Moisture_pct': 40.0,
        'Fertilizer_kg_ha': 50.0,
        'Pesticide_Litre_ha': 2.0,
        'Seed_Quality_Score': 5.0,
        'Disease_Pest_Risk_pct': 10.0
    }
    
    # 2. Predict Cost
    cost_model = CostProfitModel()
    cost_res = cost_model.predict_cost(mapped_input)
    
    if "error" in cost_res:
        return {"error": cost_res["error"]}
        
    predicted_cost = cost_res["predicted_cost_inr"]
    
    # 3. Predict Yield & Price (Stubs - to be connected to actual models later)
    # Using dummy values for now to test economic engine integration
    predicted_yield_ha = 5.0  # Dummy yield: 5 tonnes / ha
    predicted_price_tonne = 20000.0  # Dummy price: 20000 INR / tonne
    
    # 4. Economic Engine
    economics = calculate_economics(
        predicted_yield_tonnes_ha=predicted_yield_ha,
        predicted_price_inr_tonne=predicted_price_tonne,
        predicted_cost_inr=predicted_cost,
        area_hectares=mapped_input['Farm_Area_Hectares']
    )
    
    return {
        "cost_analysis": cost_res,
        "yield_analysis": {"predicted_yield_tonnes_ha": predicted_yield_ha, "note": "STUB - connect to Yield Model"},
        "market_analysis": {"predicted_price_inr_tonne": predicted_price_tonne, "note": "STUB - connect to Market Model"},
        "economic_analysis": economics
    }
