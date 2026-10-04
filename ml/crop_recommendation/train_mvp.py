import pandas as pd
import numpy as np
import os
import json
import joblib
import xgboost as xgb
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error

# 1. Load Dataset
data_dir = 'C:/Users/prana/OneDrive/Desktop/Projects/KISANcare/kisan-care/data/model1/processed'
df_full = pd.read_csv(f'{data_dir}/kisancare_model1_v0.2.csv')

# 2. Prepare Official MVP Dataset
cols = ['District', 'Season', 'Crop_Year', 'Crop', 'Area_Frequency']
df = df_full[cols].copy()
df.to_csv(f'{data_dir}/kisancare_model1_mvp_baseline.csv', index=False)

# Convert strings to pandas Categorical type for XGBoost native support
cat_cols = ['District', 'Season', 'Crop']
for col in cat_cols:
    df[col] = df[col].astype('category')

all_crops = list(df['Crop'].cat.categories)

# 3. Splits
train = df[df['Crop_Year'] <= 2012].copy()
val   = df[df['Crop_Year'] == 2013].copy()
test  = df[df['Crop_Year'] >= 2014].copy()

X_train = train[['District', 'Season', 'Crop']]
y_train = train['Area_Frequency'].values
X_val = val[['District', 'Season', 'Crop']]
y_val = val['Area_Frequency'].values
X_test = test[['District', 'Season', 'Crop']]

# 4. Evaluation Function
def evaluate_ranking(model, eval_df, X_eval):
    actual_top = eval_df.loc[eval_df.groupby(['District', 'Season'])['Area_Frequency'].idxmax()][['District', 'Season', 'Crop']]
    unique_ds = eval_df[['District', 'Season']].drop_duplicates()
    
    unique_ds['key'] = 1
    crops_df = pd.DataFrame({'Crop': all_crops, 'key': 1})
    candidates = pd.merge(unique_ds, crops_df, on='key').drop('key', axis=1)
    
    # Cast to category matching the training data
    for col in cat_cols:
        candidates[col] = pd.Categorical(candidates[col], categories=df[col].cat.categories)
        
    candidates['Pred_Freq'] = model.predict(candidates[['District', 'Season', 'Crop']])
    candidates['Rank'] = candidates.groupby(['District', 'Season'])['Pred_Freq'].rank(ascending=False, method='first')
    
    merged = pd.merge(actual_top, candidates, on=['District', 'Season'], suffixes=('_actual', '_pred'))
    hits = merged[merged['Crop_actual'] == merged['Crop_pred']]
    
    top1 = (hits['Rank'] == 1).sum() / len(actual_top)
    top3 = (hits['Rank'] <= 3).sum() / len(actual_top)
    top5 = (hits['Rank'] <= 5).sum() / len(actual_top)
    return top1, top3, top5

# Historical Baseline
def eval_historical_baseline(eval_df, train_df):
    hist_avg = train_df.groupby(['District', 'Season', 'Crop'])['Area_Frequency'].mean().reset_index()
    hist_avg['Rank'] = hist_avg.groupby(['District', 'Season'])['Area_Frequency'].rank(ascending=False, method='first')
    
    actual_top = eval_df.loc[eval_df.groupby(['District', 'Season'])['Area_Frequency'].idxmax()][['District', 'Season', 'Crop']]
    merged = pd.merge(actual_top, hist_avg, on=['District', 'Season', 'Crop'], how='left')
    
    top1 = (merged['Rank'] == 1).sum() / len(actual_top)
    top3 = (merged['Rank'] <= 3).sum() / len(actual_top)
    top5 = (merged['Rank'] <= 5).sum() / len(actual_top)
    return top1, top3, top5

print("Historical Baseline:")
val_t1_hist, val_t3_hist, _ = eval_historical_baseline(val, train)
test_t1_hist, test_t3_hist, _ = eval_historical_baseline(test, train)
print(f"Val Top-1: {val_t1_hist:.3f} | Test Top-1: {test_t1_hist:.3f}")

# 5. Train XGBoost Model
print("\nTraining XGBoostRegressor (Native Categorical Support)...")
# Must set enable_categorical=True
xgb_model = xgb.XGBRegressor(
    n_estimators=100, 
    max_depth=6, 
    learning_rate=0.1, 
    enable_categorical=True, 
    random_state=42,
    tree_method='hist'
)

