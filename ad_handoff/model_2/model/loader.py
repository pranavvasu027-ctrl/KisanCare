"""Artifact loader for Model 2: Crop Yield Prediction."""

from pathlib import Path
from typing import Dict, Any, Optional
import joblib
from huggingface_hub import hf_hub_download

MODEL_REPO = "NIHAL670/Crop-yield"
CURRENT_DIR = Path(__file__).resolve().parent

REQUIRED_FILES = [
    "model.pkl",
    "le_state.pkl",
    "le_crop.pkl",
    "le_season.pkl",
    "le_soil.pkl",
]

_CACHED_ARTIFACTS: Optional[Dict[str, Any]] = None


def load_crop_yield_model(cache_dir: Optional[str] = None) -> Dict[str, Any]:
    """Load model and label encoders, downloading from Hugging Face if not present.

    Returns:
        Dict containing 'model', 'le_state', 'le_crop', 'le_season', 'le_soil'.
    """
    global _CACHED_ARTIFACTS
    if _CACHED_ARTIFACTS is not None:
        return _CACHED_ARTIFACTS

    file_paths: Dict[str, Path] = {}
    for filename in REQUIRED_FILES:
        local_candidate = CURRENT_DIR / filename
        if local_candidate.exists() and local_candidate.stat().st_size > 0:
            file_paths[filename] = local_candidate
        else:
            downloaded = hf_hub_download(
                repo_id=MODEL_REPO,
                filename=filename,
                cache_dir=cache_dir,
            )
            file_paths[filename] = Path(downloaded)

    _CACHED_ARTIFACTS = {
        "model": joblib.load(file_paths["model.pkl"]),
        "le_state": joblib.load(file_paths["le_state.pkl"]),
        "le_crop": joblib.load(file_paths["le_crop.pkl"]),
        "le_season": joblib.load(file_paths["le_season.pkl"]),
        "le_soil": joblib.load(file_paths["le_soil.pkl"]),
    }
    return _CACHED_ARTIFACTS
