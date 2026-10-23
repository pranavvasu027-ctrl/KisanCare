"""Hugging Face Crop Recommendation Pipeline.

Integrates the official dual-model architecture from Hugging Face:
  Repo: Sheshank2609/crop-recommendation-system
  Revision: f24d6e1666bb9efa530de8f4aec0124cd83c8cfd
  License: MIT
  Author: Sheshank2609

Components:
  1. Model 1 — Soil & Climate Random Forest Classifier (model1_npk.pkl, model1_label_encoder.pkl)
     Feature order: N, P, K, temperature, humidity, ph, rainfall
     Outputs: Real class probability distribution across 22 crops.
  2. Model 2 — Regional Suitability Scoring Engine (model2_full_scored.csv)
     Scored across 35 Maharashtra districts, 4 seasons, and 33 crops using 26 years of historical data.
  3. Combined Multi-Criteria Engine:
     Final Score = w1 * Model1_probability + w2 * Model2_score
     Default weights: 60% soil/climate + 40% regional.
  4. Transparent Water Availability Decision Constraints:
     Identifies irrigation/water constraints without silently replacing or fabricating probabilities.
"""

from __future__ import annotations

import logging
import os
import threading
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from huggingface_hub import hf_hub_download

logger = logging.getLogger("kisancare.ml.crop_recommendation")

# Model configuration constants
HF_REPO_ID = "Sheshank2609/crop-recommendation-system"
PINNED_REVISION = "f24d6e1666bb9efa530de8f4aec0124cd83c8cfd"
MODEL1_BINARY_FILE = "model1_npk.pkl"
MODEL1_ENCODER_FILE = "model1_label_encoder.pkl"
MODEL2_SCORING_FILE = "model2_full_scored.csv"

# Exact feature order required by Model 1 Random Forest
FEATURE_NAMES: List[str] = [
    "N",
    "P",
    "K",
    "temperature",
    "humidity",
    "ph",
    "rainfall",
]

# Input feature validation boundaries documented by the model card
FEATURE_BOUNDS: Dict[str, Tuple[float, float, str]] = {
    "N": (0.0, 300.0, "mg/kg or kg/ha"),
    "P": (0.0, 300.0, "mg/kg or kg/ha"),
    "K": (0.0, 300.0, "mg/kg or kg/ha"),
    "temperature": (5.0, 50.0, "°C"),
    "humidity": (10.0, 100.0, "%"),
    "ph": (3.5, 9.5, "pH unit"),
    "rainfall": (20.0, 3000.0, "mm"),
}

# Maharashtra districts covered by Model 2
SUPPORTED_DISTRICTS: List[str] = [
    "Ahilyanagar", "Akola", "Amravati", "Beed", "Bhandara", "Buldhana",
    "Chandrapur", "Chhatrapati Sambhajinagar", "Dharashiv", "Dhule",
    "Gadchiroli", "Gondia", "Hingoli", "Jalgaon", "Jalna", "Kolhapur",
    "Latur", "Mumbai suburban", "Nagpur", "Nanded", "Nandurbar", "Nashik",
    "Palghar", "Parbhani", "Pune", "Raigad", "Ratnagiri", "Sangli",
    "Satara", "Sindhudurg", "Solapur", "Thane", "Wardha", "Washim", "Yavatmal",
]

# Common aliases / former names mapped to official district names in Model 2
DISTRICT_ALIASES: Dict[str, str] = {
    "ahmednagar": "Ahilyanagar",
    "aurangabad": "Chhatrapati Sambhajinagar",
    "osmanabad": "Dharashiv",
    "mumbai": "Mumbai suburban",
    "mumbai city": "Mumbai suburban",
    "bombay": "Mumbai suburban",
}

# Supported seasons in Model 2
SUPPORTED_SEASONS: List[str] = ["Kharif", "Rabi", "Summer", "Whole Year"]

SEASON_ALIASES: Dict[str, str] = {
    "monsoon": "Kharif",
    "winter": "Rabi",
    "zaid": "Summer",
    "zaid/summer": "Summer",
    "annual": "Whole Year",
    "all year": "Whole Year",
}

# Cross-model synonym and canonical name mapping
CROP_SYNONYMS: Dict[str, str] = {
    "cotton": "cotton(lint)",
    "cotton(lint)": "cotton",
    "pigeonpeas": "arhar/tur",
    "arhar/tur": "pigeonpeas",
    "chickpea": "gram",
    "gram": "chickpea",
    "mungbean": "moong(greengram)",
    "moong(greengram)": "mungbean",
    "blackgram": "urad",
    "urad": "blackgram",
    "soybean": "soyabean",
    "soyabean": "soybean",
}

