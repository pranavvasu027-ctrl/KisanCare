# AD MODEL HANDOFF AUDIT

## Model 1
- **Name:** Crop Recommendation System with Crop-History & Rotation Scorer (Model 1)
- **Purpose:** Recommends optimal crops given soil test N, P, K, pH, and local climatic conditions, adjusted by regional agro-climatic suitability and history-based crop rotation scoring.
- **Inputs:**
  - `N` (Nitrogen in soil test, mg/kg or kg/ha)
  - `P` (Phosphorus in soil test)
  - `K` (Potassium in soil test)
  - `temperature` (°C)
  - `humidity` (%)
  - `ph` (Soil pH, 0–14)
  - `rainfall` (mm)
  - `crop_history` (Previous crops grown, seasons ago, historical yields)
  - `state` / `district` (Geographic location for regional viability)
- **Outputs:** Ranked list of recommended crops with blended final score, sub-scores (soil/climate ML score, regional score, history rotation score), nutrient status advisories, and agronomic rationale.
- **Dataset:** Crop Recommendation Dataset (ICAR / Indian Agricultural Benchmark)
- **Algorithm:** `RandomForestClassifier` (22 agricultural crop classes)
- **Artifact:** `model1_npk.pkl` (7.37 MB)
- **Preprocessing:** `model1_label_encoder.pkl` (696 bytes), `knowledge_base.json` (agronomic rules and nutrient baseline ranges)
- **Inference Test:** `ad_handoff/model_1/tests/test_model_1_inference.py` — **PASS**
- **API:** Available via FastAPI (`POST /api/v1/recommend`)
- **Metrics:** Classification Accuracy ~99.0% on benchmark validation split
- **Limitations:** Trained on 22 specific crop classes; does not model simultaneous intercropping; strictly enforces Soil-Test Primacy Invariant (crop history modifies rotation dynamics but does not override current measured soil NPK deficiencies).
- **Status:** **READY**

---

## Model 2
- **Name:** India Crop Yield Predictor (Model 2)
- **Purpose:** Predicts crop yield in quintal/hectare and derives total estimated production in quintals based on state, crop, season, soil type, cultivated area, and climatic/nutrient parameters.
- **Inputs:**
  - `State` (Categorical, 28 Indian states)
  - `Crop` (Categorical, 50 crops)
  - `Season` (Categorical: `Kharif`, `Rabi`, `Summer`, `Whole Year`)
  - `Soil_Type` (Categorical: `Alluvial`, `Black`, `Clay`, `Laterite`, `Red`)
  - `Area` (Numerical, hectares > 0)
  - `Rainfall` (Numerical, mm)
  - `Temperature` (Numerical, °C)
  - `Humidity` (Numerical, %)
  - `Nitrogen` (Numerical, N)
  - `Phosphorus` (Numerical, P)
  - `Potassium` (Numerical, K)
- **Outputs:**
  - `predicted_yield`: Regression output in `quintal/hectare`
  - `estimated_production`: Mathematically calculated total production in `quintals` ($\text{Yield} \times \text{Area}$)
  - `unit`: `quintal/hectare`
  - `production_unit`: `quintal`
  - `input_summary`: Echo of provided input features
  - `model_source`: `NIHAL670/Crop-yield`
- **Dataset:** India Crop Yield Dataset (`india_crop_yield_20000_rows.csv` from Ministry of Agriculture & Farmers Welfare / DAC&FW)
- **Algorithm:** `RandomForestRegressor(n_estimators=200, random_state=42)`
- **Artifact:** `model.pkl` (~347.41 MB)
- **Preprocessing:** 4 scikit-learn LabelEncoders: `le_state.pkl` (28 classes), `le_crop.pkl` (50 classes), `le_season.pkl` (4 classes), `le_soil.pkl` (5 classes)
- **Inference Test:** `ad_handoff/model_2/tests/test_model_2_inference.py` — **PASS**
- **API:** Not yet built as standalone microservice endpoint; target API contract documented for KisanCare (`POST /api/v1/predict/yield`)
- **Metrics:** $R^2 \approx 0.88$ on validation split
- **Limitations:** Large binary model artifact (~347 MB) exceeds default GitHub 100 MB file limit and must be dynamically downloaded via `huggingface_hub` or tracked via Git LFS; categorical inputs are restricted to the 28 states, 50 crops, 4 seasons, and 5 soil types present in training data.
- **Status:** **READY**

