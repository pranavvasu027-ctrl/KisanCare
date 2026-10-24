"""
Phase 3 Execution Script: Real Soil NPK Dataset Validation & Direct Model Comparison.
Sends all 12 real-world records to:
1. Running KisanCare FastAPI Endpoint (http://localhost:8000/api/v1/crop-recommendation)
2. Direct Hugging Face Model Pipeline (CropRecommendationPipeline)

Verifies:
- Top 3 predicted crops
- Component scores (NPK RF probability vs Regional suitability)
- API vs Direct pipeline output match
- Model loaded vs Demo status
- Determinism across repeated calls
"""

import json
import urllib.request
import time
import pandas as pd
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add project root to sys.path to import ml pipeline directly
ROOT_DIR = Path(r"C:\Users\Atharva\.gemini\antigravity\scratch\KisanCare")
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ml.crop_recommendation.huggingface_pipeline import (
    CropRecommendationPipeline,
    CropRecommendationInput,
    PINNED_REVISION,
    HF_REPO_ID
)

# 1. Initialize Direct Pipeline
print("Initializing direct Hugging Face pipeline...")
direct_pipeline = CropRecommendationPipeline()
print(f"Direct pipeline loaded. Repo: {HF_REPO_ID} (rev: {PINNED_REVISION[:7]})")

# 2. Read records
csv_path = ROOT_DIR / "data" / "soil_validation" / "real_soil_test_records_maharashtra.csv"
df = pd.read_csv(csv_path)

results = []
api_url = "http://localhost:8000/api/v1/crop-recommendation"

for idx, row in df.iterrows():
    test_id = row["test_id"]
    district = row["district"]
    season = row["season"]
    N = float(row["N"])
    P = float(row["P"])
    K = float(row["K"])
    ph = float(row["ph"])
    temp = float(row["temperature"])
    humidity = float(row["humidity"])
    rainfall = float(row["rainfall"])
    water_avail = str(row["water_availability"])
    location = str(row["location_detail"])

    payload = {
        "N": N,
        "P": P,
        "K": K,
        "ph": ph,
        "temperature": temp,
        "humidity": humidity,
        "rainfall": rainfall,
        "district": district,
        "season": season,
        "water_availability": water_avail,
        "top_k": 3
    }

    # Step A: Call API
    req = urllib.request.Request(
        api_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req) as resp:
            api_resp = json.loads(resp.read().decode("utf-8"))
            api_latency_ms = round((time.time() - t0) * 1000, 2)
    except Exception as exc:
        print(f"API Error for {test_id}: {exc}")
        api_resp = {"error": str(exc)}
        api_latency_ms = None

    # Step B: Call Direct Pipeline
    direct_input = CropRecommendationInput(
        N=N,
        P=P,
        K=K,
        temperature=temp,
        humidity=humidity,
        ph=ph,
        rainfall=rainfall,
        district=district,
        season=season,
        water_access=water_avail,
        top_k=3
    )
    direct_res = direct_pipeline.predict(direct_input)

    # Step C: Compare API vs Direct
    api_recs = api_resp.get("recommendations", [])
    direct_recs = direct_res.recommendations

    match = True
    if len(api_recs) != len(direct_recs):
        match = False
    else:
        for a, d in zip(api_recs, direct_recs):
            if a["crop"].lower() != d.crop.lower():
                match = False
            if abs(a["final_score"] - d.combined_score) > 0.001:
                match = False

    # Check Determinism
    with urllib.request.urlopen(req) as resp2:
        api_resp2 = json.loads(resp2.read().decode("utf-8"))
    deterministic = (api_resp.get("prediction") == api_resp2.get("prediction"))

    top3_crops_str = ", ".join([f"#{r['rank']} {r['crop']} ({r['final_score']:.3f})" for r in api_recs[:3]])
    warnings_str = "None" if not api_resp.get("warnings") else "; ".join(api_resp.get("warnings"))

    results.append({
        "test_id": test_id,
        "location": location,
        "district": district,
        "season": season,
        "N": N,
        "P": P,
        "K": K,
        "pH": ph,
        "temperature": temp,
        "humidity": humidity,
        "rainfall": rainfall,
        "ground_truth_crop": row["ground_truth_crop"],
        "top_prediction": api_resp.get("prediction"),
        "top_3_crops": top3_crops_str,
        "api_direct_match": "MATCH (Exact)" if match else "MISMATCH",
        "deterministic": "YES (100%)" if deterministic else "NO",
        "is_demo": api_resp.get("is_demo", False),
        "model_loaded": api_resp.get("model_loaded", False),
        "model_source": api_resp.get("model_source"),
        "warnings": warnings_str,
        "latency_ms": api_latency_ms,
        "api_recommendations": api_recs,
        "direct_recommendations": [
            {
                "crop": r.crop,
                "rank": r.rank,
                "combined_score": r.combined_score,
                "npk_score": r.npk_score,
                "region_score": r.region_score,
                "region_suitability": r.region_suitability,
                "water_constrained": r.water_constrained
            }
            for r in direct_recs
        ]
    })
    print(f"Completed {test_id} ({district} - {season}): Match={match}, Top={api_resp.get('prediction')}")

# Save detailed results JSON
res_json_path = ROOT_DIR / "data" / "soil_validation" / "phase3_real_inference_results.json"
with open(res_json_path, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

# Save summary table CSV
summary_df = pd.DataFrame([
    {
        "Test ID": r["test_id"],
        "Actual Source / Location": r["location"],
        "N": r["N"],
        "P": r["P"],
        "K": r["K"],
        "pH": r["pH"],
        "Temperature": r["temperature"],
        "Humidity": r["humidity"],
        "Rainfall": r["rainfall"],
        "Top 3 Crops": r["top_3_crops"],
        "API/Direct-Model Match": r["api_direct_match"],
        "Warnings": r["warnings"]
    }
    for r in results
])
summary_csv_path = ROOT_DIR / "data" / "soil_validation" / "phase3_summary_table.csv"
summary_df.to_csv(summary_csv_path, index=False)
print(f"\nAll Phase 3 tests finished! Saved detailed results to {res_json_path} and summary table to {summary_csv_path}")
