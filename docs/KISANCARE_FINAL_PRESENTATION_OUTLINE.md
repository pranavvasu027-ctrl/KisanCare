# KISANCARE FINAL PRESENTATION OUTLINE

## 1. Problem Statement
- Agricultural decision-making is heavily fragmented.
- Farmers lack a unified view of agronomic, financial, and climate data.
- Isolated ML models cannot resolve conflicting constraints (e.g., high yield vs. water scarcity).

## 2. The KisanCare Solution
- A centralized platform mapping multiple specialized ML models to a unified data structure.
- Resolves conflicting recommendations through an intelligent Decision Engine.
- Provides actionable, human-readable insights to farmers via a mobile-first interface.

## 3. The Farm Digital Twin Concept
- A secure, persistent database schema stored in Supabase PostgreSQL.
- Hierarchical structure: Farms -> Fields -> Seasons.
- Integrates Soil, Weather, and Irrigation records to serve as the "State" for all ML predictions.

## 4. ML Architecture
- **FastAPI Backend:** Orchestrates independent ML models.
- **Orchestrator:** Safely handles missing data and conditionally triggers models.
- **Decision Engine:** Applies hard constraints (like water conservation) and soft preferences (preferred crops) to rank alternatives.

## 5. Verified Working Models (Implemented)
- **Crop Recommendation:** Live inference functioning via FastAPI (`/crop-recommendation`).
- **Cost Prediction:** Inference logic and Orchestrator integration functioning securely (currently guarded by Supabase Auth).

## 6. The 9-Model Roadmap
- ✅ Crop Recommendation (Implemented)
- ✅ Cost & Profit Prediction (Implemented / Auth Guarded)
- 📊 Market Price Forecasting (Implemented / Historical CSV Snapshot)
- ⏳ Yield Prediction (Under Development)
- ⏳ Disease/Pest Risk (Under Development)
- ⏳ Irrigation/Water Prediction (Under Development)
- ⏳ Farm Risk Assessment (Under Development)
- ⏳ Post-Harvest Loss Prediction (Under Development)
- ⏳ NPK Prediction (Under Development)

## 7. Technology Stack
- **Frontend:** Flutter (Mobile & Web-ready)
- **Backend API:** Python FastAPI
- **Database & Auth:** Supabase (PostgreSQL with strict Row Level Security)
- **Machine Learning:** Scikit-Learn, XGBoost, Pandas

## 8. Demonstration Results
- Successfully established end-to-end communication between the Flutter frontend and Python backend.
- Crop Recommendation UI accurately parses real prediction data and Suitability Scores.
- Real Row-Level Security prevents unauthorized access to the Decision Engine.

## 9. Current Limitations
- **Supabase Authentication:** The Flutter app currently lacks a login UI, meaning the JWT token required to unlock the Cost Prediction and Decision Engine models cannot be generated yet.
- **Market Data:** Market prices are based on a static July 2024 CSV snapshot, not a live internet feed.
- **Android Compilation:** Local Gradle network timeouts prevent building the Android APK, requiring the demo to run on Flutter Web/Desktop.

## 10. Future Development
- Implement Flutter Supabase Auth to unlock the full Farm Digital Twin endpoints.
- Integrate a live API for weather data to replace static database records.
- Train and deploy the remaining 6 ML models into the Orchestrator pipeline.