# Crops with high water demand (> 1000mm) that require irrigation infrastructure
HIGH_WATER_DEMAND_CROPS: Dict[str, float] = {
    "sugarcane": 1800.0,
    "rice": 1200.0,
    "banana": 1500.0,
    "jute": 1100.0,
}


class ModelUnavailableError(Exception):
    """Raised when model artifacts cannot be downloaded, cached, or loaded."""
    pass


class InputValidationError(ValueError):
    """Raised when numerical or categorical inputs fall outside acceptable ranges."""
    pass


def normalize_string(val: str) -> str:
    """Normalize string for robust token matching."""
    return (
        str(val)
        .strip()
        .lower()
        .replace(" ", "")
        .replace("(", "")
        .replace(")", "")
        .replace("-", "")
        .replace("/", "")
        .replace("&", "")
    )


@dataclass
class CropRecommendationInput:
    """Validated input parameters for crop recommendation."""
    N: float
    P: float
    K: float
    temperature: float
    humidity: float
    ph: float
    rainfall: float
    district: Optional[str] = None
    season: Optional[str] = None
    state: str = "Maharashtra"
    water_access: Optional[str] = None
    w_model1: float = 0.60
    top_k: int = 5


@dataclass
class CropRecommendationItem:
    """Ranked crop recommendation breakdown."""
    crop: str
    rank: int
    combined_score: float
    confidence_pct: float
    npk_score: float
    region_score: float
    region_suitability: str
    grown_pct_of_years: float
    avg_yield_t_ha: float
    historically_grown: bool
    water_constrained: bool
    reason: str


@dataclass
class CropRecommendationResult:
    """Full recommendation result with model metadata."""
    model: str
    model_version: str
    prediction: str
    combined_score: float
    recommendations: List[CropRecommendationItem]
    weights_used: Dict[str, float]
    soil_test_npk_status: Dict[str, str]
    input_summary: Dict[str, Any]
    warnings: List[str]
    is_demo: bool = False


