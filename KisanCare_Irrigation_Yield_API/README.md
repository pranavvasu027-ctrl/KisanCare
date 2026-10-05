# KISANCARE - AI-Powered Farm Digital Twin

KisanCare is an AI-powered Farm Digital Twin and Farm Decision Intelligence platform.

## Architecture

OBSERVE → PREDICT → SIMULATE → COMPARE → DECIDE → LEARN

- **Frontend**: React, Vite, Tailwind CSS (Farmer Experience)
- **Backend / Inference**: FastAPI, Python (Dual Agricultural Intelligence Backend)
- **Database**: PostgreSQL, PostGIS (Decision Engine, Digital Twin)

```
Existing UI / Client
       │
       ▼
FastAPI Inference Backend (Port 8000)
       ├── GET  /health
       ├── POST /api/irrigation/predict  ──> FAO-56 Physical Water Balance + ETo LSTM
       └── POST /api/yield/predict       ──> Random Forest Regressor (NIHAL670/Crop-yield)
```

---

## Machine Learning Models Integrated

This repository exposes **ONLY** two verified, production-ready AI models via clean REST endpoints:

1. **Precision Irrigation Intelligence Model**:
   - **Methodology**: FAO-56 physical dual crop coefficient soil water balance coupled with reference evapotranspiration (ETo) deep learning (PyTorch LSTM with Self-Attention).
   - **Outputs**: Soil water depletion ($D_r$), Total Available Water ($TAW$), Readily Available Water ($RAW$), crop evapotranspiration ($ET_c$), reference $ETo$, gross irrigation requirement (mm), and operational timing (`today`, `within_24h`, `none`).
   - **Weight Artifact**: Local lightweight model (`eto_punjab_best.pth`, ~821 KB) + FAO-56 crop coefficients.

