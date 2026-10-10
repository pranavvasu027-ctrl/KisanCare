import os
import numpy as np
import pandas as pd
from datetime import timedelta
from sklearn.metrics import mean_absolute_error, mean_squared_error
from ml.market_price.predict import MarketPricePredictor

def run_backtest(crop="Onion", market="Pune(Pimpri)", start_date="2025-01-01", end_date="2025-10-15"):
    predictor = MarketPricePredictor(models_dir="models", data_path="dataset/mandi_prices.csv")
    
    # Load dataset
    df = predictor.df
    crop_df = df[(df['Commodity'].str.lower() == crop.lower()) & (df['Market'].str.lower() == market.lower())].copy()
    crop_df = crop_df.sort_values('Arrival_Date').set_index('Arrival_Date')
    
    # We need to evaluate the 7-day and 14-day forecasts
    # For a given date T, we predict the price for T+7 and T+14.
    # Then we compare against actual price at T+7 and T+14.
    
    dates = pd.date_range(start=start_date, end=end_date)
    
    results_7d = []
    results_14d = []
    
    for date in dates:
        try:
            # Check if actual future prices exist in our dataset
            actual_date_7d = date + timedelta(days=7)
            actual_date_14d = date + timedelta(days=14)
            
            # Reindex internally to ffill for truth (simulating reality where prices hold over weekends)
            if actual_date_7d not in crop_df.index:
                idx = pd.date_range(crop_df.index.min(), actual_date_14d)
                temp_df = crop_df[~crop_df.index.duplicated(keep='last')].reindex(idx)
                temp_df['Modal_Price'] = temp_df['Modal_Price'].ffill()
                actual_7d = temp_df.loc[actual_date_7d, 'Modal_Price']
                actual_14d = temp_df.loc[actual_date_14d, 'Modal_Price']
            else:
                actual_7d = crop_df.loc[actual_date_7d, 'Modal_Price']
                actual_14d = crop_df.loc[actual_date_14d, 'Modal_Price']
                
            if pd.isna(actual_7d) or pd.isna(actual_14d):
                continue
                
            res = predictor.predict(crop, market, date.strftime('%Y-%m-%d'))
            
            if res.get("status") == "success":
                results_7d.append({
                    "date": date,
                    "actual": actual_7d,
                    "predicted": res["forecast_7d"]
                })
                results_14d.append({
                    "date": date,
                    "actual": actual_14d,
                    "predicted": res["forecast_14d"]
                })
        except Exception:
            # E.g., insufficient history
            pass
            
    # Calculate metrics
    print(f"--- Backtest Results for {crop} at {market} ---")
    if results_7d:
        df_7d = pd.DataFrame(results_7d)
        mae_7 = mean_absolute_error(df_7d['actual'], df_7d['predicted'])
        rmse_7 = np.sqrt(mean_squared_error(df_7d['actual'], df_7d['predicted']))
        print(f"7-Day Forecast (n={len(df_7d)}):")
        print(f"  MAE: {mae_7:.2f}")
        print(f"  RMSE: {rmse_7:.2f}")
    else:
        print("Not enough valid backtest points for 7-day forecast.")
        
    if results_14d:
        df_14d = pd.DataFrame(results_14d)
        mae_14 = mean_absolute_error(df_14d['actual'], df_14d['predicted'])
        rmse_14 = np.sqrt(mean_squared_error(df_14d['actual'], df_14d['predicted']))
        print(f"\n14-Day Forecast (n={len(df_14d)}):")
        print(f"  MAE: {mae_14:.2f}")
        print(f"  RMSE: {rmse_14:.2f}")
    else:
        print("Not enough valid backtest points for 14-day forecast.")

if __name__ == "__main__":
    run_backtest()
