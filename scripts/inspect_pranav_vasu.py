"""Detailed inspection of Pranav Vasu records in Supabase via REST API."""
import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()
url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
headers = {
    'apikey': key,
    'Authorization': f'Bearer {key}',
    'Content-Type': 'application/json'
}

PRANAV_UID = '9c851059-4259-4cd3-95c7-9ab287f60710'

def get_records(endpoint):
    r = requests.get(f'{url}/rest/v1/{endpoint}', headers=headers)
    if r.status_code != 200:
        print(f"Error {r.status_code} for {endpoint}: {r.text}")
        return []
    return r.json()

def main():
    print("=== PROFILES ===")
    profs = get_records(f"profiles?user_id=eq.{PRANAV_UID}&select=*")
    print(json.dumps(profs, indent=2))

    print("\n=== FARMS ===")
    farms = get_records(f"farms?user_id=eq.{PRANAV_UID}&select=*")
    print(json.dumps(farms, indent=2))

    if farms:
        farm_id = farms[0]['id']
        print("\n=== FIELDS ===")
        fields = get_records(f"fields?farm_id=eq.{farm_id}&select=*")
        print(json.dumps(fields, indent=2))

        for fld in fields:
            fid = fld['id']
            fname = fld['field_name']
            print(f"\n--- Field {fname} ({fid}) ---")

            seasons = get_records(f"seasons?field_id=eq.{fid}&select=*")
            print(f"SEASONS for {fname}:", json.dumps(seasons, indent=2))

            crops = get_records(f"crop_records?field_id=eq.{fid}&select=*")
            print(f"CROP RECORDS for {fname}:", json.dumps(crops, indent=2))

            soil = get_records(f"soil_records?field_id=eq.{fid}&select=*")
            print(f"SOIL for {fname}:", json.dumps(soil, indent=2))

            irrig = get_records(f"irrigation_records?field_id=eq.{fid}&select=*")
            print(f"IRRIGATION for {fname}:", json.dumps(irrig, indent=2))

            weather = get_records(f"weather_records?field_id=eq.{fid}&select=*")
            print(f"WEATHER for {fname}:", json.dumps(weather, indent=2))

        print("\n=== FARM DATA RECORDS (Costs, Memory, Market) ===")
        fdr = get_records(f"farm_data_records?farm_id=eq.{farm_id}&select=*")
        print(f"Total count: {len(fdr)}")
        for r in fdr:
            print(f"  [{r.get('record_type')}] {json.dumps(r.get('record_data'))}")

        print("\n=== OUTCOMES ===")
        outcomes = get_records(f"outcomes?farm_id=eq.{farm_id}&select=*")
        print(json.dumps(outcomes, indent=2))

if __name__ == '__main__':
    main()