class CropRecommendationPipeline:
    """Thread-safe pipeline loading and serving the Hugging Face Dual Model."""

    def __init__(
        self,
        repo_id: str = HF_REPO_ID,
        revision: str = PINNED_REVISION,
        cache_dir: Optional[str] = None,
        force_reload: bool = False,
    ):
        self.repo_id = repo_id
        self.revision = revision
        self.cache_dir = cache_dir or os.environ.get("MODEL_CACHE_DIR")
        self._lock = threading.Lock()
        self._is_loaded = False
        self._load_error: Optional[str] = None

        self.model1: Optional[Any] = None
        self.label_enc1: Optional[Any] = None
        self.model2_df: Optional[pd.DataFrame] = None
        self.model1_classes: List[str] = []

        if force_reload:
            self._is_loaded = False
        self._ensure_loaded()

    def _ensure_loaded(self) -> None:
        """Download and load model artifacts safely with thread-safety."""
        if self._is_loaded:
            return

        with self._lock:
            if self._is_loaded:
                return

            try:
                logger.info(
                    "Downloading and caching model artifacts from %s (rev: %s)...",
                    self.repo_id,
                    self.revision[:7],
                )

                model1_path = hf_hub_download(
                    repo_id=self.repo_id,
                    filename=MODEL1_BINARY_FILE,
                    revision=self.revision,
                    cache_dir=self.cache_dir,
                )
                encoder_path = hf_hub_download(
                    repo_id=self.repo_id,
                    filename=MODEL1_ENCODER_FILE,
                    revision=self.revision,
                    cache_dir=self.cache_dir,
                )
                model2_path = hf_hub_download(
                    repo_id=self.repo_id,
                    filename=MODEL2_SCORING_FILE,
                    revision=self.revision,
                    cache_dir=self.cache_dir,
                )

                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    self.model1 = joblib.load(model1_path)
                    self.label_enc1 = joblib.load(encoder_path)
                    self.model2_df = pd.read_csv(model2_path)

                self.model1_classes = [str(c).lower() for c in self.label_enc1.classes_]
                self._is_loaded = True
                self._load_error = None
                logger.info(
                    "Successfully loaded Model 1 (RandomForest with %d classes) and Model 2 (%d regional rows).",
                    len(self.model1_classes),
                    len(self.model2_df),
                )
            except Exception as exc:
                self._is_loaded = False
                self._load_error = str(exc)
                logger.error("Failed to load Hugging Face model artifacts: %s", exc, exc_info=True)
                raise ModelUnavailableError(
                    f"Failed to load crop recommendation model artifacts from {self.repo_id}@{self.revision[:7]}: {exc}"
                ) from exc

    @property
    def is_ready(self) -> bool:
        """Check if pipeline is loaded and ready for inference."""
        return self._is_loaded and self.model1 is not None and self.model2_df is not None

    def validate_inputs(self, params: CropRecommendationInput) -> Tuple[str, str, List[str]]:
        """Validate input ranges and categorical dimensions. Returns (resolved_district, resolved_season, warnings)."""
        warnings_list: List[str] = []

        # 1. Validate numerical inputs
        checks = [
            ("N", params.N),
            ("P", params.P),
            ("K", params.K),
            ("temperature", params.temperature),
            ("humidity", params.humidity),
            ("ph", params.ph),
            ("rainfall", params.rainfall),
        ]
        for name, val in checks:
            if val is None or not np.isfinite(val):
                raise InputValidationError(f"Feature '{name}' must be a valid finite number, got {val}.")
            low, high, unit = FEATURE_BOUNDS[name]
            if val < low or val > high:
                raise InputValidationError(
                    f"Feature '{name}' ({val} {unit}) is out of supported range [{low}, {high} {unit}]."
                )

        # 2. Validate district
        resolved_district: str = "Nashik"
        if params.district and params.district.strip():
            raw_dist = params.district.strip()
            norm_dist = normalize_string(raw_dist)

            # Check direct match against supported districts
            matched = None
            for d in SUPPORTED_DISTRICTS:
                if normalize_string(d) == norm_dist:
                    matched = d
                    break

            # Check aliases
            if not matched:
                for alias_k, canonical in DISTRICT_ALIASES.items():
                    if normalize_string(alias_k) == norm_dist:
                        matched = canonical
                        break

            if matched:
                resolved_district = matched
            else:
                warnings_list.append(
                    f"District '{raw_dist}' not found in Maharashtra 35-district dataset; defaulted to '{resolved_district}' for regional scoring."
                )
        else:
            warnings_list.append(f"No district specified; using default '{resolved_district}' for regional suitability.")

        # 3. Validate season
        resolved_season: str = "Kharif"
        if params.season and params.season.strip():
            raw_s = params.season.strip()
            norm_s = normalize_string(raw_s)

            matched_s = None
            for s in SUPPORTED_SEASONS:
                if normalize_string(s) == norm_s:
                    matched_s = s
                    break

            if not matched_s:
                for alias_s, canonical_s in SEASON_ALIASES.items():
                    if normalize_string(alias_s) == norm_s:
                        matched_s = canonical_s
                        break

            if matched_s:
                resolved_season = matched_s
            else:
                warnings_list.append(
                    f"Season '{raw_s}' not in supported seasons ({SUPPORTED_SEASONS}); defaulted to '{resolved_season}'."
                )
        else:
            warnings_list.append(f"No season specified; using default '{resolved_season}'.")

        # 4. Check state scope
        if params.state and params.state.strip().lower() not in ("maharashtra", "mh"):
            warnings_list.append(
                f"Model 2 regional dataset is calibrated specifically for Maharashtra agro-ecological zones (received state: '{params.state}')."
            )

        return resolved_district, resolved_season, warnings_list

    def _evaluate_npk_status(self, N: float, P: float, K: float) -> Dict[str, str]:
        """Categorize soil nutrient adequacy."""
        def level(val: float, low_cut: float, high_cut: float) -> str:
            if val < low_cut:
                return "Low"
            if val <= high_cut:
                return "Medium"
            return "High"

        return {
            "N": level(N, 50.0, 120.0),
            "P": level(P, 25.0, 60.0),
            "K": level(K, 30.0, 70.0),
        }

    def _get_suitability_label(self, score: float) -> str:
        """Derive standard suitability label from combined score percentage."""
        pct = score * 100.0
        if pct >= 75.0:
            return "Highly Suitable"
        if pct >= 50.0:
            return "Moderately Suitable"
        if pct >= 30.0:
            return "Low Suitability"
        return "Not Recommended"

    def predict(self, inputs: CropRecommendationInput) -> CropRecommendationResult:
        """Execute full multi-model recommendation pipeline."""
        self._ensure_loaded()
        if not self.is_ready:
            raise ModelUnavailableError(f"Model pipeline unavailable: {self._load_error}")

        # Validate inputs
        district, season, warnings_list = self.validate_inputs(inputs)

        # 1. Model 1: Random Forest NPK + Climate Probabilities
        features_df = pd.DataFrame(
            [[
                inputs.N,
                inputs.P,
                inputs.K,
                inputs.temperature,
                inputs.humidity,
                inputs.ph,
                inputs.rainfall,
            ]],
            columns=FEATURE_NAMES,
        )

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            probas = self.model1.predict_proba(features_df)[0]

        m1_scores: Dict[str, float] = {
            cls_name.lower(): float(p)
            for cls_name, p in zip(self.label_enc1.classes_, probas)
        }

        # 2. Model 2: Regional Suitability Scoring Table Lookup
        assert self.model2_df is not None
        region_df = self.model2_df[
            (self.model2_df["District"] == district) &
            (self.model2_df["Season"] == season)
        ]

        m2_scores: Dict[str, Dict[str, Any]] = {}
        for _, row in region_df.iterrows():
            crop_name = str(row["Crop"]).strip()
            m2_scores[normalize_string(crop_name)] = {
                "display_name": crop_name,
                "suitability_score": float(row["Suitability_Score"]),
                "suitability_pct": float(row["Suitability_Pct"]),
                "recommendation": str(row["Recommendation"]),
                "crop_freq_pct": float(row["Crop_Freq_Pct"]),
                "avg_yield": float(row["Avg_Yield"]),
                "is_historically_grown": bool(row["Is_Historically_Grown"]),
            }

        # 3. Combine Model 1 and Model 2 with weight constraints
        w1 = max(0.0, min(1.0, float(inputs.w_model1)))
        w2 = round(1.0 - w1, 4)

        # Index maps
        m1_norm: Dict[str, Tuple[str, float]] = {
            normalize_string(k): (k, v) for k, v in m1_scores.items()
        }

        all_keys = set(m1_norm.keys()) | set(m2_scores.keys())

        # Also link through synonyms
        for k_syn, target_syn in CROP_SYNONYMS.items():
            norm_k = normalize_string(k_syn)
            norm_target = normalize_string(target_syn)
            if norm_k in m1_norm and norm_target in m2_scores:
                all_keys.add(norm_k)
                all_keys.add(norm_target)

        scored_candidates: List[CropRecommendationItem] = []
        seen_crop_names: set[str] = set()

        is_rainfed = inputs.water_access and "rainfed" in inputs.water_access.lower()

        for key in all_keys:
            # Resolve Model 1 score
            s1 = 0.0
            display_name = key.title()
            if key in m1_norm:
                raw_name, s1 = m1_norm[key]
                display_name = raw_name.title()
            else:
                # Check synonym for Model 1
                for syn_from, syn_to in CROP_SYNONYMS.items():
                    if normalize_string(syn_to) == key and normalize_string(syn_from) in m1_norm:
                        raw_name, s1 = m1_norm[normalize_string(syn_from)]
                        display_name = raw_name.title()
                        break

            # Resolve Model 2 score
            s2 = 0.0
            m2_entry: Optional[Dict[str, Any]] = None
            if key in m2_scores:
                m2_entry = m2_scores[key]
                s2 = m2_entry["suitability_score"]
                display_name = m2_entry["display_name"]
            else:
                # Check synonym for Model 2
                for syn_from, syn_to in CROP_SYNONYMS.items():
                    if normalize_string(syn_from) == key and normalize_string(syn_to) in m2_scores:
                        m2_entry = m2_scores[normalize_string(syn_to)]
                        s2 = m2_entry["suitability_score"]
                        display_name = m2_entry["display_name"]
                        break

            # Canonical deduplication check
            norm_disp = normalize_string(display_name)
            if norm_disp in seen_crop_names:
                continue
            seen_crop_names.add(norm_disp)

            # Weighted combined multi-criteria score
            combined = round(w1 * s1 + w2 * s2, 4)

            # Metadata extraction from regional scoring table
            reg_label = m2_entry["recommendation"] if m2_entry else "No regional data"
            grown_pct = m2_entry["crop_freq_pct"] if m2_entry else 0.0
            avg_yield = m2_entry["avg_yield"] if m2_entry else 0.0
            hist_grown = m2_entry["is_historically_grown"] if m2_entry else False

            # Decision Engine Constraint: Water availability check
            water_constrained = False
            norm_disp = normalize_string(display_name)
            high_water_req = HIGH_WATER_DEMAND_CROPS.get(norm_disp)
            if high_water_req is not None:
                if is_rainfed and inputs.rainfall < 900.0:
                    water_constrained = True
                elif inputs.rainfall < 600.0 and (not inputs.water_access or "drip" not in inputs.water_access.lower()):
                    water_constrained = True

            # Explanatory reasoning
            reason_parts: List[str] = []
            if s1 > 0.10:
                reason_parts.append(f"Soil/Climate RF probability: {s1 * 100:.1f}%")
            if m2_entry:
                reason_parts.append(
                    f"26-yr Maharashtra suitability: {s2 * 100:.1f}% ({reg_label})"
                )
            else:
                reason_parts.append("Pan-India agronomic candidate outside Maharashtra census table")

            if water_constrained:
                reason_parts.append(
                    f"Water Advisory: High moisture requirement (~{high_water_req:.0f}mm) requires irrigation support."
                )

            reason_str = " | ".join(reason_parts)

            item = CropRecommendationItem(
                crop=display_name,
                rank=0,  # Will be assigned after sort
                combined_score=combined,
                confidence_pct=round(combined * 100.0, 1),
                npk_score=round(s1, 4),
                region_score=round(s2, 4),
                region_suitability=reg_label if reg_label != "No regional data" else self._get_suitability_label(combined),
                grown_pct_of_years=round(grown_pct, 1),
                avg_yield_t_ha=round(avg_yield, 2),
                historically_grown=hist_grown,
                water_constrained=water_constrained,
                reason=reason_str,
            )
            scored_candidates.append(item)

        # Sort descending by combined score, then by NPK probability
        scored_candidates.sort(key=lambda x: (x.combined_score, x.npk_score), reverse=True)

        # Assign ranks
        for idx, cand in enumerate(scored_candidates):
            cand.rank = idx + 1

        top_candidates = scored_candidates[: inputs.top_k]

        top_prediction = top_candidates[0].crop if top_candidates else "Unknown"
        top_combined_score = top_candidates[0].combined_score if top_candidates else 0.0

        if top_candidates and top_candidates[0].water_constrained:
            warnings_list.append(
                f"Top candidate '{top_prediction}' has high water requirement ({HIGH_WATER_DEMAND_CROPS.get(normalize_string(top_prediction))}mm); confirm supplemental irrigation."
            )

        npk_status = self._evaluate_npk_status(inputs.N, inputs.P, inputs.K)

        return CropRecommendationResult(
            model="crop_recommendation_huggingface",
            model_version=f"{self.repo_id}@{self.revision[:7]}",
            prediction=top_prediction,
            combined_score=top_combined_score,
            recommendations=top_candidates,
            weights_used={"soil_climate_npk": w1, "regional_suitability": w2},
            soil_test_npk_status=npk_status,
            input_summary={
                "N": inputs.N,
                "P": inputs.P,
                "K": inputs.K,
                "temperature": inputs.temperature,
                "humidity": inputs.humidity,
                "ph": inputs.ph,
                "rainfall": inputs.rainfall,
                "district": district,
                "season": season,
                "state": inputs.state,
                "water_access": inputs.water_access,
            },
            warnings=warnings_list,
            is_demo=False,
        )


# Global singleton pipeline instance
_GLOBAL_PIPELINE: Optional[CropRecommendationPipeline] = None
_GLOBAL_LOCK = threading.Lock()


def get_pipeline(
    repo_id: str = HF_REPO_ID,
    revision: str = PINNED_REVISION,
    cache_dir: Optional[str] = None,
) -> CropRecommendationPipeline:
    """Return thread-safe singleton pipeline instance."""
    global _GLOBAL_PIPELINE
    if _GLOBAL_PIPELINE is None:
        with _GLOBAL_LOCK:
            if _GLOBAL_PIPELINE is None:
                _GLOBAL_PIPELINE = CropRecommendationPipeline(
                    repo_id=repo_id,
                    revision=revision,
                    cache_dir=cache_dir,
                )
    return _GLOBAL_PIPELINE
