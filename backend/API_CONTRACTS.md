# KISANcare backend API contracts

All public backend routes are prefixed with `/api/v1`. The backend forwards ML
requests to `ML_SERVICE_URL` (default `http://localhost:8001`) with a bounded
timeout controlled by `ML_SERVICE_TIMEOUT_SECONDS` (default `8`).

## Crop recommendation

`POST /api/v1/crop-recommendation`

```json
{"district":"NASHIK","season":"Kharif","water_availability":"Medium","top_k":3}
```

The request is forwarded unchanged to ML at
`POST /api/v1/crop-recommendation`. A model response contains the model's
`status` and `recommendations`; callers must treat recommendation scores as
model-specific suitability values, not accuracy. Invalid client payloads are
`422`; upstream client/model validation is forwarded as its `4xx` response.

If the ML service cannot be reached, the backend returns `503` with
`detail.code = "ml_service_unavailable"`; an upstream timeout returns `504`
with `detail.code = "ml_service_timeout"`. Set
`ML_MOCK_FALLBACK_ENABLED=true` only for demos to return the existing crop
fallback. That result has `status: "mock"`, `is_mock: true`, and
`data_provenance: "backend_mock_fallback"`; it is not a prediction.

## Rule-based and market endpoints

The following proxy to their matching ML endpoints and preserve the JSON body:

| Backend route | Required request fields | ML route |
| --- | --- | --- |
| `POST /market-price` | `crop`, `market`, `date` | `/api/v1/models/market-price` |
| `POST /disease-detection` | `crop`, non-empty `symptoms` | `/api/v1/models/disease-detection` |
| `POST /pest-detection` | `crop`, non-empty `symptoms` | `/api/v1/models/pest-detection` |
| `POST /soil-assessment` | `n`, `p`, `k`, `ph` (0–14) | `/api/v1/models/soil-assessment` |
| `POST /yield-prediction` | `crop`, positive `area_acres`, `soil_health_score`, `weather_score` | `/api/v1/models/yield-prediction` |
| `POST /irrigation` | `crop`, `soil_moisture` (0–100), non-negative `days_since_rain` | `/api/v1/models/irrigation` |
| `POST /weather-risk` | `temperature`, `humidity` (0–100), non-negative `rainfall_forecast` | `/api/v1/models/weather-risk` |

For every proxy route, malformed upstream JSON is a `502` with
`detail.code = "ml_service_invalid_response"`; upstream `5xx` responses are
mapped to the explicit `503` availability response. No proxy endpoint makes a
successful-looking fallback except the opt-in crop demo fallback above.

## Backend-owned mock routes

`GET /api/v1/digital-twin/{farm_id}` and `POST /api/v1/farms` are MVP mock
routes. Their responses include `is_mock: true` and must not be treated as
persisted Supabase data. They are separate from authenticated ML farm routes
under the ML service's `/api/v1/farms` prefix.
