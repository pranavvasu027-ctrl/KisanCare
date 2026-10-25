import os
import sys
import json
from datetime import datetime
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, root_mean_squared_error

sys.stdout.reconfigure(encoding='utf-8')

def mape(y_true, y_pred):
    mask = (y_true != 0) & (~np.isnan(y_true)) & (~np.isnan(y_pred))
    if not np.any(mask):
        return 0.0
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)

def directional_accuracy(y_curr, y_true, y_pred):
    actual_dir = np.sign(y_true - y_curr)
    pred_dir = np.sign(y_pred - y_curr)
    mask = (actual_dir != 0) & (~np.isnan(actual_dir)) & (~np.isnan(pred_dir))
    if not np.any(mask):
        return 0.0
    return float(np.mean(actual_dir[mask] == pred_dir[mask]) * 100)

def build_features_and_targets(df_crop):
    df = df_crop.sort_values('Date').copy()
    daily = df.groupby('Date')['Modal_Price'].median().reset_index()
    daily = daily.set_index('Date').asfreq('D')
    
    # Impute missing days via forward-fill and rolling mean
    daily['Modal_Price'] = daily['Modal_Price'].ffill(limit=7)
    daily['Modal_Price'] = daily['Modal_Price'].fillna(daily['Modal_Price'].shift(1).rolling(14, min_periods=1).mean()).ffill()
    
    df_feat = daily.copy()
    
    # Percentage returns relative to past lags (strictly PAST)
    for lag in [1, 3, 7, 14, 28]:
        df_feat[f'ret_lag_{lag}'] = (df_feat['Modal_Price'] - df_feat['Modal_Price'].shift(lag)) / df_feat['Modal_Price'].shift(lag)
    
    df_feat['rolling_mean_7_ratio'] = df_feat['Modal_Price'].shift(1).rolling(7, min_periods=1).mean() / df_feat['Modal_Price']
    df_feat['rolling_mean_14_ratio'] = df_feat['Modal_Price'].shift(1).rolling(14, min_periods=1).mean() / df_feat['Modal_Price']
    df_feat['rolling_mean_28_ratio'] = df_feat['Modal_Price'].shift(1).rolling(28, min_periods=1).mean() / df_feat['Modal_Price']
    df_feat['volatility_7'] = df_feat['ret_lag_1'].rolling(7, min_periods=1).std().fillna(0)
    
    df_feat['day_of_week'] = df_feat.index.day_of_week
    df_feat['month'] = df_feat.index.month
    
    # Future targets: ratio delta (strictly FUTURE)
    for h in [7, 14, 28]:
        df_feat[f'target_{h}d'] = df_feat['Modal_Price'].shift(-h)
        df_feat[f'target_{h}d_ratio'] = (df_feat[f'target_{h}d'] - df_feat['Modal_Price']) / df_feat['Modal_Price']
        
    return df_feat

def evaluate_predictions(y_curr, y_true, y_pred):
    return {
        'mae': round(float(mean_absolute_error(y_true, y_pred)), 2),
        'rmse': round(float(root_mean_squared_error(y_true, y_pred)), 2),
        'mape': round(float(mape(y_true, y_pred)), 2),
        'directional_accuracy_pct': round(float(directional_accuracy(y_curr, y_true, y_pred)), 2)
    }

