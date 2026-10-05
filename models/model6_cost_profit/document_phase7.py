import json
import os

DOCS_DIR = r"C:\Users\prana\OneDrive\Desktop\Projects\KISANcare\kisan-care\docs\cost_profit"
METADATA_DIR = r"C:\Users\prana\OneDrive\Desktop\Projects\KISANcare\kisan-care\metadata"

def document_phase7():
    os.makedirs(DOCS_DIR, exist_ok=True)
    os.makedirs(METADATA_DIR, exist_ok=True)
    
    metadata = {
        "status": "MODELS_NOT_FOUND_LOCALLY",
        "search_locations": [
            "C:\\Users\\prana\\OneDrive\\Desktop\\Projects\\KISANcare\\",
            "C:\\Users\\prana\\Downloads\\"
        ],
        "search_file_types": [
            "*.joblib", "*.pkl", "*.pickle", "*.onnx", "*.h5", "*.keras", "*.pt", "*.pth", "*.cbm"
        ],
        "candidates_found": 0,
        "git_history_findings": "Checked all branches and commits for 'yield', 'market', 'price', and 'model'. No teammate models or deleted ML artifacts were found in the project's history.",
        "recommended_next_action": "Coordinate with teammate AD to physically upload/push the Yield and Market model artifacts (.joblib/.pkl) and their inference schemas to the repository."
    }
    
    with open(os.path.join(METADATA_DIR, "model7_model_discovery.json"), "w") as f:
        json.dump(metadata, f, indent=4)
        
    md = """# Phase 7 — Teammate Model Discovery & Import Audit

## 1. Objective
To automatically locate, import, and audit the Yield Prediction and Market Price models developed by teammate AD, ensuring they are physically present on the local machine before attempting API integration.

## 2. Search Strategy
A comprehensive recursive search was executed across:
* `C:\\Users\\prana\\OneDrive\\Desktop\\Projects\\KISANcare\\`
* `C:\\Users\\prana\\Downloads\\`
* Local Git history (all branches, commits, deleted files).

File types searched: `.joblib`, `.pkl`, `.pickle`, `.onnx`, `.h5`, `.keras`, `.pt`, `.pth`, `.cbm`.
Keywords searched: `yield`, `market`, `price`, `forecast`.

## 3. Search Results
* **Yield Model Found:** No
* **Market Model Found:** No
* **Candidates Identified:** 0
* **Git History:** No trace of previously committed Yield or Market models was found in the repository's history. The only `.pkl` files found belong to Model 1 (`crop_recommendation`).

## 4. Teammate Status
The models developed by teammate AD are **absent** from this workspace. They have not been pushed to the current Git branch, nor are they present in the local `Downloads` or `Projects` directories.

## 5. Recommended Next Action
Integration of the Economic Engine is blocked until the physical ML artifacts are provided. 
1. Ask teammate AD to share the trained Yield and Market model files (e.g., `.joblib` or `.pkl`).
2. Ask for the exact expected input feature schemas (JSON/Python dict format).
3. Place the models into `models/yield_prediction/` and `models/market/` respectively.

## 6. Final Status
**MODELS_NOT_FOUND_LOCALLY**
"""
    with open(os.path.join(DOCS_DIR, "phase7_model_discovery.md"), "w", encoding="utf-8") as f:
        f.write(md)
        
    print("Phase 7 Docs Created.")

if __name__ == "__main__":
    document_phase7()
