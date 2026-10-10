import os
import requests
import pandas as pd
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

API_KEY = os.environ.get("DATA_GOV_IN_API_KEY")
API_URL = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
DATASET_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "dataset", "mandi_prices.csv"))

def fetch_recent_data():
    if not API_KEY:
        logging.error("Missing DATA_GOV_IN_API_KEY. Cannot fetch real observations.")
        return None
        
    try:
        # Example API call structure for data.gov.in
        params = {
            "api-key": API_KEY,
            "format": "json",
            "limit": 1000
        }
        response = requests.get(API_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if "records" not in data:
            logging.error("Invalid response format from data source.")
            return None
            
        records = data["records"]
        return pd.DataFrame(records)
    except Exception as e:
        logging.error(f"Failed to fetch market data: {e}")
        return None

def ingest_data():
    logging.info("Starting market data ingestion pipeline...")
    
    new_df = fetch_recent_data()
    if new_df is None or new_df.empty:
        logging.warning("No new data fetched. Pipeline aborted to prevent data fabrication.")
        return
        
    # Validation and formatting
    required_cols = ['arrival_date', 'commodity', 'market', 'modal_price', 'state', 'district']
    for col in required_cols:
        if col not in new_df.columns:
            logging.error(f"Missing required column in source data: {col}")
            return
            
    # Rename to match our dataset
    rename_map = {
        'arrival_date': 'Arrival_Date',
        'commodity': 'Commodity',
        'market': 'Market',
        'modal_price': 'Modal_Price',
        'state': 'State',
        'district': 'District'
    }
    new_df = new_df.rename(columns=rename_map)
    
    # Format dates
    new_df['Arrival_Date'] = pd.to_datetime(new_df['Arrival_Date'], errors='coerce').dt.strftime('%d/%m/%Y')
    
    # Filter out invalid prices
    new_df['Modal_Price'] = pd.to_numeric(new_df['Modal_Price'], errors='coerce')
    new_df = new_df.dropna(subset=['Arrival_Date', 'Commodity', 'Market', 'Modal_Price'])
    new_df = new_df[new_df['Modal_Price'] > 0]
    
    # Load existing history
    if os.path.exists(DATASET_PATH):
        history_df = pd.read_csv(DATASET_PATH)
    else:
        logging.error(f"Historical dataset not found at {DATASET_PATH}. Cannot append.")
        return
        
    # Append and handle duplicates (keep latest)
    combined = pd.concat([history_df, new_df], ignore_index=True)
    
    # Deduplicate based on Date, Commodity, Market
    combined = combined.drop_duplicates(subset=['Arrival_Date', 'Commodity', 'Market'], keep='last')
    
    # Save back
    combined.to_csv(DATASET_PATH, index=False)
    logging.info(f"Ingestion complete. Added/updated records. Total dataset size: {len(combined)}")

if __name__ == "__main__":
    ingest_data()
