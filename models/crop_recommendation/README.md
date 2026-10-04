# Crop Recommendation Model Contract

## Overview
This document defines the input and output contract for the initial **Crop Recommendation** model (Model 1 in the KisanCare pipeline).

## Important Note
This contract represents the initial version of the model. It does not currently support all future KisanCare inputs (e.g., specific location, water availability, season, and other farm-specific variables). These will be incorporated in future iterations only when the selected dataset and model design support them.

## Inputs
The initial candidate inputs for the model are:
* **Nitrogen (N)**: Soil nitrogen content
* **Phosphorus (P)**: Soil phosphorus content
* **Potassium (K)**: Soil potassium content
* **pH**: Soil pH level
* **Temperature**: Average temperature (°C)
* **Humidity**: Average relative humidity (%)
* **Rainfall**: Average rainfall (mm)

## Outputs
The model is expected to predict:
* **Recommended crop**: The most suitable crop for the given conditions.
* **Top alternative crops**: Ranked alternative crops suitable for the conditions.
* **Prediction confidence/probability**: A metric indicating the model's certainty about its recommendations.
