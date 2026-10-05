# KisanCare - AI-Powered Farm Decision Intelligence

## 1. What is KisanCare?
KisanCare is an AI-powered Farm Decision Intelligence system. It aims to create a Farm Digital Twin that integrates various agricultural parameters to provide actionable insights for farmers.

## 2. Overall Architecture
The core architecture flows as follows:
Farmer Data → Data Processing / Fusion → Farm Digital Twin → 8 Specialized AI/ML Models → What-If Simulation → Decision & Optimization Engine → AI Copilot → Farmer Decision → Actual Outcome → Farm Memory → Improved Digital Twin.

## 3. The 8 Planned AI/ML Models
1. Crop Recommendation
2. Yield Prediction
3. Disease & Pest Detection
4. Irrigation / Water Prediction
5. Farm Risk Prediction
6. Cost & Profit Prediction
7. Market Price Forecasting
8. Post-Harvest Loss Prediction

## 4. Why We Are Implementing Models One-By-One
To maintain a high standard of quality, we build models sequentially. This ensures each model goes through rigorous phases: EDA, Training, Evaluation, and Integration. We avoid building all models simultaneously to maintain focus, prevent unmanageable complexity, and ensure each model's output correctly feeds into the next stage or the Digital Twin.

## 5. Google Colab's Role
**Experiment in Google Colab. Stabilize and integrate in GitHub.**
Google Colab is our primary environment for data exploration, model training, and ML experimentation. Notebooks should be developed such that they can seamlessly run in Colab.

## 6. GitHub's Role
GitHub is the definitive source of truth for the codebase, stabilized notebooks, trained model artifacts, backend integration, and project architecture.

## 7. Current Development Phase
**Phase 0 - Repository Foundation**: We are currently preparing the project structure and Python environment.
We will soon begin **Phase 1**, focusing exclusively on the **Crop Recommendation** model. 
*(Note: Do not start training the model yet. The dataset is pending selection.)*

## 8. How to Run the Backend
Ensure your Python environment has the packages listed in `requirements.txt`.
To start the minimal FastAPI health endpoint:
```bash
uvicorn backend.app.main:app --reload
```
You can then access the health check at `http://127.0.0.1:8000/health`.

## 9. How the ML Notebooks are Organized
ML notebooks are located in the `/notebooks` directory. Each notebook corresponds to a specific model or phase in the pipeline (e.g., `01_crop_recommendation.ipynb`). They are structured systematically with clear sections for EDA, training, evaluation, and saving, ready to be executed in Google Colab when the dataset is provided.
