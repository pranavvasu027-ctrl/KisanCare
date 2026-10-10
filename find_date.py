import pandas as pd
df = pd.read_csv('dataset/mandi_prices.csv')
df['Arrival_Date'] = pd.to_datetime(df['Arrival_Date'], format='%d/%m/%Y')
onion = df[(df['Commodity'].str.lower() == 'onion') & (df['Market'].str.lower() == 'pune(pimpri)')]
onion = onion.sort_values('Arrival_Date')
print(onion['Arrival_Date'].tail(20))
