"""
Region-Aware Crop Recommendation Engine
========================================
Combines biophysical soil and climate suitability (Random Forest Classifier)
with 26 years of Maharashtra district-and-season agricultural census evidence.

Generates farmer-facing recommendations:
- Top 3 ranked crops.
- Farmer-friendly suitability labels ('Highly Suitable', 'Moderately Suitable', 'Low Suitability').
- Clear agronomic reasons without exposing raw model probabilities or technical test values.
- Transparent water availability constraints and regional evidence warnings.
"""

from __future__ import annotations
import logging
from typing import Any, Dict, List, Optional

import numpy as np

from ml.crop_recommendation.huggingface_pipeline import (
    CropRecommendationInput,
    get_pipeline,
    HIGH_WATER_DEMAND_CROPS,
    normalize_string,
)
from .schemas import CropRecommendationFarmerItem

logger = logging.getLogger("kisancare.crop_recommendation.engine")

# District-specific agronomic notes and typical APMC market considerations
DISTRICT_AGRONOMIC_NOTES: Dict[str, Dict[str, str]] = {
    "Akola": {
        "Cotton": "Core Vidarbha cash crop; well-suited to deep black Vertisols with established ginning infrastructure at Akola and Akot APMCs.",
        "Soybean": "High-demand Kharif oilseed in Akola; excellent nitrogen-fixation precursor before Rabi Gram.",
        "Tur": "Pigeonpea intercrop standard in Vidarbha; deep taproot provides high drought resilience.",
        "Gram": "Premier Rabi pulse crop in Akola with strong local APMC liquidity.",
        "Jowar": "Drought-hardy cereal with low irrigation requirement and reliable local fodder demand.",
    },
    "Amravati": {
        "Cotton": "Major Vidarbha staple; highly adapted to medium-to-deep black cotton soil.",
        "Soybean": "Extensively cultivated Kharif crop; high liquidity across Amravati district mandis.",
        "Tur": "Staple pulse; robust performance on upland black soils.",
        "Orange": "Signature horticultural fruit of the Amravati/Morshi belt.",
    },
    "Nagpur": {
        "Cotton": "Proven kharif crop with high yield potential in eastern Vidarbha tracts.",
        "Soybean": "Dominant oilseed with extensive local processing and oil extraction facilities.",
        "Tur": "Excellent intercrop with cotton and soybean in Nagpur district.",
        "Rice": "Cultivated in eastern command areas of Nagpur with adequate irrigation.",
    },
    "Nashik": {
        "Maize": "High-yield Kharif cereal with strong poultry feed off-take across northern Maharashtra.",
        "Bajra": "Drought-tolerant millet ideal for lighter plateau soils with modest water needs.",
        "Wheat": "Staple winter irrigated crop across Niphad and Dindori blocks.",
        "Soybean": "Widely adopted rotation crop in Nashik plateau tracts.",
        "Grapes": "World-renowned export horticulture crop in Nashik irrigated command tracts.",
    },
    "Pune": {
        "Wheat": "Established Rabi staple in Baramati, Haveli, and Shirur command zones.",
        "Jowar": "Traditional staple cereal with proven drought tolerance on medium black soils.",
        "Maize": "High-demand dual-purpose grain and silage crop for dairy clusters in Pune.",
        "Sugarcane": "Heavy cash crop in canal-irrigated belts (Neera and Bhima river basins).",
    },
    "Kolhapur": {
        "Sugarcane": "Panchganga basin flagship cash crop supported by extensive cooperative sugar mills.",
        "Rice": "Abundant southwest monsoon rainfall supports high-yielding wet paddy varieties.",
        "Maize": "Rapid-growth fodder and grain crop with high local livestock demand.",
        "Ragi": "Nutrient-rich hill millet adapted to red lateritic tracts in western Kolhapur.",
    },
    "Sangli": {
        "Sugarcane": "Thrives in Krishna river command tracts with furrow/drip irrigation.",
        "Jowar": "Rabi Maldandi jowar in eastern Sangli commands premium prices for grain and fodder.",
        "Bajra": "Staple rainfed kharif millet in drought-prone blocks like Atpadi and Jath.",
        "Cotton": "Traditional cash crop in drier eastern tehsils.",
        "Grapes": "Commercial export table-grape clusters in Tasgaon and Miraj tracts.",
    },
    "Satara": {
        "Sugarcane": "Leading cash crop in Krishna and Koyna canal command tracts.",
        "Jowar": "Reliable staple across central Satara plateau tracts.",
        "Bajra": "Adapted to lighter rain-shadow soils in eastern Satara (Man and Khatav).",
        "Maize": "High-yielding fodder and grain crop for Satara dairy cooperatives.",
    },
    "Solapur": {
        "Jowar": "Celebrated Solapur Maldandi Jowar GI belt; supreme drought resistance.",
        "Tur": "Major drought-resilient pulse crop across Solapur district.",
        "Sugarcane": "Extensive in Bhima and Sina river canal commands; requires assured water.",
        "Bajra": "Proven staple in drought-prone talukas with erratic monsoon rainfall.",
    },
}

