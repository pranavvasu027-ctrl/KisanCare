import pandas as pd

def prepare_data(df, crop, market):
    sub = df[(df['Commodity'] == crop) & (df['Market'] == market)].copy()
    sub['Arrival_Date'] = pd.to_datetime(sub['Arrival_Date'], dayfirst=True)
    sub = sub.sort_values('Arrival_Date')
    
    # Handle multiple varieties per day
    sub = sub.groupby('Arrival_Date')['Modal_Price'].mean().reset_index()
    sub = sub.set_index('Arrival_Date').asfreq('D')
    
    # Impute small gaps (up to 3 days) with forward fill
    sub['Modal_Price'] = sub['Modal_Price'].ffill(limit=3)
    # Impute remaining gaps with a 7-day rolling mean
    sub['Modal_Price'] = sub['Modal_Price'].fillna(sub['Modal_Price'].rolling(7, min_periods=1).mean())
    sub['Modal_Price'] = sub['Modal_Price'].ffill() # catch-all
    
    return sub

def create_features(sub):
    df_feat = sub.copy()
    
    # Target variables (Future) - only created if building training set
    # but we can just let it create NaNs if predicting for today
    df_feat['target_7d'] = df_feat['Modal_Price'].shift(-7)
    df_feat['target_14d'] = df_feat['Modal_Price'].shift(-14)
    
    # Features (Strictly Past/Current)
    df_feat['lag_1'] = df_feat['Modal_Price'].shift(1)
    df_feat['lag_3'] = df_feat['Modal_Price'].shift(3)
    df_feat['lag_7'] = df_feat['Modal_Price'].shift(7)
    df_feat['lag_14'] = df_feat['Modal_Price'].shift(14)
    
    df_feat['rolling_mean_7'] = df_feat['lag_1'].rolling(7).mean()
    df_feat['rolling_mean_14'] = df_feat['lag_1'].rolling(14).mean()
    df_feat['rolling_std_7'] = df_feat['lag_1'].rolling(7).std()
    
    df_feat['day_of_week'] = df_feat.index.dayofweek
    df_feat['month'] = df_feat.index.month
    
    return df_feat
