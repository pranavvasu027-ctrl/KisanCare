"""Model loader for Model 1: Crop Recommendation System."""

from pathlib import Path
from typing import Tuple, Any
import joblib
from huggingface_hub import hf_hub_download

MODEL_REPO = "Sheshank2609/crop-recommendation-system"
MODEL_DIR = Path(__file__).resolve().parent

def load_crop_recommendation_model() -> Tuple[Any, Any]:
    """Load model and label encoder, downloading from Hugging Face if not present.

    Returns:
        Tuple of (model, label_encoder)
    """
    model_path = MODEL_DIR / "model1_npk.pkl"
    le_path = MODEL_DIR / "model1_label_encoder.pkl"

    if not model_path.exists():
        model_path = Path(hf_hub_download(repo_id=MODEL_REPO, filename="model1_npk.pkl"))

    if not le_path.exists():
        le_path = Path(hf_hub_download(repo_id=MODEL_REPO, filename="model1_label_encoder.pkl"))

    model = joblib.load(model_path)
    label_encoder = joblib.load(le_path)
    return model, label_encoder
