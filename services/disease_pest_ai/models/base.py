"""
Base Model Adapter Interface and Crop Validation Helpers.
"""

import abc
import io
import re
from pathlib import Path
from typing import Any, List, Optional, Tuple, Union
from PIL import Image

from disease_pest_ai.schemas.outputs import ConditionType, PredictionResult


# Crop synonyms mapping for normalization
CROP_SYNONYMS = {
    "corn": "corn",
    "maize": "corn",
    "corn maize": "corn",
    "corn (maize)": "corn",
    "bell pepper": "pepper",
    "pepper": "pepper",
    "pepper bell": "pepper",
    "pepper, bell": "pepper",
    "capsicum": "pepper",
    "cherry": "cherry",
    "cherry sour": "cherry",
    "cherry including sour": "cherry",
    "cherry (including sour)": "cherry",
    "sour cherry": "cherry",
    "apple": "apple",
    "tomato": "tomato",
    "tomatoes": "tomato",
    "potato": "potato",
    "potatoes": "potato",
    "grape": "grape",
    "grapes": "grape",
    "peach": "peach",
    "soybean": "soybean",
    "strawberry": "strawberry",
    "squash": "squash",
    "blueberry": "blueberry",
    "orange": "orange",
    "citrus": "orange",
    "cotton": "cotton",
    "cassava": "cassava",
    "rice": "rice",
    "paddy": "rice",
    "cucumber": "cucumber",
    "eggplant": "eggplant",
    "brinjal": "eggplant",
    "banana": "banana",
    "coffee": "coffee",
    "lettuce": "lettuce",
    "cabbage": "cabbage",
    "cauliflower": "cauliflower",
    "garlic": "garlic",
    "ginger": "ginger",
    "basil": "basil",
    "celery": "celery",
    "carrot": "carrot",
}


def normalize_crop_name(name: Optional[str]) -> str:
    """Normalize crop name for canonical comparison."""
    if not name:
        return ""
    clean = re.sub(r"[^\w\s]", " ", name.lower()).strip()
    clean = re.sub(r"\s+", " ", clean)
    return CROP_SYNONYMS.get(clean, clean)


def check_crop_consistency(user_crop: Optional[str], predicted_crop: Optional[str]) -> Tuple[bool, List[str]]:
    """
    Compare user's declared crop with model's predicted crop.
    
    Returns:
        (crop_mismatch: bool, warnings: List[str])
    
    Rules:
    - If user_crop is not provided, crop_mismatch = False.
    - If predicted_crop is unknown / general, crop_mismatch = False.
    - If normalized crops conflict:
        crop_mismatch = True, and explicit warning is added.
    - NEVER silently alter user_crop or predicted_crop.
    """
    if not user_crop or not predicted_crop:
        return False, []

    norm_user = normalize_crop_name(user_crop)
    norm_pred = normalize_crop_name(predicted_crop)

    if norm_pred in ("unknown", "general", "trap", "none"):
        return False, []

    # Check if either contains the other or normalized match
    if norm_user == norm_pred or norm_user in norm_pred or norm_pred in norm_user:
        return False, []

    # Mismatch detected
    warning = (
        f"Crop mismatch detected: User specified crop '{user_crop}', but model "
        f"diagnosed condition for '{predicted_crop}'. The diagnosis may be inaccurate."
    )
    return True, [warning]


def load_image_to_pil(image_source: Union[str, Path, bytes, Image.Image]) -> Image.Image:
    """Load image from path, raw bytes, or return existing PIL Image converted to RGB."""
    if isinstance(image_source, Image.Image):
        return image_source.convert("RGB")
    if isinstance(image_source, (str, Path)):
        p = Path(image_source)
        if not p.exists():
            raise FileNotFoundError(f"Image file does not exist: {p}")
        return Image.open(p).convert("RGB")
    if isinstance(image_source, (bytes, bytearray)):
        return Image.open(io.BytesIO(image_source)).convert("RGB")
    raise TypeError(f"Unsupported image input type: {type(image_source)}")


class BaseModelAdapter(abc.ABC):
    """
    Abstract Base Class for all Disease and Pest Model Adapters.
    """

    model_name: str = "BaseModel"
    model_version: str = "1.0.0"

    @abc.abstractmethod
    def is_available(self) -> bool:
        """Return True if model checkpoint and dependencies are available on system."""
        pass

    @abc.abstractmethod
    def predict(
        self,
        image: Union[str, Path, bytes, Image.Image],
        crop_name: Optional[str] = None,
        location_state: Optional[str] = None,
        growth_stage: Optional[str] = None,
        image_type: Optional[str] = None,
    ) -> PredictionResult:
        """
        Run inference using standardized adapter interface.
        
        Args:
            image: Image file path, bytes, or PIL Image.
            crop_name: User declared crop (optional for prediction, used for validation).
            location_state: Geographic state (for regional validation/treatment lookup).
            growth_stage: Crop phenological stage.
            image_type: Capture type ('leaf', 'trap_sticky_sheet', etc.).
        
        Returns:
            Standardized PredictionResult object.
        """
        pass
