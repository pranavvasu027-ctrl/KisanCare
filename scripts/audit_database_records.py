"""Inspect and display current Supabase records for Pranav Vasu."""
import os
import json
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
sb = create_client(url, key)

PRANAV_UID = '9c851059-4259-4cd3-95c7-9ab287f60710'

def audit():
    print("=== PROFILES ===")
    prof = sb.table('profiles').select('*').eq('user_id', PRANAV_UID).execute()
    print(json.dumps(prof.data, indent=2))

    print("\n=== FARMS ===")
    farms = sb.table('farms').select('*').eq('user_id', PRANAV_UID).execute()
    print(json.dumps(farms.data, indent=2))

    if farms.data:
        farm_id = farms.data[0]['id']
        print("\n=== FIELDS ===")
        fields = sb.table('fields').select('*').eq('farm_id', farm_id).execute()
        print(json.dumps(fields.data, indent=2))

        for fld in fields.data:
            fid = fld['id']
            fname = fld['field_name']
            print(f"\n=== SEASONS FOR {fname} ({fid}) ===")
            seasons = sb.table('seasons').select('*').eq('field_id', fid).execute()
            print(json.dumps(seasons.data, indent=2))

            print(f"\n=== CROP RECORDS FOR {fname} ===")
            crops = sb.table('crop_records').select('*').eq('field_id', fid).execute()
            print(json.dumps(crops.data, indent=2))

            print(f"\n=== SOIL RECORDS FOR {fname} ===")
            soil = sb.table('soil_records').select('*').eq('field_id', fid).execute()
            print(json.dumps(soil.data, indent=2))

            print(f"\n=== IRRIGATION RECORDS FOR {fname} ===")
            irrig = sb.table('irrigation_records').select('*').eq('field_id', fid).execute()
            print(json.dumps(irrig.data, indent=2))

            print(f"\n=== WEATHER RECORDS FOR {fname} ===")
            weather = sb.table('weather_records').select('*').eq('field_id', fid).execute()
            print(json.dumps(weather.data, indent=2))

        print("\n=== FARM DATA RECORDS ===")
        fdr = sb.table('farm_data_records').select('*').eq('farm_id', farm_id).execute()
        print(f"Total count: {len(fdr.data)}")
        for r in fdr.data:
            print(f"  [{r.get('record_type')}] {r.get('record_data')}")

        print("\n=== OUTCOMES ===")
        outcomes = sb.table('outcomes').select('*').eq('farm_id', farm_id).execute()
        print(json.dumps(outcomes.data, indent=2))

if __name__ == '__main__':
    audit()
