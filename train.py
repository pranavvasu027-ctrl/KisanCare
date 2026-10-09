import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, root_mean_squared_error
import os
import json
from market_price_features import prepare_data, create_features

def mape(y_true, y_pred):
    return np.mean(np.abs((y_true - y_pred) / y_true)) * 100

def directional_accuracy(y_true_curr, y_true_fut, y_pred_fut):
    actual_dir = np.sign(y_true_fut - y_true_curr)
    pred_dir = np.sign(y_pred_fut - y_true_curr)
    # Ignore flat predictions or actuals
    mask = (actual_dir != 0)
    if not np.any(mask): return 0.0
    return np.mean(actual_dir[mask] == pred_dir[mask]) * 100

def train_and_evaluate(df_feat, crop, market, horizon_col, lag_baseline_col):
    n = len(df_feat)
    train_end = int(n * 0.7)
    val_end = int(n * 0.85)
    
    train = df_feat.iloc[:train_end]
    val = df_feat.iloc[train_end:val_end]
    test = df_feat.iloc[val_end:]
    
    features = ['Modal_Price', 'lag_1', 'lag_3', 'lag_7', 'lag_14', 
                'rolling_mean_7', 'rolling_mean_14', 'rolling_std_7', 
                'day_of_week', 'month']
                
    X_train, y_train = train[features], train[horizon_col]
    X_val, y_val = val[features], val[horizon_col]
    X_test, y_test = test[features], test[horizon_col]
    
    # 1. Naive Baseline (lag from exactly H days ago -> which is Modal_Price)
    # If horizon is 7, the naive prediction of price 7 days from now is today's price (Modal_Price)
    pred_naive = test['Modal_Price']
    
    # 2. MA7 Baseline (7-day rolling mean up to today)
    pred_ma7 = test['Modal_Price'].rolling(7, min_periods=1).mean()
    
    # 3. ML Model (XGBoost)
    model = xgb.XGBRegressor(n_estimators=100, max_depth=4, learning_rate=0.05, early_stopping_rounds=10, random_state=42)
    model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
    pred_xgb = model.predict(X_test)
    
    current_price_test = test['Modal_Price'].values
    y_test_vals = y_test.values
    
    metrics = {
        'naive': {
            'mae': mean_absolute_error(y_test_vals, pred_naive),
            'rmse': root_mean_squared_error(y_test_vals, pred_naive),
            'mape': mape(y_test_vals, pred_naive),
            'da': directional_accuracy(current_price_test, y_test_vals, pred_naive)
        },
        'ma7': {
            'mae': mean_absolute_error(y_test_vals, pred_ma7),
            'rmse': root_mean_squared_error(y_test_vals, pred_ma7),
            'mape': mape(y_test_vals, pred_ma7),
            'da': directional_accuracy(current_price_test, y_test_vals, pred_ma7)
        },
        'xgb': {
            'mae': mean_absolute_error(y_test_vals, pred_xgb),
            'rmse': root_mean_squared_error(y_test_vals, pred_xgb),
            'mape': mape(y_test_vals, pred_xgb),
            'da': directional_accuracy(current_price_test, y_test_vals, pred_xgb)
        }
    }
    
    return model, metrics, test.index[0].date(), test.index[-1].date()

def main():
    print("Loading data...")
    df = pd.read_csv('data/mandi_prices.csv')
    
    targets = [
        ('Onion', 'Pune(Pimpri)'),
        ('Tomato', 'Pune(Pimpri)'),
        ('Cabbage', 'Pune(Manjri)')
    ]
    
    os.makedirs('models', exist_ok=True)
    report_data = {}
    
    for crop, market in targets:
        print(f"Processing {crop} in {market}...")
        sub = prepare_data(df, crop, market)
        df_feat = create_features(sub)
        df_feat = df_feat.dropna()
        
        # 7-Day Forecast
        model_7d, metrics_7d, test_start, test_end = train_and_evaluate(df_feat, crop, market, 'target_7d', 'lag_7')
        
        # 14-Day Forecast
        model_14d, metrics_14d, _, _ = train_and_evaluate(df_feat, crop, market, 'target_14d', 'lag_14')
        
        # Save models
        slug = f"{crop}_{market}".replace('(', '_').replace(')', '').lower()
        model_7d.save_model(f"models/{slug}_7d.json")
        model_14d.save_model(f"models/{slug}_14d.json")
        
        report_data[f"{crop}_{market}"] = {
            'crop': crop,
            'market': market,
            'test_period': f"{test_start} to {test_end}",
            'metrics_7d': metrics_7d,
            'metrics_14d': metrics_14d
        }
        
    with open('models/training_report.json', 'w') as f:
        json.dump(report_data, f, indent=4)
        
    print("Training complete. Report saved to models/training_report.json")

if __name__ == '__main__':
    main()
