# Market Price Forecasting Model

## 1. Model Purpose
The Market Price Forecasting model is designed to predict the future price of specific agricultural commodities in designated markets for a given horizon (7 or 14 days). This empowers farmers and stakeholders with actionable market insights for better timing of crop sales and storage decisions.

## 2. Existing Artifact Format
The model artifacts are saved as raw XGBoost JSON models in the `models/` directory.
Example: `models/onion_pune_pimpri_7d.json`
These files contain the parameters of a fully trained gradient boosting tree ensemble, preserving the split logic, feature weights, and base scores.

## 3. Actual Forecasting Method
The forecasting algorithm implemented is **XGBoost (Extreme Gradient Boosting)** with the `reg:squarederror` objective.
It relies on a time-series regression approach, treating lagged historical prices and rolling statistics as independent features to predict the future target price point.

## 4. Input Features
The model requires exactly 10 features, constructed from historical daily Modal Prices:
1. `Modal_Price`: The current/base day's modal price.
2. `lag_1`: The price 1 day prior.
3. `lag_3`: The price 3 days prior.
4. `lag_7`: The price 7 days prior.
5. `lag_14`: The price 14 days prior.
6. `rolling_mean_7`: The 7-day rolling mean of the 1-day lagged price.
7. `rolling_mean_14`: The 14-day rolling mean of the 1-day lagged price.
8. `rolling_std_7`: The 7-day rolling standard deviation of the 1-day lagged price.
9. `day_of_week`: The day of the week (0-6).
10. `month`: The month of the year (1-12).

## 5. Output Fields
- `crop`: The targeted crop.
- `market`: The targeted market.
- `forecast_horizon_days`: The requested horizon (7 or 14 days).
- `current_price`: The known current modal price.
- `forecast_price`: The predicted modal price.
- `trend`: Derived directional forecast ("rising", "falling", "stable").
- `model`: Identifies the exact model architecture used.
- `generated_at`: ISO timestamp of generation.

## 6. Supported Crops
- Onion
- Potato
- Tomato
- Cabbage
- Cauliflower

## 7. Supported Markets
Pune district markets including, but not limited to:
- Pune(Pimpri)
- Pune(Manjri) APMC
(Subject to the availability of historical data in `mandi_prices.csv` and an associated trained artifact).

## 8. Forecast Horizon
- 7 Days
- 14 Days

## 9. API Endpoint
**POST** `/api/market-price/`
**GET** `/api/market-price/health`

## 10. Example Request
```json
{
  "crop": "onion",
  "market": "Pune(Pimpri)",
  "date": "2024-07-29",
  "horizon_days": 7
}
```

## 11. Example Response
```json
{
  "crop": "onion",
  "market": "Pune(Pimpri)",
  "forecast_horizon_days": 7,
  "current_price": 2200.0,
  "forecast_price": 2345.50,
  "trend": "rising",
  "model": "xgboost_7d",
  "generated_at": "2026-10-06T18:50:00.000Z"
}
```

## 12. Limitations
- Does not inherently predict confidence intervals since XGBoost reg:squarederror is deterministic.
- Requires contiguous historical data for lag/rolling features to execute accurately.
- Missing past values limit accuracy as they require naive rolling means or forward-fill imputations.

## 13. Test Results
All API endpoints, error handlers, and prediction mechanisms successfully validated against existing 7-day and 14-day JSON artifacts via `pytest` (`tests/test_market_price.py`). Result: `7 passed`.
