"""
Real ML Fertilizer Application Recommendation Model Adapter.

Model: DNgigi/FertiliserApplication (Hugging Face)
Architecture: Multi-Output Random Forest Regressor & Classifier
Framework: Scikit-Learn
Pinned Revision: 5a38c5eda9989b72fe76cebf884da2e4acdb6971
License: MIT
"""

import hashlib
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import joblib
import pandas as pd

logger = logging.getLogger(__name__)

HF_REPO_ID = "DNgigi/FertiliserApplication"
PINNED_REVISION = "5a38c5eda9989b72fe76cebf884da2e4acdb6971"

EXPECTED_CHECKSUMS = {
    "preprocessor.joblib": "0d9657cb703d86beda547ca5a997446a50c7b1054a1a21e17207711e25e9dae1",
    "numerical_model.joblib": "35bbb7ec84f5bf5ce63c2631bced4f9defd4affc110e25e343399dcfaa3d781c",
    "categorical_model.joblib": "d987cccc2a107fb869482ea822ac2646f7d29f56a0c2f39ef40effd035663246",
}

NUMERICAL_TARGETS = [
    "Nitrogen (N) Need",
    "Phosphorus (P2O5) Need",
    "Potassium (K2O) Need",
    "Organic Matter Need",
    "Lime Need",
    "Lime Application - Requirement",
    "Organic Matter Application - Requirement",
    "1st Application - Requirement (1)",
    "1st Application - Requirement (2)",
    "2nd Application - Requirement (1)",
]

SUPPORTED_TRAINING_CROPS = {
    "cabbage": "cabbage",
    "coffee": "coffee (green beans)",
    "coffee (green beans)": "coffee (green beans)",
    "maize": "maize (corn)",
    "corn": "maize (corn)",
    "maize (corn)": "maize (corn)",
    "maize-beans intercrop": "maize-beans intercrop",
    "potato": "potato",
}


def _verify_sha256(filepath: Path, expected_hash: str) -> bool:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    actual_hash = hasher.hexdigest()
    if actual_hash != expected_hash:
        logger.warning("Checksum mismatch for %s: expected %s, got %s", filepath.name, expected_hash, actual_hash)
        return False
    return True


class FertilizerModelAdapter:
    """Production adapter for DNgigi/FertiliserApplication Multi-Output Random Forest."""

    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or (Path.home() / ".cache" / "kisancare" / "fertilizer_model")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.preprocessor = None
        self.numerical_model = None
        self.categorical_model = None
        self._is_loaded = False
        self._load_error = None

    def _ensure_loaded(self):
        if self._is_loaded:
            return
        if self._load_error:
            raise RuntimeError(f"Fertilizer model previously failed to load: {self._load_error}")

        try:
            from huggingface_hub import hf_hub_download

            artifacts = {}
            for filename, expected_hash in EXPECTED_CHECKSUMS.items():
                cached_path = self.cache_dir / filename
                if not cached_path.exists() or not _verify_sha256(cached_path, expected_hash):
                    downloaded = hf_hub_download(
                        repo_id=HF_REPO_ID,
                        filename=filename,
                        revision=PINNED_REVISION,
                        local_dir=str(self.cache_dir),
                    )
                    cached_path = Path(downloaded)
                    _verify_sha256(cached_path, expected_hash)
                artifacts[filename] = cached_path

            # Load models
            prep = joblib.load(artifacts["preprocessor.joblib"])
            num_model = joblib.load(artifacts["numerical_model.joblib"])
            cat_model = joblib.load(artifacts["categorical_model.joblib"])

            # Scikit-learn 1.4 -> 1.9 compatibility patch for SimpleImputer
            for name, trans, cols in getattr(prep, "transformers_", []):
                if hasattr(trans, "named_steps"):
                    for step_name, step in trans.named_steps.items():
                        if hasattr(step, "_fit_dtype") and not hasattr(step, "_fill_dtype"):
                            step._fill_dtype = step._fit_dtype

            self.preprocessor = prep
            self.numerical_model = num_model
            self.categorical_model = cat_model
            self._is_loaded = True
            logger.info("FertilizerApplication model loaded successfully from %s", self.cache_dir)
        except Exception as e:
            self._load_error = str(e)
            logger.error("Failed to load FertilizerApplication model: %s", e)
            raise RuntimeError(f"Unable to load fertilizer model: {e}") from e

    def is_available(self) -> bool:
        try:
            self._ensure_loaded()
            return self._is_loaded
        except Exception:
            return False

    def predict(
        self,
        crop_name: str,
        target_yield_kg_ha: float,
        field_size_ha: float,
        ph: float,
        organic_carbon: float,
        total_nitrogen: float,
        available_phosphorus: float,
        exchangeable_potassium: float,
    ) -> Dict[str, Any]:
        """
        Execute real inference with DNgigi/FertiliserApplication.
        """
        self._ensure_loaded()

        raw_crop = crop_name.strip().lower()
        model_crop = SUPPORTED_TRAINING_CROPS.get(raw_crop)
        is_crop_in_training_distribution = model_crop is not None
        effective_crop = model_crop or raw_crop

        warnings: List[str] = []
        if not is_crop_in_training_distribution:
            warnings.append(
                f"Crop '{crop_name}' was not part of the model's 5 core training crops "
                f"(maize, potato, cabbage, coffee, maize-beans). One-hot features defaulted via "
                f"handle_unknown='ignore'; predictions reflect generalized soil chemistry response."
            )

        if ph > 7.5:
            warnings.append(
                f"Soil pH is alkaline ({ph:.2f}), typical of Maharashtra black cotton soils. "
                f"Do not apply agricultural lime (calcium carbonate). If sulfur/gypsum amendment "
                f"is needed for alkalinity, consult an agronomist."
            )

        # Build feature dataframe exactly matching model's expected column names
        input_dict = {
            "Crop Name": effective_crop,
            "Target Yield": float(target_yield_kg_ha),
            "Field Size": float(field_size_ha),
            "pH (water)": float(ph),
            "Organic Carbon": float(organic_carbon),
            "Total Nitrogen": float(total_nitrogen),
            "Phosphorus (M3)": float(available_phosphorus),
            "Potassium (exch.)": float(exchangeable_potassium),
        }
        df_input = pd.DataFrame([input_dict])

        # Execute real scikit-learn pipeline transformation
        X_transformed = self.preprocessor.transform(df_input)

        # Numerical multi-output predictions
        num_preds = self.numerical_model.predict(X_transformed)[0]

        predictions_dict: Dict[str, float] = {}
        for target_name, pred_val in zip(NUMERICAL_TARGETS, num_preds):
            # Clamp negative nutrient needs to 0.0 (nutrient requirement cannot be negative)
            predictions_dict[target_name] = max(0.0, float(round(pred_val, 2)))

        return {
            "predictions": predictions_dict,
            "crop_used": effective_crop,
            "is_in_training_distribution": is_crop_in_training_distribution,
            "inputs_evaluated": input_dict,
            "warnings": warnings,
            "model_metadata": {
                "model_identifier": HF_REPO_ID,
                "pinned_revision": PINNED_REVISION,
                "architecture": "RandomForest MultiOutputRegressor (scikit-learn)",
                "license": "MIT",
                "training_dataset_region": "East Africa Agricultural Soil Survey",
            },
        }


# Global singleton instance
fertilizer_model_adapter = FertilizerModelAdapter()
