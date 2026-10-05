import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from economic_engine.engine import calculate_economics

def test_profitable_farm():
    res = calculate_economics(farm_area_hectares=2.0, predicted_total_cost_inr=50000, 
                              predicted_yield_tonnes_per_hectare=3.0, predicted_market_price_inr_per_tonne=20000)
    assert res["economic_status"] == "PROFITABLE"
    assert res["expected_revenue_inr"] == 120000 # 2 * 3 * 20000
    assert res["expected_profit_inr"] == 70000 # 120000 - 50000
    assert res["roi_percent"] == 140.0 # 70k / 50k
    assert res["break_even_price_inr_per_tonne"] == 50000 / 6.0

def test_loss_making_farm():
    res = calculate_economics(farm_area_hectares=2.0, predicted_total_cost_inr=150000, 
                              predicted_yield_tonnes_per_hectare=3.0, predicted_market_price_inr_per_tonne=20000)
    assert res["economic_status"] == "LOSS"
    assert res["expected_profit_inr"] == -30000

def test_break_even_farm():
    res = calculate_economics(farm_area_hectares=2.0, predicted_total_cost_inr=120000, 
                              predicted_yield_tonnes_per_hectare=3.0, predicted_market_price_inr_per_tonne=20000)
    assert res["economic_status"] == "BREAK_EVEN"
    assert res["expected_profit_inr"] == 0.0

def test_small_farm():
    res = calculate_economics(farm_area_hectares=0.5, predicted_total_cost_inr=25000, 
                              predicted_yield_tonnes_per_hectare=3.0, predicted_market_price_inr_per_tonne=20000)
    assert res["expected_revenue_inr"] == 30000 # 0.5 * 3 * 20k

def test_large_farm():
    res = calculate_economics(farm_area_hectares=20.0, predicted_total_cost_inr=1000000, 
                              predicted_yield_tonnes_per_hectare=3.0, predicted_market_price_inr_per_tonne=20000)
    assert res["expected_revenue_inr"] == 1200000 # 20 * 3 * 20k

def test_high_yield():
    res = calculate_economics(farm_area_hectares=1.0, predicted_total_cost_inr=50000, 
                              predicted_yield_tonnes_per_hectare=10.0, predicted_market_price_inr_per_tonne=20000)
    assert res["expected_revenue_inr"] == 200000

def test_low_yield():
    res = calculate_economics(farm_area_hectares=1.0, predicted_total_cost_inr=50000, 
                              predicted_yield_tonnes_per_hectare=0.5, predicted_market_price_inr_per_tonne=20000)
    assert res["expected_revenue_inr"] == 10000

def test_high_market_price():
    res = calculate_economics(farm_area_hectares=1.0, predicted_total_cost_inr=50000, 
                              predicted_yield_tonnes_per_hectare=3.0, predicted_market_price_inr_per_tonne=100000)
    assert res["expected_revenue_inr"] == 300000

def test_low_market_price():
    res = calculate_economics(farm_area_hectares=1.0, predicted_total_cost_inr=50000, 
                              predicted_yield_tonnes_per_hectare=3.0, predicted_market_price_inr_per_tonne=5000)
    assert res["expected_revenue_inr"] == 15000

def test_zero_cost():
    res = calculate_economics(farm_area_hectares=1.0, predicted_total_cost_inr=0, 
                              predicted_yield_tonnes_per_hectare=3.0, predicted_market_price_inr_per_tonne=20000)
    assert res["roi_percent"] is None # Avoid div by zero

def test_zero_revenue():
    res = calculate_economics(farm_area_hectares=1.0, predicted_total_cost_inr=50000, 
                              predicted_yield_tonnes_per_hectare=0.0, predicted_market_price_inr_per_tonne=20000)
    assert res["profit_margin_percent"] is None # Avoid div by zero
    assert res["expected_revenue_inr"] == 0

def test_zero_production():
    res = calculate_economics(farm_area_hectares=1.0, predicted_total_cost_inr=50000, 
                              predicted_yield_tonnes_per_hectare=0.0, predicted_market_price_inr_per_tonne=20000)
    assert res["break_even_price_inr_per_tonne"] is None # Avoid div by zero

def test_zero_farm_area():
    res = calculate_economics(farm_area_hectares=0.0, predicted_total_cost_inr=50000, 
                              predicted_yield_tonnes_per_hectare=3.0, predicted_market_price_inr_per_tonne=20000)
    assert res["economic_engine_status"] == "FAILED_ZERO_AREA"

def test_quintal_to_tonne_conversion():
    res = calculate_economics(farm_area_hectares=1.0, predicted_total_cost_inr=50000, 
                              predicted_yield_tonnes_per_hectare=30.0, predicted_market_price_inr_per_tonne=2000,
                              yield_unit="quintals/hectare", price_unit="INR/quintal")
    # 30 quintals = 3 tonnes
    # 2000 INR/quintal = 20000 INR/tonne
    assert res["predicted_yield_tonnes_per_hectare"] == 3.0
    assert res["predicted_market_price_inr_per_tonne"] == 20000.0
    assert res["expected_revenue_inr"] == 60000.0

def test_maharashtra_scenario():
    # Soybean typical
    res = calculate_economics(farm_area_hectares=2.0, predicted_total_cost_inr=125000, 
                              predicted_yield_tonnes_per_hectare=1.5, predicted_market_price_inr_per_tonne=45000)
    # Revenue = 2 * 1.5 * 45000 = 135000
    # Profit = 135000 - 125000 = 10000
    assert res["expected_revenue_inr"] == 135000
    assert res["expected_profit_inr"] == 10000
    assert res["economic_status"] == "PROFITABLE"
