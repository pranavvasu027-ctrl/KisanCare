# 06 — Official ML Development & Training Workflow

**Date:** 2026-10-04  
**Task:** Define the standard ML development, experimentation, and training workflow across Jupyter, Google Colab, and GitHub.  
**Author:** KisanCare Engineering (AI-assisted)  
**Branch:** `research-reports`  

---

## 1. Official KisanCare ML Environments

The machine learning lifecycle for KisanCare is strictly segmented across three primary environments, each with distinct responsibilities. 

### A. Jupyter Notebook — Local Experimentation
Jupyter is strictly for local, small-scale experimentation. It is **NOT** the official final training environment.
*   **Responsibilities:**
    *   Exploratory Data Analysis (EDA)
    *   Dataset inspection and visualization
    *   Data cleaning experiments
    *   Feature analysis and preprocessing tests
    *   Debugging ML code and testing prediction functions
    *   Comparing algorithms on small/medium datasets

### B. Google Colab — Official Training Environment
Google Colab is the **STANDARDIZED official training environment**.
*   **Responsibilities:**
    *   Full model training and large dataset processing
    *   Hyperparameter experiments and cross-validation
    *   Final model evaluation and generation
    *   GPU-based experiments (when the selected model actually benefits from GPU acceleration; do not force GPU usage for simple models like Random Forests where CPU is sufficient)

### C. GitHub — Source of Truth
GitHub hosts the permanent record of the project.
*   **Responsibilities:**
    *   Python source code, Jupyter/Colab notebooks, and training scripts
    *   Preprocessing code and evaluation scripts
    *   Model configurations, research reports, and experiment documentation
    *   Final model artifacts (only when appropriately sized)
*   **Prohibited Items:**
    *   Large raw datasets, temporary files, Colab cache files, secrets/API keys, and huge checkpoints.

---

## 2. Standard Model Development Workflow

Every ML model in KisanCare (including Model 1) follows this 12-step pipeline:

1.  **Research** existing GitHub models/repositories.
2.  **Inspect** the existing model/dataset.
3.  **Local Experimentation (Jupyter)**: EDA, data inspection, preprocessing tests, small experiments.
4.  **Finalize** the dataset and feature contract.
5.  **Migration**: Move the finalized training pipeline to Google Colab.
6.  **Official Training**: Train and evaluate in Google Colab.
7.  **Compare** experiments based on standardized metrics.
8.  **Select** the best model based on proper evaluation.
9.  **Save** the final model and preprocessing artifacts.
10. **Test Inference** independently.
11. **Integration**: Integrate the model into the FastAPI backend via GitHub.
12. **Test API Predictions** end-to-end.

---

## 3. Workflow Architecture Diagram

The lifecycle of data, notebooks, and models flows sequentially:

```text
    [ Jupyter ]
        ↓
 EDA / Local Experiments
        ↓
    [ GitHub ] (Commit Notebooks & Scripts)
        ↓
 [ Google Colab ]
        ↓
 Official Training
        ↓
    Evaluation
        ↓
    Best Model
        ↓
    [ GitHub ] (Commit Final .pkl / Artifacts)
        ↓
   [ FastAPI ] (Backend Integration)
        ↓
  [ KisanCare ] (Production App)
```

---

## 4. Reproducibility Rule

The **exact same** preprocessing and feature pipeline must work locally in Jupyter, remotely in Google Colab, and finally in the API. 
*   **Do NOT** create separate logic that behaves differently between environments.
*   **Requirements:** Use fixed random seeds, explicit preprocessing steps, versioned datasets, and documented dependencies. 
*   Every final training experiment must be 100% reproducible directly from the repository code.

---

## 5. Experiment Tracking

Every serious training experiment must be rigorously tracked. Required metadata includes:

*   **Experiment ID** (e.g., `model1_exp01_baseline`)
*   **Date & Runtime Environment**
*   **Dataset:** Version, Source, Number of samples, Number of classes, Feature list, Train/test/validation split.
*   **Training Details:** Random seed, Algorithm, Hyperparameters, GPU/CPU used, Training time.
*   **Metrics:** Accuracy, Precision, Recall, Macro-F1, Per-class performance, Confusion matrix.
*   **Outputs:** Important limitations and the Final Model Artifact Name.

---

## 6. Current Status & Next Steps for Model 1

*   **Model 1 (Crop Recommendation)** currently prioritizes 20 V1 crops (Rice, Wheat, Maize, Soybean, Cotton, Sugarcane, Chickpea, Pigeon Pea, Groundnut, Sorghum, Pearl Millet, Green Gram, Black Gram, Mustard, Onion, Potato, Tomato, Banana, Mango, Grapes).
*   **Preservation Rule:** Additional crops found in source datasets must be preserved for future versions. Do NOT delete extra crop classes to artificially hit exactly 20 crops.
*   **Status Block:** We have identified that the current baseline (`djdhairya`) covers only 10/20 crops, and blind synthetic generation using NPK fertilizer data is scientifically indefensible. 
*   **Immediate Next Step:** Training is blocked. The dataset/input strategy must be resolved first before any training pipeline can be initiated in Colab.
