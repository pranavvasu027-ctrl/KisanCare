import xgboost as xgb
import os
import pandas as pd

def test_model_load(slug, horizon):
    path = f"models/{slug}_{horizon}.json"
    if not os.path.exists(path):
        print(f"[FAIL] Missing model file: {path}")
        return False
        
    try:
        model = xgb.XGBRegressor()
        model.load_model(path)
        
        # Test predict with dummy data
        dummy_df = pd.DataFrame([{
            'Modal_Price': 1000, 'lag_1': 1000, 'lag_3': 1000, 'lag_7': 1000, 'lag_14': 1000,
            'rolling_mean_7': 1000, 'rolling_mean_14': 1000, 'rolling_std_7': 10,
            'day_of_week': 2, 'month': 6
        }])
        
        pred = model.predict(dummy_df)
        print(f"[PASS] Successfully loaded {path} and predicted: {pred[0]:.2f}")
        return True
    except Exception as e:
        print(f"[FAIL] Failed to load/predict {path}: {e}")
        return False

print("Testing Phase 4 Models...")
test_model_load("potato_punemanjriapmc", "7d")
test_model_load("potato_punemanjriapmc", "14d")
test_model_load("cauliflower_punemanjriapmc", "7d")
test_model_load("cauliflower_punemanjriapmc", "14d")
