import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, root_mean_squared_error
import os
import json
from market_price_features import prepare_data, create_features

def mape(y_true, y_pred):
    # Avoid div by zero
    mask = y_true != 0
    if not np.any(mask): return 0.0
    return np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100

def directional_accuracy(y_true_curr, y_true_fut, y_pred_fut):
    actual_dir = np.sign(y_true_fut - y_true_curr)
    pred_dir = np.sign(y_pred_fut - y_true_curr)
    mask = (actual_dir != 0)
    if not np.any(mask): return 0.0
def get_metrics(X, y_true_curr, y_true_fut, model=None, baseline_type=None):
    if baseline_type == 'naive':
        pred = y_true_curr
    elif baseline_type == 'ma7':
        # Recreate rolling ma7. It's stored in X['rolling_mean_7']
        pred = X['rolling_mean_7'].values
    else:
        pred = model.predict(X)
        
    y = y_true_fut.values
    
    return {
        'mae': mean_absolute_error(y, pred),
        'rmse': root_mean_squared_error(y, pred),
        'mape': mape(y, pred),
        'da': directional_accuracy(y_true_curr.values, y, pred)
    }

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
    
    model = xgb.XGBRegressor(n_estimators=100, max_depth=4, learning_rate=0.05, early_stopping_rounds=10, random_state=42)
    model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
    
    val_metrics = {
        'naive': get_metrics(X_val, val['Modal_Price'], y_val, baseline_type='naive'),
        'ma7': get_metrics(X_val, val['Modal_Price'], y_val, baseline_type='ma7'),
        'xgb': get_metrics(X_val, val['Modal_Price'], y_val, model=model)
    }
    
    test_metrics = {
        'naive': get_metrics(X_test, test['Modal_Price'], y_test, baseline_type='naive'),
        'ma7': get_metrics(X_test, test['Modal_Price'], y_test, baseline_type='ma7'),
        'xgb': get_metrics(X_test, test['Modal_Price'], y_test, model=model)
    }
    
    bounds = {
        'train_start': str(train.index[0].date()),
        'train_end': str(train.index[-1].date()),
        'val_start': str(val.index[0].date()),
        'val_end': str(val.index[-1].date()),
        'test_start': str(test.index[0].date()),
        'test_end': str(test.index[-1].date()),
        'n_train': len(train),
        'n_val': len(val),
        'n_test': len(test)
    }
    
    return model, val_metrics, test_metrics, bounds

def main():
    print("Loading data...")
    df = pd.read_csv('data/mandi_prices.csv')
    
    targets = [
        ('Potato', 'Pune(Manjri) APMC'),
        ('Cauliflower', 'Pune(Manjri) APMC')
    ]
    
    os.makedirs('models', exist_ok=True)
    
    # Load existing report to not overwrite
    if os.path.exists('models/training_report.json'):
        with open('models/training_report.json', 'r') as f:
            report_data = json.load(f)
    else:
        report_data = {}
    
    stats_data = {}
    
    for crop, market in targets:
        print(f"Processing {crop} in {market}...")
        
        # Data Audit
        raw_rows = len(df[(df['Commodity'] == crop) & (df['Market'] == market)])
        sub = prepare_data(df, crop, market)
        
        df_feat = create_features(sub)
        df_feat = df_feat.dropna()
        
        print(f"{crop} usable rows after features: {len(df_feat)}")
        
        # 7-Day Forecast
        model_7d, val_metrics_7d, test_metrics_7d, bounds = train_and_evaluate(df_feat, crop, market, 'target_7d', 'lag_7')
        
        # 14-Day Forecast
        model_14d, val_metrics_14d, test_metrics_14d, _ = train_and_evaluate(df_feat, crop, market, 'target_14d', 'lag_14')
        
        # Save models
        slug = f"{crop}_{market}".replace('(', '_').replace(')', '').replace(' ', '').lower()
        model_7d.save_model(f"models/{slug}_7d.json")
        model_14d.save_model(f"models/{slug}_14d.json")
        
        stats_data[crop] = {
            'bounds': bounds,
            'val_metrics_7d': val_metrics_7d,
            'test_metrics_7d': test_metrics_7d,
            'val_metrics_14d': val_metrics_14d,
            'test_metrics_14d': test_metrics_14d,
            'raw_rows': raw_rows,
            'usable_rows': len(df_feat)
        }
        
        # Saving TEST metrics to report_data for API backwards compatibility
        report_data[f"{crop}_{market}"] = {
            'crop': crop,
            'market': market,
            'test_period': f"{bounds['test_start']} to {bounds['test_end']}",
            'metrics_7d': test_metrics_7d,
            'metrics_14d': test_metrics_14d
        }
        
    with open('models/training_report.json', 'w') as f:
        json.dump(report_data, f, indent=4)
        
    with open('phase4_stats.json', 'w') as f:
        json.dump(stats_data, f, indent=4)
        
    print("Training complete. Stats saved.")

if __name__ == '__main__':
    main()
