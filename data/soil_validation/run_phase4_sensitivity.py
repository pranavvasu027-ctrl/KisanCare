"""
Phase 4: Controlled Sensitivity & Boundary Testing for KisanCare Crop Recommendation Engine.
Tests independent variable shifts and records model behavior, step-function stability, and out-of-distribution extrapolation.
"""

import json
import urllib.request
import pandas as pd
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
api_url = "http://localhost:8000/api/v1/crop-recommendation"

baseline = {
    "N": 90.0,
    "P": 45.0,
    "K": 45.0,
    "ph": 6.5,
    "temperature": 26.0,
    "humidity": 70.0,
    "rainfall": 150.0, # Within Model 1 training distribution
    "district": "Pune",
    "season": "Kharif",
    "water_availability": "Medium",
    "top_k": 3
}

def call_api(payload):
    req = urllib.request.Request(
        api_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        try:
            err_json = json.loads(err.read().decode("utf-8"))
            return err.status, err_json
        except Exception:
            return err.status, {"error": str(err)}
    except Exception as exc:
        return 500, {"error": str(exc)}

sensitivity_results = {}

# 1. Nitrogen Sweep
n_results = []
for n_val in [10.0, 40.0, 80.0, 120.0, 180.0, 250.0]:
    p = dict(baseline, N=n_val)
    st, res = call_api(p)
    top_crop = res.get("prediction", "ERROR")
    recs = res.get("recommendations", [])
    top3 = ", ".join([f"{r['crop']}({r['final_score']:.3f})" for r in recs[:3]])
    m1_score = recs[0]["npk_score"] if recs else 0.0
    n_results.append({
        "N": n_val, "top_crop": top_crop, "top_3": top3, "m1_npk_score": m1_score,
        "combined_score": recs[0]["final_score"] if recs else 0.0
    })
sensitivity_results["nitrogen_sweep"] = n_results

# 2. Phosphorus Sweep
p_results = []
for p_val in [10.0, 30.0, 50.0, 80.0, 120.0, 140.0]:
    p = dict(baseline, P=p_val)
    st, res = call_api(p)
    top_crop = res.get("prediction", "ERROR")
    recs = res.get("recommendations", [])
    top3 = ", ".join([f"{r['crop']}({r['final_score']:.3f})" for r in recs[:3]])
    p_results.append({
        "P": p_val, "top_crop": top_crop, "top_3": top3,
        "combined_score": recs[0]["final_score"] if recs else 0.0
    })
sensitivity_results["phosphorus_sweep"] = p_results

# 3. Potassium Sweep
k_results = []
for k_val in [15.0, 40.0, 80.0, 150.0, 200.0, 350.0, 500.0]:
    p = dict(baseline, K=k_val)
    st, res = call_api(p)
    top_crop = res.get("prediction", "ERROR")
    recs = res.get("recommendations", [])
    top3 = ", ".join([f"{r['crop']}({r['final_score']:.3f})" for r in recs[:3]])
    k_results.append({
        "K": k_val, "top_crop": top_crop, "top_3": top3,
        "combined_score": recs[0]["final_score"] if recs else 0.0,
        "warnings_count": len(res.get("warnings", []))
    })
sensitivity_results["potassium_sweep"] = k_results

# 4. pH Sweep
ph_results = []
for ph_val in [4.5, 5.5, 6.5, 7.5, 8.5, 9.2]:
    p = dict(baseline, ph=ph_val)
    st, res = call_api(p)
    top_crop = res.get("prediction", "ERROR")
    recs = res.get("recommendations", [])
    top3 = ", ".join([f"{r['crop']}({r['final_score']:.3f})" for r in recs[:3]])
    ph_results.append({
        "pH": ph_val, "top_crop": top_crop, "top_3": top3,
        "combined_score": recs[0]["final_score"] if recs else 0.0
    })
sensitivity_results["ph_sweep"] = ph_results

# 5. Rainfall Sweep (CRITICAL)
rain_results = []
for rain_val in [30.0, 60.0, 100.0, 150.0, 220.0, 350.0, 750.0, 1200.0]:
    p = dict(baseline, rainfall=rain_val)
    st, res = call_api(p)
    top_crop = res.get("prediction", "ERROR")
    recs = res.get("recommendations", [])
    top3 = ", ".join([f"{r['crop']}({r['final_score']:.3f})" for r in recs[:3]])
    rice_score = next((r["final_score"] for r in recs if r["crop"].lower() == "rice"), 0.0)
    rice_m1 = next((r["npk_score"] for r in recs if r["crop"].lower() == "rice"), 0.0)
    rain_results.append({
        "rainfall_mm": rain_val, "top_crop": top_crop, "top_3": top3,
        "rice_combined": rice_score, "rice_m1_npk": rice_m1,
        "is_extrapolated": rain_val > 298.6
    })
sensitivity_results["rainfall_sweep"] = rain_results

# 6. Temperature & Humidity Shifts
temp_hum_results = []
climate_scenarios = [
    ("Winter / Rabi Cool & Dry", 15.0, 35.0),
    ("Moderate Sub-tropical", 24.0, 65.0),
    ("Monsoon Warm & Humid", 28.0, 85.0),
    ("Hot Semi-Arid Summer", 38.0, 30.0),
]
for label, t_val, h_val in climate_scenarios:
    p = dict(baseline, temperature=t_val, humidity=h_val)
    st, res = call_api(p)
    top_crop = res.get("prediction", "ERROR")
    recs = res.get("recommendations", [])
    top3 = ", ".join([f"{r['crop']}({r['final_score']:.3f})" for r in recs[:3]])
    temp_hum_results.append({
        "scenario": label, "temperature": t_val, "humidity": h_val,
        "top_crop": top_crop, "top_3": top3
    })
sensitivity_results["climate_scenarios"] = temp_hum_results

# 7. Boundary & Error Cases
boundary_cases = [
    ("Negative Nitrogen (N=-10)", dict(baseline, N=-10.0), 422),
    ("Extreme pH (pH=12.0)", dict(baseline, ph=12.0), 422),
    ("Excessive Temperature (T=55°C)", dict(baseline, temperature=55.0), 422),
    ("Missing Rainfall field", {k: v for k, v in baseline.items() if k != "rainfall"}, 422),
    ("Non-Maharashtra District (Patna)", dict(baseline, district="Patna"), 200), # Expect fallback warning
    ("Unsupported Season (Autumn)", dict(baseline, season="Autumn"), 200), # Expect fallback warning
]
boundary_results = []
for label, p, expected_status in boundary_cases:
    st, res = call_api(p)
    warnings = res.get("warnings", []) if st == 200 else [res.get("detail", "Error")]
    boundary_results.append({
        "case": label,
        "http_status": st,
        "expected_status": expected_status,
        "passed": (st == expected_status),
        "detail_or_warnings": warnings
    })
sensitivity_results["boundary_cases"] = boundary_results

# Save sensitivity JSON
out_path = ROOT_DIR / "data" / "soil_validation" / "phase4_sensitivity_results.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(sensitivity_results, f, indent=2)

print(f"Phase 4 sensitivity tests completed successfully! Saved to {out_path}")
