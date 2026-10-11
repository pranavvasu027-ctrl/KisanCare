"""Model loader module for Crop Yield Prediction.

Loads the pretrained Random Forest Regressor and categorical LabelEncoders
from the Hugging Face repository NIHAL670/Crop-yield or local directory.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import joblib
from huggingface_hub import hf_hub_download
from sklearn.preprocessing import LabelEncoder

MODEL_SOURCE: str = os.getenv("CROP_YIELD_REPO_ID", "NIHAL670/Crop-yield")
MODEL_LOADED: bool = False

CURRENT_DIR = Path(__file__).resolve().parent

REQUIRED_ENCODERS = [
    "le_state.pkl",
    "le_crop.pkl",
    "le_season.pkl",
    "le_soil.pkl",
]

_CACHED_ARTIFACTS: Optional[Dict[str, Any]] = None


def resolve_artifact_path(
    filename: str,
    repo_id: str = MODEL_SOURCE,
    cache_dir: Optional[str] = None,
) -> Path:
    """Find artifact in local directory or download from Hugging Face."""
    local_path = CURRENT_DIR / filename
    if local_path.exists() and local_path.stat().st_size > 0:
        return local_path

    # Download from Hugging Face
    try:
        downloaded = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            cache_dir=cache_dir,
        )
        return Path(downloaded)
    except Exception as exc:
        raise RuntimeError(
            f"Failed to retrieve model artifact '{filename}' from Hugging Face repository '{repo_id}': {str(exc)}. "
            "Please check network connectivity or verify the repository identifier in CROP_YIELD_REPO_ID."
        ) from exc


def load_model_artifacts(
    repo_id: str = MODEL_SOURCE,
    cache_dir: Optional[str] = None,
    force_reload: bool = False,
) -> Dict[str, Any]:
    """Load model and label encoders into memory once and cache.

    Returns:
        Dict containing 'model', 'le_state', 'le_crop', 'le_season', 'le_soil'.
    """
    global _CACHED_ARTIFACTS, MODEL_LOADED

    if _CACHED_ARTIFACTS is not None and not force_reload:
        return _CACHED_ARTIFACTS

    model_path = resolve_artifact_path("model.pkl", repo_id=repo_id, cache_dir=cache_dir)
    model = joblib.load(model_path)

    encoders: Dict[str, LabelEncoder] = {}
    for enc_name in REQUIRED_ENCODERS:
        enc_path = resolve_artifact_path(enc_name, repo_id=repo_id, cache_dir=cache_dir)
        key = enc_name.replace(".pkl", "")
        encoders[key] = joblib.load(enc_path)

    _CACHED_ARTIFACTS = {
        "model": model,
        "le_state": encoders["le_state"],
        "le_crop": encoders["le_crop"],
        "le_season": encoders["le_season"],
        "le_soil": encoders["le_soil"],
    }
    MODEL_LOADED = True
    return _CACHED_ARTIFACTS


def get_model_status() -> Dict[str, Any]:
    """Return status information for the crop yield model."""
    return {
        "MODEL_SOURCE": MODEL_SOURCE,
        "MODEL_LOADED": MODEL_LOADED,
    }


def get_supported_categories(artifacts: Optional[Dict[str, Any]] = None) -> Dict[str, List[str]]:
    """Return all supported categories directly from the loaded label encoders."""
    if artifacts is None:
        artifacts = load_model_artifacts()
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
    """Validate that categorical inputs exist in the encoder classes."""
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
            valid_options = ", ".join(f"'{c}'" for c in encoder.classes_[:10]) + ("..." if len(encoder.classes_) > 10 else "")
            raise ValueError(
                f"Unsupported {label}: '{val}'. Valid options include: [{valid_options}]"
            )
