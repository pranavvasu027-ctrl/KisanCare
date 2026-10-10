# KISANcare Current State Audit

## Executive Summary
This document summarizes the current technical state of the KISANcare platform, detailing the nature of its 8 agricultural capabilities, verified functionalities, and areas needing remediation.

## Eight Capabilities Audit

### A. Crop Recommendation
* **Implementation Method**: Trained ML Model (Scikit-Learn).
* **Required Input Data**: District, Season, Water Availability.
* **Logic/Format**: Uses `crop_recommendation_mvp_v2.pkl`. Outputs top crops based on probability.
* **Status**: **PASS**. Verified by endpoint execution.

### B. Market Price Forecasting
* **Implementation Method**: Trained ML Model (XGBoost).
* **Required Input Data**: Crop, Market, Date. Requires trailing 14-day history in `mandi_prices.csv`.
* **Logic/Format**: Predicts 7-day future price based on lag/rolling means. 14-day forecast disabled.
* **Status**: **PASS (7-day)**. 14-day is accurately disabled. Requires live data ingestion to remain functional.

### C. Crop Disease Detection
* **Implementation Method**: Rule-Based text matching.
* **Required Input Data**: List of text symptoms.
* **Logic/Format**: Matches hardcoded strings (e.g., "yellow leaves") to diseases. DOES NOT process images.
* **Status**: **NOT TESTED** for image upload (since it does not exist). Verified as a text-only heuristic.

### D. Pest Detection
* **Implementation Method**: Rule-Based text matching.
* **Required Input Data**: List of text symptoms.
* **Logic/Format**: Matches hardcoded strings. DOES NOT process images.
* **Status**: **PASS (as rule-based)**, but misleading if presented as Computer Vision.

### E. Soil Nutrient Assessment
* **Implementation Method**: Rule-Based bounds checking.
* **Required Input Data**: N, P, K, pH.
* **Logic/Format**: Simple `<` or `>` thresholds.
* **Status**: **PASS (as rule-based)**.

### F. Crop Yield Prediction
* **Implementation Method**: Rule-Based math heuristic.
* **Required Input Data**: Crop, Area, Soil Score, Weather Score.
* **Logic/Format**: Base yield * Area * ((Soil + Weather) / 200). Explicitly rejects unknown crops.
* **Status**: **PASS (as heuristic)**. Not a trained ML model.

### G. Weather Risk Assessment
* **Implementation Method**: Rule-Based.
* **Required Input Data**: Temp, Humidity, Rainfall Forecast.
* **Logic/Format**: Thresholds for heat stress, frost, fungus, flooding.
* **Status**: **PASS (as rule-based)**.

### H. Irrigation Recommendation
* **Implementation Method**: Rule-Based.
* **Required Input Data**: Crop, Soil Moisture, Days Since Rain.
* **Logic/Format**: Recommends fixed volumes (2000L or 5000L) if moisture < 30% or (<50% and >7 days no rain).
* **Status**: **PASS (as rule-based)**. Safely prevents overwatering.
