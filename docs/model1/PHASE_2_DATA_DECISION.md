# KisanCare Model 1 — PHASE 2 DATA DECISION

## Dataset Selected
**Kaggle Crop Recommendation Dataset (Fallback / Baseline)**
*Note: This is the dataset corresponding to the underlying Model 1 (NPK) of the Sheshank repository.*

## Source
* **Origin:** Kaggle (Atharva Ingle) / Harvestify GitHub Mirror
* **Type:** Open-source synthetic/curated baseline.

## Dataset Dimensions & Features
* **Number of rows:** 2,200
* **Number of features:** 7
* **Feature List:** `N`, `P`, `K`, `temperature`, `humidity`, `ph`, `rainfall`
* **Target:** `label` (Crop name)

## Contextual Features
* **Districts:** NOT AVAILABLE
* **Years:** NOT AVAILABLE
* **Season:** NOT AVAILABLE

## Crop Distribution
* **Total Crops:** 22
* **Crops:** `rice`, `maize`, `chickpea`, `kidneybeans`, `pigeonpeas`, `mothbeans`, `mungbean`, `blackgram`, `lentil`, `pomegranate`, `banana`, `mango`, `grapes`, `watermelon`, `muskmelon`, `apple`, `orange`, `papaya`, `coconut`, `cotton`, `jute`, `coffee`
* **Distribution:** Exactly 100 samples per crop (perfectly balanced).

## Data Quality
* **Missing values:** 0
* **Exact duplicates:** 0

## Preprocessing Performed
1. **Raw Copy Preserved:** The original dataset was saved unmodified.
2. **Numeric Smoothing:** All floating-point features (temperature, humidity, pH, rainfall) were rounded to 2 decimal places. This removes the highly unique, algorithmically generated precision present in the synthetic Kaggle data to make it closer to realistic sensor/test-report precision.
3. **Label Standardization:** All crop labels were stripped of whitespace and converted to lowercase.
4. **Saved as:** `Crop_recommendation_cleaned.csv`

## Rationale for Selection
A direct download of real-world Agricultural Production Yield (APY) data from government sources (like UPAg or data.gov.in) failed or could not be reliably accessed via API within the strict 30-minute limit.

As dictated by the strict fallback protocol, we ceased searching and reverted to the pre-audited baseline dataset from the `Sheshank2609/crop-recommendation-system` architecture. We explicitly avoided the 69,718-row `anant13sharma` dataset due to our earlier finding of severe data leakage and synthetic expansion.

## Limitations
1. **No Geographic/Temporal Context:** The data cannot map a recommendation to a specific district or season.
2. **Synthetic Balancing:** Real agricultural data is highly imbalanced. This dataset is perfectly balanced (100 per class), meaning models trained on it may not reflect real-world prior probabilities.
3. **Interpolated Ranges:** Feature distributions are synthetic, which may result in overly optimistic validation accuracy (~99%) that will fail to generalize to actual field data.

## Classification
**BASELINE DATA** (Not Real Data)