# General agronomic notes by crop when district-specific notes are not available
DEFAULT_CROP_AGRONOMIC_NOTES: Dict[str, str] = {
    "Cotton": "Major Maharashtra cash crop; thrives in deep black soils with good internal drainage.",
    "Soybean": "Short-duration (90-100 days) oilseed crop with excellent market liquidity across Maharashtra mandis.",
    "Tur": "Deep-rooted leguminous pulse that enriches soil nitrogen and withstands mid-season dry spells.",
    "Sugarcane": "High-value long-duration cash crop; requires continuous soil moisture and assured irrigation.",
    "Wheat": "Cool-season Rabi staple cereal requiring cool nights and 3-4 timely irrigations during tillering.",
    "Jowar": "Deeply adapted Deccan cereal with exceptional drought tolerance and premium local food and fodder value.",
    "Bajra": "Short-duration millet requiring minimal water; ideal for light-to-medium rain-shadow soils.",
    "Maize": "High biomass cereal responding vigorously to applied nitrogen with steady local feed demand.",
    "Rice": "Monsoon staple requiring wet soil conditions and abundant seasonal moisture during vegetative stages.",
    "Groundnut": "Valuable oilseed pulse suited to well-drained sandy loam or friable black soils.",
    "Gram": "Key Rabi pulse utilizing residual soil moisture; vulnerable to excess vegetative growth in wet soils.",
    "Moong": "Quick 65-day pulse suitable for green manuring and short-window Kharif cultivation.",
    "Urad": "Nutritious black gram pulse thriving in warm, humid conditions during the southwest monsoon.",
}


def _get_suitability_label(combined_score: float, is_top: bool, is_verified: bool) -> str:
    """Derive farmer-friendly suitability label."""
    pct = combined_score * 100.0
    if not is_verified:
        return "Experimental Trial Only"
    if is_top or pct >= 28.0:
        return "Highly Suitable"
    if pct >= 18.0:
        return "Moderately Suitable"
    return "Low Suitability"


def _generate_farmer_reason(
    crop: str,
    district: str,
    season: str,
    npk_status: Dict[str, str],
    is_verified: bool,
    regional_label: str
) -> str:
    """Generate concise, farmer-friendly reason without technical jargon or raw probabilities."""
    n_stat = npk_status.get("N", "Medium")
    p_stat = npk_status.get("P", "Medium")
    k_stat = npk_status.get("K", "Medium")

    crop_lower = crop.lower()

    if "cotton" in crop_lower:
        return f"Ideal match for {district}'s soil nutrient balance ({n_stat} Nitrogen, {k_stat} Potassium) and {season} climate."
    elif "soybean" in crop_lower or "soyabean" in crop_lower:
        return f"Well-aligned with current soil conditions; effective nitrogen-fixer suited to {district} {season} rainfall."
    elif "tur" in crop_lower or "pigeonpeas" in crop_lower or "arhar" in crop_lower:
        return f"Deep-rooted drought resilience matches {district} soil profile; helps replenish soil nitrogen naturally."
    elif "sugarcane" in crop_lower:
        return f"High vegetative growth supported by current soil nutrient reserves in {district} ({regional_label})."
    elif "wheat" in crop_lower:
        return f"Strong agronomic fit for cool {season} conditions and balanced soil Potassium in {district}."
    elif "jowar" in crop_lower or "sorghum" in crop_lower:
        return f"Proven seasonal drought hardiness and excellent nutrient efficiency on {district} soils."
    elif "bajra" in crop_lower:
        return f"High grain and fodder potential on {district} soil with modest moisture demand in {season}."
    elif "maize" in crop_lower:
        return f"Fast-growing cereal that efficiently utilizes available soil Nitrogen in {district} {season}."
    elif "rice" in crop_lower or "paddy" in crop_lower:
        return f"Favorable match for heavy moisture retention and seasonal precipitation in {district}."
    elif "groundnut" in crop_lower:
        return f"Well-suited to friable soil structure with balanced Phosphorus for healthy pod development."
    else:
        if is_verified:
            return f"Historically proven performance in {district} during {season} with good soil compatibility."
        return f"Biophysically compatible with soil chemical profile, but lacks historical census evidence in {district}."


