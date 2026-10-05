import requests
import os
import urllib3

urllib3.disable_warnings()

url = "https://desagri.gov.in/wp-content/uploads/2024/09/Agricultural-Statistics-at-a-Glance-2023.pdf"
output_path = r"C:\Users\prana\OneDrive\Desktop\Projects\KISANcare\kisan-care\data\model6_cost_profit\external\source_1_des_cost\raw\official\Agri_Stat_At_A_Glance_2023.pdf"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

print("Downloading PDF...")
try:
    response = requests.get(url, headers=headers, verify=False, timeout=30)
    response.raise_for_status()
    with open(output_path, "wb") as f:
        f.write(response.content)
    print(f"Downloaded successfully: {os.path.getsize(output_path)} bytes")
except Exception as e:
    print(f"Failed to download: {e}")
