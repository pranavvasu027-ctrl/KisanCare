# Repository Technical Audit

## 1. shreyzo/Crop-yield-and-profitability-prediction
* **Description**: A repository containing two CSV files: one large file for crop production and one tiny file for crop costs. Includes classification models (KNN, Decision Trees, etc.) for profit binary classification.
* **Datasets**:
  * `crop_production.csv` (246,091 rows) - Contains Area and Production for various states from 1997-2015.
  * `datafile.csv` (49 rows) - Contains Cost of Cultivation and Support Price for 10 crops across 13 states.
* **Code Quality**: Poor. The training code manually calculates a profit boolean label from inputs, then trains a KNN using those very same cost inputs. This is massive data leakage.
* **Suitability**: ⭐⭐ Poor. The cost dataset is incredibly small (49 rows). The main dataset is just standard yield data without financial metrics.

## 2. Samarth-2003-web/Crop-profit-prediction
* **Description**: A Flask web application predicting crop yield, prices, and calculating profit.
* **Datasets**:
  * `Crop_yield_enriched.csv` (19,171 rows) - Contains soil, weather, and yield data. **Note**: District data is strictly limited to Karnataka.
  * `crop_price_trends_2015_2025.csv` (1,320 rows) - Synthetic data generated mathematically using a base price and a fixed 6% annual inflation rate.
* **Code Quality**: Excellent architecture (Hybrid approach). The ML models independently predict yield and price, while profit is derived deterministically from user-input costs.
* **Suitability**: ⭐⭐⭐ Usable for code reference. The dataset is rejected because it only covers Karnataka and uses artificially generated prices.

## 3. Kusuma-97/Agriculture_DA_VIOS
* **Description**: Comprehensive analysis of seasonal agriculture performance across 4000 farm records.
* **Datasets**:
  * `seasonal_agriculture_performance_dataset.csv` (4,000 rows) - Contains environmental factors, soil nutrients, irrigation, costs, revenues, and yields.
* **Code Quality**: Contains Jupyter notebooks with thorough EDA.
* **Suitability**: ⭐⭐⭐⭐⭐ Excellent. This dataset is internally consistent. The mathematical relationships (`Production = Yield * Area`, `Revenue = Production * Price`, `Profit = Revenue - Cost`) hold exactly true. It covers 8 states including Maharashtra (512 records) and 8 major crops.

## 4. mithil-exe/agriculture-crop-dataset
* **Description**: A modified version of a standard cultivation cost dataset.
* **Datasets**:
  * `agriculture-crop-dataset.csv` (130 rows) - Contains Costs per hectare and Cost per quintal.
* **Code Quality**: No modeling code provided.
* **Suitability**: ⭐ Reject as primary. The dataset is far too small (130 rows) and completely lacks a Yield column (despite README claims), making it impossible to calculate Revenue or Profit directly.
