"""Crop Yield Predictor module.

Provides the primary inference function for predicting crop yield using
the pretrained Hugging Face model from NIHAL670/Crop-yield.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional, Union
import numpy as np
import pandas as pd

from crop_yield.model_loader import (
    MODEL_SOURCE,
    load_model_artifacts,
    validate_categorical_inputs,
)

# Feature ordering matching the original training script and model training
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
class PredictionResult:
    """Structured result returned by predict_yield."""

    predicted_yield: float
    unit: str
    estimated_production: float
    input_summary: Dict[str, Any]
    model_source: str
    production_unit: str = PRODUCTION_UNIT

    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a Python dictionary."""
        return asdict(self)

    def __getitem__(self, key: str) -> Any:
        """Allow dict-like indexing (e.g. result['predicted_yield'])."""
        return getattr(self, key)


def predict_yield(
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
) -> PredictionResult:
    """Predict crop yield and calculate estimated total production.

    Unit & Conversion Rationale:
        In the source Indian agriculture dataset and training pipeline (train_model.py),
        Yield is computed as:
            Yield = Production / Area
        where Production is in quintals (1 quintal = 100 kg) and Area is in hectares.
        Thus, the model's regression output represents Yield in 'quintal/hectare'.
        Estimated Production is mathematically derived as:
            Production = predicted_yield * area  [quintal = (quintal/hectare) * hectare]
        No external conversion factor is required or invented.

    Args:
        state: Name of the Indian State (e.g. 'Maharashtra').
        crop: Name of the crop (e.g. 'Rice').
        season: Agricultural season ('Kharif', 'Rabi', 'Summer', 'Whole Year').
        soil_type: Soil category ('Alluvial', 'Black', 'Clay', 'Laterite', 'Red').
        area: Cultivated land area in hectares.
        rainfall: Average rainfall in millimeters (mm).
        temperature: Temperature in degrees Celsius (°C).
        humidity: Relative humidity percentage (%).
        nitrogen: Soil Nitrogen (N) content.
        phosphorus: Soil Phosphorus (P) content.
        potassium: Soil Potassium (K) content.
        cache_dir: Optional custom cache directory for downloaded artifacts.

    Returns:
        PredictionResult with predicted_yield, unit, estimated_production,
        input_summary, and model_source.

    Raises:
        ValueError: If categorical inputs are unsupported or numeric inputs are invalid.
    """
    # 1. Validate numeric inputs
    if area <= 0:
        raise ValueError(f"Area must be positive, got {area}")

    # 2. Load model & encoders
    artifacts = load_model_artifacts(cache_dir=cache_dir)
    model = artifacts["model"]
    le_state = artifacts["le_state"]
    le_crop = artifacts["le_crop"]
    le_season = artifacts["le_season"]
    le_soil = artifacts["le_soil"]

    # 3. Validate categorical inputs against encoder classes
    validate_categorical_inputs(state, crop, season, soil_type, artifacts=artifacts)

    # 4. Encode categorical features
    state_enc = int(le_state.transform([state])[0])
    crop_enc = int(le_crop.transform([crop])[0])
    season_enc = int(le_season.transform([season])[0])
    soil_enc = int(le_soil.transform([soil_type])[0])

    # 5. Build feature dataframe matching the exact training columns
    features_df = pd.DataFrame(
        [
            [
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
            ]
        ],
        columns=FEATURE_COLUMNS,
    )

    # 6. Execute prediction
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

    return PredictionResult(
        predicted_yield=predicted_yield,
        unit=YIELD_UNIT,
        estimated_production=estimated_production,
        input_summary=input_summary,
        model_source=MODEL_SOURCE,
        production_unit=PRODUCTION_UNIT,
    )
