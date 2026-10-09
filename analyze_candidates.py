import pandas as pd
import numpy as np

# Load Data
df = pd.read_csv('data/mandi_prices.csv')
df['Arrival_Date'] = pd.to_datetime(df['Arrival_Date'], dayfirst=True)

# Calculate global dataset limits for freshness
global_max_date = df['Arrival_Date'].max()

def analyze_series(sub, is_crop=False):
    total_records = len(sub)
    earliest = sub['Arrival_Date'].min()
    latest = sub['Arrival_Date'].max()
    span = (latest - earliest).days + 1 if pd.notnull(latest) else 0
    unique_dates = sub['Arrival_Date'].nunique()
    
    unique_mandis = sub['Market'].nunique() if is_crop else 1
    
    missing_pct = 100 * (1 - (unique_dates / span)) if span > 0 else 100
    continuity = (unique_dates / span) * 100 if span > 0 else 0
    
    # Recent data (last 30, 60, 90 days from global_max_date)
    recent_30 = len(sub[sub['Arrival_Date'] >= global_max_date - pd.Timedelta(days=30)])
    recent_60 = len(sub[sub['Arrival_Date'] >= global_max_date - pd.Timedelta(days=60)])
    recent_90 = len(sub[sub['Arrival_Date'] >= global_max_date - pd.Timedelta(days=90)])
    
    # Invalid prices
    invalid_price = len(sub[(sub['Modal_Price'] <= 0) | (sub['Modal_Price'].isnull())])
    missing_modal = sub['Modal_Price'].isnull().sum()
    
    # Suitability checks
    # To forecast 14 days, we need at least, say, 180 days of span, decent continuity, and recent data
    suitable_7d = span >= 90 and continuity >= 50 and recent_30 > 0
    suitable_14d = span >= 180 and continuity >= 50 and recent_30 > 0
    
    return {
        'total_records': total_records,
        'earliest': earliest,
        'latest': latest,
        'span_days': span,
        'unique_dates': unique_dates,
        'unique_mandis': unique_mandis,
        'missing_pct': missing_pct,
        'continuity': continuity,
        'recent_30': recent_30,
        'recent_60': recent_60,
        'recent_90': recent_90,
        'invalid_price': invalid_price,
        'missing_modal': missing_modal,
        'suitable_7d': suitable_7d,
        'suitable_14d': suitable_14d
    }

# Analyze Crops
crop_stats = []
for crop, group in df.groupby('Commodity'):
    stats = analyze_series(group, is_crop=True)
    stats['Commodity'] = crop
    crop_stats.append(stats)
crop_df = pd.DataFrame(crop_stats)

# Analyze Crop + Mandi
combo_stats = []
for (crop, market), group in df.groupby(['Commodity', 'Market']):
    stats = analyze_series(group, is_crop=False)
    stats['Commodity'] = crop
    stats['Market'] = market
    
    # Scoring
    score = 0
    
    # DATA QUALITY - 50%
    # Historical depth (10): span > 365 gets 10, linearly scale down
    score += min(10, (stats['span_days'] / 365.0) * 10)
    # Daily continuity (15): continuity / 100 * 15
    score += (stats['continuity'] / 100.0) * 15
    # Sufficient observations (10): unique_dates > 200 gets 10
    score += min(10, (stats['unique_dates'] / 200.0) * 10)
    # Valid prices (10): (1 - invalid_ratio) * 10
    invalid_ratio = stats['invalid_price'] / stats['total_records'] if stats['total_records'] > 0 else 1
    score += (1 - invalid_ratio) * 10
    # Missing-data quality (5): 5 - (missing_pct / 100 * 5)
    score += max(0, 5 - (stats['missing_pct'] / 100.0 * 5))
    
    # FRESHNESS - 25%
    # Recent usable data (15): recent_90 > 45 gets 15
    score += min(15, (stats['recent_90'] / 45.0) * 15)
    # Recent continuity (10): recent_30 > 15 gets 10
    score += min(10, (stats['recent_30'] / 15.0) * 10)
    
    # FARMER IMPORTANCE - 25% (Requires Manual Review)
    stats['Farmer_Importance_Score'] = 'REQUIRES MANUAL REVIEW'
    
    # We will score out of 75 for sorting, then normalize to 100 for display?
    # Or just say the score is out of 75 currently, and user review adds 25.
    stats['Score_Out_Of_75'] = round(score, 2)
    
    combo_stats.append(stats)

combo_df = pd.DataFrame(combo_stats)
combo_df = combo_df.sort_values('Score_Out_Of_75', ascending=False)
combo_df.to_csv('market_crop_mandi_candidates.csv', index=False)

# Get top 15 crops based on max score of their best mandi
crop_max_scores = combo_df.groupby('Commodity')['Score_Out_Of_75'].max().reset_index()
crop_max_scores = crop_max_scores.sort_values('Score_Out_Of_75', ascending=False)
top_15_crops = crop_max_scores.head(15)['Commodity'].tolist()

print("CANDIDATE ANALYSIS COMPLETE\n")
print("TOP 10 CROP + MANDI COMBINATIONS:\n")
display_cols = ['Commodity', 'Market', 'span_days', 'continuity', 'recent_30', 'Score_Out_Of_75', 'Farmer_Importance_Score']
print(combo_df[display_cols].head(10).to_string(index=False))
