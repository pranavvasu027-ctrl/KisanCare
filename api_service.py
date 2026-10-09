import pandas as pd
import numpy as np
import xgboost as xgb
import json
import os
from datetime import datetime
from market_price_features import prepare_data, create_features

REGISTRY = {
    ('Onion', 'Pune(Pimpri) APMC'): {
        'dataset_market': 'Pune(Pimpri)',
        'report_key': 'Onion_Pune(Pimpri)',
        7: {'type': 'ma7', 'path': None, 'version': 'v1.0'},
        14: {'type': 'ma7', 'path': None, 'version': 'v1.0'}
    },
    ('Tomato', 'Pune(Pimpri) APMC'): {
        'dataset_market': 'Pune(Pimpri)',
        'report_key': 'Tomato_Pune(Pimpri)',
        7: {'type': 'ma7', 'path': None, 'version': 'v1.0'},
        14: {'type': 'XGBoost', 'path': 'tomato_pune_pimpri_14d.json', 'version': 'v1.0'}
    },
    ('Cabbage', 'Pune(Manjri) APMC'): {
        'dataset_market': 'Pune(Manjri)',
        'report_key': 'Cabbage_Pune(Manjri)',
        7: {'type': 'XGBoost', 'path': 'cabbage_pune_manjri_7d.json', 'version': 'v1.0'},
        14: {'type': 'XGBoost', 'path': 'cabbage_pune_manjri_14d.json', 'version': 'v1.0'}
    },
    ('Potato', 'Pune(Manjri) APMC'): {
        'dataset_market': 'Pune(Manjri) APMC',
        'report_key': 'Potato_Pune(Manjri) APMC',
        7: {'type': 'XGBoost', 'path': 'potato_pune_manjriapmc_7d.json', 'version': 'v1.0', 'status': 'YELLOW'},
        14: {'type': 'ma7', 'path': None, 'version': 'v1.0', 'status': 'YELLOW'}
    },
    ('Cauliflower', 'Pune(Manjri) APMC'): {
        'dataset_market': 'Pune(Manjri) APMC',
        'report_key': 'Cauliflower_Pune(Manjri) APMC',
        7: {'type': 'ma7', 'path': None, 'version': 'v1.0', 'status': 'YELLOW'},
        14: {'type': 'ma7', 'path': None, 'version': 'v1.0', 'status': 'YELLOW'}
    }
}

