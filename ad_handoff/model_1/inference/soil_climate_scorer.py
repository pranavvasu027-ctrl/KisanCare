"""Soil and Climate Scoring Layer.

Integrates the official Hugging Face Random Forest model:
  Repo: Sheshank2609/crop-recommendation-system
  Model: model1_npk.pkl
  Label Encoder: model1_label_encoder.pkl

Required feature order:
  1. N
  2. P
  3. K
  4. temperature
  5. humidity
  6. ph
  7. rainfall

Maintains an explicit, clearly labeled fallback agronomic scoring engine
if the model cannot be loaded or for crops outside the model's 22 classes.
"""

import logging
import math
import warnings
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import pandas as pd
import joblib

logger = logging.getLogger(__name__)

HF_REPO_ID: str = "Sheshank2609/crop-recommendation-system"
MODEL_FILE: str = "model1_npk.pkl"
LABEL_ENCODER_FILE: str = "model1_label_encoder.pkl"
LOCAL_MODEL_DIR: Path = Path(__file__).resolve().parent / "hf_model"

FEATURE_ORDER: List[str] = [
    "N",
    "P",
    "K",
    "temperature",
    "humidity",
    "ph",
    "rainfall"
]

# Global module status indicators
MODEL_SOURCE: str = f"Hugging Face: {HF_REPO_ID}"
MODEL_LOADED: bool = False
MODEL_TYPE: Optional[str] = None


# Explicit fallback profiles for crops outside the HF 22-class set or offline fallback
FALLBACK_CROP_PROFILES: Dict[str, Dict[str, Dict[str, float]]] = {
    "sugarcane": {"N": {"opt": 120, "tol": 35}, "P": {"opt": 60, "tol": 25}, "K": {"opt": 70, "tol": 25}, "temp": {"opt": 27, "tol": 6}, "humidity": {"opt": 75, "tol": 15}, "ph": {"opt": 6.8, "tol": 1.0}, "rainfall": {"opt": 150, "tol": 50}},
    "wheat": {"N": {"opt": 70, "tol": 30}, "P": {"opt": 50, "tol": 20}, "K": {"opt": 40, "tol": 20}, "temp": {"opt": 20, "tol": 6}, "humidity": {"opt": 60, "tol": 15}, "ph": {"opt": 6.8, "tol": 1.0}, "rainfall": {"opt": 80, "tol": 40}},
    "mustard": {"N": {"opt": 60, "tol": 25}, "P": {"opt": 45, "tol": 20}, "K": {"opt": 35, "tol": 15}, "temp": {"opt": 20, "tol": 6}, "humidity": {"opt": 60, "tol": 15}, "ph": {"opt": 7.0, "tol": 1.0}, "rainfall": {"opt": 55, "tol": 30}},
    "soybean": {"N": {"opt": 30, "tol": 15}, "P": {"opt": 60, "tol": 20}, "K": {"opt": 40, "tol": 15}, "temp": {"opt": 26, "tol": 5}, "humidity": {"opt": 70, "tol": 15}, "ph": {"opt": 6.5, "tol": 0.8}, "rainfall": {"opt": 90, "tol": 35}},
    "groundnut": {"N": {"opt": 25, "tol": 15}, "P": {"opt": 45, "tol": 20}, "K": {"opt": 35, "tol": 15}, "temp": {"opt": 27, "tol": 5}, "humidity": {"opt": 65, "tol": 15}, "ph": {"opt": 6.5, "tol": 0.8}, "rainfall": {"opt": 70, "tol": 30}},
    "potato": {"N": {"opt": 110, "tol": 30}, "P": {"opt": 70, "tol": 25}, "K": {"opt": 120, "tol": 35}, "temp": {"opt": 18, "tol": 5}, "humidity": {"opt": 70, "tol": 15}, "ph": {"opt": 5.8, "tol": 0.8}, "rainfall": {"opt": 70, "tol": 30}},
    "tomato": {"N": {"opt": 90, "tol": 30}, "P": {"opt": 60, "tol": 20}, "K": {"opt": 70, "tol": 25}, "temp": {"opt": 23, "tol": 6}, "humidity": {"opt": 65, "tol": 15}, "ph": {"opt": 6.5, "tol": 0.8}, "rainfall": {"opt": 80, "tol": 35}},
    "bajra": {"N": {"opt": 45, "tol": 25}, "P": {"opt": 25, "tol": 15}, "K": {"opt": 25, "tol": 15}, "temp": {"opt": 30, "tol": 7}, "humidity": {"opt": 45, "tol": 20}, "ph": {"opt": 7.2, "tol": 1.2}, "rainfall": {"opt": 45, "tol": 25}},
    "jowar": {"N": {"opt": 55, "tol": 25}, "P": {"opt": 35, "tol": 18}, "K": {"opt": 35, "tol": 18}, "temp": {"opt": 28, "tol": 6}, "humidity": {"opt": 50, "tol": 20}, "ph": {"opt": 7.0, "tol": 1.0}, "rainfall": {"opt": 60, "tol": 30}},
    "onion": {"N": {"opt": 60, "tol": 25}, "P": {"opt": 40, "tol": 20}, "K": {"opt": 50, "tol": 20}, "temp": {"opt": 22, "tol": 6}, "humidity": {"opt": 60, "tol": 15}, "ph": {"opt": 6.8, "tol": 0.8}, "rainfall": {"opt": 65, "tol": 30}},
}


