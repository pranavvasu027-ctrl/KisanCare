"""
Model Comparison and Validation Suite: Random Forest vs LightGBM
Evaluated on Western Maharashtra Soil-Crop Dataset (4,513 records)
and 12 Independent Field Soil Test Records across Maharashtra.
"""

from __future__ import annotations
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_recall_fscore_support
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import LabelEncoder
import lightgbm as lgb

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("evaluate_models")


def top_k_accuracy(y_true_indices: np.ndarray, y_proba: np.ndarray, k: int = 3) -> float:
    """Calculates top-k accuracy from predicted probability distribution."""
    if y_proba.ndim != 2:
        raise ValueError(f"y_proba must be 2D, got shape {y_proba.shape}")
    k = min(k, y_proba.shape[1])
    top_k_preds = np.argsort(y_proba, axis=1)[:, -k:]
    correct = [y in top_k_preds[i] for i, y in enumerate(y_true_indices)]
    return float(np.mean(correct))


def run_stratified_cv(
    X: np.ndarray,
    y: np.ndarray,
    feature_names: List[str],
    class_names: List[str],
    n_splits: int = 5,
    random_state: int = 42
) -> Dict[str, Any]:
    """Runs 5-fold Stratified Cross-Validation for RF and LightGBM."""
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    
    rf_top1, rf_top3, rf_macro_f1 = [], [], []
    lgb_top1, lgb_top3, lgb_macro_f1 = [], [], []
    
    n_classes = len(class_names)
    rf_oof_proba = np.zeros((len(X), n_classes))
    lgb_oof_proba = np.zeros((len(X), n_classes))
    
    for fold, (train_idx, val_idx) in enumerate(skf.split(X, y)):
        X_train, X_val = X[train_idx], X[val_idx]
        y_train, y_val = y[train_idx], y[val_idx]
        
        # 1. Random Forest
        rf = RandomForestClassifier(
            n_estimators=150,
            max_depth=16,
            min_samples_leaf=2,
            random_state=random_state + fold,
            n_jobs=1
        )
        rf.fit(X_train, y_train)
        rf_proba = rf.predict_proba(X_val)
        rf_oof_proba[val_idx] = rf_proba
        
        rf_pred = np.argmax(rf_proba, axis=1)
        rf_top1.append(accuracy_score(y_val, rf_pred))
        rf_top3.append(top_k_accuracy(y_val, rf_proba, k=3))
        rf_macro_f1.append(f1_score(y_val, rf_pred, average="macro", zero_division=0))
        
        # 2. LightGBM
        lgbm = lgb.LGBMClassifier(
            n_estimators=150,
            max_depth=10,
            learning_rate=0.08,
            num_leaves=31,
            random_state=random_state + fold,
            verbosity=-1,
            n_jobs=1
        )
        lgbm.fit(X_train, y_train)
        lgb_proba = lgbm.predict_proba(X_val)
        lgb_oof_proba[val_idx] = lgb_proba
        
        lgb_pred = np.argmax(lgb_proba, axis=1)
        lgb_top1.append(accuracy_score(y_val, lgb_pred))
        lgb_top3.append(top_k_accuracy(y_val, lgb_proba, k=3))
        lgb_macro_f1.append(f1_score(y_val, lgb_pred, average="macro", zero_division=0))

    # Overall OOF metrics
    rf_oof_pred = np.argmax(rf_oof_proba, axis=1)
    lgb_oof_pred = np.argmax(lgb_oof_proba, axis=1)
    
    rf_p, rf_r, rf_f, rf_s = precision_recall_fscore_support(y, rf_oof_pred, zero_division=0)
    lgb_p, lgb_r, lgb_f, lgb_s = precision_recall_fscore_support(y, lgb_oof_pred, zero_division=0)
    
    per_crop = {}
    for i, name in enumerate(class_names):
        per_crop[name] = {
            "samples": int(rf_s[i]),
            "rf_precision": round(float(rf_p[i]), 4),
            "rf_recall": round(float(rf_r[i]), 4),
            "rf_f1": round(float(rf_f[i]), 4),
            "lgb_precision": round(float(lgb_p[i]), 4),
            "lgb_recall": round(float(lgb_r[i]), 4),
            "lgb_f1": round(float(lgb_f[i]), 4),
        }
        
    return {
        "random_forest": {
            "mean_top1": round(float(np.mean(rf_top1)), 4),
            "std_top1": round(float(np.std(rf_top1)), 4),
            "mean_top3": round(float(np.mean(rf_top3)), 4),
            "std_top3": round(float(np.std(rf_top3)), 4),
            "mean_macro_f1": round(float(np.mean(rf_macro_f1)), 4),
            "std_macro_f1": round(float(np.std(rf_macro_f1)), 4),
            "oof_top1": round(float(accuracy_score(y, rf_oof_pred)), 4),
            "oof_top3": round(float(top_k_accuracy(y, rf_oof_proba, k=3)), 4),
            "oof_macro_f1": round(float(f1_score(y, rf_oof_pred, average="macro", zero_division=0)), 4),
        },
        "lightgbm": {
            "mean_top1": round(float(np.mean(lgb_top1)), 4),
            "std_top1": round(float(np.std(lgb_top1)), 4),
            "mean_top3": round(float(np.mean(lgb_top3)), 4),
            "std_top3": round(float(np.std(lgb_top3)), 4),
            "mean_macro_f1": round(float(np.mean(lgb_macro_f1)), 4),
            "std_macro_f1": round(float(np.std(lgb_macro_f1)), 4),
            "oof_top1": round(float(accuracy_score(y, lgb_oof_pred)), 4),
            "oof_top3": round(float(top_k_accuracy(y, lgb_oof_proba, k=3)), 4),
            "oof_macro_f1": round(float(f1_score(y, lgb_oof_pred, average="macro", zero_division=0)), 4),
        },
        "per_crop": per_crop
    }


