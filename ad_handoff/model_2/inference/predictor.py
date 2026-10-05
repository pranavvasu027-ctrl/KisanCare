"""Inference predictor for Model 2: Crop Yield Prediction."""

from dataclasses import dataclass, asdict
from typing import Dict, Any, Union
import pandas as pd
from ad_handoff.model_2.model.loader import load_crop_yield_model
from ad_handoff.model_2.preprocessing.encoder_utils import validate_and_encode_inputs

FEATURE_COLUMNS = [
    "State", "Crop", "Season", "Soil_Type", "Area",
    "Rainfall", "Temperature", "Humidity",
    "Nitrogen", "Phosphorus", "Potassium"
]


@dataclass
class YieldPredictionResult:
    predicted_yield: float
    unit: str
    estimated_production: float
    production_unit: str
    input_summary: Dict[str, Any]
    model_source: str

    def to_dict(self) -> Dict[str, Any]:
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
) -> YieldPredictionResult:
    """Predict crop yield (quintal/hectare) and estimated production (quintal)."""
    if area <= 0:
        raise ValueError(f"Area must be positive, got {area}")

    artifacts = load_crop_yield_model()
    model = artifacts["model"]

    encoded = validate_and_encode_inputs(
        state=state,
        crop=crop,
        season=season,
        soil_type=soil_type,
        encoders=artifacts,
    )

    features_df = pd.DataFrame(
        [[
            encoded["State"],
            encoded["Crop"],
            encoded["Season"],
            encoded["Soil Type"],
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

    return YieldPredictionResult(
        predicted_yield=predicted_yield,
        unit="quintal/hectare",
        estimated_production=estimated_production,
        production_unit="quintal",
        input_summary={
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
        },
        model_source="NIHAL670/Crop-yield",
    )
