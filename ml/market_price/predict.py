import os
import xgboost as xgb
import numpy as np
from typing import Dict, Any

class MarketPricePredictor:
    def __init__(self, models_dir: str = "models"):
        self.models_dir = models_dir
        self.loaded_models = {}

    def _get_model_path(self, crop: str, market: str, horizon: int) -> str:
        # e.g. models/onion_pune_pimpri_7d.json
        crop_clean = crop.lower().replace(" ", "_")
        market_clean = market.lower().replace("(", "").replace(")", "").replace(" ", "_")
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

    def predict(self, crop: str, market: str, current_price: float, month: int, day_of_week: int) -> Dict[str, Any]:
        """
        Synthesizes historical features from the current price and predicts 7d and 14d horizons.
        Since we lack a live historical DB, we approximate the lag features for inference testing.
        """
        try:
            model_7d_path = self._get_model_path(crop, market, 7)
            model_14d_path = self._get_model_path(crop, market, 14)
            
            model_7d = self._load_model(model_7d_path)
            model_14d = self._load_model(model_14d_path)
            
            # Features: ['Modal_Price', 'lag_1', 'lag_3', 'lag_7', 'lag_14', 'rolling_mean_7', 'rolling_mean_14', 'rolling_std_7', 'day_of_week', 'month']
            # We synthesize realistic recent data
            lag_1 = current_price * 0.99
            lag_3 = current_price * 1.02
            lag_7 = current_price * 0.95
            lag_14 = current_price * 1.05
            rolling_mean_7 = current_price * 0.98
            rolling_mean_14 = current_price * 1.01
            rolling_std_7 = current_price * 0.05
            
            features = np.array([[
                current_price, lag_1, lag_3, lag_7, lag_14, 
                rolling_mean_7, rolling_mean_14, rolling_std_7, 
                day_of_week, month
            ]])
            
            dmatrix = xgb.DMatrix(features, feature_names=model_7d.feature_names)
            
            pred_7d = float(model_7d.predict(dmatrix)[0])
            pred_14d = float(model_14d.predict(dmatrix)[0])
            
            return {
                "status": "success",
                "model_type": "xgboost_trained",
                "crop": crop,
                "market": market,
                "current_price": current_price,
                "forecast_7d": round(pred_7d, 2),
                "forecast_14d": round(pred_14d, 2),
                "trend": "Up" if pred_7d > current_price else "Down"
            }
        except FileNotFoundError as e:
            return {
                "status": "error",
                "message": str(e),
                "model_type": "xgboost_trained"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Inference error: {str(e)}",
                "model_type": "xgboost_trained"
            }
