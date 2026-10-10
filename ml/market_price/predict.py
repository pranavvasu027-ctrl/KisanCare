import os
import xgboost as xgb
import numpy as np
import pandas as pd
from typing import Dict, Any
from datetime import datetime, timedelta

class MarketPricePredictor:
    def __init__(self, models_dir: str = "models", data_path: str = "dataset/mandi_prices.csv"):
        self.models_dir = models_dir
        self.data_path = data_path
        self.loaded_models = {}
        # Load dataset once
        if os.path.exists(self.data_path):
            self.df = pd.read_csv(self.data_path)
            self.df['Arrival_Date'] = pd.to_datetime(self.df['Arrival_Date'], format='%d/%m/%Y')
        else:
            self.df = None

    def _get_model_path(self, crop: str, market: str, horizon: int) -> str:
        crop_clean = crop.lower().replace(" ", "_")
        # Handle "Pune(Pimpri)" -> "pune_pimpri"
        market_clean = market.lower().replace("(", "_").replace(")", "").replace(" ", "_")
        filename = f"{crop_clean}_{market_clean}_{horizon}d.json"
        return os.path.join(self.models_dir, filename)

    def _load_model(self, model_path: str) -> xgb.Booster:
        if model_path in self.loaded_models:
            return self.loaded_models[model_path]
            
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")
            
        model = xgb.Booster()
        model.load_model(model_path)
        self.loaded_models[model_path] = model
        return model

    def _generate_features(self, crop: str, market: str, target_date: datetime) -> np.ndarray:
        if self.df is None:
            raise ValueError("Historical dataset (mandi_prices.csv) not found. Forecasting requires historical ingestion.")
            
        # Filter for crop and market
        # Note: Dataset has 'Commodity' and 'Market'
        crop_df = self.df[(self.df['Commodity'].str.lower() == crop.lower()) & 
                          (self.df['Market'].str.lower() == market.lower())].copy()
                          
        if crop_df.empty:
            raise ValueError(f"No historical data found for {crop} at {market}.")
            
        # Sort by date
        crop_df = crop_df.sort_values('Arrival_Date').set_index('Arrival_Date')
        
        # We need continuous daily data up to the target_date
        # Create a full date range to find missing days
        min_date = crop_df.index.min()
        if target_date < min_date:
            raise ValueError("Target date is before the available historical data.")
            
        idx = pd.date_range(min_date, target_date)
        
        # Reindex and forward-fill missing prices
        crop_df = crop_df[~crop_df.index.duplicated(keep='last')]
        crop_df = crop_df.reindex(idx)
        crop_df['Modal_Price'] = crop_df['Modal_Price'].ffill()
        
        # If the target date (and preceding 14 days) are entirely NaN, we lack recent history
        if pd.isna(crop_df.loc[target_date, 'Modal_Price']):
            raise ValueError("Insufficient recent historical data. Please ingest fresh market data.")
            
        # Check if we have at least 14 days prior to target date
        if target_date - timedelta(days=14) < min_date:
            raise ValueError("Require at least 14 days of historical data prior to target date.")
            
        # Extract the relevant window
        window = crop_df.loc[target_date - timedelta(days=14) : target_date, 'Modal_Price']
        
        # If there are still NaNs in the window, we cannot compute
        if window.isna().any():
            raise ValueError("Historical data contains unfillable gaps.")
            
        # Calculate features
        current_price = window.loc[target_date]
        lag_1 = window.loc[target_date - timedelta(days=1)]
        lag_3 = window.loc[target_date - timedelta(days=3)]
        lag_7 = window.loc[target_date - timedelta(days=7)]
        lag_14 = window.loc[target_date - timedelta(days=14)]
        
        rolling_7 = window.loc[target_date - timedelta(days=6) : target_date]
        rolling_mean_7 = rolling_7.mean()
        rolling_std_7 = rolling_7.std() if len(rolling_7) > 1 else 0
        
        rolling_14 = window.loc[target_date - timedelta(days=13) : target_date]
        rolling_mean_14 = rolling_14.mean()
        
        month = target_date.month
        day_of_week = target_date.weekday() # Monday=0, Sunday=6. Note: Verify if model uses 0-6 or 1-7.
        
        features = np.array([[
            current_price, lag_1, lag_3, lag_7, lag_14,
            rolling_mean_7, rolling_mean_14, rolling_std_7,
            day_of_week, month
        ]])
        
        return features, current_price

    def predict(self, crop: str, market: str, date_str: str) -> Dict[str, Any]:
        """
        Uses genuine historical data to extract lags and rolling features.
        """
        try:
            target_date = pd.to_datetime(date_str).normalize()
            
            model_7d_path = self._get_model_path(crop, market, 7)
            model_14d_path = self._get_model_path(crop, market, 14)
            
            model_7d = self._load_model(model_7d_path)
            model_14d = self._load_model(model_14d_path)
            
            features, current_price = self._generate_features(crop, market, target_date)
            
            dmatrix = xgb.DMatrix(features, feature_names=model_7d.feature_names)
            
            pred_7d = float(model_7d.predict(dmatrix)[0])
            # pred_14d = float(model_14d.predict(dmatrix)[0])
            
            return {
                "status": "success",
                "model_type": "xgboost_trained",
                "crop": crop,
                "market": market,
                "target_date": date_str,
                "current_price": float(current_price),
                "forecast_7d": round(pred_7d, 2),
                "forecast_14d": "Unavailable (Undergoing Recalibration)",
                "trend": "Up" if pred_7d > current_price else "Down"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "model_type": "xgboost_trained"
            }