class SoilClimateScorer:
    """Computes SoilClimateScore using the real Hugging Face model

    Sheshank2609/crop-recommendation-system.
    """

    def __init__(self, force_fallback: bool = False):
        self.force_fallback = force_fallback
        self.model = None
        self.label_encoder = None
        self.model_loaded = False
        self.model_source = "Uninitialized"
        self.classes: List[str] = []

        if not force_fallback:
            self._load_huggingface_model()
        else:
            self.model_source = "Explicit Fallback Agronomic Scorer"
            self.model_loaded = False

    def _load_huggingface_model(self) -> None:
        """Loads model1_npk.pkl and model1_label_encoder.pkl from local directory or Hugging Face Hub."""
        global MODEL_LOADED, MODEL_SOURCE, MODEL_TYPE
        model_path = LOCAL_MODEL_DIR / MODEL_FILE
        le_path = LOCAL_MODEL_DIR / LABEL_ENCODER_FILE

        try:
            # 1. Try local package directory first
            if not (model_path.exists() and le_path.exists()):
                logger.info(f"Local model files not found in {LOCAL_MODEL_DIR}. Downloading from Hugging Face Hub: {HF_REPO_ID}...")
                from huggingface_hub import hf_hub_download
                LOCAL_MODEL_DIR.mkdir(parents=True, exist_ok=True)
                downloaded_m = hf_hub_download(repo_id=HF_REPO_ID, filename=MODEL_FILE)
                downloaded_le = hf_hub_download(repo_id=HF_REPO_ID, filename=LABEL_ENCODER_FILE)
                import shutil
                shutil.copy(downloaded_m, model_path)
                shutil.copy(downloaded_le, le_path)

            # Load pickles with warnings suppressed for scikit-learn version differences
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                self.model = joblib.load(model_path)
                self.label_encoder = joblib.load(le_path)

            self.model_loaded = True
            self.model_source = f"Hugging Face: {HF_REPO_ID}"
            self.classes = [c.lower() for c in self.label_encoder.classes_]

            MODEL_LOADED = True
            MODEL_SOURCE = self.model_source
            MODEL_TYPE = type(self.model).__name__

            logger.info(f"MODEL_SOURCE = \"{self.model_source}\"")
            logger.info(f"MODEL_LOADED = {self.model_loaded}")
            logger.info(f"MODEL_TYPE = {MODEL_TYPE}")
            logger.info(f"Loaded {len(self.classes)} classes from Hugging Face model.")

        except Exception as e:
            logger.warning(f"Could not load Hugging Face model ({e}). Using Fallback Agronomic Scorer.")
            self.model = None
            self.label_encoder = None
            self.model_loaded = False
            self.model_source = f"Fallback Agronomic Scorer (Failed loading HF model: {e})"
            MODEL_LOADED = False
            MODEL_SOURCE = self.model_source

    def predict_model_probabilities(self, soil_climate: Any) -> Dict[str, float]:
        """Runs inference through the real Hugging Face Random Forest model.

        Enforces the exact feature order:
          N, P, K, Temperature, Humidity, pH, Rainfall
        """
        if not self.model_loaded or self.model is None:
            return {}

        temp = float(soil_climate.temperature if soil_climate.temperature is not None else 25.0)
        hum = float(soil_climate.humidity if soil_climate.humidity is not None else 70.0)
        ph = float(soil_climate.ph if soil_climate.ph is not None else 6.5)
        rain = float(soil_climate.rainfall if soil_climate.rainfall is not None else 100.0)

        # Build feature DataFrame with exact names and order expected by model1_npk.pkl
        features_df = pd.DataFrame(
            [[
                float(soil_climate.N),
                float(soil_climate.P),
                float(soil_climate.K),
                temp,
                hum,
                ph,
                rain,
            ]],
            columns=FEATURE_ORDER
        )

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            probas = self.model.predict_proba(features_df)[0]

        return {str(cls_name).lower(): float(p) for cls_name, p in zip(self.label_encoder.classes_, probas)}

    def score(self, candidate_crop: str, soil_climate: Any) -> Tuple[float, str]:
        """Computes the SoilClimateScore in [0.0, 1.0].

        Returns:
            Tuple of (score, score_source)
        """
        cand_clean = candidate_crop.strip().lower()

        # 1. Try real Hugging Face model prediction
        if self.model_loaded and self.model is not None:
            probas = self.predict_model_probabilities(soil_climate)
            if cand_clean in probas:
                prob = probas[cand_clean]
                return round(float(prob), 4), f"Hugging Face: {HF_REPO_ID} (RandomForestClassifier)"

        # 2. Explicit Fallback Agronomic Scorer
        fallback_val = self.fallback_score(cand_clean, soil_climate)
        reason_source = (
            "Explicit Fallback Agronomic Engine (Crop not in 22 HF classes)"
            if self.model_loaded
            else "Explicit Fallback Agronomic Engine (HF Model Not Loaded)"
        )
        return round(fallback_val, 4), reason_source

    def fallback_score(self, candidate_crop: str, soil_climate: Any) -> float:
        """Calibrated fallback agronomic score based on crop physiological response curves.

        Clearly marked as explicit fallback.
        """
        cand_clean = candidate_crop.strip().lower()
        profile = FALLBACK_CROP_PROFILES.get(cand_clean)

        if not profile:
            # If not in fallback profile either, calculate generic nutrient satisfaction
            n_ratio = min(1.0, float(soil_climate.N) / 80.0)
            p_ratio = min(1.0, float(soil_climate.P) / 45.0)
            k_ratio = min(1.0, float(soil_climate.K) / 45.0)
            return round((n_ratio + p_ratio + k_ratio) / 3.0 * 0.70, 4)

        feature_scores = []
        for feat, val in [("N", float(soil_climate.N)), ("P", float(soil_climate.P)), ("K", float(soil_climate.K))]:
            opt = profile[feat]["opt"]
            tol = profile[feat]["tol"]
            dev = abs(val - opt) / (tol * 1.5)
            s = math.exp(-0.5 * (dev ** 2))
            feature_scores.append(s)

        if soil_climate.temperature is not None and "temp" in profile:
            dev = abs(soil_climate.temperature - profile["temp"]["opt"]) / profile["temp"]["tol"]
            feature_scores.append(math.exp(-0.5 * (dev ** 2)))

        if soil_climate.humidity is not None and "humidity" in profile:
            dev = abs(soil_climate.humidity - profile["humidity"]["opt"]) / profile["humidity"]["tol"]
            feature_scores.append(math.exp(-0.5 * (dev ** 2)))

        if soil_climate.ph is not None and "ph" in profile:
            dev = abs(soil_climate.ph - profile["ph"]["opt"]) / profile["ph"]["tol"]
            feature_scores.append(math.exp(-0.5 * (dev ** 2)))

        return sum(feature_scores) / len(feature_scores)


_default_scorer: Optional[SoilClimateScorer] = None


def get_default_soil_climate_scorer() -> SoilClimateScorer:
    """Returns singleton SoilClimateScorer instance."""
    global _default_scorer
    if _default_scorer is None:
        _default_scorer = SoilClimateScorer()
    return _default_scorer


# Initialize on import to populate MODEL_LOADED, MODEL_SOURCE, and MODEL_TYPE
try:
    _init_scorer = get_default_soil_climate_scorer()
    MODEL_LOADED = _init_scorer.model_loaded
    MODEL_SOURCE = _init_scorer.model_source
    MODEL_TYPE = type(_init_scorer.model).__name__ if _init_scorer.model else None
except Exception:
    pass