def run_held_out_district_cv(
    df: pd.DataFrame,
    features: List[str],
    label_encoder: LabelEncoder,
    random_state: int = 42
) -> Dict[str, Any]:
    """Leave-One-District-Out cross-validation across the 5 districts in the dataset."""
    districts = sorted(df["District_Name"].unique())
    results = {}
    total_classes = len(label_encoder.classes_)
    
    for held_out in districts:
        train_df = df[df["District_Name"] != held_out]
        val_df = df[df["District_Name"] == held_out]
        
        X_train = train_df[features].values
        y_train = label_encoder.transform(train_df["Crop"])
        
        X_val = val_df[features].values
        y_val = label_encoder.transform(val_df["Crop"])
        
        # RF
        rf = RandomForestClassifier(n_estimators=150, max_depth=16, random_state=random_state, n_jobs=1)
        rf.fit(X_train, y_train)
        
        # Align probabilities to total_classes
        rf_raw_p = rf.predict_proba(X_val)
        rf_proba = np.zeros((len(X_val), total_classes))
        for local_idx, global_cls in enumerate(rf.classes_):
            rf_proba[:, global_cls] = rf_raw_p[:, local_idx]
            
        rf_pred = np.argmax(rf_proba, axis=1)
        
        # LightGBM
        lgbm = lgb.LGBMClassifier(n_estimators=150, max_depth=10, random_state=random_state, verbosity=-1, n_jobs=1)
        lgbm.fit(X_train, y_train)
        
        lgb_raw_p = lgbm.predict_proba(X_val)
        lgb_proba = np.zeros((len(X_val), total_classes))
        for local_idx, global_cls in enumerate(lgbm.classes_):
            lgb_proba[:, global_cls] = lgb_raw_p[:, local_idx]
            
        lgb_pred = np.argmax(lgb_proba, axis=1)
        
        results[held_out] = {
            "val_samples": len(val_df),
            "rf": {
                "top1": round(float(accuracy_score(y_val, rf_pred)), 4),
                "top3": round(float(top_k_accuracy(y_val, rf_proba, k=3)), 4),
                "macro_f1": round(float(f1_score(y_val, rf_pred, average="macro", zero_division=0)), 4),
            },
            "lightgbm": {
                "top1": round(float(accuracy_score(y_val, lgb_pred)), 4),
                "top3": round(float(top_k_accuracy(y_val, lgb_proba, k=3)), 4),
                "macro_f1": round(float(f1_score(y_val, lgb_pred, average="macro", zero_division=0)), 4),
            }
        }
    return results


