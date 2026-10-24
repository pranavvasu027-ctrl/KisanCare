# Agriculture AI — Plant Disease & Pest Detection System (`diseasemodel`)

Production-grade Multimodal Diagnostics and Statutory CIB&RC Treatment Advisory Service.

---

## 🌟 Highlights & Capabilities
- **Foliar Disease Classifier:** EfficientNetV2-S (BiernyVR / PlantVillage, 38 classes).
- **Arthropod Pest Detector:** YOLO11s Object Detector (IP102 taxonomy, 102 classes).
- **Crop Compatibility Validator:** Guardrail preventing off-label recommendations on mismatched crop hosts.
- **Treatment Recommendation Engine:** Dual-key lookup against official Indian CIB&RC "Major Uses of Pesticides" (31-03-2024 register) with ICAR/TNAU/PAU IPM cultural practices.
- **Explainability:** Real-time Grad-CAM saliency heatmaps & bounding box overlays.
- **Dual Interface:**
  1. **RESTful FastAPI Service:** Authenticated with API Key (`X-API-Key` or Bearer token).
  2. **Interactive Streamlit Web UI:** Intuitive visual interface for direct inspection.

---

## 🔐 API Key Configuration (`.env`)

The service uses an API Key for authentication. Configure your credentials in `.env`:

```env
API_KEY=kc_disease_pest_sec_key_2026_prod
API_HOST=0.0.0.0
API_PORT=8002
ALLOWED_ORIGINS=*
```

---

## 🚀 Running the Services

### 1. Start the FastAPI REST Microservice
```powershell
python -m disease_pest_ai.api.main
# Or using uvicorn directly:
uvicorn disease_pest_ai.api.main:app --host 0.0.0.0 --port 8002
```
- Interactive Swagger UI: `http://localhost:8002/docs`
- ReDoc Documentation: `http://localhost:8002/redoc`

### 2. Start the Interactive Streamlit Web UI
```powershell
streamlit run ui/app.py
```
- Web Application: `http://localhost:8501`

---

## 📡 REST API Usage Examples

### Health Check (Public)
```bash
curl -X GET http://localhost:8002/health
```

### Disease & Pest Diagnosis (Requires API Key)

#### Using `curl` with `X-API-Key` Header:
```bash
curl -X POST "http://localhost:8002/api/v1/diagnose" \
  -H "X-API-Key: kc_disease_pest_sec_key_2026_prod" \
  -F "file=@test_data/tomato_early_blight.jpg" \
  -F "crop_name=Tomato" \
  -F "location_state=Maharashtra" \
  -F "growth_stage=fruiting" \
  -F "image_type=leaf" \
  -F "generate_visual_explanation=true"
```

#### Using Python (`requests`):
```python
import requests

url = "http://localhost:8002/api/v1/diagnose"
headers = {"X-API-Key": "kc_disease_pest_sec_key_2026_prod"}
files = {"file": open("test_data/tomato_early_blight.jpg", "rb")}
data = {
    "crop_name": "Tomato",
    "location_state": "Maharashtra",
    "growth_stage": "fruiting",
    "image_type": "leaf",
    "generate_visual_explanation": "true",
}

response = requests.post(url, headers=headers, files=files, data=data)
print(response.json())
```

---

## 🧪 Automated Testing
Run the complete regression suite:
```powershell
pytest tests/ -v
```
All 85 automated tests pass (79 domain & UI tests + 6 API & security tests).

---

## 📜 Statutory Disclaimers
1. All chemical recommendations originate from official CIB&RC registers.
2. AI-assisted diagnosis requires ground field verification before chemical application.
3. Always consult registered physical container labels and local agricultural extension officers.
