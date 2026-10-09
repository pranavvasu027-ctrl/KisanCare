import uuid
from datetime import datetime
from typing import Dict, Any, List
from ml.schemas.decision import DecisionRequest, DecisionResponse, RecommendationAlternative
from ml.schemas.prediction import ModelResult

class DecisionEngine:
    def __init__(self):
        # Explicit rules/constraints
        self.water_intensive_crops = ["Rice", "Sugarcane"]
        
    def _evaluate_crop_selection(self, req: DecisionRequest, orchestrator_results: Dict[str, ModelResult]) -> DecisionResponse:
        crop_res = orchestrator_results.get("crop_recommendation")
        cost_res = orchestrator_results.get("cost_prediction")
        
        missing_info = []
        model_versions = {}
        status = "ready"
        
        if not crop_res or crop_res.status != "success":
            status = "needs_more_data"
            missing_info.append("Crop Recommendation is unavailable or lacks sufficient data (requires district, season, water_availability).")
            return DecisionResponse(
                decision_id=str(uuid.uuid4()),
                decision_type=req.decision_type,
                status=status,
                missing_information=missing_info,
                timestamp=datetime.utcnow()
            )
            
        model_versions["crop_recommendation"] = crop_res.model_version
        recommendations = crop_res.prediction.get("recommendations", [])
        
        if not recommendations:
            return DecisionResponse(
                decision_id=str(uuid.uuid4()),
                decision_type=req.decision_type,
                status="blocked",
                missing_information=["Crop model returned no suitable crops for this location and season."],
                model_versions=model_versions,
                timestamp=datetime.utcnow()
            )
            
        if cost_res and cost_res.status == "success":
            model_versions["cost_prediction"] = cost_res.model_version
        else:
            missing_info.append("Cost Prediction is unavailable or lacks inputs. Recommendations will be made purely on agronomic suitability without financial context.")
            
        # Hard Constraints & Preferences
        prefs = req.preferences
        
        alternatives = []
        for i, crop_rec in enumerate(recommendations):
            crop_name = crop_rec.get("crop", "Unknown")
            prob = crop_rec.get("probability", 0.0)
            
            warnings = []
            trade_offs = []
            
            # Constraint check: Water priority vs Water intensive crops
            if prefs and prefs.water_conservation_priority and crop_name in self.water_intensive_crops:
                warnings.append(f"Hard Constraint Conflict: {crop_name} is highly water-intensive, but you prioritized water conservation.")
            
            # Preference check: Preferred crops
            if prefs and prefs.preferred_crops:
                if crop_name not in prefs.preferred_crops:
                    trade_offs.append(f"{crop_name} is highly suitable agronomically, but is not in your preferred crops list.")
            
            # Cost checking (if available)
            predicted_cost = None
            if cost_res and cost_res.status == "success":
                # Note: Currently Cost Prediction is a single-prediction model based on context.
                # If we dynamically ran it for *each* recommended crop, it would be a real trade-off. 
                # For now, it represents the cost of the *currently selected crop in context*. 
                # Since this is a "crop selection" decision, cost prediction for a new crop would require re-running the model.
                # We will just note that the cost model requires the user to select the crop first.
                pass
                
            alt = RecommendationAlternative(
                identifier=f"REC-{i}",
                recommended_action=f"Cultivate {crop_name}",
                explanation=f"Agronomically suitable for your district and season based on historical patterns.",
                supporting_evidence={
                    "crop_probability": prob,
                    "rank": crop_rec.get("rank")
                },
                trade_offs=trade_offs,
                warnings=warnings
            )
            alternatives.append(alt)
            
        # Determine primary recommendation
        # Filter out warnings if possible
        viable_alts = [a for a in alternatives if not any("Hard Constraint Conflict" in w for w in a.warnings)]
        
        if not viable_alts:
            return DecisionResponse(
                decision_id=str(uuid.uuid4()),
                decision_type=req.decision_type,
                status="blocked",
                primary_recommendation=None,
                alternatives=alternatives,
                missing_information=missing_info,
                model_versions=model_versions,
                timestamp=datetime.utcnow()
            )
            
        primary = viable_alts[0]
        remaining = [a for a in alternatives if a.identifier != primary.identifier]
        
        return DecisionResponse(
            decision_id=str(uuid.uuid4()),
            decision_type=req.decision_type,
            status=status,
            primary_recommendation=primary,
            alternatives=remaining,
            missing_information=missing_info,
            model_versions=model_versions,
            timestamp=datetime.utcnow()
        )

    def generate_decision(self, req: DecisionRequest, orchestrator_results: Dict[str, ModelResult]) -> DecisionResponse:
        if req.decision_type == "crop_selection":
            return self._evaluate_crop_selection(req, orchestrator_results)
        else:
            return DecisionResponse(
                decision_id=str(uuid.uuid4()),
                decision_type=req.decision_type,
                status="blocked",
                missing_information=[f"Unsupported decision type: {req.decision_type}"],
                timestamp=datetime.utcnow()
            )
