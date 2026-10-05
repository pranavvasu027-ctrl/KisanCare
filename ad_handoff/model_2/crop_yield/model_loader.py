"""Model loader module for India Crop Yield Prediction.

Loads the pretrained Random Forest Regressor and categorical LabelEncoders
from the Hugging Face repository NIHAL670/Crop-yield.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Tuple
import joblib
from huggingface_hub import hf_hub_download
from sklearn.preprocessing import LabelEncoder

MODEL_SOURCE: str = "NIHAL670/Crop-yield"
MODEL_LOADED: bool = False

REQUIRED_FILES = [
    "model.pkl",
    "le_state.pkl",
    "le_crop.pkl",
    "le_season.pkl",
    "le_soil.pkl",
]

_CACHED_ARTIFACTS: Optional[Dict[str, Any]] = None


def download_artifacts(
    repo_id: str = MODEL_SOURCE,
    cache_dir: Optional[str] = None,
    force_download: bool = False,
) -> Dict[str, str]:
    """Download required model and encoder files from Hugging Face if not cached.

    Args:
        repo_id: Hugging Face repository ID.
        cache_dir: Optional directory to store cached files.
        force_download: If True, forces re-downloading files.

    Returns:
        Dict mapping filename to local file path.
    """
    file_paths: Dict[str, str] = {}
    for filename in REQUIRED_FILES:
        file_path = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            cache_dir=cache_dir,
            force_download=force_download,
        )
        file_paths[filename] = file_path
    return file_paths


def load_model_artifacts(
    repo_id: str = MODEL_SOURCE,
    cache_dir: Optional[str] = None,
    force_reload: bool = False,
) -> Dict[str, Any]:
    """Load model and label encoders into memory.

    Args:
        repo_id: Hugging Face repository ID.
        cache_dir: Optional cache directory.
        force_reload: Force re-download and re-load artifacts.

    Returns:
        Dict containing:
            - 'model': trained Random Forest Regressor
            - 'le_state': LabelEncoder for State
            - 'le_crop': LabelEncoder for Crop
            - 'le_season': LabelEncoder for Season
            - 'le_soil': LabelEncoder for Soil_Type
    """
    global _CACHED_ARTIFACTS, MODEL_LOADED

    if _CACHED_ARTIFACTS is not None and not force_reload:
        return _CACHED_ARTIFACTS

    file_paths = download_artifacts(repo_id=repo_id, cache_dir=cache_dir, force_download=force_reload)

    model = joblib.load(file_paths["model.pkl"])
    le_state: LabelEncoder = joblib.load(file_paths["le_state.pkl"])
    le_crop: LabelEncoder = joblib.load(file_paths["le_crop.pkl"])
    le_season: LabelEncoder = joblib.load(file_paths["le_season.pkl"])
    le_soil: LabelEncoder = joblib.load(file_paths["le_soil.pkl"])

    _CACHED_ARTIFACTS = {
        "model": model,
        "le_state": le_state,
        "le_crop": le_crop,
        "le_season": le_season,
        "le_soil": le_soil,
    }
    MODEL_LOADED = True

    return _CACHED_ARTIFACTS


def get_model_status() -> Dict[str, Any]:
    """Return status information for the crop yield model."""
    return {
        "MODEL_SOURCE": MODEL_SOURCE,
        "MODEL_LOADED": MODEL_LOADED,
    }


def get_supported_categories(
    repo_id: str = MODEL_SOURCE, cache_dir: Optional[str] = None
) -> Dict[str, List[str]]:
    """Return all supported categories directly from the loaded label encoders."""
    artifacts = load_model_artifacts(repo_id=repo_id, cache_dir=cache_dir)
    return {
        "states": sorted(list(artifacts["le_state"].classes_)),
        "crops": sorted(list(artifacts["le_crop"].classes_)),
        "seasons": sorted(list(artifacts["le_season"].classes_)),
        "soil_types": sorted(list(artifacts["le_soil"].classes_)),
    }


def validate_categorical_inputs(
    state: str,
    crop: str,
    season: str,
    soil_type: str,
    artifacts: Optional[Dict[str, Any]] = None,
) -> None:
    """Validate that categorical inputs exist in the encoder classes.

    Raises:
        ValueError: If any input category is unsupported, detailing valid options.
    """
    if artifacts is None:
        artifacts = load_model_artifacts()

    checks: List[Tuple[str, str, LabelEncoder]] = [
        ("State", state, artifacts["le_state"]),
        ("Crop", crop, artifacts["le_crop"]),
        ("Season", season, artifacts["le_season"]),
        ("Soil Type", soil_type, artifacts["le_soil"]),
    ]

    for label, val, encoder in checks:
        if val not in encoder.classes_:
            valid_options = ", ".join(f"'{c}'" for c in encoder.classes_)
            raise ValueError(
                f"Unsupported {label}: '{val}'. Valid options are: [{valid_options}]"
            )
