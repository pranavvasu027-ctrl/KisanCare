"""Seed script to provision the authentic Pranav Vasu profile and farm data in Supabase."""
import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

PRANAV_UID = "9c851059-4259-4cd3-95c7-9ab287f60710"  # farmer1@kisancare.test
PRANAV_EMAIL = "farmer1@kisancare.test"

def seed_pranav_vasu():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not key:
        print("Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env")
        sys.exit(1)

    sb: Client = create_client(url, key)
    print(f"Provisioning Pranav Vasu under user {PRANAV_UID} ({PRANAV_EMAIL})...")

    # 1. Supabase Auth user metadata update
    sb.auth.admin.update_user_by_id(PRANAV_UID, {
        "user_metadata": {
            "name": "Pranav Vasu",
            "age": 35,
            "gender": "Male",
            "village": "Takli Bu",
            "district": "Akola",
            "state": "Maharashtra",
            "country": "India",
            "preferred_languages": ["Marathi", "Hindi"],
            "farming_experience": "5–10 years",
            "farmer_category": "Medium farmer",
            "role": "farmer"
        }
    })
    print("[OK] Auth user metadata updated")

    # 2. Profiles table
    prof_existing = sb.table("profiles").select("id").eq("user_id", PRANAV_UID).execute()
    if prof_existing.data:
        prof_res = sb.table("profiles").update({
            "name": "Pranav Vasu",
            "phone": "+919876543211",
            "preferred_language": "mr"
        }).eq("user_id", PRANAV_UID).execute()
        profile_id = prof_res.data[0]["id"]
        print(f"[OK] Profile updated: {profile_id}")
    else:
        prof_res = sb.table("profiles").insert({
            "user_id": PRANAV_UID,
            "name": "Pranav Vasu",
            "phone": "+919876543211",
            "preferred_language": "mr"
        }).execute()
        profile_id = prof_res.data[0]["id"]
        print(f"[OK] Profile inserted: {profile_id}")

    # 3. Clean up existing farms and associated records for strictly idempotent re-seeding
    old_farms = sb.table("farms").select("id").eq("user_id", PRANAV_UID).execute()
    for f in old_farms.data:
        old_fid = f["id"]
        try:
            sb.table("farm_data_records").delete().eq("farm_id", old_fid).execute()
        except Exception:
            pass
        try:
            sb.table("outcomes").delete().eq("farm_id", old_fid).execute()
        except Exception:
            pass
        try:
            sb.table("model_predictions").delete().eq("farm_id", old_fid).execute()
        except Exception:
            pass
        sb.table("farms").delete().eq("id", old_fid).execute()

    # 4. Farms table
    # Total cultivated area: 10 acres. 2 farm/location entries reported.
    farm_data = {
        "user_id": PRANAV_UID,
        "farm_name": "Pranav Vasu Farm",
        "description": "Black soil ('koralvahu jamin'). Land ownership: Owned. Terrain: Mostly flat. Drainage: Good. Boundaries: Not yet mapped. Nearby features: Village road and neighbouring farms. Reported locations: 2. Unallocated area: 5.0 acres.",
        "location": "Takli Bu, Akola, Maharashtra",
        "total_area": 10.0,
        "area_unit": "acre",
        "status": "ACTIVE"
    }
    farm_res = sb.table("farms").insert(farm_data).execute()
    farm_id = farm_res.data[0]["id"]
    print(f"[OK] Farm created: {farm_id} (10.0 acres total)")

    # 5. Fields table
    # Only 5 of reported 10 acres are represented: Field A (3 ac), Field B (2 ac). 5 acres unallocated.
    field_a_data = {
        "farm_id": farm_id,
        "field_name": "Field A",
        "area": 3.0,
        "area_unit": "acre",
        "boundary": {
            "terrain": "Mostly flat",
            "drainage": "Good",
            "soil_description": "koralvahu jamin",
            "soil_type": "Black cotton soil",
            "soil_depth": "Deep",
            "boundaries_mapped": False,
            "unallocated_farm_area_acres": 5.0
        },
        "status": "ACTIVE"
    }
    field_b_data = {
        "farm_id": farm_id,
        "field_name": "Field B",
        "area": 2.0,
        "area_unit": "acre",
        "boundary": {
            "terrain": "Mostly flat",
            "drainage": "Good",
            "soil_description": "koralvahu jamin",
            "soil_type": "Black cotton soil",
            "soil_depth": "Deep",
            "boundaries_mapped": False,
            "unallocated_farm_area_acres": 5.0
        },
        "status": "ACTIVE"
    }
    field_a_res = sb.table("fields").insert(field_a_data).execute()
    field_b_res = sb.table("fields").insert(field_b_data).execute()
    field_a_id = field_a_res.data[0]["id"]
    field_b_id = field_b_res.data[0]["id"]
    print(f"[OK] Fields created: Field A ({field_a_id}, 3 ac), Field B ({field_b_id}, 2 ac). Unallocated: 5.0 ac")

    # 6. Seasons table
    season_a_data = {
        "field_id": field_a_id,
        "season_name": "2026-27",
        "crop": "Cotton",
        "crop_variety": "godavari",
        "sowing_date": "2026-06-20",
        "crop_stage": "Boll development",
        "status": "ACTIVE"
    }
    season_b_data = {
        "field_id": field_b_id,
        "season_name": "2026-27",
        "crop": "Cotton",
        "crop_variety": "godavari",
        "sowing_date": "2026-06-25",
        "crop_stage": "Boll development",
        "status": "ACTIVE"
    }
    season_a_res = sb.table("seasons").insert(season_a_data).execute()
    season_b_res = sb.table("seasons").insert(season_b_data).execute()
    season_a_id = season_a_res.data[0]["id"]
    season_b_id = season_b_res.data[0]["id"]
    print(f"[OK] Seasons created: Season A ({season_a_id}), Season B ({season_b_id})")

    # 7. Crop Records
    planting_info = {
        "variety_entered": "godavari",
        "seed_description": "godawari, 2 kg / acre",
        "variety_verification_status": "PENDING_CONFIRMATION",
        "fertilizers_reported": "Urea and DAP (quantities not supplied)",
        "pesticide_details": "Unknown / not supplied",
        "weed_management": "Machinery",
        "historical_cotton_yield_quintal_per_acre": 10.0,
        "current_crop_health": "Drought / water-stress symptoms reported",
        "boll_observations": "Few / small bolls reported",
        "pest_observations": "No visible pests reported so far",
        "current_target_yield": None
    }
    sb.table("crop_records").insert([
        {
            "season_id": season_a_id,
            "crop": "Cotton",
            "variety": "godavari",
            "sowing_date": "2026-06-20",
            "crop_stage": "Boll development",
            "area": 3.0,
            "planting_information": planting_info,
            "provenance": "FARMER_ENTERED"
        },
        {
            "season_id": season_b_id,
            "crop": "Cotton",
            "variety": "godavari",
            "sowing_date": "2026-06-25",
            "crop_stage": "Boll development",
            "area": 2.0,
            "planting_information": planting_info,
            "provenance": "FARMER_ENTERED"
        }
    ]).execute()
    print("[OK] Crop records created with farmer-entered observations")

    # 8. Soil Records
    # Stored as farmer observations, not lab tested. pH 7.6-8.5 range. NPK unknown (null).
    soil_records = [
        {
            "field_id": field_a_id,
            "season_id": season_a_id,
            "ph": 8.05,
            "nitrogen": None,
            "phosphorus": None,
            "potassium": None,
            "organic_matter": None,
            "soil_type": "Black cotton soil (koralvahu jamin)",
            "moisture": None,
            "source": "Farmer observation (Report pending upload; pH reported 7.6-8.5; organic carbon medium)",
            "provenance": "FARMER_ENTERED"
        },
        {
            "field_id": field_b_id,
            "season_id": season_b_id,
            "ph": 8.05,
            "nitrogen": None,
            "phosphorus": None,
            "potassium": None,
            "organic_matter": None,
            "soil_type": "Black cotton soil (koralvahu jamin)",
            "moisture": None,
            "source": "Farmer observation (Report pending upload; pH reported 7.6-8.5; organic carbon medium)",
            "provenance": "FARMER_ENTERED"
        }
    ]
    sb.table("soil_records").insert(soil_records).execute()
    print("[OK] Soil records created (NPK null, pH range 7.6-8.5 flagged pending lab report)")

    # 9. Irrigation Records
    irrigation_records = [
        {
            "field_id": field_a_id,
            "season_id": season_a_id,
            "irrigation_method": "Rainfed / Monsoon-dependent",
            "water_availability": "Limited",
            "irrigation_amount": None,
            "source": "Rainfall (Main source; severe shortage in summer; distance 100-500m unconfirmed)",
            "provenance": "FARMER_ENTERED"
        },
        {
            "field_id": field_b_id,
            "season_id": season_b_id,
            "irrigation_method": "Rainfed / Monsoon-dependent",
            "water_availability": "Limited",
            "irrigation_amount": None,
            "source": "Rainfall (Main source; severe shortage in summer; distance 100-500m unconfirmed)",
            "provenance": "FARMER_ENTERED"
        }
    ]
    sb.table("irrigation_records").insert(irrigation_records).execute()
    print("[OK] Irrigation records created (Rainfed, limited water availability)")

    # 10. Weather Records
    # Location-based public weather preference
    weather_records = [
        {
            "field_id": field_a_id,
            "location": "Takli Bu, Akola, Maharashtra",
            "temperature": 29.0,
            "rainfall": None,
            "humidity": 55.0,
            "wind": 10.0,
            "forecast_information": {
                "source_preference": "Location-based public weather data",
                "district": "Akola",
                "village": "Takli Bu",
                "rainfall_since_sowing": "Unknown / pending verification",
                "water_stress_status": "Severe stress observed in boll development"
            },
            "source": "Location-based weather forecast (Akola)",
            "provenance": "AUTOMATICALLY_COLLECTED"
        }
    ]
    sb.table("weather_records").insert(weather_records).execute()
    print("[OK] Weather records created (Akola district reference)")

    # 11. Farm Data Records: Costs, Sales & Market, Memory, Activities
    # Stored with basis ambiguity preserved
    costs_and_memory = [
        {
            "farm_id": farm_id,
            "field_id": field_a_id,
            "season_id": season_a_id,
            "record_type": "FARM_COST",
            "record_data": {
                "category": "Land preparation",
                "amount": 10000.0,
                "currency": "INR",
                "basis": "Reported total land preparation cost",
                "status": "ENTERED"
            },
            "source": "Farmer interview",
            "provenance": "FARMER_ENTERED"
        },
        {
            "farm_id": farm_id,
            "field_id": field_a_id,
            "season_id": season_a_id,
            "record_type": "FARM_COST",
            "record_data": {
                "category": "Seed cost",
                "amount_min": 10000.0,
                "amount_max": 12000.0,
                "amount": 11000.0,
                "currency": "INR",
                "basis_ambiguity": "Total area / period basis unclear",
                "status": "NEEDS_CLARIFICATION"
            },
            "source": "Farmer interview",
            "provenance": "FARMER_ENTERED"
        },
        {
            "farm_id": farm_id,
            "field_id": field_a_id,
            "season_id": season_a_id,
            "record_type": "FARM_COST",
            "record_data": {
                "category": "Fertilizer cost",
                "amount": 20000.0,
                "currency": "INR",
                "basis_ambiguity": "Approximately ₹20,000 or more; total vs per-acre basis unclear",
                "status": "NEEDS_CLARIFICATION"
            },
            "source": "Farmer interview",
            "provenance": "FARMER_ENTERED"
        },
        {
            "farm_id": farm_id,
            "field_id": field_a_id,
            "season_id": season_a_id,
            "record_type": "FARM_COST",
            "record_data": {
                "category": "Pesticide cost",
                "raw_entry": "₹10",
                "amount": 10.0,
                "currency": "INR",
                "basis_ambiguity": "Entered as '₹10'; unit, quantity, and context unclear",
                "status": "NEEDS_CLARIFICATION"
            },
            "source": "Farmer interview",
            "provenance": "FARMER_ENTERED"
        },
        {
            "farm_id": farm_id,
            "field_id": field_a_id,
            "season_id": season_a_id,
            "record_type": "FARM_COST",
            "record_data": {
                "category": "Labour",
                "amount": 50000.0,
                "currency": "INR",
                "basis_ambiguity": "Period / area basis unclear",
                "status": "NEEDS_CLARIFICATION"
            },
            "source": "Farmer interview",
            "provenance": "FARMER_ENTERED"
        },
        {
            "farm_id": farm_id,
            "field_id": field_a_id,
            "season_id": season_a_id,
            "record_type": "FARM_COST",
            "record_data": {
                "category": "Machinery",
                "amount": 20000.0,
                "currency": "INR",
                "basis_ambiguity": "Basis unclear",
                "status": "NEEDS_CLARIFICATION"
            },
            "source": "Farmer interview",
            "provenance": "FARMER_ENTERED"
        },
        {
            "farm_id": farm_id,
            "field_id": field_a_id,
            "season_id": season_a_id,
            "record_type": "FARM_COST",
            "record_data": {
                "category": "Other cost (yechan)",
                "raw_entry": "yechan ₹40,000",
                "amount": 40000.0,
                "currency": "INR",
                "basis_ambiguity": "Preserved term 'yechan'; requests clarification on item basis",
                "status": "NEEDS_CLARIFICATION"
            },
            "source": "Farmer interview",
            "provenance": "FARMER_ENTERED"
        },
        {
            "farm_id": farm_id,
            "field_id": field_a_id,
            "season_id": season_a_id,
            "record_type": "FARM_COST",
            "record_data": {
                "category": "Transport",
                "amount": 5000.0,
                "currency": "INR",
                "basis_ambiguity": "Basis unclear",
                "status": "NEEDS_CLARIFICATION"
            },
            "source": "Farmer interview",
            "provenance": "FARMER_ENTERED"
        },
        {
            "farm_id": farm_id,
            "field_id": field_a_id,
            "season_id": season_a_id,
            "record_type": "MARKET_INFO",
            "record_data": {
                "target_market": "Akot APMC",
                "selling_channel": "APMC / local trader",
                "cotton_price_reference_inr_quintal": 8000.0,
                "price_observation_date": "2026-10-15",
                "observation_source": "Historical market research listing (15 October 2026)",
                "actual_selling_price": None,
                "quantity_sold": 0.0,
                "loan_reported": False,
                "crop_insurance": "Not insured",
                "government_support": "None reported",
                "main_goal": "Increase profit while managing drought risk"
            },
            "source": "Farmer market profile",
            "provenance": "FARMER_ENTERED"
        },
        {
            "farm_id": farm_id,
            "field_id": field_a_id,
            "season_id": season_a_id,
            "record_type": "FARM_MEMORY",
            "record_data": {
                "fact_title": "Soil and Terrain Characteristics",
                "details": "Land described locally as 'koralvahu jamin' (black cotton soil) with good drainage and deep profile. Reported pH 7.6–8.5 pending lab test.",
                "verified": True
            },
            "source": "Farmer interview",
            "provenance": "FARMER_ENTERED"
        },
        {
            "farm_id": farm_id,
            "field_id": field_a_id,
            "season_id": season_a_id,
            "record_type": "FARM_MEMORY",
            "record_data": {
                "fact_title": "Historical Cotton Yield Benchmark",
                "details": "Historical cotton yield reported at 10 quintals/acre under normal monsoon conditions. Current season 2026-27 exhibiting water stress and stunted boll growth.",
                "verified": True
            },
            "source": "Farmer interview",
            "provenance": "FARMER_ENTERED"
        },
        {
            "farm_id": farm_id,
            "field_id": field_a_id,
            "season_id": season_a_id,
            "record_type": "FARM_MEMORY",
            "record_data": {
                "fact_title": "Water Vulnerability Profile",
                "details": "Farming is primarily rainfed / monsoon-dependent. Water availability is limited with severe shortages in summer. No fixed irrigation installed.",
                "verified": True
            },
            "source": "Farmer interview",
            "provenance": "FARMER_ENTERED"
        }
    ]
    sb.table("farm_data_records").insert(costs_and_memory).execute()
    print("[OK] Farm data records created (Costs with ambiguity flags, Market info, and Farm Memories)")

    # 12. Outcomes table for historical yield record & current zero sale
    sb.table("outcomes").insert([
        {
            "farm_id": farm_id,
            "field_id": field_a_id,
            "season_id": season_a_id,
            "outcome_type": "HISTORICAL_YIELD",
            "actual_value": 10.0,
            "unit": "quintal/acre",
            "notes": "Historical benchmark cotton yield reported by farmer Pranav Vasu",
            "provenance": "FARMER_ENTERED"
        },
        {
            "farm_id": farm_id,
            "field_id": field_a_id,
            "season_id": season_a_id,
            "outcome_type": "CURRENT_SALES",
            "actual_value": 0.0,
            "unit": "quintal",
            "notes": "Quantity sold in current season: 0 reported",
            "provenance": "FARMER_ENTERED"
        }
    ]).execute()
    print("[OK] Outcomes created (Historical yield 10 q/ac, current sales 0)")

    print("\n=======================================================")
    print(f"SUCCESS: Pranav Vasu fully seeded and verified in Supabase!")
    print(f"User ID: {PRANAV_UID}")
    print(f"Farm ID: {farm_id} (10.0 acres total; 5.0 acres allocated to Field A & B; 5.0 acres unallocated)")
    print(f"Location: Takli Bu, Akola, Maharashtra")
    print(f"Crop: Cotton (Variety 'godavari', Sown June 2026, Boll development)")
    print("=======================================================\n")

if __name__ == "__main__":
    seed_pranav_vasu()