class RegionalCropRecommendationEngine:
    """Executes validated multi-model crop recommendation inference."""

    def __init__(self):
        self.pipeline = get_pipeline()

    def recommend_top3(
        self,
        N: float,
        P: float,
        K: float,
        ph: float,
        temperature: float,
        humidity: float,
        rainfall: float,
        district: str = "Nashik",
        season: str = "Kharif",
        water_access: Optional[str] = None,
    ) -> List[CropRecommendationFarmerItem]:
        """
        Runs dual-model biophysical + regional inference and returns exactly the top 3 recommended crops.
        """
        inp = CropRecommendationInput(
            N=float(N),
            P=float(P),
            K=float(K),
            temperature=float(temperature),
            humidity=float(humidity),
            ph=float(ph),
            rainfall=float(rainfall),
            district=district,
            season=season,
            water_access=water_access,
            w_model1=0.60,
            top_k=10,
        )

        res = self.pipeline.predict(inp)
        npk_status = res.soil_test_npk_status
        resolved_district = res.input_summary.get("district", district)
        resolved_season = res.input_summary.get("season", season)

        is_rainfed = water_access and "rainfed" in water_access.lower()

        # Take top 3 crops
        top_candidates = res.recommendations[:3]
        farmer_items: List[CropRecommendationFarmerItem] = []

        district_notes = DISTRICT_AGRONOMIC_NOTES.get(resolved_district, {})

        for idx, cand in enumerate(top_candidates):
            rank = idx + 1
            is_top = (rank == 1)
            is_verified = cand.is_regionally_supported

            label = _get_suitability_label(cand.combined_score, is_top, is_verified)

            clean_name = cand.crop
            if clean_name.lower() in ["cotton(lint)", "cotton"]:
                clean_name = "Cotton"
            elif clean_name.lower() in ["arhar/tur", "pigeonpeas", "tur"]:
                clean_name = "Tur (Pigeonpea)"
            elif clean_name.lower() in ["soyabean", "soybean"]:
                clean_name = "Soybean"
            elif clean_name.lower() in ["gram", "chickpea"]:
                clean_name = "Gram (Chickpea)"
            elif clean_name.lower() in ["moong(greengram)", "moong(green gram)", "mungbean", "moong"]:
                clean_name = "Moong (Green Gram)"
            elif clean_name.lower() in ["urad", "blackgram", "urad(black gram)"]:
                clean_name = "Urad (Black Gram)"

            reason = _generate_farmer_reason(
                crop=clean_name,
                district=resolved_district,
                season=resolved_season,
                npk_status=npk_status,
                is_verified=is_verified,
                regional_label=cand.region_suitability,
            )

            # Local considerations
            local_note = None
            for key_crop, note in district_notes.items():
                if key_crop.lower() in clean_name.lower():
                    local_note = note
                    break

            if not local_note:
                for key_crop, note in DEFAULT_CROP_AGRONOMIC_NOTES.items():
                    if key_crop.lower() in clean_name.lower():
                        local_note = note
                        break

            if not local_note:
                local_note = f"Standard commercial crop suitable for cultivation in {resolved_district} during the {resolved_season} season."

            # Water advisory
            water_adv = None
            norm_name = normalize_string(cand.crop)
            high_water_req = HIGH_WATER_DEMAND_CROPS.get(norm_name)
            if high_water_req is not None:
                if is_rainfed or rainfall < 900.0:
                    water_adv = f"High water requirement (~{high_water_req:.0f}mm). Supplemental irrigation is strongly advised."

            # Warning
            warning_msg = None
            if not is_verified:
                warning_msg = f"Biophysical Candidate Only: 0 historical records in {resolved_district} ({resolved_season}). Experimental trial recommended."

            item = CropRecommendationFarmerItem(
                crop=clean_name,
                rank=rank,
                suitability_label=label,
                reason=reason,
                local_considerations=local_note,
                water_advisory=water_adv,
                warning=warning_msg,
                is_regionally_verified=is_verified,
            )
            farmer_items.append(item)

        return farmer_items
