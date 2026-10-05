# KisanCare — Agriculture AI (AD) Models Handoff Package

This directory (`ad_handoff/`) contains the complete packaging, metadata, preprocessing artifacts, and verified inference modules for the **3 completed Agricultural AI Models** designed for integration into the KisanCare platform.

---

## 1. Overview of the 3 Completed Models

| Model | Subsystem Name | Primary Algorithm | Source / Upstream | Key Output |
|---|---|---|---|---|
| **Model 1** | Crop Recommendation | `RandomForestClassifier` | `Sheshank2609/crop-recommendation-system` | Top recommended crops with blended soil, regional, and rotation scores |
| **Model 2** | Crop Yield Prediction | `RandomForestRegressor` | `NIHAL670/Crop-yield` | Predicted yield (`quintal/ha`) and total production (`quintal`) |
| **Model 3** | Crop Disease & Pest Diagnosis | EfficientNetV2-S + YOLO11s | `BiernyVR/crop-disease-classifier` + `underdogquality/yolo11s-pest-detection` | Pathology classification, pest localization, and CIBRC treatment recommendations |

---

## 2. Directory Structure

```text
ad_handoff/
├── README.md
├── requirements.txt
├── model_1/
│   ├── metadata.json
│   ├── model/
│   │   ├── loader.py
│   │   ├── model1_label_encoder.pkl
│   │   └── model1_npk.pkl
│   ├── preprocessing/
│   │   ├── knowledge_base.json
│   │   └── knowledge_base.py
│   ├── inference/
│   │   ├── api.py
│   │   ├── config.py
│   │   ├── engine.py
│   │   ├── regional_scorer.py
│   │   ├── rotation_scorer.py
│   │   ├── schemas.py
│   │   └── soil_climate_scorer.py
│   └── tests/
│       └── test_model_1_inference.py
├── model_2/
│   ├── metadata.json
│   ├── model/
│   │   ├── loader.py
│   │   ├── le_state.pkl
│   │   ├── le_crop.pkl
│   │   ├── le_season.pkl
│   │   └── le_soil.pkl
│   ├── preprocessing/
│   │   └── encoder_utils.py
│   ├── inference/
│   │   └── predictor.py
│   └── tests/
│       └── test_model_2_inference.py
└── model_3/
    ├── metadata.json
    ├── model/
    │   └── loader.py
    ├── preprocessing/
    │   ├── cibrc_database.json
    │   ├── treatments.json
    │   ├── pest_taxonomy.json
    │   └── normalization.py
    ├── inference/
    ├── tests/
    │   ├── apple_scab_bierny.jpg
    │   └── test_model_3_inference.py
    └── disease_pest_ai/
```

---

## 3. Dependency Installation

Install the unified handoff requirements:

```bash
pip install -r ad_handoff/requirements.txt
```

---

## 4. How to Load Each Model

Each model folder contains a dedicated `model/loader.py` that checks for local checkpoints and dynamically downloads verified weights from Hugging Face if absent:

```python
# Model 1
from ad_handoff.model_1.model.loader import load_crop_recommendation_model
model1, label_encoder1 = load_crop_recommendation_model()

# Model 2
from ad_handoff.model_2.model.loader import load_crop_yield_model
artifacts2 = load_crop_yield_model()
model2 = artifacts2["model"]

# Model 3
from ad_handoff.model_3.model.loader import load_disease_model, load_pest_model
disease_checkpoint_path = load_disease_model()
pest_checkpoint_path = load_pest_model()
```

---

## 5. How to Run Inference

### Model 1: Crop Recommendation

```python
from ad_handoff.model_1.inference.engine import RecommendationEngine
from ad_handoff.model_1.inference.schemas import SoilClimateData, CropHistoryInput

engine = RecommendationEngine()

soil_climate = SoilClimateData(
    N=90.0, P=42.0, K=43.0,
    temperature=26.0, humidity=75.0, ph=6.5, rainfall=800.0,
    state="Maharashtra"
)
history = CropHistoryInput(
    crops_grown=["Cotton", "Soybean"],
    seasons_ago=[1, 2],
    yields=[20.0, 15.0]
)

response = engine.recommend(soil_climate=soil_climate, history=history, top_k=3)
for rec in response.recommendations:
    print(f"Crop: {rec.crop}, Score: {rec.final_score:.3f}")
```

### Model 2: Crop Yield Prediction

```python
from ad_handoff.model_2.inference.predictor import predict_crop_yield

result = predict_crop_yield(
    state="Maharashtra",
    crop="Rice",
    season="Kharif",
    soil_type="Clay",
    area=2.5,
    rainfall=800.0,
    temperature=26.0,
    humidity=75.0,
    nitrogen=90.0,
    phosphorus=42.0,
    potassium=43.0
)

print(f"Predicted Yield: {result.predicted_yield:.2f} {result.unit}")
print(f"Estimated Production: {result.estimated_production:.2f} {result.production_unit}")
```

### Model 3: Crop Disease & Pest Diagnosis

```python
from disease_pest_ai.inference.pipeline import DiseasePestPipeline

pipeline = DiseasePestPipeline()

result = pipeline.predict(
    plant_image="ad_handoff/model_3/tests/apple_scab_bierny.jpg",
    crop_name="Apple",
    location_state="Himachal Pradesh",
    growth_stage="fruiting",
    image_type="leaf"
)

print(f"Diagnosis: {result.disease.condition} (Score: {result.disease.score:.4f})")
print(f"Is Healthy: {result.disease.is_healthy}")
print(f"Approved Chemical Treatments: {len(result.treatment.disease_recommendations.get('chemical_treatments', []))}")
```

---

## 6. Running Handoff Verification Tests

Run the unified test suite across all 3 models:

```bash
python -m pytest -v ad_handoff/model_1/tests/test_model_1_inference.py ad_handoff/model_2/tests/test_model_2_inference.py ad_handoff/model_3/tests/test_model_3_inference.py
```

---

## 7. Model Artifact Locations & Transfer Guidance

Due to GitHub repository limits (<100 MB per file, recommended <50 MB):

1. **`model1_npk.pkl` (7.37 MB):** Included directly in handoff package and available on Hugging Face (`Sheshank2609/crop-recommendation-system`).
2. **`model.pkl` (347.41 MB, Model 2):** Exceeds GitHub push limits. Dynamically retrieved via `hf_hub_download` or tracked with Git LFS.
3. **`efficientnet_v2_s_best.pth` (81.82 MB, Model 3):** Exceeds GitHub warning threshold (50 MB). Cached dynamically via `hf_hub_download` or tracked with Git LFS.
4. **`best.pt` (38.32 MB, Model 3):** Cached dynamically via `hf_hub_download` or tracked with Git LFS.

---

## 8. Digital Twin Integration Architecture

When integrating into `backend/app/digital_twin/`:
- **Model 1 Adapter:** Reads `farm.soil_test`, `farm.weather`, `farm.history`, outputs `recommendations`.
- **Model 2 Adapter:** Reads `farm.location.state`, `farm.active_crop`, `farm.area`, outputs `predicted_yield` and `estimated_production`.
- **Model 3 Adapter:** Reads uploaded image, outputs `disease`, `pests`, `severity`, and `cibrc_treatments`.
- Output is captured under `farm.model_outputs[model_name]`.
