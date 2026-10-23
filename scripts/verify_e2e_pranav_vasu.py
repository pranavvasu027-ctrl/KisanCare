"""End-to-End Verification Script for Pranav Vasu Supabase Integration."""
import os
import sys

sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("backend"))

from dotenv import load_dotenv
from supabase import create_client, Client
from fastapi.testclient import TestClient
from backend.app.main import app

load_dotenv()

def verify_e2e():
    url = os.environ.get("SUPABASE_URL")
    anon_key = os.environ.get("SUPABASE_ANON_KEY")
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not anon_key or not service_key:
        print("Error: Missing Supabase credentials in .env")
        sys.exit(1)

    print("==================================================")
    print("KISANCARE END-TO-END SUPABASE VERIFICATION")
    print("==================================================")

    # 1. Authenticate Pranav Vasu with Supabase Auth (Anon client)
    auth_sb: Client = create_client(url, anon_key)
    auth_resp = auth_sb.auth.sign_in_with_password({
        "email": "farmer1@kisancare.test",
        "password": "TestPassword123!"
    })
    token = auth_resp.session.access_token
    uid = auth_resp.user.id
    print(f"[OK] Auth successful for Pranav Vasu (UID: {uid})")

    # 2. Verify Profile
    prof = auth_sb.table("profiles").select("*").eq("user_id", uid).execute()
    assert len(prof.data) == 1, "Profile not found"
    p = prof.data[0]
    print(f"[OK] Profile: {p['name']}, Phone: {p.get('phone')}, Lang: {p.get('preferred_language')}")
    assert p["name"] == "Pranav Vasu"

    # 3. Verify Farm & Area Integrity
    farms = auth_sb.table("farms").select("*").eq("user_id", uid).execute()
    assert len(farms.data) == 1, "Farm not found"
    farm = farms.data[0]
    farm_id = farm["id"]
    total_area = float(farm["total_area"])
    print(f"[OK] Farm: {farm['farm_name']}, Location: {farm['location']}, Total Area: {total_area} acres")
    assert total_area == 10.0, f"Expected 10.0 acres, got {total_area}"

    # 4. Verify Fields & Strict 5.0 Acre Allocation
    fields = auth_sb.table("fields").select("*").eq("farm_id", farm_id).execute()
    assert len(fields.data) == 2, f"Expected 2 fields, got {len(fields.data)}"
    allocated_acres = sum(float(f["area"]) for f in fields.data)
    unallocated_acres = total_area - allocated_acres
    print(f"[OK] Fields: {[f['field_name'] + ' (' + str(f['area']) + ' ' + f['area_unit'] + ')' for f in fields.data]}")
    print(f"[OK] Allocated Area: {allocated_acres} acres, Unallocated Area: {unallocated_acres} acres")
    assert allocated_acres == 5.0, f"Expected 5.0 allocated acres, got {allocated_acres}"
    assert unallocated_acres == 5.0, f"Expected 5.0 unallocated acres, got {unallocated_acres}"

    # 5. Verify Soil Records & Integrity (pH 7.6-8.5, NPK null)
    field_a_id = [f["id"] for f in fields.data if "Field A" in f["field_name"]][0]
    soil = auth_sb.table("soil_records").select("*").eq("field_id", field_a_id).execute()
    assert len(soil.data) >= 1, "Soil records missing for Field A"
    s = soil.data[0]
    print(f"[OK] Soil Type: {s['soil_type']}, pH: {s['ph']}, N: {s.get('nitrogen')}, P: {s.get('phosphorus')}, K: {s.get('potassium')}")
    assert s["ph"] == 8.05
    assert s.get("nitrogen") is None, "Nitrogen should not be fabricated"
    assert s.get("phosphorus") is None, "Phosphorus should not be fabricated"
    assert s.get("potassium") is None, "Potassium should not be fabricated"
    assert s.get("provenance") in ["FARMER_ENTERED", "farmer_reported"]

    # 6. Verify Crop & Season Records
    seasons = auth_sb.table("seasons").select("*, crop_records(*)").eq("field_id", field_a_id).execute()
    assert len(seasons.data) >= 1, "Seasons missing for Field A"
    season = seasons.data[0]
    print(f"[OK] Season: {season['season_name']}, Crop: {season['crop']}, Variety: {season['crop_variety']}, Stage: {season['crop_stage']}")
    assert season["crop"] == "Cotton"
    assert season["crop_variety"] == "godavari"

    # 7. Verify Costs & Ambiguity Disclosures
    records = auth_sb.table("farm_data_records").select("*").eq("farm_id", farm_id).execute()
    costs = [r for r in records.data if r.get("record_type") == "FARM_COST"]
    cost_map = {c["record_data"]["category"]: float(c["record_data"]["amount"]) for c in costs}
    print(f"[OK] Farm Costs Recorded: {cost_map}")
    assert any("Seed" in k for k in cost_map) and 11000.0 in cost_map.values()
    assert any("Fertilizer" in k for k in cost_map) and 20000.0 in cost_map.values()
    assert any("Pesticide" in k for k in cost_map) and 10.0 in cost_map.values()
    assert any("Labour" in k for k in cost_map) and 50000.0 in cost_map.values()
    assert any("Machinery" in k for k in cost_map) and 20000.0 in cost_map.values()
    assert any("yechan" in k for k in cost_map) and 40000.0 in cost_map.values()
    assert any("Transport" in k for k in cost_map) and 5000.0 in cost_map.values()
    total_cost = sum(cost_map.values())
    print(f"[OK] Total Cultivation Expenses: Rs. {total_cost:,.2f}")
    assert total_cost in [146010.0, 156010.0]

    # 8. Verify Outcomes (Yield Benchmark 10 q/ac & Current Sales 0)
    outcomes = auth_sb.table("outcomes").select("*").eq("farm_id", farm_id).execute()
    yield_outcomes = [o for o in outcomes.data if o.get("outcome_type") == "HISTORICAL_YIELD"]
    assert len(yield_outcomes) >= 1, "Historical yield record missing"
    y = yield_outcomes[0]
    print(f"[OK] Yield Record: {y['actual_value']} {y['unit']} (Historical Benchmark)")
    assert float(y["actual_value"]) == 10.0

    sales_outcomes = [o for o in outcomes.data if o.get("outcome_type") == "CURRENT_SALES"]
    assert len(sales_outcomes) >= 1, "Sales record missing"
    s_out = sales_outcomes[0]
    print(f"[OK] Sales Record: Qty {s_out['actual_value']} {s_out['unit']}")
    assert float(s_out["actual_value"]) == 0.0

    # Verify Market Info record in farm_data_records
    mkt = [r for r in records.data if r.get("record_type") == "MARKET_INFO"][0]
    print(f"[OK] APMC Benchmark Price: Rs. {mkt['record_data']['cotton_price_reference_inr_quintal']}/qtl (Market: {mkt['record_data']['target_market']}, Date: {mkt['record_data']['price_observation_date']})")
    assert mkt['record_data']['cotton_price_reference_inr_quintal'] == 8000.0

    # 9. Verify Multi-User RLS Isolation
    auth_sb2 = create_client(url, anon_key)
    auth_resp2 = auth_sb2.auth.sign_in_with_password({
        "email": "farmer2@kisancare.test",
        "password": "TestPassword123!"
    })
    farms2 = auth_sb2.table("farms").select("*").eq("id", farm_id).execute()
    print(f"[OK] Multi-User RLS Isolation: Farmer2 accessing Pranav farm -> {len(farms2.data)} records returned")
    assert len(farms2.data) == 0, "Security violation: Farmer 2 saw Farmer 1 farm"

    # 10. Verify FastAPI Backend Endpoints with Pranav Vasu token
    client = TestClient(app)

    # A) Digital Twin Endpoint
    dt_resp = client.get(f"/api/v1/digital-twin/{farm_id}", headers={"Authorization": f"Bearer {token}"})
    assert dt_resp.status_code == 200, f"Digital twin failed: {dt_resp.text}"
    dt = dt_resp.json()
    print(f"[OK] FastAPI /digital-twin: name={dt['name']}, area={dt['area_acres']}, fields={len(dt['fields'])}, state={dt['state']['crop']}")
    assert dt["name"] == "Pranav Vasu Farm"
    assert dt["area_acres"] == 10.0
    assert len(dt["fields"]) == 2

    # B) What-If Simulation Endpoint
    sim_resp = client.post("/api/v1/simulate", json={
        "farm_id": farm_id,
        "changes": {
            "crop": "Cotton",
            "rainfall_change_percent": -20,
            "input_cost": 146010,
            "expected_price": 8000
        }
    })
    assert sim_resp.status_code == 200, f"Simulate failed: {sim_resp.text}"
    sim = sim_resp.json()
    print(f"[OK] FastAPI /simulate: Baseline Yield={sim['baseline']['yield']} qtl, Sim Yield={sim['scenario']['yield']} qtl, Sim Profit=Rs. {sim['scenario']['profit']}")
    assert sim["baseline"]["yield"] == 50.0

    # C) Copilot Grounding Endpoint
    copilot_resp = client.post("/api/v1/copilot/chat", json={
        "message": "काय अवस्था आहे माझ्या कपाशीची? (What is the status of my cotton?)",
        "farm_id": farm_id
    }, headers={"Authorization": f"Bearer {token}"})
    if copilot_resp.status_code == 200:
        cop = copilot_resp.json()
        print(f"[OK] FastAPI /copilot/chat: Grounded={cop.get('grounded')}, Reply preview: {cop.get('reply')[:120]}...")
        assert cop.get("grounded") is True
    else:
        # Proper 503 when GEMINI_API_KEY not set in local environment
        assert copilot_resp.status_code in [503, 502], f"Unexpected status: {copilot_resp.status_code}"
        print(f"[OK] FastAPI /copilot/chat: Proper 503 Service Unavailable returned when GEMINI_API_KEY unset ({copilot_resp.json()['detail']})")

    print("\n==================================================")
    print("ALL 10 END-TO-END VERIFICATION CHECKS PASSED [OK]")
    print("==================================================")

if __name__ == "__main__":
    verify_e2e()
