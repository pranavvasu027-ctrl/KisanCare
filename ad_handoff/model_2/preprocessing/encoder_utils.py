"""Preprocessing utilities for Model 2: Crop Yield Prediction."""

from typing import Dict, List, Any
from sklearn.preprocessing import LabelEncoder


def validate_and_encode_inputs(
    state: str,
    crop: str,
    season: str,
    soil_type: str,
    encoders: Dict[str, LabelEncoder],
) -> Dict[str, int]:
    """Validate and encode categorical features.

    Raises:
        ValueError: If any category is not recognized by the corresponding encoder.
    """
    field_mapping = [
        ("State", state, encoders["le_state"]),
        ("Crop", crop, encoders["le_crop"]),
        ("Season", season, encoders["le_season"]),
        ("Soil Type", soil_type, encoders["le_soil"]),
    ]

    encoded = {}
    for label, val, enc in field_mapping:
        if val not in enc.classes_:
            valid = ", ".join(f"'{c}'" for c in enc.classes_[:10]) + ("..." if len(enc.classes_) > 10 else "")
            raise ValueError(f"Unsupported {label}: '{val}'. Valid options include: [{valid}]")
        encoded[label] = int(enc.transform([val])[0])

    return encoded