2. **Crop Yield Prediction Model**:
   - **Methodology**: Scikit-Learn `RandomForestRegressor(n_estimators=200)` trained on 20,000+ Indian agro-climatic records.
   - **Outputs**: Predicted agricultural yield (`quintal/hectare`) and total harvest production (`quintal`).
   - **Weight Artifact**: Downloaded at runtime and cached from Hugging Face repository [`NIHAL670/Crop-yield`](https://huggingface.co/NIHAL670/Crop-yield) (`model.pkl`, ~347 MB). Not committed to Git.

> [!NOTE]
> The Disease/Pest model (`disease_pest_ai`) is strictly excluded from this backend.

---

## Quickstart & Local Setup

### 1. Clone the repository
```bash
git clone https://github.com/pranavvasu027-ctrl/KisanCare.git
cd KisanCare
```

### 2. Create virtual environment
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment
```bash
cp .env.example .env
```
Key settings in `.env`:
- `API_HOST`: `0.0.0.0`
- `API_PORT`: `8000`
- `ALLOWED_ORIGINS`: Comma-separated frontend URLs (e.g., `http://localhost:5173,http://localhost:3000`)
- `CROP_YIELD_REPO_ID`: `NIHAL670/Crop-yield`

### 5. Start the Inference API
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### 6. Interactive Swagger Documentation
Open your browser at:
```
http://localhost:8000/docs
```
or ReDoc documentation:
```
http://localhost:8000/redoc
```

---

## Testing & Verification

Run the comprehensive test suite (including health check, input validation, memory caching verification, direct model parity, and disease/pest exclusion):

```bash
pytest tests/ -v
```

---

## Frontend Integration Guide

The frontend communicates with the AI models strictly through the HTTP REST API. The UI should not embed Python execution.

### 1. Irrigation Prediction

- **Endpoint**: `POST /api/irrigation/predict`
- **Content-Type**: `application/json`

#### Request Body
```json
{
  "crop": "wheat",
  "crop_stage": "mid",
  "soil_type": "loam",
  "soil_moisture": 0.15,
  "rainfall": 0.0,
  "decision_date": "2026-10-05"
}
```

| Field | Type | Range / Options | Description |
|---|---|---|---|
| `crop` | string | `wheat`, `rice`, `maize`, `cotton`, `sugarcane`, `barley`, `potato`, `tomato`, `mustard` | Crop to evaluate |
| `crop_stage` | string | `initial`, `mid`, `late` | Current crop growth stage |
| `soil_type` | string | `loam`, `clay`, `sand`, `sandy loam`, `clay loam`, `silt loam` | Soil texture classification |
| `soil_moisture` | float | `0.0` to `1.0` | Volumetric soil moisture ($m^3/m^3$ fraction) |
| `rainfall` | float | $\ge 0.0$ | Observed or forecasted precipitation today (mm) |
| `decision_date` | string (optional) | `YYYY-MM-DD` | Advisory date (defaults to current date) |

#### Response (`200 OK`)
```json
{
  "success": true,
  "model": "irrigation",
  "prediction": {
    "irrigation_required": true,
    "irrigation_quantity_mm": 51.53,
    "irrigation_timing": "today",
    "decision_date": "2026-10-05",
    "crop": "wheat",
    "crop_stage": "mid",
    "soil_type": "loam",
    "soil_moisture": 0.15,
    "rainfall_mm": 0.0,
    "water_balance": {
      "soil_water_depletion_mm": 37.5,
      "total_available_water_mm": 225.0,
      "readily_available_water_mm": 123.75,
      "crop_evapotranspiration_mm": 5.75,
      "reference_eto_mm": 5.0,
      "net_irrigation_requirement_mm": 43.8
    },
    "decision_reason_codes": [
      "HIGH_ROOT_ZONE_DEPLETION"
    ],
    "warnings": [],
    "model_source": "FAO-56 Physical Balance + ETo-LSTM-Attention",
    "units": {
      "irrigation_quantity": "mm",
      "soil_water_depletion": "mm",
      "total_available_water": "mm",
      "readily_available_water": "mm",
      "crop_evapotranspiration": "mm",
      "reference_eto": "mm",
      "net_irrigation_requirement": "mm",
      "soil_moisture": "m³/m³ (fraction)",
      "rainfall": "mm"
    }
  }
}
```

#### JavaScript `fetch()` Example:
```javascript
async function fetchIrrigationAdvisory(agronomicData) {
  try {
    const response = await fetch("http://localhost:8000/api/irrigation/predict", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        crop: agronomicData.crop,
        crop_stage: agronomicData.cropStage,
        soil_type: agronomicData.soilType,
        soil_moisture: agronomicData.soilMoisture,
        rainfall: agronomicData.rainfall || 0.0,
        decision_date: agronomicData.date || new Date().toISOString().split("T")[0]
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || "Irrigation prediction failed");
    }

    const result = await response.json();
    console.log("Irrigation needed:", result.prediction.irrigation_required);
    console.log("Recommended quantity (mm):", result.prediction.irrigation_quantity_mm);
    return result.prediction;
  } catch (err) {
    console.error("Irrigation API error:", err);
    throw err;
  }
}
```

---

### 2. Crop Yield Prediction

- **Endpoint**: `POST /api/yield/predict`
- **Content-Type**: `application/json`

#### Request Body
```json
{
  "state": "Punjab",
  "crop": "Wheat",
  "season": "Rabi",
  "soil_type": "Alluvial",
  "area": 10.0,
  "rainfall": 650.0,
  "temperature": 22.5,
  "humidity": 65.0,
  "nitrogen": 120.0,
  "phosphorus": 50.0,
  "potassium": 40.0
}
```

| Field | Type | Range / Options | Description |
|---|---|---|---|
| `state` | string | 28 Indian States (e.g., `Punjab`, `Haryana`, `Uttar Pradesh`) | State of farm location |
| `crop` | string | 50 Indian crops (e.g., `Wheat`, `Rice`, `Maize`, `Cotton`, `Sugarcane`) | Target crop |
| `season` | string | `Kharif`, `Rabi`, `Summer`, `Whole Year` | Agricultural cropping season |
| `soil_type` | string | `Alluvial`, `Black`, `Clay`, `Laterite`, `Red` | Soil classification |
| `area` | float | $> 0.0$ | Cultivated area in hectares |
| `rainfall` | float | $\ge 0.0$ | Seasonal precipitation in mm |
| `temperature` | float | $-20.0$ to $60.0$ | Ambient temperature in °C |
| `humidity` | float | $0.0$ to $100.0$ | Relative humidity percentage |
| `nitrogen` | float | $\ge 0.0$ | Soil Nitrogen (N) content |
| `phosphorus` | float | $\ge 0.0$ | Soil Phosphorus (P) content |
| `potassium` | float | $\ge 0.0$ | Soil Potassium (K) content |

#### Response (`200 OK`)
```json
{
  "success": true,
  "model": "yield",
  "prediction": {
    "predicted_yield": 42.15,
    "yield_unit": "quintal/hectare",
    "estimated_production": 421.5,
    "production_unit": "quintal",
    "cultivated_area_hectares": 10.0,
    "input_summary": {
      "state": "Punjab",
      "crop": "Wheat",
      "season": "Rabi",
      "soil_type": "Alluvial",
      "area": 10.0,
      "rainfall": 650.0,
      "temperature": 22.5,
      "humidity": 65.0,
      "nitrogen": 120.0,
      "phosphorus": 50.0,
      "potassium": 40.0
    },
    "model_source": "Hugging Face NIHAL670/Crop-yield (RandomForestRegressor)"
  }
}
```

#### JavaScript `fetch()` Example:
```javascript
async function fetchCropYieldPrediction(farmData) {
  try {
    const response = await fetch("http://localhost:8000/api/yield/predict", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        state: farmData.state,
        crop: farmData.crop,
        season: farmData.season,
        soil_type: farmData.soilType,
        area: farmData.areaHectares,
        rainfall: farmData.rainfallMm,
        temperature: farmData.temperatureC,
        humidity: farmData.humidityPct,
        nitrogen: farmData.nitrogen,
        phosphorus: farmData.phosphorus,
        potassium: farmData.potassium
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || "Yield prediction failed");
    }

    const result = await response.json();
    console.log("Predicted Yield:", result.prediction.predicted_yield, result.prediction.yield_unit);
    console.log("Total Harvest:", result.prediction.estimated_production, result.prediction.production_unit);
    return result.prediction;
  } catch (err) {
    console.error("Yield API error:", err);
    throw err;
  }
}
```

---

### Error Handling

When invalid agronomic parameters or unseen categories are passed, the API returns a structured HTTP `422 Unprocessable Content` response:

```json
{
  "detail": "Unsupported Crop: 'ExoticBerry'. Valid options include: ['Apple', 'Banana', 'Barley', 'Beetroot', 'Brinjal', 'Cabbage', 'Cardamom', 'Carrot', 'Cashew', 'Castor'...]"
}
```
