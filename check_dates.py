import pandas as pd
df = pd.read_csv('dataset/mandi_prices.csv')
df['Arrival_Date'] = pd.to_datetime(df['Arrival_Date'], format='%d/%m/%Y')
onion_pune = df[(df['Commodity'].str.lower() == 'onion') & (df['Market'].str.lower() == 'pune(pimpri)')]
if len(onion_pune) > 0:
    print("Min date:", onion_pune['Arrival_Date'].min())
    print("Max date:", onion_pune['Arrival_Date'].max())
    print("Total rows:", len(onion_pune))
else:
    print("No data for Onion in Pune(Pimpri)")
