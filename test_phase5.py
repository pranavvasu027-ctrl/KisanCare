import json
from api_service import KisanCareForecaster
import pandas as pd
from datetime import datetime, timedelta

api = KisanCareForecaster()

def run_test(name, req):
    print(f"\n--- {name} ---")
    try:
        res = api.predict(req)
        print(json.dumps(res, indent=2))
        return res
    except Exception as e:
        print(f"EXCEPTION: {e}")
        return None

# Find correct max dates dynamically to test freshness properly
df = pd.read_csv('data/mandi_prices.csv')
df['Arrival_Date'] = pd.to_datetime(df['Arrival_Date'], dayfirst=True)
onion_max = df[(df['Commodity'] == 'Onion') & (df['Market'] == 'Pune(Pimpri)')]['Arrival_Date'].max()
tomato_max = df[(df['Commodity'] == 'Tomato') & (df['Market'] == 'Pune(Pimpri)')]['Arrival_Date'].max()
cabbage_max = df[(df['Commodity'] == 'Cabbage') & (df['Market'] == 'Pune(Manjri)')]['Arrival_Date'].max()
potato_max = df[(df['Commodity'] == 'Potato') & (df['Market'] == 'Pune(Manjri) APMC')]['Arrival_Date'].max()
cauliflower_max = df[(df['Commodity'] == 'Cauliflower') & (df['Market'] == 'Pune(Manjri) APMC')]['Arrival_Date'].max()

def d2s(date_obj): return date_obj.strftime("%Y-%m-%d")

# 1-10: Basic Tests
run_test("1. Onion 7D", {"crop": "onion", "market": "Pune", "horizon_days": 7, "date": d2s(onion_max)})
run_test("2. Onion 14D", {"crop": "onion", "market": "Pune", "horizon_days": 14, "date": d2s(onion_max)})
run_test("3. Tomato 7D", {"crop": "tomato", "market": "Pune", "horizon_days": 7, "date": d2s(tomato_max)})
run_test("4. Tomato 14D", {"crop": "tomato", "market": "Pune", "horizon_days": 14, "date": d2s(tomato_max)})
run_test("5. Cabbage 7D", {"crop": "cabbage", "market": "Pune", "horizon_days": 7, "date": d2s(cabbage_max)})
run_test("6. Cabbage 14D", {"crop": "cabbage", "market": "Pune", "horizon_days": 14, "date": d2s(cabbage_max)})
run_test("7. Potato 7D", {"crop": "potato", "market": "Pune", "horizon_days": 7, "date": d2s(potato_max)})
run_test("8. Potato 14D", {"crop": "potato", "market": "Pune", "horizon_days": 14, "date": d2s(potato_max)})
run_test("9. Cauliflower 7D", {"crop": "cauliflower", "market": "Pune", "horizon_days": 7, "date": d2s(cauliflower_max)})
run_test("10. Cauliflower 14D", {"crop": "cauliflower", "market": "Pune", "horizon_days": 14, "date": d2s(cauliflower_max)})

# 11-13 Validation tests
run_test("11. Unknown crop", {"crop": "mango", "market": "Pune", "horizon_days": 7, "date": d2s(onion_max)})
run_test("12. Unsupported market", {"crop": "onion", "market": "Mumbai", "horizon_days": 7, "date": d2s(onion_max)})
run_test("13. Unsupported horizon", {"crop": "onion", "market": "Pune", "horizon_days": 10, "date": d2s(onion_max)})

# 14. Missing Price (Gap filling inherently handled via market_price_features ffill limit 3)
run_test("14. Missing price (imputed gap)", {"crop": "onion", "market": "Pune", "horizon_days": 7, "date": d2s(onion_max - timedelta(days=1))})

# 17. Fresh price (gap <= 4) -> 3 days old
run_test("17. Fresh price", {"crop": "onion", "market": "Pune", "horizon_days": 7, "date": d2s(onion_max + timedelta(days=3))})

# 18. Exactly 4-day-old price
run_test("18. Exactly 4-day-old", {"crop": "onion", "market": "Pune", "horizon_days": 7, "date": d2s(onion_max + timedelta(days=4))})

# 19. > 4-day-old price
run_test("19. > 4-day-old", {"crop": "onion", "market": "Pune", "horizon_days": 7, "date": d2s(onion_max + timedelta(days=5))})

# 20. Insufficient history
run_test("20. Insufficient history", {"crop": "onion", "market": "Pune", "horizon_days": 7, "date": "2024-07-07"})

# 24. Prediction reproducibility
print("\n--- 24. Prediction Reproducibility ---")
res1 = api.predict({"crop": "potato", "market": "Pune", "horizon_days": 7, "date": d2s(potato_max)})
res2 = api.predict({"crop": "potato", "market": "Pune", "horizon_days": 7, "date": d2s(potato_max)})
if 'forecast' in res1 and 'forecast' in res2:
    if res1['forecast']['expected_price'] == res2['forecast']['expected_price']:
        print("PASS: Reproducible predictions")

print("\nTests Complete!")
