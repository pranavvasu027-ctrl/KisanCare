import json
import os
import pandas as pd

DOCS_DIR = r"C:\Users\prana\OneDrive\Desktop\Projects\KISANcare\kisan-care\docs\cost_profit"
METADATA_DIR = r"C:\Users\prana\OneDrive\Desktop\Projects\KISANcare\kisan-care\metadata"

def document_phase6():
    os.makedirs(DOCS_DIR, exist_ok=True)
    os.makedirs(METADATA_DIR, exist_ok=True)
    
    # 1. Crop Compatibility CSV
    v1_crops = ["Rice", "Wheat", "Maize", "Soybean", "Cotton", "Sugarcane", "Chickpea", "Pigeon Pea", "Groundnut", "Sorghum", "Pearl Millet", "Green Gram", "Black Gram", "Mustard", "Onion", "Potato", "Tomato", "Banana", "Mango", "Grapes"]
    
    crop_data = []
    for crop in v1_crops:
        crop_data.append({
            "crop": crop,
            "cost_model": "SUPPORTED" if crop in ["Rice", "Wheat", "Maize", "Soybean", "Cotton", "Sugarcane", "Chickpea", "Groundnut", "Sorghum", "Pearl Millet", "Onion", "Tomato"] else "UNSUPPORTED",
            "yield_model": "UNKNOWN (Model Not Found)",
            "market_model": "UNKNOWN (Model Not Found)",
            "economic_engine": "SUPPORTED (Agnostic)",
            "integration_status": "UNSUPPORTED",
            "notes": "Missing Yield & Market models."
        })
    pd.DataFrame(crop_data).to_csv(os.path.join(DOCS_DIR, "phase6_crop_compatibility.csv"), index=False)
    
    # 2. Input Compatibility CSV
    input_data = [
        {"field": "State", "cost_model": "Required", "yield_model": "Unknown", "market_model": "Unknown", "economic_engine": "Not Required", "datatype": "str", "unit": "N/A", "required": "Yes", "transformation_required": "Unknown", "notes": ""},
        {"field": "Crop", "cost_model": "Required", "yield_model": "Unknown", "market_model": "Unknown", "economic_engine": "Not Required", "datatype": "str", "unit": "N/A", "required": "Yes", "transformation_required": "Unknown", "notes": ""},
        {"field": "Farm_Area_Hectares", "cost_model": "Required", "yield_model": "Unknown", "market_model": "Unknown", "economic_engine": "Required", "datatype": "float", "unit": "hectares", "required": "Yes", "transformation_required": "Unknown", "notes": ""}
    ]
    pd.DataFrame(input_data).to_csv(os.path.join(DOCS_DIR, "phase6_input_compatibility.csv"), index=False)
    
    # 3. Metadata JSON
    metadata = {
        "status": "MODEL_NOT_FOUND",
        "yield_model_found": False,
        "yield_artifact_path": None,
        "market_model_found": False,
        "market_artifact_path": None,
        "cost_model_compatibility": "VALIDATED",
        "integration_risks": [
            {"risk": "Missing Models", "severity": "BLOCKER", "description": "Yield and Market models do not exist in the repository."}
        ],
        "highest_priority_blocker": "No trained Yield or Market artifacts found."
    }
    with open(os.path.join(METADATA_DIR, "model6_phase6_integration_audit.json"), "w") as f:
        json.dump(metadata, f, indent=4)
        
    # 4. Markdown Report
    md = """# Phase 6 — Yield & Market Model Integration Audit

## 1. Repository Discovery Results
A comprehensive search was conducted across the `kisan-care` repository for any existing Yield or Market Price models.
* Found directories: `models/yield_prediction`, `models/market`, `ml/yield_prediction`, `ml/price_prediction`.
* **Findings:** All of these directories are completely **empty**. There are no model artifacts, inference scripts, or schemas for Yield or Market Prediction in this repository.

## 2. Yield Model Audit
* **Artifact Path:** N/A (Not Found)
* **Input/Output Schema:** UNKNOWN
* **Unit:** UNKNOWN

## 3. Market Model Audit
* **Artifact Path:** N/A (Not Found)
* **Input/Output Schema:** UNKNOWN
* **Unit:** UNKNOWN
* **Forecast Horizon:** UNKNOWN

## 4. Cost Model & Economic Engine Compatibility
* Cost Model: `models/model6_cost_profit/artifacts/cost_model.joblib` (VALIDATED)
* Economic Engine: `models/model6_cost_profit/economic_engine/engine.py` (VALIDATED)
* Unit Compatibility: The Economic Engine is fully prepared to handle `tonnes/hectare` and `INR/tonne` and dynamically convert from quintals if specified. However, the upstream models are absent.

## 5. Integration Risks
| Risk | Severity | Description |
|---|---|---|
| **Missing Dependencies** | **BLOCKER** | Yield and Market models do not physically exist yet. |
| **Unknown Schemas** | **BLOCKER** | Cannot establish a data contract without knowing what inputs the future models will require. |

## 6. Recommended Integration Architecture
Once the Yield and Market models are developed, the API should orchestrate them sequentially:
1. `Farm Inputs` -> **Yield Model** -> `Predicted Yield (t/ha)`
2. `Farm Inputs` -> **Cost Model** -> `Predicted Total Cost (INR)`
3. `Farm Inputs` + `Current Date` -> **Market Model** -> `Predicted Market Price (INR/t)`
4. `Predicted Yield` + `Predicted Cost` + `Predicted Market Price` + `Farm Area` -> **Economic Engine** -> `Profit / ROI / Status`

## 7. Final Status
**MODEL_NOT_FOUND**
"""
    with open(os.path.join(DOCS_DIR, "phase6_model_integration_audit.md"), "w", encoding="utf-8") as f:
        f.write(md)
        
    print("Phase 6 Docs Created.")

if __name__ == "__main__":
    document_phase6()
