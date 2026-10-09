
# KISANcare Dataset Audit Report

## 1-8. Data Quality Statistics
* **Dataset location:** `dataset/mandi_prices.csv`
* **Rows × columns:** 142676 × 11
* **Date range:** 2024-07-01 to 2026-07-01
* **Number of commodities:** 117
* **Number of markets:** 45
* **Duplicates:** 22 exact duplicate rows
* **Invalid/Zero Prices:** 0 records with Modal_Price <= 0

**Missing Values:**
{'Arrival_Date': 0, 'Commodity': 0, 'Commodity_Code': 0, 'District': 0, 'Grade': 0, 'Market': 0, 'Max_Price': 0, 'Min_Price': 0, 'Modal_Price': 0, 'State': 0, 'Variety': 0}

## 9-11. Recommended V1 Crops & Markets
| Crop | Best Markets | Records | Date Range | Data Quality | Suitable for Forecasting? |
|---|---|---|---|---|---|
| Cabbage | Pune(Manjri) | 450 | 2024-07-01 to 2025-11-03 | 8.4% missing days | Yes |
| Cucumbar(Kheera) | Pune(Manjri) | 449 | 2024-07-01 to 2025-11-03 | 8.6% missing days | Yes |
| Cauliflower | Pune(Manjri) | 451 | 2024-07-01 to 2025-11-03 | 8.1% missing days | Yes |
| Onion | Pune(Pimpri) | 458 | 2024-07-02 to 2025-11-04 | 6.9% missing days | Yes |
| Brinjal | Pune(Manjri) | 449 | 2024-07-01 to 2025-11-03 | 8.6% missing days | Yes |
| Coriander(Leaves) | Pune(Pimpri) | 468 | 2024-07-02 to 2025-11-04 | 4.9% missing days | Yes |
| Bhindi(Ladies Finger) | Pune(Manjri) | 452 | 2024-07-01 to 2025-11-03 | 7.9% missing days | Yes |
| Bottle gourd | Pune(Manjri) | 446 | 2024-07-01 to 2025-11-03 | 9.2% missing days | Yes |
| Green Chilli | Pune(Manjri) | 441 | 2024-07-01 to 2025-11-03 | 10.2% missing days | Yes |
| Tomato | Pune(Pimpri) | 466 | 2024-07-02 to 2025-11-04 | 5.3% missing days | Yes |

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
