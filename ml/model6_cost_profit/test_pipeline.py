import json
from predict_cost import api_profit_endpoint
from economic_engine import calculate_economics

def run_tests():
    print("--- TESTING ECONOMIC ENGINE EDGE CASES ---")
    
    # 1. Zero cost
    res = calculate_economics(5.0, 20000, 0, 2.0)
    print("Zero cost:", res)
    assert res['roi_percentage'] == 0.0
    
    # 2. Zero yield
    res = calculate_economics(0.0, 20000, 50000, 2.0)
    print("Zero yield:", res)
    assert res['revenue_inr'] == 0.0
    assert res['profit_inr'] == -50000.0
    
    # 3. Missing values
    res = calculate_economics(None, None, None, None)
    print("Missing inputs:", res)
    assert res['revenue_inr'] == 0.0
    
    # 4. Negative values
    res = calculate_economics(-5.0, -1000, -500, -2.0)
    print("Negative inputs (should be handled/floored):", res)
    
    print("\n--- TESTING API PIPELINE (COST MODEL INTEGRATION) ---")
    
    # 5. Standard Farm
    farm_1 = {
      "crop": "Rice",
      "state": "Maharashtra",
      "district": "Nashik",
      "area_hectares": 2.0,
      "soil_ph": 6.5,
      "nitrogen": 80,
      "phosphorus": 40,
      "potassium": 50,
      "rainfall_mm": 850,
      "temperature_c": 27,
      "humidity_pct": 70,
      "irrigation_method": "Drip"
    }
    res_1 = api_profit_endpoint(farm_1)
    print("\nStandard Farm (Rice in Nashik):")
    print(json.dumps(res_1, indent=2))
    
    # 6. Unsupported Crop (Coverage Warning Test)
    farm_2 = farm_1.copy()
    farm_2["crop"] = "Onion"
    res_2 = api_profit_endpoint(farm_2)
    print("\nUnsupported Crop (Onion):")
    print(res_2["cost_analysis"]["coverage_warning"])
    assert "Onion is outside training support" in res_2["cost_analysis"]["coverage_warning"]
    
    # 7. Extremely large area
    farm_3 = farm_1.copy()
    farm_3["area_hectares"] = 1000.0
    res_3 = api_profit_endpoint(farm_3)
    print("\nExtremely Large Area (1000 ha) Cost:", res_3["cost_analysis"]["predicted_cost_inr"])
    
    print("\nALL TESTS COMPLETED SUCCESSFULLY.")

if __name__ == "__main__":
    run_tests()
