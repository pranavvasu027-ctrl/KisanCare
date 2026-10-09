import json
import os
import pandas as pd
from datetime import datetime, timedelta
from api_service import KisanCareForecaster

api = KisanCareForecaster()

# Load latest date for Onion in Pune(Pimpri)
api.df['Arrival_Date'] = pd.to_datetime(api.df['Arrival_Date'], dayfirst=True)
max_date = api.df[(api.df['Commodity'] == 'Onion') & (api.df['Market'] == 'Pune(Pimpri)')]['Arrival_Date'].max()

def run_test(name, req):
    print(f"\n--- {name} ---")
    try:
        res = api.predict(req)
        print(json.dumps(res, indent=2))
    except Exception as e:
        print("ERROR:", e)

# 1. Normal prediction (latest date)
run_test("1. Normal prediction", {"crop": "onion", "market": "Pune", "date": max_date.strftime("%Y-%m-%d")})

# 4. Missing current price (should fall back to latest verified mandi price + forecast if within 4 days)
# 5. 3-day-old price
d3 = max_date + timedelta(days=3)
run_test("5. 3-day-old price", {"crop": "onion", "market": "Pune", "date": d3.strftime("%Y-%m-%d")})

# 6. 4-day-old price
d4 = max_date + timedelta(days=4)
run_test("6. 4-day-old price", {"crop": "onion", "market": "Pune", "date": d4.strftime("%Y-%m-%d")})

# 7. > 4-day-old price
d5 = max_date + timedelta(days=5)
run_test("7. > 4-day-old price", {"crop": "onion", "market": "Pune", "date": d5.strftime("%Y-%m-%d")})

# 8. Unknown crop
run_test("8. Unknown crop", {"crop": "potato", "market": "Pune", "date": max_date.strftime("%Y-%m-%d")})

# 9. Unknown market
run_test("9. Unknown market", {"crop": "onion", "market": "Mumbai", "date": max_date.strftime("%Y-%m-%d")})

# 10. Insufficient history
min_date = api.df[api.df['Commodity'] == 'Onion']['Arrival_Date'].min()
d_insuf = min_date + timedelta(days=5)
run_test("10. Insufficient history", {"crop": "onion", "market": "Pune", "date": d_insuf.strftime("%Y-%m-%d")})

# Check if prediction_logs.jsonl exists
if os.path.exists("prediction_logs.jsonl"):
    print("\n[PASS] Prediction logging works. Logs created.")
else:
    print("\n[FAIL] Prediction logging failed.")
