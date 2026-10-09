import json
import pandas as pd
import numpy as np

def run_monitoring_report(logs_path="prediction_logs.jsonl", actuals_path="data/mandi_prices.csv"):
    try:
        logs = []
        with open(logs_path, 'r') as f:
            for line in f:
                logs.append(json.loads(line))
        
        if not logs:
            print("No prediction logs found.")
            return
            
        logs_df = pd.DataFrame(logs)
        
        # Load actuals
        actuals_df = pd.read_csv(actuals_path)
        actuals_df['Arrival_Date'] = pd.to_datetime(actuals_df['Arrival_Date'], dayfirst=True)
        
        print("--- MODEL MONITORING REPORT ---")
        
        # 1. Abnormal forecasts increasing?
        abnormal_count = logs_df['abnormal'].sum()
        total_preds = len(logs_df)
        print(f"Abnormal Forecasts: {abnormal_count} out of {total_preds} ({(abnormal_count/total_preds)*100:.1f}%)")
        
        # We would then join with actuals_df to calculate error metrics.
        # This is a structural mock-up that establishes the required capabilities:
        # 
        # actuals_df['key'] = actuals_df['Commodity'].str.lower() + "_" + actuals_df['Arrival_Date'].astype(str)
        # logs_df['target_date_7d'] = pd.to_datetime(logs_df['prediction_date']) + pd.Timedelta(days=7)
        # logs_df['key_7d'] = logs_df['crop'].str.lower() + "_" + logs_df['target_date_7d'].astype(str)
        # 
        # merged = pd.merge(logs_df, actuals_df, left_on='key_7d', right_on='key', how='inner')
        # if not merged.empty:
        #    merged['abs_error_7d'] = abs(merged['exp_7d'] - merged['Modal_Price'])
        #    merged['mape_7d'] = (merged['abs_error_7d'] / merged['Modal_Price']) * 100
        #    print(f"Overall 7D MAPE: {merged['mape_7d'].mean():.2f}%")
        
        print("\nStructure for answering:")
        print("- Is the model getting worse? (Track MAPE over time)")
        print("- Which crop is deteriorating? (Group by crop)")
        print("- Which market is deteriorating? (Group by market)")
        print("- Is 7D/14D still reliable? (Compare error distributions to Phase 1 baselines)")
        
    except Exception as e:
        print(f"Monitoring error: {e}")

if __name__ == "__main__":
    run_monitoring_report()
