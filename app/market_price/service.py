import os
import json
from datetime import datetime
import pandas as pd
import xgboost as xgb
from datetime import datetime
import sys

# Need to import market_price_features from the root dir or recreate its logic here
# Recreating the logic here to avoid sys.path issues
def prepare_data(df, crop, market):
    sub = df[(df['Commodity'].str.lower() == crop.lower()) & (df['Market'].str.lower() == market.lower())].copy()
    if sub.empty:
        return sub
    sub['Arrival_Date'] = pd.to_datetime(sub['Arrival_Date'], dayfirst=True)
    sub = sub.sort_values('Arrival_Date')
    
    # Handle multiple varieties per day
    sub = sub.groupby('Arrival_Date')['Modal_Price'].mean().reset_index()
    sub = sub.set_index('Arrival_Date').asfreq('D')
    
    # Impute small gaps (up to 3 days) with forward fill
    sub['Modal_Price'] = sub['Modal_Price'].ffill(limit=3)
    # Impute remaining gaps with a 7-day rolling mean
    sub['Modal_Price'] = sub['Modal_Price'].fillna(sub['Modal_Price'].rolling(7, min_periods=1).mean())
    sub['Modal_Price'] = sub['Modal_Price'].ffill() # catch-all
    
    return sub

def create_features(sub):
    df_feat = sub.copy()
    # Features (Strictly Past/Current)
    df_feat['lag_1'] = df_feat['Modal_Price'].shift(1)
    df_feat['lag_3'] = df_feat['Modal_Price'].shift(3)
    df_feat['lag_7'] = df_feat['Modal_Price'].shift(7)
    df_feat['lag_14'] = df_feat['Modal_Price'].shift(14)
    
    df_feat['rolling_mean_7'] = df_feat['lag_1'].rolling(7).mean()
    df_feat['rolling_mean_14'] = df_feat['lag_1'].rolling(14).mean()
    df_feat['rolling_std_7'] = df_feat['lag_1'].rolling(7).std()
    
    df_feat['day_of_week'] = df_feat.index.dayofweek
    df_feat['month'] = df_feat.index.month
    
    return df_feat

class MarketPriceService:
    def __init__(self, base_dir=None):
        if base_dir is None:
            self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
        else:
            self.base_dir = base_dir
            
        self.models_dir = os.path.join(self.base_dir, "models")
        self.data_file = os.path.join(self.base_dir, "data", "mandi_prices.csv")
        
        self.canonical_crops = {
            "onion": "Onion",
            "potato": "Potato",
            "tomato": "Tomato",
            "cabbage": "Cabbage",
            "cauliflower": "Cauliflower"
        }
        
    def _get_model_path(self, crop, market, horizon_days):
        crop_clean = crop.lower()
        market_clean = market.lower().replace("(", "_").replace(")", "").replace(" ", "")
        return os.path.join(self.models_dir, f"{crop_clean}_{market_clean}_{horizon_days}d.json")
        
    def health_check(self):
        # Verify data and at least one model exists
        data_exists = os.path.exists(self.data_file)
        # Check if any .json files exist in models dir
        models_exist = False
        if os.path.exists(self.models_dir):
            models_exist = any(f.endswith(".json") for f in os.listdir(self.models_dir))
            
        return {
            "status": "up" if data_exists and models_exist else "down",
            "data_available": data_exists,
            "models_available": models_exist
        }
        
    def predict(self, crop: str, market: str, target_date: str, horizon_days: int):
        # 1. Validate and normalize inputs
        if horizon_days not in [7, 14]:
            raise ValueError(f"Unsupported horizon_days: {horizon_days}. Supported: 7, 14")
            
        canonical_crop = self.canonical_crops.get(crop.lower(), crop.capitalize())
        
        # 2. Check if model exists
        model_path = self._get_model_path(canonical_crop, market, horizon_days)
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"No trained model found for {canonical_crop} in {market} for {horizon_days}d horizon.")
            
        # 3. Load data and generate features
        if not os.path.exists(self.data_file):
            raise FileNotFoundError(f"Historical data file not found at {self.data_file}")
            
        df = pd.read_csv(self.data_file)
        sub = prepare_data(df, canonical_crop, market)
        if sub.empty:
            raise ValueError(f"No historical data found for {canonical_crop} in {market}")
            
        features_df = create_features(sub)
        
        # If target_date is not in index, we can't reliably predict (or we just take the latest available)
        # The prompt says: "date": "YYYY-MM-DD". If the user specifies a date, we try to use it.
        # Otherwise, take the last available date.
        target_ts = pd.to_datetime(target_date)
        
        # If the exact date is missing from features, we try to use the closest past date, or just latest.
        # Wait, if we use a specific date, we get the features as of that date.
        if target_ts in features_df.index:
            row = features_df.loc[target_ts]
        else:
            # Get latest available
            row = features_df.iloc[-1]
            target_ts = features_df.index[-1]
            
        # Features array
        feature_cols = ['Modal_Price', 'lag_1', 'lag_3', 'lag_7', 'lag_14', 
                        'rolling_mean_7', 'rolling_mean_14', 'rolling_std_7', 
                        'day_of_week', 'month']
                        
        X_input = row[feature_cols].to_frame().T
        
        # If there are NaNs due to rolling window, fill them with something safe or drop?
        # A trained model expects numbers.
        X_input = X_input.fillna(0)
        
        # 4. Load XGBoost model
        booster = xgb.Booster()
        booster.load_model(model_path)
        
        dmatrix = xgb.DMatrix(X_input)
        prediction = booster.predict(dmatrix)[0]
        
        current_price = float(row['Modal_Price'])
        forecast_price = float(prediction)
        
        trend = "stable"
        if forecast_price > current_price * 1.02:
            trend = "rising"
        elif forecast_price < current_price * 0.98:
            trend = "falling"
            
        return {
            "crop": crop.lower(),
            "market": market,
            "forecast_horizon_days": horizon_days,
            "current_price": current_price,
            "forecast_price": round(forecast_price, 2),
            "trend": trend,
            "model": f"xgboost_{horizon_days}d",
            "generated_at": datetime.utcnow().isoformat()
        }
