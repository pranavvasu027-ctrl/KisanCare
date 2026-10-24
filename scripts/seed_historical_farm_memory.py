"""Seed script to provision historical farm memory demo records (2022–2026) for KisanCare in Supabase.

Historical crop allocation:
- Kharif 2022–23: Soybean (Demo data, only if missing)
- Kharif 2023–24: Cotton  (Demo data, only if missing)
- Kharif 2024–25: Cotton  (Demo data, only if missing)
- Kharif 2025–26: Cotton  (Demo data, only if missing - preserved/reused if existing)
- Kharif 2026–27: Cotton  (Active season - strictly preserved)

Idempotent: Reuses existing records, creates missing ones, marks demo data with source='DEMO_SEED' and is_demo=True in JSONB.
"""
import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

PRANAV_UID = "9c851059-4259-4cd3-95c7-9ab287f60710"
PRANAV_FARM_ID = "52120432-c948-4026-87c4-7e2c481a7bf5"
FIELD_A_ID = "e5d69ac6-bfe4-4015-a3cd-7cab06c476a6"  # Field A (3.0 acres)

HISTORICAL_SEASONS_SPEC = [
    {
        "season_name": "Kharif 2022-23",
        "crop": "Soybean",
        "crop_variety": "JS 335",
        "sowing_date": "2022-06-22",
        "actual_harvest_date": "2022-10-15",
        "status": "COMPLETED",
        "yieldQuantity": 8.5,
        "yieldUnit": "qtl/ac",
        "areaAcres": 3.0,
        "soilTest": {
            "n": 22.0,
            "p": 16.0,
            "k": 180.0,
            "ph": 7.9
        },
        "fertilizers": [
            {"product": "DAP (Di-ammonium Phosphate)", "quantityKg": 75, "cost": 10500, "applicationDate": "2022-06-25"},
            {"product": "Single Super Phosphate (SSP)", "quantityKg": 50, "cost": 4500, "applicationDate": "2022-07-10"}
        ],
        "pesticides": [
            {"product": "Chlorantraniliprole (Coragen)", "targetPest": "Semilooper & Spodoptera", "quantityMl": 150, "cost": 3200, "applicationDate": "2022-08-05"}
        ],
        "irrigation": {
            "method": "Rainfed with drainage management",
            "waterAvailability": "Medium",
            "hoursTotal": 0,
            "cost": 0
        },
        "weatherObservations": "Timely monsoon onset with 720 mm seasonal rain; adequate moisture throughout pod-filling stage.",
        "economics": {
            "inputCost": 18200,       # Seeds (5000) + Fert (10500+4500=15000) + Pest (3200) -> 23200
            "laborCost": 28000,
            "irrigationCost": 0,
            "sellingPrice": 4600,     # ₹4,600 / quintal
            "revenue": 117300,        # 8.5 qtl/ac * 3 ac = 25.5 qtl * 4600 = 117300
            "profit": 66100           # 117300 - (23200 + 28000) = 66100
        },
        "learnings": [
            "Soybean rotation effectively fixes atmospheric nitrogen and leaves residual soil friability for subsequent deep-root crops.",
            "JS 335 responded favorably to early sowing within 48 hours of 50mm cumulative monsoon rain."
        ],
        "farmerNotes": "Illustrative historical benchmark for legume crop rotation in Field A (black cotton soil)."
    },
    {
        "season_name": "Kharif 2023-24",
        "crop": "Cotton",
        "crop_variety": "godavari",
        "sowing_date": "2023-06-18",
        "actual_harvest_date": "2023-11-20",
        "status": "COMPLETED",
        "yieldQuantity": 9.2,
        "yieldUnit": "qtl/ac",
        "areaAcres": 3.0,
        "soilTest": {
            "n": 24.0,
            "p": 14.0,
            "k": 175.0,
            "ph": 8.0
        },
        "fertilizers": [
            {"product": "10:26:26 Complex Fertilizer", "quantityKg": 100, "cost": 14500, "applicationDate": "2023-07-01"},
            {"product": "Urea Top Dressing", "quantityKg": 60, "cost": 3600, "applicationDate": "2023-08-10"}
        ],
        "pesticides": [
            {"product": "Neem Oil 1500 ppm & Bio-fungicide", "targetPest": "Whitefly & Sucking Pests", "quantityMl": 500, "cost": 2800, "applicationDate": "2023-07-28"}
        ],
        "irrigation": {
            "method": "Rainfed / Monsoon Dependent",
            "waterAvailability": "Low",
            "hoursTotal": 6,
            "cost": 1200
        },
        "weatherObservations": "Dry spell during early square formation; late August revival saved boll retention.",
        "economics": {
            "inputCost": 26900,       # Seeds (6000) + Fert (18100) + Pest (2800) = 26900
            "laborCost": 42000,
            "irrigationCost": 1200,
            "sellingPrice": 7100,     # ₹7,100 / quintal
            "revenue": 195960,        # 9.2 qtl/ac * 3 ac = 27.6 qtl * 7100 = 195960
            "profit": 125860          # 195960 - (26900 + 42000 + 1200) = 125860
        },
        "learnings": [
            "Medium-staple Cotton variety godavari exhibited good early-season drought tolerance on black cotton soil.",
            "Timely inter-culture weeding in week 4 conserved vital soil moisture during the dry spell."
        ],
        "farmerNotes": "Demonstration benchmark showing resilience under moderate rainfall variation."
    },
    {
        "season_name": "Kharif 2024-25",
        "crop": "Cotton",
        "crop_variety": "godavari",
        "sowing_date": "2024-06-25",
        "actual_harvest_date": "2024-11-28",
        "status": "COMPLETED",
        "yieldQuantity": 10.5,
        "yieldUnit": "qtl/ac",
        "areaAcres": 3.0,
        "soilTest": {
            "n": 26.0,
            "p": 15.0,
            "k": 190.0,
            "ph": 8.05
        },
        "fertilizers": [
            {"product": "DAP + Potash split application", "quantityKg": 120, "cost": 16500, "applicationDate": "2024-07-04"},
            {"product": "Urea & Micronutrient Spray", "quantityKg": 50, "cost": 4200, "applicationDate": "2024-08-15"}
        ],
        "pesticides": [
            {"product": "Flonicamid 50 WG", "targetPest": "Jassids & Thrips", "quantityMl": 200, "cost": 3500, "applicationDate": "2024-08-02"}
        ],
        "irrigation": {
            "method": "Rainfed + Protective Irrigation",
            "waterAvailability": "Medium",
            "hoursTotal": 10,
            "cost": 1400
        },
        "weatherObservations": "Favorable monsoon distribution with well-timed September showers supporting optimal boll opening.",
        "economics": {
            "inputCost": 30200,       # Seeds (6000) + Fert (20700) + Pest (3500) = 30200
            "laborCost": 46000,
            "irrigationCost": 1400,
            "sellingPrice": 7400,     # ₹7,400 / quintal
            "revenue": 233100,        # 10.5 qtl/ac * 3 ac = 31.5 qtl * 7400 = 233100
            "profit": 155500          # 233100 - (30200 + 46000 + 1400) = 155500
        },
        "learnings": [
            "Peak yield of 10.5 quintals/acre achieved with split potash application during boll development.",
            "Protective irrigation applied at 50% boll development prevented premature boll shedding."
        ],
        "farmerNotes": "Demonstration benchmark representing favorable climatic conditions and balanced nutrition."
    },
    {
        "season_name": "Kharif 2025-26",
        "crop": "Cotton",
        "crop_variety": "godavari",
        "sowing_date": "2025-06-20",
        "actual_harvest_date": "2025-11-25",
        "status": "COMPLETED",
        "yieldQuantity": 10.0,
        "yieldUnit": "qtl/ac",
        "areaAcres": 3.0,
        "soilTest": {
            "ph": 8.0
        },
        "fertilizers": [
            {"product": "Fertilizers (bulk unitemized)", "cost": 18000, "applicationDate": "2025-07-05"}
        ],
        "pesticides": [],
        "irrigation": {
            "method": "Rainfed + Occasional Irrigation",
            "waterAvailability": "Medium",
            "hoursTotal": 12,
            "cost": 1500
        },
        "weatherObservations": "Adequate late-monsoon showers supported boll development.",
        "economics": {
            "inputCost": 28000,
            "laborCost": 45000,
            "irrigationCost": 1500,
            "sellingPrice": 7600,
            "revenue": 228000,
            "profit": 153500
        },
        "learnings": [
            "Historical yield of 10 quintals/acre verified when late-season moisture is preserved.",
            "Akot APMC market provides best price realization for Vidarbha medium-staple cotton."
        ],
        "farmerNotes": "Achieved 10 quintals/acre historical benchmark."
    }
]

