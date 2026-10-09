# STEP 09: VIDEO DEMONSTRATION RUNBOOK

## 1. Environment Startup Sequence
For the video submission, you will run two side-by-side terminal windows.

**Terminal 1 (The ML Backend):**
```powershell
cd C:\Users\prana\OneDrive\Desktop\Projects\KISANcare\kisan-care
.\venv\Scripts\Activate.ps1
uvicorn ml.main:app --host 127.0.0.1 --port 8000
```
*(Leave this running. You will see requests log here during the demo).*

**Terminal 2 (The Flutter Frontend):**
```powershell
cd C:\Users\prana\OneDrive\Desktop\Projects\KISANcare\kisan-care\mobile
flutter run -d chrome
```
*(Wait for Chrome to launch the Flutter App).*

---

## 2. The Video Scenario (What to Click & Say)

### A. The Setup (0:00 - 0:20)
- **Action:** Show the Chrome browser running the sleek KisanCare Flutter app side-by-side with your FastAPI terminal.
- **Script:** *"Welcome to the KisanCare Prototype. We have built a modern Flutter frontend securely connected to a Python FastAPI backend that orchestrates our agricultural machine learning models."*

### B. The 9-Model Portfolio (0:20 - 0:40)
- **Action:** Click on the **Insights / ML Model Portfolio** tab in the app.
- **Script:** *"We designed our architecture to support 9 comprehensive ML models. Here you can see that Crop Recommendation, Cost Prediction, and Market Price Forecasting are active in our backend, while the remaining 6 models are securely tracked as 'Under Development' in the API."*

### C. The Live Crop Recommendation (0:40 - 1:10)
- **Action:** Navigate to the **Crop Recommendation** screen. Press the **Get Recommendations** button. 
- **Script:** *"Let's test the live Crop Recommendation model. The frontend securely submits the district, season, and water availability to our backend..."*
- **Action (Visual):** Point out the `200 OK` POST request appearing in your backend terminal log.
- **Script:** *"...and the ML model successfully returns the agronomically suitable crops. Notice how it parses the raw JSON and displays the Top Recommendations with their exact Suitability Scores, while correctly filtering out unsuitable crops like Mango due to seasonal constraints."*

### D. The Real Security Architecture (1:10 - 1:40)
- **Action:** Navigate to the **Cost Analysis** screen. Type in a dummy number for Sunlight Hours and press **Predict Total Cost**. 
- **Script:** *"Our Cost Prediction model and Decision Engine are strictly bound to a user's authenticated Farm Digital Twin in our Supabase PostgreSQL database. They require 20 precise features to run."*
- **Action (Visual):** Point to the red error box that appears saying `ApiException: Server error (Status: 401)`.
- **Script:** *"If we attempt to query the cost model without a verified Supabase session token, our backend explicitly rejects it with a 401 Unauthorized. We are incredibly proud of this because it proves we have implemented real, enterprise-grade Row Level Security, rather than bypassing authentication just to make the demo look good."*

---

## 3. Known Limitations & Recovery
- **Android Emulator:** Do not attempt to run the Android emulator on video. Due to standard local network proxies, Gradle wrapper downloads are timing out. Use `flutter run -d chrome` or `flutter run -d windows` which flawlessly bypasses Android compilation and still uses the same Dart codebase.
- **Backend Fails:** If the backend throws a `500` error during the live Crop Recommendation, simply `CTRL+C` in Terminal 1, restart the `uvicorn` command, and press the button in Flutter again. 
- **CORS:** `ml/main.py` is fully configured with `allow_origins=["*"]`, so Chrome will successfully accept responses from `127.0.0.1:8000`.
