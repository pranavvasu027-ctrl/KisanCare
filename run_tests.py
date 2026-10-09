import os
import json

print("Running Training...")
os.system("python train.py")

print("\nTesting Model Loading & API...")
from api_service import KisanCareForecaster
api = KisanCareForecaster()

test_request = {
    "crop": "onion",
    "market": "Pune",
    "location": "Pune, Maharashtra",
    "date": "2025-05-15"
}

res1 = api.predict(test_request)
print("Result 1 Expected:", res1['forecast_7_day']['expected'])

# Reproducibility check - retrain and predict again
print("\nRetraining for Reproducibility Check...")
os.system("python train.py")

api2 = KisanCareForecaster()
res2 = api2.predict(test_request)
print("Result 2 Expected:", res2['forecast_7_day']['expected'])

if res1['forecast_7_day']['expected'] == res2['forecast_7_day']['expected']:
    print("REPRODUCIBILITY PASS")
else:
    print("REPRODUCIBILITY FAIL")