def seed_historical_farm_memory():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not key:
        print("Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env")
        sys.exit(1)

    sb: Client = create_client(url, key)
    print("=" * 60)
    print("KisanCare: Idempotent Historical Farm Memory Seeding")
    print(f"Target Farm ID: {PRANAV_FARM_ID}")
    print(f"Target Field ID: {FIELD_A_ID} (Field A - 3.0 Acres)")
    print("=" * 60)

    # 1. Fetch existing seasons for Field A
    existing_seasons_res = sb.table("seasons").select("*").eq("field_id", FIELD_A_ID).execute()
    existing_seasons = existing_seasons_res.data or []
    existing_by_name = {s["season_name"]: s for s in existing_seasons}
    print(f"Found {len(existing_seasons)} existing season(s) on Field A: {[s['season_name'] for s in existing_seasons]}")

    results = []

    for spec in HISTORICAL_SEASONS_SPEC:
        season_name = spec["season_name"]
        crop = spec["crop"]
        crop_variety = spec["crop_variety"]
        sowing_date = spec["sowing_date"]
        actual_harvest_date = spec["actual_harvest_date"]
        status = spec["status"]

        is_new = False
        season_id = None

        if season_name in existing_by_name:
            existing = existing_by_name[season_name]
            season_id = existing["id"]
            print(f"[REUSE] Season '{season_name}' already exists (ID: {season_id}, Crop: {existing.get('crop')}).")
            # If crop differed, update it to match required crop allocation
            if existing.get("crop") != crop:
                print(f"  -> Updating crop from {existing.get('crop')} to {crop} as per required allocation.")
                sb.table("seasons").update({"crop": crop, "crop_variety": crop_variety}).eq("id", season_id).execute()
        else:
            print(f"[INSERT] Creating missing historical demo season: '{season_name}' ({crop})")
            insert_data = {
                "field_id": FIELD_A_ID,
                "season_name": season_name,
                "crop": crop,
                "crop_variety": crop_variety,
                "sowing_date": sowing_date,
                "actual_harvest_date": actual_harvest_date,
                "status": status
            }
            res = sb.table("seasons").insert(insert_data).execute()
            if not res.data:
                print(f"  [ERROR] Failed to insert season '{season_name}'")
                continue
            season_id = res.data[0]["id"]
            is_new = True
            print(f"  -> Created with ID: {season_id}")

        # Check existing extended detail in farm_data_records
        fdr_res = sb.table("farm_data_records").select("id").eq("season_id", season_id).eq("record_type", "historical_season_detail").execute()
        fdr_existing = fdr_res.data or []

        extended_data = {
            "yieldQuantity": spec["yieldQuantity"],
            "yieldUnit": spec["yieldUnit"],
            "areaAcres": spec["areaAcres"],
            "soilTest": spec["soilTest"],
            "fertilizers": spec["fertilizers"],
            "pesticides": spec["pesticides"],
            "irrigation": spec["irrigation"],
            "weatherObservations": spec["weatherObservations"],
            "economics": spec["economics"],
            "learnings": spec["learnings"],
            "farmerNotes": spec["farmerNotes"],
            "isDemo": True
        }

        if fdr_existing:
            fdr_id = fdr_existing[0]["id"]
            print(f"  -> Updating existing historical_season_detail record ({fdr_id})")
            sb.table("farm_data_records").update({
                "record_data": extended_data,
                "source": "DEMO_SEED",
                "reliability": 0.9
            }).eq("id", fdr_id).execute()
        else:
            print(f"  -> Inserting historical_season_detail record")
            sb.table("farm_data_records").insert({
                "farm_id": PRANAV_FARM_ID,
                "field_id": FIELD_A_ID,
                "season_id": season_id,
                "record_type": "historical_season_detail",
                "record_data": extended_data,
                "source": "DEMO_SEED",
                "reliability": 0.9,
                "created_by": PRANAV_UID
            }).execute()

        results.append({
            "season_name": season_name,
            "crop": crop,
            "season_id": season_id,
            "action": "INSERTED" if is_new else "REUSED",
            "yield": f"{spec['yieldQuantity']} {spec['yieldUnit']}",
            "profit": f"INR {spec['economics']['profit']:,}"
        })

    print("\n" + "=" * 60)
    print("HISTORICAL DEMO SEEDING SUMMARY")
    print("=" * 60)
    for r in results:
        print(f"* {r['season_name']} | {r['crop']:<8} | {r['action']:<8} | Yield: {r['yield']:<12} | Profit: {r['profit']}")

    print("\nPreserving Kharif 2026-27 (Active) records intact.")
    active_res = sb.table("seasons").select("id, season_name, crop, status").eq("field_id", FIELD_A_ID).eq("status", "ACTIVE").execute()
    for s in active_res.data:
        print(f"* Active Season Preserved: {s['season_name']} | {s['crop']} | Status: {s['status']}")
    print("=" * 60)

if __name__ == "__main__":
    seed_historical_farm_memory()
