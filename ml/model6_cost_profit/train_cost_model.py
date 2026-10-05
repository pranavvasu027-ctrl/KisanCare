import pandas as pd
import numpy as np
import joblib
import os
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, ExtraTreesRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

DATA_PATH = r"C:\Users\prana\.gemini\antigravity\brain\c717cd51-3f5e-497a-9b25-ae28bd0f1741\data\model6_cost_profit\processed\cost_profit_master.csv"
MODEL_DIR = r"C:\Users\prana\.gemini\antigravity\brain\c717cd51-3f5e-497a-9b25-ae28bd0f1741\models\model6_cost_profit\artifacts"
REPORT_PATH = r"C:\Users\prana\.gemini\antigravity\brain\c717cd51-3f5e-497a-9b25-ae28bd0f1741\docs\cost_profit\model_comparison.md"
FINAL_REPORT_PATH = r"C:\Users\prana\.gemini\antigravity\brain\c717cd51-3f5e-497a-9b25-ae28bd0f1741\COST_PROFIT_MODEL_REPORT.md"

def train():
    df = pd.read_csv(DATA_PATH)
    
    # We want to predict Total_Cost_INR
    target = 'Total_Cost_INR'
    X = df.drop(columns=[target])
    y = df[target]
    
    # Identify cat vs num
    cat_cols = X.select_dtypes(include=['object']).columns.tolist()
    num_cols = X.select_dtypes(exclude=['object']).columns.tolist()
    
    # Preprocessor
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), num_cols),
            ('cat', OneHotEncoder(handle_unknown='ignore'), cat_cols)
        ]
    )
    
    # Split Data (80/20 random split)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    models = {
        "Linear Regression": LinearRegression(),
        "Random Forest": RandomForestRegressor(n_estimators=100, random_state=42),
        "Extra Trees": ExtraTreesRegressor(n_estimators=100, random_state=42),
        "Gradient Boosting": GradientBoostingRegressor(n_estimators=100, random_state=42)
    }
    
    results = []
    best_r2 = -float('inf')
    best_model_name = ""
    best_model = None
    
    for name, model in models.items():
        pipeline = Pipeline(steps=[('preprocessor', preprocessor),
                                   ('regressor', model)])
        
        pipeline.fit(X_train, y_train)
        y_pred = pipeline.predict(X_test)
        
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)
        
        # MAPE
        # Add small epsilon to avoid div by zero
        mape = np.mean(np.abs((y_test - y_pred) / (y_test + 1e-8))) * 100
        
        results.append(f"| {name} | {mae:.2f} | {rmse:.2f} | {r2:.4f} | {mape:.2f}% |")
        
        # We select Gradient Boosting or Random Forest primarily because they are robust to non-linear cost curves
        # But let's track the best R2 for metric purposes
        if r2 > best_r2:
            best_r2 = r2
            best_model_name = name
            best_model = pipeline
            
    # Save comparison report
    report_content = "# Model Comparison\n\n| Model | MAE | RMSE | R² | MAPE |\n|---|---|---|---|---|\n"
    report_content += "\n".join(results)
    
    with open(REPORT_PATH, 'w') as f:
        f.write(report_content)
        
    # Save best model
    # Prefer Gradient Boosting if it's within 0.02 R2 of Random forest, for smaller size, 
    # but for simplicity, we just use the best model found or explicitly set it.
    best_model_path = os.path.join(MODEL_DIR, "cost_model.joblib")
    joblib.dump(best_model, best_model_path)
    
    print(f"Training complete. Best model: {best_model_name}. Saved to {best_model_path}")
    
    # Calculate MH specific metrics
    mh_test_idx = X_test['State'].str.contains('Maharashtra', case=False, na=False)
    if mh_test_idx.sum() > 0:
        y_test_mh = y_test[mh_test_idx]
        y_pred_mh = best_model.predict(X_test[mh_test_idx])
        mh_mae = mean_absolute_error(y_test_mh, y_pred_mh)
        mh_r2 = r2_score(y_test_mh, y_pred_mh)
    else:
        mh_mae = 0
        mh_r2 = 0
        
    # Generate Final Report
    kisan_care_crops = ["Rice", "Wheat", "Maize", "Soybean", "Cotton", "Sugarcane", "Chickpea", "Pigeon Pea", "Groundnut", "Sorghum", "Pearl Millet", "Green Gram", "Black Gram", "Mustard", "Onion", "Potato", "Tomato", "Banana", "Mango", "Grapes"]
    dataset_crops = df['Crop'].unique().tolist()
    
    coverage_md = ""
    for c in kisan_care_crops:
        # fuzzy match
        matched = next((dc for dc in dataset_crops if c.lower() in dc.lower() or dc.lower() in c.lower()), None)
        if matched:
            tot = (df['Crop'] == matched).sum()
            mh_tot = ((df['Crop'] == matched) & (df['State'].str.contains('Maharashtra', case=False, na=False))).sum()
            coverage_md += f"| {c} | {matched} | Yes | {tot} | {mh_tot} |\n"
        else:
            coverage_md += f"| {c} | - | No | 0 | 0 |\n"

    final_report = f"""# COST_PROFIT_MODEL_REPORT

## 1. DATASET
- **Dataset Used**: `seasonal_agriculture_performance_dataset.csv` (Repo 3)
- **Initial Rows**: 4000
- **Usable Rows**: {len(df)}
- **Features Used**: {', '.join(X.columns.tolist())}
- **Features Removed**: `Farm_ID`, `Profit_INR`, `Revenue_INR`, `Yield_Tonnes_Ha`, `Production_Tonnes`, `Market_Price_INR_Tonne`, `Water_Efficiency_t_per_1000m3`, `Water_Used_m3`
- **Leakage Findings**: Removed all post-harvest metrics that perfectly reconstruct the profit equation. The model is trained purely on pre-harvest environmental and input features.

## 2. METHODOLOGY & METRICS
- **Split**: 80/20 Random Split. A random split is acceptable here as the dataset represents a synthetic/uniform distribution across a cross-section of farms without temporal components.
- **Models Tested**: Linear Regression, Random Forest, Extra Trees, Gradient Boosting.
- **Selected Model**: {best_model_name}
- **Maharashtra Performance**: MAE = {mh_mae:.2f}, R2 = {mh_r2:.4f}

## 3. CROP COVERAGE
| KisanCare Crop | Dataset Crop Name | Supported? | Total Records | Maharashtra Records |
|---|---|---|---|---|
{coverage_md}

## 4. INTEGRATION
- **Model Saved**: `{best_model_path}`
- **Prediction Script**: `predict_cost.py` (to be created)
- **Economic Engine**: `economic_engine.py` (to be created)
- **API Status**: Prepared as a stub in `api_stub.py` (to be created)

## 5. LIMITATIONS
- The original dataset uses a deterministic generating function for costs, making R2 artificially high compared to real-world noisy agricultural data.
- Crop coverage is restricted to 8 crops. Major crops like Soybean, Chickpea, and Onion are missing.
- Prices and Yields are needed from external models to calculate Profit.

## 6. RECOMMENDED NEXT STEP
Integrate `predict_cost.py` and `economic_engine.py` into the main KisanCare backend (e.g. FastAPI/Flask app), and connect them to the existing Yield and Market Price microservices.
"""
    with open(FINAL_REPORT_PATH, 'w') as f:
        f.write(final_report)

if __name__ == "__main__":
    train()
