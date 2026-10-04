import pandas as pd
import json
import difflib

def resolve_districts():
    # Load mapping
    df = pd.read_csv("data/model1/external/metadata/district_mapping.csv")
    
    # Load geojson to get all boundary districts
    with open("data/model1/external/raw/boundaries/india_districts.geojson", 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    boundary_districts = []
    for feat in data['features']:
        props = feat.get('properties', {})
        name = props.get('NAME_2') or props.get('dtname') or props.get('district')
        if name:
            boundary_districts.append(name)
    boundary_districts = list(set(boundary_districts))
    
    # Manual overrides for notorious Indian district historical names
    manual_overrides = {
        'VISAKHAPATANAM': 'Visakhapatnam',
        'KADAPA': 'Y.S.R.',
        'SPSR NELLORE': 'Sri Potti Sriramulu Nellore',
        'NICOBARS': 'Nicobar',
        'NORTH AND MIDDLE ANDAMAN': 'North & Middle Andaman',
        'SOUTH ANDAMANS': 'South Andaman',
        # Added based on common APY names
        'PASHCHIM CHAMPARAN': 'West Champaran',
        'PURBI CHAMPARAN': 'East Champaran',
        'KAMRUP METRO': 'Kamrup Metropolitan',
        'DIMA HASAO': 'North Cachar Hills',
        'KAIMUR (BHABUA)': 'Kaimur',
        'BOMDILA': 'West Kameng',
    }
    
    for idx, row in df.iterrows():
        if row['Match_Status'] == 'UNMATCHED':
            apy = row['APY_District']
            # Try manual override
            if apy in manual_overrides and manual_overrides[apy] in boundary_districts:
                df.at[idx, 'Boundary_District'] = manual_overrides[apy]
                df.at[idx, 'Match_Status'] = 'MANUAL_RESOLUTION'
                df.at[idx, 'Notes'] = 'Historical/Alias map'
                continue
            
            # Try fuzzy matching
            matches = difflib.get_close_matches(apy, boundary_districts, n=1, cutoff=0.75)
            if matches:
                df.at[idx, 'Boundary_District'] = matches[0]
                df.at[idx, 'Match_Status'] = 'FUZZY_RESOLUTION'
                df.at[idx, 'Notes'] = 'difflib cutoff >= 0.75'
                
    unmatched_left = df[df['Match_Status'] == 'UNMATCHED'].shape[0]
    print(f"Districts left unmatched: {unmatched_left}")
    
    df.to_csv("data/model1/external/metadata/district_mapping_final.csv", index=False)

if __name__ == "__main__":
    resolve_districts()
