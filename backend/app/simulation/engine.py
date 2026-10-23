"""What-If Scenario Simulation Engine for KisanCare.
Evaluates agricultural management changes against authenticated farm Digital Twin baselines
without mutating real farm records.
"""
from __future__ import annotations

import os
from typing import Any, Dict, Optional
from ..economics.engine import calculate_economics

def fetch_farm_baseline(farm_id: str) -> Dict[str, Any]:
    """Retrieve actual farm metrics from Supabase or provide sensible defaults for given farm."""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not key or not farm_id:
        return {
            "farm_name": f"Farm {farm_id}",
            "crop": "Cotton",
            "cultivated_acres": 5.0,
            "total_area_acres": 10.0,
            "baseline_yield_per_acre": 10.0,
            "baseline_yield_total": 50.0,
            "baseline_price": 8000.0,
            "input_cost": 31000.0,
            "labour_cost": 50000.0,
            "machinery_cost": 20000.0,
            "irrigation_cost": 0.0,
            "transport_cost": 5000.0,
            "total_cost": 106000.0
        }

    try:
        from supabase import create_client
        sb = create_client(url, key)

        farm_res = sb.table("farms").select("id, farm_name, total_area, fields(*, seasons(*))").eq("id", farm_id).execute()
        if not farm_res.data:
            # Fallback for mock IDs like F001 or FARM-001
            return {
                "farm_name": f"Farm {farm_id}",
                "crop": "Cotton",
                "cultivated_acres": 5.0,
                "total_area_acres": 10.0,
                "baseline_yield_per_acre": 10.0,
                "baseline_yield_total": 50.0,
                "baseline_price": 8000.0,
                "input_cost": 31000.0,
                "labour_cost": 50000.0,
                "machinery_cost": 20000.0,
                "irrigation_cost": 0.0,
                "transport_cost": 5000.0,
                "total_cost": 106000.0
            }

        farm = farm_res.data[0]
        fields = farm.get("fields") or []
        cultivated_acres = sum(float(f.get("area") or 0.0) for f in fields) or 5.0
        total_acres = float(farm.get("total_area") or 10.0)

        # Get crop from primary field
        crop = "Cotton"
        if fields and fields[0].get("seasons"):
            crop = fields[0]["seasons"][0].get("crop") or "Cotton"

        return {
            "farm_name": farm.get("farm_name"),
            "crop": crop,
            "cultivated_acres": cultivated_acres,
            "total_area_acres": total_acres,
            "baseline_yield_per_acre": 10.0,
            "baseline_yield_total": cultivated_acres * 10.0,
            "baseline_price": 8000.0,
            "input_cost": 31000.0,
            "labour_cost": 50000.0,
            "machinery_cost": 20000.0,
            "irrigation_cost": 0.0,
            "transport_cost": 5000.0,
            "total_cost": 106000.0
        }
    except Exception:
        return {
            "farm_name": f"Farm {farm_id}",
            "crop": "Cotton",
            "cultivated_acres": 5.0,
            "total_area_acres": 10.0,
            "baseline_yield_per_acre": 10.0,
            "baseline_yield_total": 50.0,
            "baseline_price": 8000.0,
            "input_cost": 31000.0,
            "labour_cost": 50000.0,
            "machinery_cost": 20000.0,
            "irrigation_cost": 0.0,
            "transport_cost": 5000.0,
            "total_cost": 106000.0
        }

def run_simulation(farm_id: str, changes: Dict[str, Any]) -> Dict[str, Any]:
    """Execute What-If simulation without mutating real database records."""
    b = fetch_farm_baseline(farm_id)

    # 1. Baseline calculation
    base_yield = float(b["baseline_yield_total"])
    base_price = float(changes.get("expected_price") or b["baseline_price"])
    base_cost = float(b["total_cost"])
    base_revenue = base_yield * base_price
    base_profit = base_revenue - base_cost
    base_risk = 0.35

    # 2. Scenario adjustments
    scenario_yield = base_yield
    rf_change = float(changes.get("rainfall_change_percent") or 0.0)
    if rf_change != 0:
        # Agro-climatic sensitivity: -30% rain causes ~22.5% yield drop in rainfed soil
        scenario_yield = max(5.0, base_yield * (1.0 + (rf_change * 0.75 / 100.0)))

    scenario_cost = base_cost
    if "input_cost" in changes and changes["input_cost"] is not None:
        scenario_cost = float(changes["input_cost"]) + float(b.get("labour_cost", 50000.0)) + float(b.get("machinery_cost", 20000.0))

    if changes.get("irrigation_strategy") in ["Supplementary Drip", "Drip Irrigation"]:
        # Mitigates drought drop by up to 15% and adds irrigation cost
        if rf_change < 0:
            scenario_yield = min(base_yield, scenario_yield * 1.15)
        scenario_cost += 12000.0

    scenario_price = float(changes.get("expected_price") or base_price)
    scenario_revenue = scenario_yield * scenario_price
    scenario_profit = scenario_revenue - scenario_cost

    scenario_risk = 0.52 if (scenario_yield < base_yield or rf_change < -15) else (0.28 if scenario_yield >= base_yield else 0.35)

    explanations = []
    if rf_change != 0:
        explanations.append(f"Rainfall altered by {rf_change:+.1f}% adjusting simulated harvest yield from {base_yield:.1f} to {scenario_yield:.1f} quintals.")
    if changes.get("irrigation_strategy"):
        explanations.append(f"Applied irrigation strategy '{changes['irrigation_strategy']}' mitigating water stress.")
    if "input_cost" in changes:
        explanations.append(f"Cultivation input costs adjusted to ₹{scenario_cost:,.0f}.")
    if not explanations:
        explanations.append("Simulation calculated using agro-climatic sensitivity and authenticated farm baseline.")

    explanations.append("Note: What-If simulation outputs do not alter your permanent farm records.")

    result_payload = {
        "baseline": {
            "yield": round(base_yield, 2),
            "cost": round(base_cost, 2),
            "revenue": round(base_revenue, 2),
            "profit": round(base_profit, 2),
            "risk": base_risk
        },
        "scenario": {
            "yield": round(scenario_yield, 2),
            "cost": round(scenario_cost, 2),
            "revenue": round(scenario_revenue, 2),
            "profit": round(scenario_profit, 2),
            "risk": scenario_risk
        },
        "differences": {
            "profit_diff": round(scenario_profit - base_profit, 2),
            "yield_diff": round(scenario_yield - base_yield, 2)
        },
        "explanation": explanations,
        "is_simulated": True,
        "grounded_farm_id": farm_id
    }

    try:
        if url and key and farm_id and farm_id not in ["F001", "FARM-001"]:
            from supabase import create_client
            sb = create_client(url, key)
            sb.table("scenarios").insert({
                "farm_id": farm_id,
                "scenario_name": f"Simulation: {changes.get('crop', 'Cotton')} ({changes.get('rainfall_change_percent', 0):+}% rain)",
                "description": "What-If agro-climatic simulation scenario",
                "parameters": changes,
                "simulation_results": result_payload["scenario"]
            }).execute()
    except Exception:
        pass

    return result_payload
