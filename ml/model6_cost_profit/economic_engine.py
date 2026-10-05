def calculate_economics(predicted_yield_tonnes_ha, predicted_price_inr_tonne, predicted_cost_inr, area_hectares=1.0):
    """
    Deterministic economic engine for KisanCare.
    """
    # Handle invalid or missing inputs gracefully
    try:
        y = float(predicted_yield_tonnes_ha) if predicted_yield_tonnes_ha is not None else 0.0
        p = float(predicted_price_inr_tonne) if predicted_price_inr_tonne is not None else 0.0
        c = float(predicted_cost_inr) if predicted_cost_inr is not None else 0.0
        a = float(area_hectares) if area_hectares is not None else 1.0
    except (ValueError, TypeError):
        y, p, c, a = 0.0, 0.0, 0.0, 1.0

    if y < 0: y = 0.0
    if p < 0: p = 0.0
    if c < 0: c = 0.0
    if a <= 0: a = 1.0
    
    # Economics calculation
    revenue = y * a * p
    profit = revenue - c
    
    if c > 0:
        roi = (profit / c) * 100.0
    else:
        roi = 0.0
        
    if y > 0 and a > 0:
        break_even_price = c / (y * a)
    else:
        break_even_price = 0.0
        
    return {
        "revenue_inr": round(revenue, 2),
        "profit_inr": round(profit, 2),
        "roi_percentage": round(roi, 2),
        "break_even_price_inr_tonne": round(break_even_price, 2)
    }
