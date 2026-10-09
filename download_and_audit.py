import pandas as pd
import urllib.request
import os

os.makedirs('data', exist_ok=True)
url = "https://raw.githubusercontent.com/tunalikashikar/maharashtra-mandi-price-analysis/main/Data/mandi_prices.csv"
print(f"Downloading {url}...")
urllib.request.urlretrieve(url, 'data/mandi_prices.csv')
print("Downloaded successfully.")

df = pd.read_csv('data/mandi_prices.csv')
print(f"Dataset Shape: {df.shape}")
print(df.head())
