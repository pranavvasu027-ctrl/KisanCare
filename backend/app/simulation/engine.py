from app.economics.engine import calculate_economics

def run_simulation(farm_id: str, changes: dict) -> dict:
    # Baseline dummy data
    baseline_yield = 24
    baseline_cost = 30000
    baseline_revenue = 60000
    
    # Apply changes for scenario
    scenario_yield = baseline_yield
    if "rainfall_change_percent" in changes:
        rf_change = changes["rainfall_change_percent"]
        # Dummy sensitivity: -20% rainfall = -15% yield
        scenario_yield = baseline_yield * (1 + (rf_change * 0.75 / 100))
        
    scenario_cost = baseline_cost
    if "input_cost" in changes:
        scenario_cost = changes["input_cost"]
        
    scenario_revenue = scenario_yield * 2500
    
    baseline_metrics = calculate_economics({"expected_yield": baseline_yield, "input_cost": 10000, "labour_cost": 15000, "irrigation_cost": 5000})
    scenario_metrics = calculate_economics({"expected_yield": scenario_yield, "input_cost": scenario_cost - 20000, "labour_cost": 15000, "irrigation_cost": 5000})
    
    return {
        "baseline": {
            "yield": baseline_yield,
            "cost": baseline_metrics["total_cost"],
            "revenue": baseline_metrics["expected_revenue"],
            "profit": baseline_metrics["expected_profit"],
            "risk": 0.35
        },
        "scenario": {
            "yield": round(scenario_yield, 2),
            "cost": scenario_metrics["total_cost"],
            "revenue": scenario_metrics["expected_revenue"],
            "profit": scenario_metrics["expected_profit"],
            "risk": 0.52 if scenario_yield < baseline_yield else 0.30
        },
        "differences": {
            "profit_diff": scenario_metrics["expected_profit"] - baseline_metrics["expected_profit"]
        },
        "explanation": [
            f"Rainfall changed by {changes.get('rainfall_change_percent', 0)}% affecting yield.",
            "This is a mocked simulation for MVP."
        ]
    }
