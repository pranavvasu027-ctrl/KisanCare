# Crop Recommendation System — Hugging Face Integration

This module integrates the official dual-model **Crop Recommendation System** for Maharashtra from Hugging Face:
- **Repository:** [`Sheshank2609/crop-recommendation-system`](https://huggingface.co/Sheshank2609/crop-recommendation-system)
- **Pinned Revision:** `f24d6e1666bb9efa530de8f4aec0124cd83c8cfd`
- **License:** MIT License
- **Author Attribution:** Sheshank2609

---

## 1. System Architecture

The recommendation engine combines **soil chemistry and climate science** with **26 years of historical agricultural statistics (1997–2022)** from Maharashtra:

```
                  ┌──────────────────────────────────────────────┐
                  │          Farmer Agronomic Inputs             │
                  │   N, P, K, Temp, Humidity, pH, Rainfall      │
                  │              District & Season               │
                  └──────────────┬───────────────────────────────┘
                                 │
                 ┌───────────────┴───────────────┐
                 ▼                               ▼
  ┌─────────────────────────────┐ ┌─────────────────────────────┐
  │           Model 1           │ │           Model 2           │
  │     Soil & Climate RF       │ │     Regional Viability      │
  │     (RandomForestClassifier)│ │     (Empirical Scoring)     │
  │  2,200 samples / 22 crops   │ │  35 districts × 4 seasons   │
  │    Outputs: Probabilities   │ │   Outputs: Viability Score  │
  └──────────────┬──────────────┘ └──────────────┬──────────────┘
                 │ (Weight: w₁ = 0.60)           │ (Weight: w₂ = 0.40)
                 └───────────────┬───────────────┘
                                 ▼
                  ┌──────────────────────────────┐
                  │    Blended Decision Engine   │
                  │   Combined Score = w₁·S₁ + w₂·S₂  │
                  │  + Transparent Water Rules   │
                  └──────────────┬───────────────┘
                                 ▼
                  ┌──────────────────────────────┐
                  │    Ranked Recommendations    │
                  │  (Score, Labels, Reasoning)  │
                  └──────────────────────────────┘
```

---

## 2. Model 1 — Soil & Climate Random Forest Classifier

Predicts crop probabilities based on laboratory soil tests and climatic parameters.

- **Artifacts:** `model1_npk.pkl`, `model1_label_encoder.pkl`
- **Algorithm:** Scikit-Learn `RandomForestClassifier` (100–200 estimators)
- **Classes:** 22 crops (`apple`, `banana`, `blackgram`, `chickpea`, `coconut`, `coffee`, `cotton`, `grapes`, `jute`, `kidneybeans`, `lentil`, `maize`, `mango`, `mothbeans`, `mungbean`, `muskmelon`, `orange`, `papaya`, `pigeonpeas`, `pomegranate`, `rice`, `watermelon`)
- **Required Feature Order:**
  ```python
  ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]
  ```

### Valid Feature Boundaries

| Feature | Min | Max | Unit |
|---|---|---|---|
| **N** (Nitrogen) | 0.0 | 300.0 | mg/kg or kg/ha |
| **P** (Phosphorus) | 0.0 | 300.0 | mg/kg or kg/ha |
| **K** (Potassium) | 0.0 | 300.0 | mg/kg or kg/ha |
| **Temperature** | 5.0 | 50.0 | °C |
| **Humidity** | 10.0 | 100.0 | % |
| **pH** | 3.5 | 9.5 | pH unit |
| **Rainfall** | 20.0 | 3000.0 | mm |

---

## 3. Model 2 — Regional Suitability Scoring Table

Scores crops based on 26 years of district-level agricultural data (1997–2022) across Maharashtra.

- **Artifact:** `model2_full_scored.csv` (1,603 rows)
- **Coverage:** 35 Maharashtra districts × 4 seasons (`Kharif`, `Rabi`, `Summer`, `Whole Year`) × 33 crops
- **District Coverage:**
  Ahilyanagar, Akola, Amravati, Beed, Bhandara, Buldhana, Chandrapur, Chhatrapati Sambhajinagar, Dharashiv, Dhule, Gadchiroli, Gondia, Hingoli, Jalgaon, Jalna, Kolhapur, Latur, Mumbai suburban, Nagpur, Nanded, Nandurbar, Nashik, Palghar, Parbhani, Pune, Raigad, Ratnagiri, Sangli, Satara, Sindhudurg, Solapur, Thane, Wardha, Washim, Yavatmal.
- **Scoring Formula (Documented in Model Card):**
  $$\text{Score} = 0.35 \times \text{Frequency} + 0.25 \times \text{Historical Presence} + 0.20 \times \text{Avg Yield} + 0.10 \times \text{Dominance} + 0.05 \times \text{Recent Growth} + 0.05 \times \text{Stability}$$

### Suitability Categorization

| Categorical Label | Score Threshold | Interpretation |
|---|---|---|
| 🟢 **Highly Suitable** | $\ge 75\%$ | Strongly established agronomic record in selected district/season |
| 🟡 **Moderately Suitable** | $50\% - 74.9\%$ | Moderate historical cultivation with acceptable performance |
| 🟠 **Low Suitability** | $30\% - 49.9\%$ | Marginal or opportunistic regional evidence |
| 🔴 **Not Recommended** | $< 30\%$ | Scant or no historical adaptation in selected district/season |

---

## 4. Multi-Criteria Combined Scoring

$$\text{Final Score} = w_1 \times \text{Model1\_probability} + w_2 \times \text{Model2\_score}$$

- Default weights: $w_1 = 0.60$ (Soil/Climate), $w_2 = 0.40$ (Regional Viability).
- **Important Distinction:** The final combined score is a multi-criteria decision metric and is **not** a calibrated single-distribution probability. Model probabilities and regional viability scores are reported separately.

---

## 5. Transparent Water Availability Decision Constraints

Water-availability rules are applied as an explicit, transparent decision constraint rather than distorting raw ML probabilities:
- High water-demand crops (e.g. Sugarcane: ~1,800 mm, Rice: ~1,200 mm, Banana: ~1,500 mm) flagged when planted in "Strictly Rainfed" settings or low rainfall (< 800 mm).
- A transparent warning (`water_constrained = true`) is surfaced in the response without fabricating scores.

---

## 6. Runtime Artifact Caching & Network Configuration

Model binaries and lookup tables are **not stored in the Git repository**. They are downloaded and cached at runtime using `huggingface_hub`:

```python
from huggingface_hub import hf_hub_download

m1_path = hf_hub_download(
    repo_id="Sheshank2609/crop-recommendation-system",
    filename="model1_npk.pkl",
    revision="f24d6e1666bb9efa530de8f4aec0124cd83c8cfd",
)
```

- Cache location defaults to `~/.cache/huggingface/hub` or can be overridden via `MODEL_CACHE_DIR` / `HF_HOME`.
- Offline deployment: Pre-populate the cache directory during Docker build.

---

## 7. API Endpoints

- `POST /api/v1/crop-recommendation`: Primary versioned recommendation endpoint.
- `POST /api/v1/recommend`: Backward-compatible recommendation endpoint.
- `POST /predict/crop`: Flexible ML microservice forwarder.