def train_crop_horizon(df_feat, crop_name, horizon_days, feature_cols, output_models_dir):
    target_ratio_col = f'target_{horizon_days}d_ratio'
    target_price_col = f'target_{horizon_days}d'
    
    valid = df_feat.dropna(subset=feature_cols + [target_ratio_col, target_price_col, 'Modal_Price']).copy()
    n = len(valid)
    
    # Strict chronological split: 70% Train, 15% Val, 15% Test
    train_end = int(n * 0.70)
    val_end = int(n * 0.85)
    
    train = valid.iloc[:train_end]
    val = valid.iloc[train_end:val_end]
    test = valid.iloc[val_end:]
    
    X_train, y_train = train[feature_cols], train[target_ratio_col]
    X_val, y_val = val[feature_cols], val[target_ratio_col]
    X_test = test[feature_cols]
    
    model = xgb.XGBRegressor(
        n_estimators=150,
        max_depth=3,
        learning_rate=0.03,
        subsample=0.8,
        colsample_bytree=0.8,
        early_stopping_rounds=15,
        random_state=42
    )
    
    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        verbose=False
    )
    
    # Predict on test
    pred_ratio = model.predict(X_test)
    pred_price = test['Modal_Price'].values * (1.0 + pred_ratio)
    actual_price = test[target_price_col].values
    curr_price = test['Modal_Price'].values
    
    # Naive baseline (predict no change)
    naive_pred_price = curr_price
    # MA7 baseline
    ma7_pred_price = test['Modal_Price'].shift(1).rolling(7, min_periods=1).mean().bfill().values
    
    test_metrics = {
        'xgb': evaluate_predictions(curr_price, actual_price, pred_price),
        'naive_baseline': evaluate_predictions(curr_price, actual_price, naive_pred_price),
        'ma7_baseline': evaluate_predictions(curr_price, actual_price, ma7_pred_price)
    }
    
    crop_slug = crop_name.lower().strip()
    model_filename = f"{crop_slug}_market_{horizon_days}d.json"
    model_path = os.path.join(output_models_dir, model_filename)
    model.save_model(model_path)
    
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
    
    return {
        'model_file': model_filename,
        'feature_cols': feature_cols,
        'bounds': bounds,
        'test_metrics': test_metrics
    }

def main():
    base_dir = r"C:\Users\prana\Downloads\KISANcare\KISANcare\kisan-care"
    dataset_path = os.path.join(base_dir, "data", "cotton_tur_mandi_prices.csv")
    models_dir = os.path.join(base_dir, "models")
    os.makedirs(models_dir, exist_ok=True)
    
    print(f"Loading real data from {dataset_path}...")
    df = pd.read_csv(dataset_path)
    df['Date'] = pd.to_datetime(df['Date'])
    
    feature_cols = [
        'ret_lag_1', 'ret_lag_3', 'ret_lag_7', 'ret_lag_14', 'ret_lag_28',
        'rolling_mean_7_ratio', 'rolling_mean_14_ratio', 'rolling_mean_28_ratio',
        'volatility_7', 'day_of_week', 'month'
    ]
    
    report = {
        'generated_at': datetime.now().isoformat(),
        'dataset_source': 'Agmarknet (Ministry of Agriculture & Farmers Welfare, Government of India) and Maharashtra State Mandis',
        'dataset_records_count': len(df),
        'time_series_date_span': f"{df['Date'].min().strftime('%Y-%m-%d')} to {df['Date'].max().strftime('%Y-%m-%d')}",
        'crops': {}
    }
    
    for crop in ['Cotton', 'Tur']:
        print(f"\n==========================================")
        print(f"Training and Evaluating Models for {crop}")
        print(f"==========================================")
        
        df_crop = df[df['Commodity'].str.lower() == crop.lower()]
        print(f"Total raw observations: {len(df_crop)}")
        
        df_feat = build_features_and_targets(df_crop)
        print(f"Continuous time series days: {len(df_feat)}")
        
        crop_report = {}
        for horizon in [7, 14, 28]:
            res = train_crop_horizon(df_feat, crop, horizon, feature_cols, models_dir)
            crop_report[f'{horizon}d'] = res
            
            xgb_m = res['test_metrics']['xgb']
            print(f"--- Horizon {horizon} Days ---")
            print(f"  Test Window: {res['bounds']['test_start']} to {res['bounds']['test_end']} (N={res['bounds']['n_test']})")
            print(f"  XGBoost -> MAE: Rs.{xgb_m['mae']}/q, RMSE: Rs.{xgb_m['rmse']}/q, MAPE: {xgb_m['mape']}%, Dir Acc: {xgb_m['directional_accuracy_pct']}%")
            print(f"  Naive   -> MAE: Rs.{res['test_metrics']['naive_baseline']['mae']}/q, MAPE: {res['test_metrics']['naive_baseline']['mape']}%")
            
        report['crops'][crop] = crop_report
        
    report_file = os.path.join(models_dir, "market_evaluation_report.json")
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    print(f"\nFull evaluation report saved to {report_file}")

if __name__ == '__main__':
    main()
