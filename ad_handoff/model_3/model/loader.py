"""Model artifact loader for Model 3: Crop Disease & Pest Diagnosis."""

from pathlib import Path
from typing import Tuple, Any, Optional
from huggingface_hub import hf_hub_download
import torch

DISEASE_REPO = "BiernyVR/crop-disease-classifier"
PEST_REPO = "underdogquality/yolo11s-pest-detection"
CURRENT_DIR = Path(__file__).resolve().parent

def load_disease_model(cache_dir: Optional[str] = None) -> Path:
    """Download/locate EfficientNetV2-S disease classification weights.

    Returns:
        Path to the local .pth checkpoint file.
    """
    local_pth = CURRENT_DIR / "efficientnet_v2_s_best.pth"
    if local_pth.exists() and local_pth.stat().st_size > 0:
        return local_pth

    downloaded = hf_hub_download(
        repo_id=DISEASE_REPO,
        filename="efficientnet_v2_s_best.pth",
        cache_dir=cache_dir,
    )
    return Path(downloaded)


def load_pest_model(cache_dir: Optional[str] = None) -> Path:
    """Download/locate YOLO11s pest detection weights.

    Returns:
        Path to the local .pt checkpoint file.
    """
    local_pt = CURRENT_DIR / "best.pt"
    if local_pt.exists() and local_pt.stat().st_size > 0:
        return local_pt

    downloaded = hf_hub_download(
        repo_id=PEST_REPO,
        filename="best.pt",
        cache_dir=cache_dir,
    )
    return Path(downloaded)