---

## Model 3
- **Name:** Crop Disease & Pest Diagnosis System (Model 3)
- **Purpose:** Dual-task vision intelligence combining foliar disease classification, field pest object detection, and CIBRC regulatory-backed treatment recommendations (chemical, biological, cultural).
- **Inputs:**
  - `image`: Plant foliar image or pest trap photograph (filepath or RGB array)
  - `crop_name`: Declared host crop name (e.g. `Apple`, `Tomato`, `Corn`, `Cotton`, `Rice`)
  - `location_state`: Geographic Indian state (e.g. `Himachal Pradesh`, `Maharashtra`)
  - `growth_stage`: Agricultural growth stage (`seedling`, `vegetative`, `flowering`, `fruiting`, `harvest`)
  - `image_type`: Image classification mode (`leaf`, `canopy`, `trap_sticky_sheet`)
- **Outputs:**
  - `disease`: Identified foliar condition, confidence score, healthy foliage confirmation, top-5 probability distribution, and user crop match flag
  - `pests`: Detected pest species (102 IP102 classes), bounding box coordinates, and detection confidence
  - `treatment`: CIBRC-registered active ingredients, chemical formulations, biological alternatives, and cultural sanitation practices
  - `provenance`: Model latency breakdown (ms), framework version, regulatory sources, and diagnostic timestamps
- **Dataset:** PlantVillage Benchmark (54,306 images) + IP102 Large-scale Pest Benchmark (75,222 images) + CIBRC Regulatory Database (Ministry of Agriculture, GoI)
- **Algorithm:** EfficientNetV2-S (PyTorch foliar classifier) + YOLO11s (Ultralytics pest object detector)
- **Artifact:** `efficientnet_v2_s_best.pth` (81.82 MB) + `best.pt` (38.32 MB)
- **Preprocessing:** Torchvision transforms (Resize 384x384, ImageNet normalization), YOLO letterbox resizing (896x896), `cibrc_database.json`, `treatments.json`, `pest_taxonomy.json`, `normalization.py`
- **Inference Test:** `ad_handoff/model_3/tests/test_model_3_inference.py` — **PASS**
- **API:** Not yet built as backend FastAPI endpoint; target API contract documented for KisanCare (`POST /api/v1/predict/disease`)
- **Metrics:**
  - Disease Classifier: Top-1 Accuracy 99.2% on validation; 100% on benchmark sample evaluation
  - Pest Detector: mAP50 0.68 on IP102 benchmark
- **Limitations:** Disease classification is optimized for single-leaf macro photographs; field canopy shots require cropping to diseased foliage; weights require PyTorch and Ultralytics environment.
- **Status:** **READY**

---

## Integration Requirements

### Model 1: Crop Recommendation
- **Digital Twin inputs:**
  - `farm.soil_test.N`, `farm.soil_test.P`, `farm.soil_test.K`, `farm.soil_test.ph`
  - `farm.weather.temperature`, `farm.weather.humidity`, `farm.weather.rainfall`
  - `farm.history.crops_grown`, `farm.history.seasons_ago`, `farm.history.yields`
  - `farm.location.state`, `farm.location.district`
