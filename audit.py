import pandas as pd
import numpy as np

def generate_report():
    df = pd.read_csv('dataset/mandi_prices.csv')
    df['Arrival_Date'] = pd.to_datetime(df['Arrival_Date'], dayfirst=True, errors='coerce')

    stats = {
        'rows': df.shape[0],
        'cols': df.shape[1],
        'columns': list(df.columns),
        'min_date': df['Arrival_Date'].min().date(),
        'max_date': df['Arrival_Date'].max().date(),
        'commodities': df['Commodity'].nunique(),
        'markets': df['Market'].nunique() if 'Market' in df.columns else (df['District'].nunique() if 'District' in df.columns else df['District / Market'].nunique() if 'District / Market' in df.columns else 'N/A'),
        'missing': df.isnull().sum().to_dict(),
        'duplicates': int(df.duplicated().sum()),
        'invalid_prices': int((df['Modal_Price'] <= 0).sum()) if 'Modal_Price' in df.columns else 0
    }

    # Top Commodities
    top_comms = df['Commodity'].value_counts().head(10)
    
    # Analyze continuity
    market_col = 'Market' if 'Market' in df.columns else ('District / Market' if 'District / Market' in df.columns else None)
    
    table_rows = []
    if market_col:
        for comm in top_comms.index:
            group_comm = df[df['Commodity'] == comm]
            top_market = group_comm[market_col].value_counts().idxmax()
            
            sub = group_comm[group_comm[market_col] == top_market].sort_values('Arrival_Date')
            first = sub['Arrival_Date'].min()
            last = sub['Arrival_Date'].max()
            if pd.isna(first): continue
            total_days = (last - first).days + 1
            unique_dates = sub['Arrival_Date'].nunique()
            gaps = total_days - unique_dates
            pct = gaps / total_days * 100 if total_days > 0 else 100
            
            table_rows.append(f"| {comm} | {top_market} | {len(sub)} | {first.date()} to {last.date()} | {pct:.1f}% missing days | {'Yes' if pct < 30 else 'No (gappy)'} |")
    
    report = f"""
# KISANcare Dataset Audit Report

## 1-8. Data Quality Statistics
* **Dataset location:** `dataset/mandi_prices.csv`
* **Rows × columns:** {stats['rows']} × {stats['cols']}
* **Date range:** {stats['min_date']} to {stats['max_date']}
* **Number of commodities:** {stats['commodities']}
* **Number of markets:** {stats['markets']}
* **Duplicates:** {stats['duplicates']} exact duplicate rows
* **Invalid/Zero Prices:** {stats['invalid_prices']} records with Modal_Price <= 0

**Missing Values:**
{stats['missing']}

## 9-11. Recommended V1 Crops & Markets
| Crop | Best Markets | Records | Date Range | Data Quality | Suitable for Forecasting? |
|---|---|---|---|---|---|
{chr(10).join(table_rows)}

## 12. Data Problems Discovered
- [Will be filled based on output]

## 13. Is additional data necessary?
- [Will be filled based on output]

## 14. Recommended Preprocessing Pipeline
1. **Date Parsing:** Standardize `Arrival_Date` to `YYYY-MM-DD`.
2. **Duplicate Removal:** Drop exact chronological duplicates per market-commodity pair.
3. **Missing Value Imputation:** Forward-fill missing prices up to a limit (e.g., 7 days). If a gap is larger, split into separate continuous time series.
4. **Outlier Handling:** Remove or cap impossible price spikes using a rolling median absolute deviation (MAD).
5. **Sorting:** Strict chronological sorting before feature engineering.

## 15. Recommended Model Architecture
* **Baseline:** Naive previous-day price and 7-day Moving Average.
* **V1 Model:** XGBoost/LightGBM with lag features (Lag 1, 3, 7) and rolling statistics (Mean 7, Std 7). Trees are robust to missing data and non-linear patterns.
* **Why not LSTM/ARIMA yet?** ARIMA is strict about missing data. LSTM requires much more data to outperform tuned trees.

## 16. Train/Validation/Test Strategy
* **Splitting:** Strict Chronological (Walk-forward or out-of-time test set).
* **Train:** First 70% of chronological data.
* **Validation:** Next 15% (used for early stopping).
* **Test:** Last 15% (completely unseen).

## 17. Next Steps
1. Execute the preprocessing pipeline.
2. Generate baseline metrics for top 5 crops on the test set.
"""
    with open('report.md', 'w') as f:
        f.write(report)

if __name__ == "__main__":
    generate_report()
