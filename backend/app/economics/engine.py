def calculate_economics(data: dict) -> dict:
    # Dummy economics logic for demo
    expected_yield = data.get("expected_yield", 24)
    expected_price = data.get("expected_price", 2500)
    input_cost = data.get("input_cost", 10000)
    labour_cost = data.get("labour_cost", 15000)
    irrigation_cost = data.get("irrigation_cost", 5000)
    
    total_cost = input_cost + labour_cost + irrigation_cost
    expected_revenue = expected_yield * expected_price
    expected_profit = expected_revenue - total_cost
    roi = (expected_profit / total_cost) * 100 if total_cost > 0 else 0
    
    return {
        "total_cost": total_cost,
        "expected_revenue": expected_revenue,
        "expected_profit": expected_profit,
        "roi_percent": round(roi, 2),
        "break_even_price": total_cost / expected_yield if expected_yield > 0 else 0
    }