xgb_model.fit(X_train, y_train)

val_t1, val_t3, val_t5 = evaluate_ranking(xgb_model, val, X_val)
print(f"XGBoost -> Val Top-1: {val_t1:.3f} | Top-3: {val_t3:.3f}")

test_t1, test_t3, test_t5 = evaluate_ranking(xgb_model, test, X_test)
print(f"XGBoost -> Test Top-1: {test_t1:.3f} | Top-3: {test_t3:.3f}")

# 6. Optional Experiment: Add proxy weather/soil features
print("\nRunning Experimental Proxy Feature Model (XGBoost)...")
exp_cols = ['District', 'Season', 'Crop', 'Hist_Rainfall', 'Hist_Temperature', 'Soil_N', 'Soil_pH']
df_exp = df_full[exp_cols + ['Crop_Year', 'Area_Frequency']].copy()

for col in cat_cols:
    df_exp[col] = df_exp[col].astype('category')

train_exp = df_exp[df_exp['Crop_Year'] <= 2012]
val_exp = df_exp[df_exp['Crop_Year'] == 2013]

X_train_exp = train_exp[exp_cols]
X_val_exp = val_exp[exp_cols]

xgb_exp = xgb.XGBRegressor(
    n_estimators=100, max_depth=6, learning_rate=0.1, 
    enable_categorical=True, random_state=42, tree_method='hist'
)
xgb_exp.fit(X_train_exp, y_train)

def evaluate_exp_ranking(model, eval_df):
    actual_top = eval_df.loc[eval_df.groupby(['District', 'Season'])['Area_Frequency'].idxmax()][['District', 'Season', 'Crop']]
    unique_ds = eval_df[['District', 'Season', 'Hist_Rainfall', 'Hist_Temperature', 'Soil_N', 'Soil_pH']].drop_duplicates()
    
    unique_ds['key'] = 1
    crops_df = pd.DataFrame({'Crop': all_crops, 'key': 1})
    candidates = pd.merge(unique_ds, crops_df, on='key').drop('key', axis=1)
    
    for col in cat_cols:
        candidates[col] = pd.Categorical(candidates[col], categories=df_full[col].unique())
        
    candidates['Pred_Freq'] = model.predict(candidates[exp_cols])
    candidates['Rank'] = candidates.groupby(['District', 'Season'])['Pred_Freq'].rank(ascending=False, method='first')
    
    merged = pd.merge(actual_top, candidates, on=['District', 'Season'], suffixes=('_actual', '_pred'))
    hits = merged[merged['Crop_actual'] == merged['Crop_pred']]
    top1 = (hits['Rank'] == 1).sum() / len(actual_top)
    return top1

exp_top1 = evaluate_exp_ranking(xgb_exp, val_exp)
print(f"Proxy Exp Val Top-1: {exp_top1:.3f}")

# 7. Save Models and Metadata
out_dir = 'C:/Users/prana/OneDrive/Desktop/Projects/KISANcare/kisan-care/models/crop_recommendation'
joblib.dump(xgb_model, f'{out_dir}/crop_recommendation_mvp_v1.pkl')
# Save category levels for preprocessing
cat_levels = {col: list(df[col].cat.categories) for col in cat_cols}
joblib.dump(cat_levels, f'{out_dir}/preprocessing_mvp.pkl')

metadata = {
    'model_version': 'crop-recommendation-mvp-v1',
    'algorithm': 'XGBoostRegressor (Hist)',
    'training_years': '2005-2012',
    'test_years': '2014-2015',
    'features': cat_cols,
    'target': 'Area_Frequency',
    'metrics': {
        'val_top1': val_t1,
        'val_top3': val_t3,
        'test_top1': test_t1,
        'test_top3': test_t3,
        'historical_baseline_val_top1': val_t1_hist,
        'historical_baseline_test_top1': test_t1_hist,
        'proxy_exp_val_top1': exp_top1
    }
}
with open(f'{out_dir}/metadata_mvp.json', 'w') as f:
    json.dump(metadata, f, indent=4)
print("Artifacts saved successfully.")
