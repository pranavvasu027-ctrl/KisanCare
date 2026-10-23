"""Inference prediction module for Crop Recommendation.

Provides high-level functions for invoking the Hugging Face Crop Recommendation
Pipeline from API endpoints, CLI tools, and background services.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from ml.crop_recommendation.huggingface_pipeline import (
    CropRecommendationInput,
    CropRecommendationResult,
    InputValidationError,
    ModelUnavailableError,
    get_pipeline,
)

logger = logging.getLogger("kisancare.ml.crop_recommendation.predict")


def predict_crop_recommendation(
    N: float,
    P: float,
    K: float,
    temperature: float,
    humidity: float,
    ph: float,
    rainfall: float,
    district: Optional[str] = "Nashik",
    season: Optional[str] = "Kharif",
    state: str = "Maharashtra",
    water_access: Optional[str] = None,
    w_model1: float = 0.60,
    top_k: int = 5,
) -> CropRecommendationResult:
    """Execute crop recommendation inference using Hugging Face pipeline.

    Args:
        N: Nitrogen content (0 - 300)
        P: Phosphorus content (0 - 300)
        K: Potassium content (0 - 300)
        temperature: Temperature in °C (5 - 50)
        humidity: Relative humidity in % (10 - 100)
        ph: Soil pH (3.5 - 9.5)
        rainfall: Rainfall in mm (20 - 3000)
        district: Maharashtra district name (e.g., 'Nashik', 'Pune')
        season: Agricultural season ('Kharif', 'Rabi', 'Summer', 'Whole Year')
        state: State name (default: 'Maharashtra')
        water_access: Irrigation source description
        w_model1: Weight for Model 1 NPK RF model (default 0.60)
        top_k: Number of recommendations to return

    Returns:
        CropRecommendationResult with ranked candidates and score breakdown.
    """
    inputs = CropRecommendationInput(
        N=float(N),
        P=float(P),
        K=float(K),
        temperature=float(temperature),
        humidity=float(humidity),
        ph=float(ph),
        rainfall=float(rainfall),
        district=district,
        season=season,
        state=state,
        water_access=water_access,
        w_model1=float(w_model1),
        top_k=int(top_k),
    )
    pipeline = get_pipeline()
    return pipeline.predict(inputs)


def predict_crop_from_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Accepts arbitrary payload dictionary, validates inputs, runs inference, and returns serializable dict.

    Strictly enforces that soil and climate measurements must not be silently invented.
    """
    inner = data.get("data", data) if isinstance(data, dict) else {}
    weather = inner.get("weather", {}) if isinstance(inner.get("weather"), dict) else {}

    # Strict check: Do not invent soil values when data is missing
    raw_n = inner.get("N") if inner.get("N") is not None else inner.get("nitrogen")
    raw_p = inner.get("P") if inner.get("P") is not None else inner.get("phosphorus")
    raw_k = inner.get("K") if inner.get("K") is not None else inner.get("potassium")
    raw_ph = inner.get("ph") if inner.get("ph") is not None else inner.get("soil_ph")

    if raw_n is None:
        raise InputValidationError("Missing required soil test measurement: 'N' (Nitrogen). Soil values must not be silently invented.")
    if raw_p is None:
        raise InputValidationError("Missing required soil test measurement: 'P' (Phosphorus). Soil values must not be silently invented.")
    if raw_k is None:
        raise InputValidationError("Missing required soil test measurement: 'K' (Potassium). Soil values must not be silently invented.")
    if raw_ph is None:
        raise InputValidationError("Missing required soil test measurement: 'ph' (Soil pH). Soil values must not be silently invented.")

    # Strict check: Do not silently assume weather measurements when missing
    raw_rain = inner.get("rainfall") if inner.get("rainfall") is not None else weather.get("rainfall")
    raw_temp = inner.get("temperature") if inner.get("temperature") is not None else weather.get("temperature")
    raw_hum = inner.get("humidity") if inner.get("humidity") is not None else weather.get("humidity")

    if raw_rain is None:
        raise InputValidationError("Missing required climate measurement: 'rainfall'. Climate values must not be silently assumed.")
    if raw_temp is None:
        raise InputValidationError("Missing required climate measurement: 'temperature'. Climate values must not be silently assumed.")
    if raw_hum is None:
        raise InputValidationError("Missing required climate measurement: 'humidity'. Climate values must not be silently assumed.")

    # Extract all 7 numerical features with strict type conversion
    try:
        n_val = float(raw_n)
        p_val = float(raw_p)
        k_val = float(raw_k)
        ph_val = float(raw_ph)
        temp_val = float(raw_temp)
        hum_val = float(raw_hum)
        rain_val = float(raw_rain)
    except (TypeError, ValueError) as exc:
        raise InputValidationError(f"Invalid numerical soil/climate input: {exc}") from exc

    district = inner.get("district", "Nashik")
    season = inner.get("season", "Kharif")
    state = str(inner.get("state", inner.get("location", "Maharashtra")))
    water_access = inner.get("water_access", inner.get("irrigation_source"))
    w_model1 = float(inner.get("w_model1", inner.get("model1_weight", 0.60)))
    top_k = int(inner.get("top_k", 5))

    res = predict_crop_recommendation(
        N=n_val,
        P=p_val,
        K=k_val,
        temperature=temp_val,
        humidity=hum_val,
        ph=ph_val,
        rainfall=rain_val,
        district=district,
        season=season,
        state=state,
        water_access=water_access,
        w_model1=w_model1,
        top_k=top_k,
    )

    # Format into serializable response
    return {
        "success": True,
        "model": res.model,
        "model_version": res.model_version,
        "prediction": res.prediction,
        "final_score": res.combined_score,
        "combined_score": res.combined_score,
        "unit": "crop_type",
        "recommendations": [
            {
                "crop": r.crop,
                "rank": r.rank,
                "combined_score": r.combined_score,
                "confidence_pct": r.confidence_pct,
                "npk_score": r.npk_score,
                "region_score": r.region_score,
                "region_suitability": r.region_suitability,
                "grown_pct_of_years": r.grown_pct_of_years,
                "avg_yield_t_ha": r.avg_yield_t_ha,
                "historically_grown": r.historically_grown,
                "water_constrained": r.water_constrained,
                "reason": r.reason,
                "is_regionally_supported": r.is_regionally_supported,
                "evidence_tier": r.evidence_tier,
            }
            for r in res.recommendations
        ],
        "factors": [f"{r.crop} (Score: {r.combined_score:.2f}): {r.reason}" for r in res.recommendations[:3]],
        "soil_test_npk_status": res.soil_test_npk_status,
        "input_summary": res.input_summary,
        "weights_used": res.weights_used,
        "warnings": res.warnings,
        "is_demo": False,
        "limitations": [
            "RandomForest soil/climate classifier trained on 2,200 benchmark observations across 22 crops.",
            "Regional suitability scoring based on 26 years of Maharashtra district crop records (1997-2022).",
            "Blended multi-criteria score (60% NPK / 40% Regional); not a calibrated single-distribution probability.",
        ],
    }
