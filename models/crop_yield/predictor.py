"""Crop Yield Predictor module."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional, Union
import pandas as pd

from models.crop_yield.model_loader import (
    MODEL_SOURCE,
    load_model_artifacts,
    validate_categorical_inputs,
)

FEATURE_COLUMNS = [
    "State",
    "Crop",
    "Season",
    "Soil_Type",
    "Area",
    "Rainfall",
    "Temperature",
    "Humidity",
    "Nitrogen",
    "Phosphorus",
    "Potassium",
]

YIELD_UNIT = "quintal/hectare"
PRODUCTION_UNIT = "quintal"


@dataclass
class YieldPredictionResult:
    """Structured result returned by predict_crop_yield."""

    predicted_yield: float
    yield_unit: str
    estimated_production: float
    production_unit: str
    cultivated_area_hectares: float
    input_summary: Dict[str, Any]
    model_source: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


def predict_crop_yield(
    state: str,
    crop: str,
    season: str,
    soil_type: str,
    area: Union[int, float],
    rainfall: Union[int, float],
    temperature: Union[int, float],
    humidity: Union[int, float],
    nitrogen: Union[int, float],
    phosphorus: Union[int, float],
    potassium: Union[int, float],
    cache_dir: Optional[str] = None,
) -> YieldPredictionResult:
    """Predict crop yield (quintal/hectare) and calculate estimated total production (quintal)."""
    if area <= 0:
        raise ValueError(f"Area must be positive, got {area}")

    artifacts = load_model_artifacts(cache_dir=cache_dir)
    model = artifacts["model"]
    le_state = artifacts["le_state"]
    le_crop = artifacts["le_crop"]
    le_season = artifacts["le_season"]
    le_soil = artifacts["le_soil"]

    # Validate categories against trained encoder classes
    validate_categorical_inputs(state, crop, season, soil_type, artifacts=artifacts)

    # Encode categorical features
    state_enc = int(le_state.transform([state])[0])
    crop_enc = int(le_crop.transform([crop])[0])
    season_enc = int(le_season.transform([season])[0])
    soil_enc = int(le_soil.transform([soil_type])[0])

    features_df = pd.DataFrame(
        [[
            state_enc,
            crop_enc,
            season_enc,
            soil_enc,
            float(area),
            float(rainfall),
            float(temperature),
            float(humidity),
            float(nitrogen),
            float(phosphorus),
            float(potassium),
        ]],
        columns=FEATURE_COLUMNS,
    )

    prediction = model.predict(features_df)
    predicted_yield = float(prediction[0])
    estimated_production = float(predicted_yield * float(area))

    input_summary = {
        "state": state,
        "crop": crop,
        "season": season,
        "soil_type": soil_type,
        "area": float(area),
        "rainfall": float(rainfall),
        "temperature": float(temperature),
        "humidity": float(humidity),
        "nitrogen": float(nitrogen),
        "phosphorus": float(phosphorus),
        "potassium": float(potassium),
    }

    return YieldPredictionResult(
        predicted_yield=predicted_yield,
        yield_unit=YIELD_UNIT,
        estimated_production=estimated_production,
        production_unit=PRODUCTION_UNIT,
        cultivated_area_hectares=float(area),
        input_summary=input_summary,
        model_source=MODEL_SOURCE,
    )