def run_noise_robustness_test(
    model: Any,
    X_val: np.ndarray,
    y_val: np.ndarray,
    noise_levels: List[float] = [0.05, 0.10, 0.20]
) -> Dict[str, Any]:
    """Tests model robustness to OCR/sensor measurement perturbation."""
    np.random.seed(42)
    base_proba = model.predict_proba(X_val)
    base_pred = np.argmax(base_proba, axis=1)
    base_acc = float(accuracy_score(y_val, base_pred))
    base_top3 = float(top_k_accuracy(y_val, base_proba, k=3))
    
    robustness = {"clean": {"top1": round(base_acc, 4), "top3": round(base_top3, 4)}}
    
    for noise in noise_levels:
        noise_matrix = np.random.normal(loc=1.0, scale=noise, size=X_val.shape)
        X_perturbed = np.clip(X_val * noise_matrix, a_min=0.0, a_max=None)
        p_proba = model.predict_proba(X_perturbed)
        p_pred = np.argmax(p_proba, axis=1)
        
        # Stability: fraction of predictions identical to clean predictions
        stability = float(np.mean(p_pred == base_pred))
        p_acc = float(accuracy_score(y_val, p_pred))
        p_top3 = float(top_k_accuracy(y_val, p_proba, k=3))
        
        robustness[f"noise_{int(noise*100)}pct"] = {
            "top1": round(p_acc, 4),
            "top3": round(p_top3, 4),
            "stability_vs_clean": round(stability, 4)
        }
    return robustness


