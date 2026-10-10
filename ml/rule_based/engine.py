from typing import List, Dict, Any

class RuleBasedModels:
    @staticmethod
    def detect_disease(symptoms: List[str], crop: str) -> Dict[str, Any]:
        """Rule-based experimental disease detection."""
        symptoms_lower = [s.lower() for s in symptoms]
        
        # Simple rule matching
        if "yellow leaves" in symptoms_lower and "stunted growth" in symptoms_lower:
            disease = "Nitrogen Deficiency / Root Rot"
            confidence = 0.75
            treatment = "Apply nitrogen-rich fertilizer. Ensure proper drainage."
        elif "white powdery spots" in symptoms_lower:
            disease = "Powdery Mildew"
            confidence = 0.85
            treatment = "Apply sulfur-based fungicide. Improve air circulation."
        elif "black spots" in symptoms_lower:
            disease = "Leaf Spot"
            confidence = 0.80
            treatment = "Remove infected leaves. Apply copper fungicide."
        else:
            disease = "Unknown / Healthy"
            confidence = 0.50
            treatment = "Monitor closely and consult a local agricultural expert."
            
        return {
            "model_type": "rule_based",
            "prediction": disease,
            "confidence": confidence,
            "treatment": treatment
        }

    @staticmethod
    def detect_pest(symptoms: List[str], crop: str) -> Dict[str, Any]:
        """Rule-based experimental pest detection."""
        symptoms_lower = [s.lower() for s in symptoms]
        
        if "holes in leaves" in symptoms_lower:
            pest = "Caterpillars / Beetles"
            confidence = 0.80
            treatment = "Use neem oil or Bacillus thuringiensis (Bt)."
        elif "sticky residue" in symptoms_lower or "curled leaves" in symptoms_lower:
            pest = "Aphids"
            confidence = 0.85
            treatment = "Introduce ladybugs or apply insecticidal soap."
        else:
            pest = "No major pest detected"
            confidence = 0.60
            treatment = "Continue regular monitoring."
            
        return {
            "model_type": "rule_based",
            "prediction": pest,
            "confidence": confidence,
            "treatment": treatment
        }

    @staticmethod
    def assess_soil_nutrients(n: float, p: float, k: float, ph: float) -> Dict[str, Any]:
        """Rule-based soil nutrient assessment."""
        status = []
        if n < 20: status.append("Low Nitrogen")
        elif n > 50: status.append("Excess Nitrogen")
        
        if p < 10: status.append("Low Phosphorus")
        if k < 150: status.append("Low Potassium")
        
        if ph < 5.5: status.append("Acidic Soil")
        elif ph > 7.5: status.append("Alkaline Soil")
        
        overall = "Healthy" if not status else "Deficient/Imbalanced"
        
        return {
            "model_type": "rule_based",
            "overall_status": overall,
            "issues": status if status else ["Optimal nutrient levels"],
            "recommendation": "Add NPK fertilizer balancing the deficiencies." if status else "Maintain current soil management."
        }

    @staticmethod
    def predict_yield(crop: str, area_acres: float, soil_health_score: float, weather_score: float) -> Dict[str, Any]:
        """Rule-based crop yield prediction."""
        base_yield_per_acre = {
            "Wheat": 1.2,
            "Rice": 1.5,
            "Soybean": 0.8,
            "Cotton": 0.6,
            "Corn": 2.0
        }
        
        base = base_yield_per_acre.get(crop, 1.0)
        
        # Adjust based on scores (0-100)
        soil_factor = soil_health_score / 100.0
        weather_factor = weather_score / 100.0
        
        predicted_yield = base * area_acres * ((soil_factor + weather_factor) / 2)
        
        return {
            "model_type": "rule_based",
            "crop": crop,
            "predicted_yield_tons": round(predicted_yield, 2),
            "factors": {
                "soil_impact": "Positive" if soil_health_score > 70 else "Negative",
                "weather_impact": "Positive" if weather_score > 70 else "Negative"
            }
        }

    @staticmethod
    def assess_weather_risk(temp: float, humidity: float, rainfall_forecast: float) -> Dict[str, Any]:
        """Rule-based weather risk assessment."""
        risk_level = "Low"
        risks = []
        
        if temp > 35:
            risks.append("Heat Stress")
            risk_level = "High"
        elif temp < 5:
            risks.append("Frost Damage")
            risk_level = "High"
            
        if humidity > 85 and rainfall_forecast > 50:
            risks.append("Fungal Infection Risk")
            risk_level = "Medium" if risk_level != "High" else "High"
            
        if rainfall_forecast > 100:
            risks.append("Flooding Risk")
            risk_level = "High"
            
        return {
            "model_type": "rule_based",
            "overall_risk": risk_level,
            "identified_risks": risks if risks else ["Favorable weather conditions"],
            "mitigation": "Ensure irrigation." if "Heat Stress" in risks else "Normal operations."
        }

    @staticmethod
    def recommend_irrigation(crop: str, soil_moisture: float, days_since_rain: int) -> Dict[str, Any]:
        """Rule-based irrigation recommendation."""
        water_needed = False
        amount_liters = 0
        
        if soil_moisture < 30.0 or days_since_rain > 7:
            water_needed = True
            amount_liters = 5000 if crop in ["Rice", "Sugarcane"] else 2000
            
        return {
            "model_type": "rule_based",
            "irrigation_required": water_needed,
            "recommended_amount_liters_per_acre": amount_liters,
            "reasoning": f"Soil moisture is at {soil_moisture}% and it hasn't rained for {days_since_rain} days."
        }