class KisanCareForecaster:
    def __init__(self, data_path='data/mandi_prices.csv', model_dir='models'):
        self.data_path = data_path
        self.model_dir = model_dir
        
        self.df = pd.read_csv(data_path)
        
        report_path = os.path.join(model_dir, 'training_report.json')
        if os.path.exists(report_path):
            with open(report_path, 'r') as f:
                self.metrics = json.load(f)
        else:
            self.metrics = {}
            
        self.loaded_models = {}

    def _load_model(self, path):
        if not path: return None
        if path not in self.loaded_models:
            full_path = os.path.join(self.model_dir, path)
            if not os.path.exists(full_path):
                raise FileNotFoundError(f"Model artifact {full_path} missing.")
            model = xgb.XGBRegressor()
            model.load_model(full_path)
            self.loaded_models[path] = model
        return self.loaded_models[path]

    def _format_error(self, req, msg):
        return {
            "crop": req.get('crop'),
            "market": req.get('market'),
            "horizon_days": req.get('horizon_days'),
            "error": msg
        }

    def predict(self, req):
        # 1. Validation
        crop = req.get('crop', '').capitalize()
        # Handle cases where user sends "Pune" but we map to APMC
        market = req.get('market', '')
        if market == 'Pune':
            # Resolve to the correct default locked market
            if crop in ['Onion', 'Tomato']: market = 'Pune(Pimpri) APMC'
            elif crop in ['Cabbage', 'Potato', 'Cauliflower']: market = 'Pune(Manjri) APMC'
            
        # Ensure exact match
        horizon = req.get('horizon_days')
        date_str = req.get('date')
        
        if (crop, market) not in REGISTRY:
            return self._format_error(req, f"Crop '{crop}' in '{market}' is not supported in V1.")
            
        if horizon not in [7, 14]:
            return self._format_error(req, f"Horizon {horizon} is unsupported. Use 7 or 14.")
            
        try:
            target_date = pd.to_datetime(date_str)
        except:
            return self._format_error(req, f"Invalid or missing date '{date_str}'")

        # 2. Get Registry Info
        reg_info = REGISTRY[(crop, market)]
        dataset_market = reg_info['dataset_market']
        report_key = reg_info['report_key']
        model_info = reg_info[horizon]
        
        # 3. Data Prep
        sub = prepare_data(self.df, crop, dataset_market)
        sub = sub[sub.index <= target_date]
        
        if sub.empty:
            return self._format_error(req, "Insufficient historical data to calculate forecasts.")
            
        # Freshness Check
        last_date = sub.index[-1]
        gap_days = (target_date - last_date).days
        current_price = float(sub['Modal_Price'].iloc[-1])
        
        if current_price <= 0:
            return self._format_error(req, f"Invalid historical negative/zero price detected: {current_price}")
            
        warnings = []
        if gap_days > 4:
            return {
                "crop": crop,
                "market": market,
                "horizon_days": horizon,
                "current_price": {
                    "value": round(current_price, 2),
                    "date": str(last_date.date()),
                    "source_status": "verified (stale)"
                },
                "forecast_status": "unavailable",
                "warnings": [f"Stale mandi price ({gap_days} days old). No forecast generated."]
            }
            
        if len(sub) < 15:
            return {
                "crop": crop,
                "market": market,
                "horizon_days": horizon,
                "current_price": {
                    "value": round(current_price, 2),
                    "date": str(last_date.date()),
                    "source_status": "verified"
                },
                "forecast_status": "insufficient_data",
                "warnings": ["Insufficient historical data (requires > 15 days)."]
            }
            
        # Features
        all_features = create_features(sub)
        features = all_features.iloc[[-1]].copy()
        
        rolling_mean_7 = float(features['rolling_mean_7'].iloc[0])
        rolling_std_7 = float(features['rolling_std_7'].iloc[0])
        
        feature_cols = ['Modal_Price', 'lag_1', 'lag_3', 'lag_7', 'lag_14', 
                        'rolling_mean_7', 'rolling_mean_14', 'rolling_std_7', 
                        'day_of_week', 'month']
        features_df = features[feature_cols]
        
        # Load Model
        try:
            model_obj = self._load_model(model_info['path'])
        except Exception as e:
            return self._format_error(req, f"Model load failure: {e}")
            
        # Predict
        if model_info['type'] == 'ma7':
            exp = rolling_mean_7
        else:
            exp = float(model_obj.predict(features_df)[0])
            
        if np.isnan(exp) or np.isinf(exp) or exp <= 0:
            exp = current_price
            
        exp = max(0.1, exp)
        
        # Uncertainty
        crop_metrics = self.metrics.get(report_key, {})
        metrics_dict = crop_metrics.get(f'metrics_{horizon}d', {})
        # Depending on phase 1 vs phase 4, metrics structure slightly varies (nested 'xgb' or 'ma7')
        type_key = 'xgb' if model_info['type'] == 'XGBoost' else 'ma7'
        mape_val = metrics_dict.get(type_key, {}).get('mape', 15.0) / 100.0
        
        uncert = exp * max(0.05, min(0.50, mape_val))
        min_p = max(0.0, exp - uncert)
        max_p = exp + uncert
        
        # Volatility
        cv = rolling_std_7 / rolling_mean_7 if rolling_mean_7 > 0 else 0
        if cv < 0.05: vol_class = "LOW"
        elif cv <= 0.15: vol_class = "MEDIUM"
        else: vol_class = "HIGH"
        
        # Trend
        if exp > current_price * 1.01: trend = "RISING"
        elif exp < current_price * 0.99: trend = "FALLING"
        else: trend = "STABLE"
        
        # Abnormal detection
        abnormal = False
        if len(sub) >= 30:
            rolling_mean_30 = sub['Modal_Price'].iloc[-30:].mean()
            rolling_std_30 = sub['Modal_Price'].iloc[-30:].std()
            z_score = abs(exp - rolling_mean_30) / (rolling_std_30 + 1e-5)
            if z_score > 3.0:
                abnormal = True
                warnings.append("Abnormal forecast \u2014 use with caution.")
                
        if model_info.get('status') == 'YELLOW':
            warnings.append("Short training history \u2014 model relies on limited seasonal data.")
                
        # Confidence
        conf_score = 100 - (mape_val * 100)
        if vol_class == "HIGH": conf_score -= 15
        elif vol_class == "MEDIUM": conf_score -= 5
        
        if abnormal:
            conf_class = "LOW"
        elif conf_score >= 80:
            conf_class = "HIGH"
        elif conf_score >= 60:
            conf_class = "MEDIUM"
        else:
            conf_class = "LOW"
            
        if conf_class == "LOW" and not abnormal:
            warnings.append("Low confidence forecast")
            
        # Structure Response
        response = {
            "crop": crop,
            "market": market,
            "horizon_days": horizon,
            "current_price": {
                "value": round(current_price, 2),
                "date": str(last_date.date()),
                "source_status": "verified"
            },
            "forecast": {
                "expected_price": round(exp, 2),
                "min_price": round(min_p, 2) if conf_class != "LOW" else None,
                "max_price": round(max_p, 2) if conf_class != "LOW" else None,
                "trend": trend
            },
            "confidence": conf_class,
            "volatility": vol_class,
            "model": {
                "type": model_info['type'],
                "version": model_info['version']
            },
            "warnings": warnings
        }
        
        # Logging
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "prediction_date": target_date.isoformat(),
            "crop": crop,
            "market": market,
            "horizon": horizon,
            "current_price": current_price,
            "predicted_price": exp,
            "model": model_info['type'],
            "confidence": conf_class,
            "volatility": vol_class,
            "warning_status": bool(warnings)
        }
        with open("prediction_logs.jsonl", "a") as lf:
            lf.write(json.dumps(log_entry) + "\n")
            
        return response
