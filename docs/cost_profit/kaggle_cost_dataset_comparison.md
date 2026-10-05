# KAGGLE VS DES COMPARISON

## KAGGLE: `agricuture-crops-production-in-india/datafile.csv`
* **Provenance**: Uploaded by independent Kaggle user (srinivas1).
* **Granularity**: State/Crop averages.
* **Size**: 49 rows.
* **Variables**: Cost A2+FL (₹/Hectare), Cost C2 (₹/Hectare), Cost C2 (₹/Quintal), Yield.

## OFFICIAL DES / CACP (Source 1)
* **Provenance**: Ministry of Agriculture & Farmers Welfare.
* **Granularity**: State/Crop averages.
* **Size**: Thousands of rows historically (published annually).
* **Variables**: Cost A2, Cost A2+FL, Cost B, Cost C1, Cost C2.

## CONCLUSION
The Kaggle dataset is merely a **tiny 49-row subset** of the official DES aggregate reports. It is not independent data. It does not contain 10,000+ records. It does not contain farm-level variance. It must NOT be merged as new training data to artificially boost row counts.