- **Model adapter requirements:** Construct `SoilClimateData` and `CropHistoryInput` pydantic models from Farm Digital Twin entities; call `engine.recommend()`.
- **Expected output:** Ranked list of recommended crops with blended final score, nutrient status, and rotation advisories.
- **Expected model_outputs structure:**
  ```json
  {
    "model1_crop_recommendation": {
      "model": "Sheshank2609/crop-recommendation-system",
      "model_version": "1.0.0",
      "output": {
        "recommended_crops": [
          {
            "crop": "sugarcane",
            "final_score": 0.865,
            "soil_climate_score": 0.85,
            "history_rotation_score": 0.90,
            "regional_score": 1.0,
            "reason": "Optimal climate match and favorable rotation following Cotton."
          }
        ],
        "soil_test_npk_status": {
          "N": "adequate",
          "P": "adequate",
          "K": "adequate"
        }
      },
      "timestamp": "2026-10-05T12:00:00Z"
    }
  }
  ```

---

### Model 2: Crop Yield Prediction
- **Digital Twin inputs:**
  - `farm.location.state`
  - `farm.active_crop.crop_name`
  - `farm.active_crop.season`
  - `farm.soil_type`
  - `farm.area` (hectares)
  - `farm.weather.expected_rainfall`, `farm.weather.avg_temperature`, `farm.weather.avg_humidity`
  - `farm.soil_test.N`, `farm.soil_test.P`, `farm.soil_test.K`
- **Model adapter requirements:** Validate categorical strings against LabelEncoder classes; format 11-feature tabular vector in exact order: `['State', 'Crop', 'Season', 'Soil_Type', 'Area', 'Rainfall', 'Temperature', 'Humidity', 'Nitrogen', 'Phosphorus', 'Potassium']`; execute `predict_crop_yield()`.
- **Expected output:** `predicted_yield` (quintal/hectare) and `estimated_production` (quintals).
- **Expected model_outputs structure:**
  ```json
  {
    "model2_yield_prediction": {
      "model": "NIHAL670/Crop-yield",
      "model_version": "1.0.0",
      "output": {
        "predicted_yield": 18.99,
        "yield_unit": "quintal/hectare",
        "estimated_production": 47.47,
        "production_unit": "quintal",
        "cultivated_area": 2.5
      },
      "timestamp": "2026-10-05T12:00:00Z"
    }
  }
  ```

---

### Model 3: Crop Disease & Pest Diagnosis
- **Digital Twin inputs:**
  - `farm.observation.image_path` (or image byte payload from farmer mobile/web upload)
  - `farm.active_crop.crop_name`
  - `farm.location.state`
  - `farm.active_crop.growth_stage`
- **Model adapter requirements:** Decode image into RGB format; pass to `DiseasePestPipeline.predict()`; retrieve diagnosis and query CIBRC knowledge base repository for verified chemical/biological treatments.
- **Expected output:** Disease diagnosis, pest presence, probability score, crop compatibility verification, and structured CIBRC treatments.
- **Expected model_outputs structure:**
  ```json
  {
    "model3_disease_pest": {
      "model": "BiernyVR/crop-disease-classifier + underdogquality/yolo11s-pest-detection",
      "model_version": "1.0.0",
      "output": {
        "condition": "Apple Scab",
        "condition_type": "disease",
        "confidence": 0.9035,
        "is_healthy": false,
        "crop_mismatch": false,
        "pests_detected": [],
        "treatments": {
          "chemical": [
            {
              "chemical_name": "Difenoconazole 25% EC",
              "dosage": "0.5 ml/L",
              "cpr_registration": "CIBRC-REG-2024"
            }
          ],
          "biological": [
            {
              "agent": "Bacillus subtilis",
              "notes": "Preventative foliar spray"
            }
          ],
          "cultural": [
            "Prune infected branches",
            "Collect and destroy fallen leaf litter"
          ]
        }
      },
      "timestamp": "2026-10-05T12:00:00Z"
    }
  }
  ```

---

## Final Status

- **Model 1 (Crop Recommendation):** **READY**
- **Model 2 (Crop Yield Prediction):** **READY**
- **Model 3 (Crop Disease & Pest Diagnosis):** **READY**
