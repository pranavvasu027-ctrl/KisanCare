from api_service import KisanCareForecaster
import json

api = KisanCareForecaster()

tests = [
    # Normal cases
    {"crop": "onion", "market": "Pune", "date": "2025-05-15"},
    {"crop": "tomato", "market": "Pune", "date": "2025-05-15"},
    {"crop": "cabbage", "market": "Pune", "date": "2025-05-15"},
    
    # Edge cases
    {"crop": "unknown_crop", "market": "Pune", "date": "2025-05-15"},
    {"crop": "onion", "market": "unknown_market", "date": "2025-05-15"},
    {"crop": "onion", "market": "Pune", "date": "1999-01-01"}, # very old date
    {"crop": "onion", "market": "Pune", "date": "2024-07-16"}, # very early date, insufficient data
]

for i, req in enumerate(tests):
    print(f"\n--- Test {i+1} ---")
    print(f"Request: {req}")
    try:
        res = api.predict(req)
        print("Response:", json.dumps(res, indent=2))
    except Exception as e:
        print("ERROR:", str(e))