def main():
    repo_root = Path(__file__).resolve().parent.parent.parent
    data_path = repo_root / "data" / "soil_validation" / "Western_Maharashtra_soil_crop_data.csv"
    real_records_path = repo_root / "data" / "soil_validation" / "real_soil_test_records_maharashtra.csv"
    
    if not data_path.exists():
        logger.error("Dataset not found at %s", data_path)
        sys.exit(1)
        
    df = pd.read_csv(data_path)
    logger.info("Loaded Western Maharashtra dataset: %d rows, %d cols", len(df), len(df.columns))
    
    features = ["Nitrogen", "Phosphorus", "Potassium", "pH", "Rainfall", "Temperature"]
    target_col = "Crop"
    
    le = LabelEncoder()
    df["Crop_Code"] = le.fit_transform(df[target_col])
    class_names = list(le.classes_)
    logger.info("Target classes (%d): %s", len(class_names), class_names)
    
    X = df[features].values
    y = df["Crop_Code"].values
    
    # 1. 5-Fold Stratified Cross-Validation
    logger.info("Running 5-fold Stratified Cross-Validation...")
    stratified_results = run_stratified_cv(X, y, features, class_names)
    
    # 2. Held-Out District Evaluation
    logger.info("Running Leave-One-District-Out CV across 5 Western Maharashtra districts...")
    district_results = run_held_out_district_cv(df, features, le)
    
    # 3. Train final models on entire Western Maharashtra dataset for Noise and Field Evaluation
    rf_final = RandomForestClassifier(n_estimators=150, max_depth=16, random_state=42, n_jobs=1)
    rf_final.fit(X, y)
    
    lgb_final = lgb.LGBMClassifier(n_estimators=150, max_depth=10, random_state=42, verbosity=-1, n_jobs=1)
    lgb_final.fit(X, y)
    
    # 4. Noise Robustness Evaluation
    logger.info("Running Noise Robustness Tests...")
    rf_robustness = run_noise_robustness_test(rf_final, X, y)
    lgb_robustness = run_noise_robustness_test(lgb_final, X, y)
    
    # 5. Independent Validation on 12 Real Field Soil Records
    real_field_results = []
    if real_records_path.exists():
        real_df = pd.read_csv(real_records_path)
        logger.info("Evaluating on %d real field test records...", len(real_df))
        
        for _, row in real_df.iterrows():
            rec_id = row["test_id"]
            dist = row["district"]
            season = row["season"]
            true_crop = row["ground_truth_crop"]
            
            x_test = np.array([[row["N"], row["P"], row["K"], row["ph"], row["rainfall"], row["temperature"]]])
            
            rf_p = rf_final.predict_proba(x_test)[0]
            lgb_p = lgb_final.predict_proba(x_test)[0]
            
            rf_top3_idx = np.argsort(rf_p)[-3:][::-1]
            lgb_top3_idx = np.argsort(lgb_p)[-3:][::-1]
            
            rf_top3 = [(class_names[idx], round(float(rf_p[idx]), 3)) for idx in rf_top3_idx]
            lgb_top3 = [(class_names[idx], round(float(lgb_p[idx]), 3)) for idx in lgb_top3_idx]
            
            real_field_results.append({
                "test_id": rec_id,
                "district": dist,
                "season": season,
                "ground_truth": true_crop,
                "rf_top3": rf_top3,
                "lgb_top3": lgb_top3,
                "rf_hit": any(true_crop.lower() in c.lower() or c.lower() in true_crop.lower() for c, _ in rf_top3),
                "lgb_hit": any(true_crop.lower() in c.lower() or c.lower() in true_crop.lower() for c, _ in lgb_top3),
            })
            
    summary = {
        "dataset": {
            "name": "Western Maharashtra Soil-Crop Research Dataset (MittiSeva / Sanchita Gholap)",
            "license": "CC0 1.0 Universal (Public Domain)",
            "total_samples": len(df),
            "features": features,
            "crop_classes_count": len(class_names),
            "crops": class_names,
            "districts": list(df["District_Name"].value_counts().to_dict().keys()),
        },
        "stratified_cv_5fold": stratified_results,
        "held_out_district_cv": district_results,
        "noise_robustness": {
            "random_forest": rf_robustness,
            "lightgbm": lgb_robustness
        },
        "real_field_validation_12_records": {
            "total_records": len(real_field_results),
            "rf_top3_hit_rate": round(float(np.mean([r["rf_hit"] for r in real_field_results])), 4) if real_field_results else None,
            "lgb_top3_hit_rate": round(float(np.mean([r["lgb_hit"] for r in real_field_results])), 4) if real_field_results else None,
            "records": real_field_results
        }
    }
    
    out_json = repo_root / "data" / "soil_validation" / "model_comparison_results.json"
    with open(out_json, "w") as f:
        json.dump(summary, f, indent=2)
    logger.info("Saved evaluation summary to %s", out_json)
    
    print("\n================== STRATIFIED 5-FOLD CV COMPARISON ==================")
    print(f"Metric              | Random Forest         | LightGBM")
    print(f"--------------------|-----------------------|----------------------")
    print(f"Top-1 Accuracy      | {stratified_results['random_forest']['mean_top1']*100:.2f}% ± {stratified_results['random_forest']['std_top1']*100:.2f}% | {stratified_results['lightgbm']['mean_top1']*100:.2f}% ± {stratified_results['lightgbm']['std_top1']*100:.2f}%")
    print(f"Top-3 Accuracy      | {stratified_results['random_forest']['mean_top3']*100:.2f}% ± {stratified_results['random_forest']['std_top3']*100:.2f}% | {stratified_results['lightgbm']['mean_top3']*100:.2f}% ± {stratified_results['lightgbm']['std_top3']*100:.2f}%")
    print(f"Macro F1 Score      | {stratified_results['random_forest']['mean_macro_f1']:.4f}             | {stratified_results['lightgbm']['mean_macro_f1']:.4f}")
    print(f"OOF Top-1 Accuracy  | {stratified_results['random_forest']['oof_top1']*100:.2f}%            | {stratified_results['lightgbm']['oof_top1']*100:.2f}%")
    print(f"OOF Top-3 Accuracy  | {stratified_results['random_forest']['oof_top3']*100:.2f}%            | {stratified_results['lightgbm']['oof_top3']*100:.2f}%")
    print(f"OOF Macro F1        | {stratified_results['random_forest']['oof_macro_f1']:.4f}             | {stratified_results['lightgbm']['oof_macro_f1']:.4f}")
    
    print("\n================== KEY CROPS (F1 SCORE) ==================")
    for crop in ["Soybean", "Tur", "Cotton", "Sugarcane", "Wheat", "Jowar", "Rice"]:
        if crop in stratified_results["per_crop"]:
            data = stratified_results["per_crop"][crop]
            print(f"{crop:12s} (N={data['samples']:3d}) | RF F1: {data['rf_f1']:.4f} (P={data['rf_precision']:.2f}, R={data['rf_recall']:.2f}) | LGB F1: {data['lgb_f1']:.4f} (P={data['lgb_precision']:.2f}, R={data['lgb_recall']:.2f})")

    print("\n================== HELD-OUT DISTRICT ACCURACY ==================")
    for dist, d_res in district_results.items():
        print(f"{dist:12s} (N={d_res['val_samples']:4d}) | RF Top-1: {d_res['rf']['top1']*100:.1f}%, Top-3: {d_res['rf']['top3']*100:.1f}% | LGB Top-1: {d_res['lightgbm']['top1']*100:.1f}%, Top-3: {d_res['lightgbm']['top3']*100:.1f}%")

    if real_field_results:
        print("\n================== 12 REAL FIELD RECORDS TOP-3 MATCH ==================")
        print(f"Random Forest Top-3 Match: {summary['real_field_validation_12_records']['rf_top3_hit_rate']*100:.1f}%")
        print(f"LightGBM      Top-3 Match: {summary['real_field_validation_12_records']['lgb_top3_hit_rate']*100:.1f}%")


if __name__ == "__main__":
    main()
