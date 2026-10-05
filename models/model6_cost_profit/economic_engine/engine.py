def calculate_economics(
    farm_area_hectares: float,
    predicted_total_cost_inr: float,
    predicted_yield_tonnes_per_hectare: float = None,
    predicted_market_price_inr_per_tonne: float = None,
    cost_model_status: str = "SUCCESS",
    yield_model_status: str = "NOT_CONNECTED",
    market_model_status: str = "NOT_CONNECTED",
    yield_unit: str = "tonnes/hectare",
    price_unit: str = "INR/tonne"
) -> dict:
    
    # Unit Conversions
    if yield_unit == "quintals/hectare" and predicted_yield_tonnes_per_hectare is not None:
        predicted_yield_tonnes_per_hectare = predicted_yield_tonnes_per_hectare / 10.0
        
    if price_unit == "INR/quintal" and predicted_market_price_inr_per_tonne is not None:
        predicted_market_price_inr_per_tonne = predicted_market_price_inr_per_tonne * 10.0

    # Initialize defaults
    engine_status = "CALCULATED"
    production_tonnes = 0.0
    revenue_inr = 0.0
    profit_inr = 0.0
    roi_percent = None
    profit_margin_percent = None
    break_even_price = None
    break_even_yield = None
    economic_status = "UNKNOWN"
    
    # Area Safety
    if farm_area_hectares <= 0:
        return {
            "farm_area_hectares": farm_area_hectares,
            "predicted_yield_tonnes_per_hectare": predicted_yield_tonnes_per_hectare,
            "expected_production_tonnes": None,
            "predicted_market_price_inr_per_tonne": predicted_market_price_inr_per_tonne,
            "predicted_total_cost_inr": predicted_total_cost_inr,
            "predicted_cost_per_hectare_inr": None,
            "expected_revenue_inr": None,
            "expected_profit_inr": None,
            "roi_percent": None,
            "profit_margin_percent": None,
            "break_even_price_inr_per_tonne": None,
            "break_even_yield_tonnes_per_hectare": None,
            "economic_status": "ERROR_ZERO_AREA",
            "cost_model_status": cost_model_status,
            "yield_model_status": yield_model_status,
            "market_model_status": market_model_status,
            "economic_engine_status": "FAILED_ZERO_AREA"
        }
        
    cost_per_hectare = predicted_total_cost_inr / farm_area_hectares
    
    if predicted_yield_tonnes_per_hectare is not None and predicted_market_price_inr_per_tonne is not None:
        production_tonnes = predicted_yield_tonnes_per_hectare * farm_area_hectares
        revenue_inr = production_tonnes * predicted_market_price_inr_per_tonne
        profit_inr = revenue_inr - predicted_total_cost_inr
        
        # Economic Status
        if profit_inr > 0:
            economic_status = "PROFITABLE"
        elif profit_inr < 0:
            economic_status = "LOSS"
        else:
            economic_status = "BREAK_EVEN"
            
        # ROI
        if predicted_total_cost_inr > 0:
            roi_percent = (profit_inr / predicted_total_cost_inr) * 100.0
            
        # Margin
        if revenue_inr > 0:
            profit_margin_percent = (profit_inr / revenue_inr) * 100.0
            
        # Break Even Price
        if production_tonnes > 0:
            break_even_price = predicted_total_cost_inr / production_tonnes
            
        # Break Even Yield
        if predicted_market_price_inr_per_tonne > 0:
            break_even_yield = predicted_total_cost_inr / (farm_area_hectares * predicted_market_price_inr_per_tonne)

    return {
        "farm_area_hectares": float(farm_area_hectares),
        "predicted_yield_tonnes_per_hectare": float(predicted_yield_tonnes_per_hectare) if predicted_yield_tonnes_per_hectare is not None else None,
        "expected_production_tonnes": float(production_tonnes) if predicted_yield_tonnes_per_hectare is not None else None,
        "predicted_market_price_inr_per_tonne": float(predicted_market_price_inr_per_tonne) if predicted_market_price_inr_per_tonne is not None else None,
        "predicted_total_cost_inr": float(predicted_total_cost_inr),
        "predicted_cost_per_hectare_inr": float(cost_per_hectare),
        "expected_revenue_inr": float(revenue_inr) if predicted_yield_tonnes_per_hectare is not None else None,
        "expected_profit_inr": float(profit_inr) if predicted_yield_tonnes_per_hectare is not None else None,
        "roi_percent": float(roi_percent) if roi_percent is not None else None,
        "profit_margin_percent": float(profit_margin_percent) if profit_margin_percent is not None else None,
        "break_even_price_inr_per_tonne": float(break_even_price) if break_even_price is not None else None,
        "break_even_yield_tonnes_per_hectare": float(break_even_yield) if break_even_yield is not None else None,
        "economic_status": economic_status,
        "cost_model_status": cost_model_status,
        "yield_model_status": yield_model_status,
        "market_model_status": market_model_status,
        "economic_engine_status": engine_status
    }
