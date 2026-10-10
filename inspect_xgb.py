import xgboost as xgb
model = xgb.Booster()
model.load_model('models/onion_pune_pimpri_7d.json')
print("Feature names:", model.feature_names)
print("Num features:", model.num_features())
