import os
import json
import time
import numpy as np
import pandas as pd
from datetime import datetime

from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report, confusion_matrix
import joblib
import xgboost as xgb

def top_k_accuracy(y_true, probas, k=3):
    top_k_preds = np.argsort(probas, axis=1)[:, -k:]
    hits = [1 if y_true[i] in top_k_preds[i] else 0 for i in range(len(y_true))]
    return sum(hits) / len(hits)

def main():
    print("PHASE 3.1: DATA VALIDATION")
    data_path = "C:/Users/prana/.gemini/antigravity/brain/7285b068-cb5b-46c4-87fb-410bdec4b8a1/scratch/Crop_recommendation_cleaned.csv"
    df = pd.read_csv(data_path)
    
    print("Schema:\n", df.dtypes)
    print(f"Rows: {len(df)}, Columns: {len(df.columns)}")
    print(f"Missing Values: {df.isnull().sum().sum()}")
    print(f"Duplicates: {df.duplicated().sum()}")
    
    X = df.drop(columns=['label'])
    y = df['label']
    
    print("Crops:", y.nunique())
    
    print("\nPHASE 3.2: TRAIN/TEST SPLIT")
    # Encode target
    le = LabelEncoder()
    y_enc = le.fit_transform(y)
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(X, y_enc, test_size=0.2, random_state=42, stratify=y_enc)
    print(f"Train size: {len(X_train)}, Test size: {len(X_test)}")
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    print("\nPHASE 3.3 & 3.4 & 3.5: TRAINING AND EVALUATION")
    
    models = {
        "Random_Forest": RandomForestClassifier(random_state=42, n_jobs=-1),
        "Decision_Tree": DecisionTreeClassifier(random_state=42),
        "Logistic_Regression": LogisticRegression(random_state=42, max_iter=1000, n_jobs=-1),
        "KNN": KNeighborsClassifier(n_jobs=-1),
        "XGBoost": xgb.XGBClassifier(random_state=42, n_jobs=-1, eval_metric='mlogloss')
    }
    
    results = {}
    best_model_name = None
    best_macro_f1 = -1
    best_model_obj = None
    
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    
    for name, model in models.items():
        print(f"Evaluating {name}...")
        t0 = time.time()
        
        # Cross-validation
        cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=cv, scoring='f1_macro', n_jobs=-1)
        
        # Train on full train
        model.fit(X_train_scaled, y_train)
        
        # Predict on test
        preds = model.predict(X_test_scaled)
        probas = model.predict_proba(X_test_scaled)
        
        # Metrics
        acc = accuracy_score(y_test, preds)
        macro_f1 = f1_score(y_test, preds, average='macro')
        weighted_f1 = f1_score(y_test, preds, average='weighted')
        top3 = top_k_accuracy(y_test, probas, k=3)
        top5 = top_k_accuracy(y_test, probas, k=5)
        
        results[name] = {
            "accuracy": acc,
            "macro_f1": macro_f1,
            "weighted_f1": weighted_f1,
            "top3_accuracy": top3,
            "top5_accuracy": top5,
            "cv_macro_f1_mean": cv_scores.mean(),
            "cv_macro_f1_std": cv_scores.std(),
            "train_time_sec": time.time() - t0
        }
        
        if macro_f1 > best_macro_f1:
            best_macro_f1 = macro_f1
            best_model_name = name
            best_model_obj = model
            
    print("\nModel Results:")
    print(json.dumps(results, indent=2))
    
    print(f"\nPHASE 3.7: BEST MODEL -> {best_model_name}")
    
    print("\nPHASE 3.6: FEATURE ANALYSIS")
    importances = {}
    if hasattr(best_model_obj, 'feature_importances_'):
        imps = best_model_obj.feature_importances_
        importances = {X.columns[i]: float(imps[i]) for i in range(len(X.columns))}
    print("Feature Importances:", importances)
    
    print("\nPHASE 3.9: SAVING ARTIFACTS")
    out_dir = "models/model1"
    os.makedirs(out_dir, exist_ok=True)
    
    # Save objects
    joblib.dump(best_model_obj, os.path.join(out_dir, "crop_recommendation_model.pkl"))
    joblib.dump(scaler, os.path.join(out_dir, "preprocessor.pkl"))
    joblib.dump(le, os.path.join(out_dir, "label_encoder.pkl"))
    
    # Per-crop metrics
    preds = best_model_obj.predict(X_test_scaled)
    report = classification_report(y_test, preds, target_names=le.classes_, output_dict=True)
    
    metadata = {
        "model_name": f"{best_model_name}_Baseline",
        "model_version": "1.0.0",
        "training_dataset": "Kaggle_Crop_Recommendation_Fallback",
        "feature_names": list(X.columns),
        "target": "crop",
        "number_of_crops": len(le.classes_),
        "training_samples": len(X_train),
        "test_samples": len(X_test),
        "random_seed": 42,
        "metrics": {
            "accuracy": results[best_model_name]["accuracy"],
            "macro_f1": results[best_model_name]["macro_f1"],
            "weighted_f1": results[best_model_name]["weighted_f1"],
            "top3_accuracy": results[best_model_name]["top3_accuracy"],
            "top5_accuracy": results[best_model_name]["top5_accuracy"]
        },
        "cv_metrics": {
            "mean_macro_f1": results[best_model_name]["cv_macro_f1_mean"],
            "std_macro_f1": results[best_model_name]["cv_macro_f1_std"]
        },
        "feature_importances": importances,
        "training_date": datetime.now().isoformat(),
        "known_limitations": [
            "Trained on synthetic/interpolated baseline Kaggle dataset, not real field data.",
            "Lacks geographic context (district/state).",
            "Perfectly balanced classes do not reflect real-world prior probabilities."
        ],
        "per_crop_metrics": report
    }
    
    with open(os.path.join(out_dir, "model_metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)
        
    print("Artifacts saved successfully.")

if __name__ == "__main__":
    main()
