# API Contract

## Core Endpoints

### Farms & Digital Twin
- `POST /api/v1/farms` - Create a new farm profile.
- `GET /api/v1/farms/{farm_id}` - Get farm profile.
- `GET /api/v1/farms/{farm_id}/digital-twin` - Get the current state of the farm's digital twin.

### Predictions (Forwarded to ML/Decision Engine)
- `POST /api/v1/predict/crop`
- `POST /api/v1/predict/yield`
- `POST /api/v1/predict/risk`
- `POST /api/v1/predict/price`

**Prediction Response Standard:**
```json
{
  "prediction": "...",
  "confidence": 0.82,
  "unit": "...",
  "factors": ["factor1", "factor2"],
  "limitations": ["limitation1"]
}
```

### Economics
- `POST /api/v1/economics/calculate`

### Simulation
- `POST /api/v1/simulate`

**Simulation Request:**
```json
{
  "farm_id": "F001",
  "changes": {
    "crop": "soybean",
    "rainfall_change_percent": -20
  }
}
```

**Simulation Response:**
```json
{
  "baseline": {
    "yield": 24,
    "cost": 30000,
    "revenue": 60000,
    "profit": 30000,
    "risk": 0.35
  },
  "scenario": {
    "yield": 20,
    "cost": 31000,
    "revenue": 50000,
    "profit": 19000,
    "risk": 0.52
  },
  "differences": {},
  "explanation": []
}
```

### Decision & Copilot
- `POST /api/v1/decision/recommend`
- `POST /api/v1/copilot/query`
