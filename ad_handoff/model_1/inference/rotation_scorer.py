"""Crop History and Rotation Scoring Layer.

Evaluates candidate crops against historical cultivation sequence across 5 core dimensions:
1. Repeated cultivation of the same crop (monoculture penalty)
2. Recent nutrient-demanding crops (nutrient pressure vs current soil-test invariant)
3. Benefits of crop diversification (botanical family & root depth alternation)
4. Legume rotation dynamics (N-fixation synergy vs pulse-on-pulse disease risk)
5. Crop sequence compatibility (known agronomic successor synergies & antagonisms)
"""

from typing import Dict, List, Optional, Tuple, Any
from crop_recommendation.models import (
    CropHistoryInput,
    SoilClimateData,
    CropKnowledge,
)
from crop_recommendation.knowledge_base import KnowledgeBase, get_default_knowledge_base
from crop_recommendation.config import (
    BASE_HISTORY_SCORE,
    MIN_HISTORY_SCORE,
    MAX_HISTORY_SCORE,
    PENALTY_CONSECUTIVE_CURRENT,
    PENALTY_CONSECUTIVE_PREV1,
    PENALTY_RECURRENT_MONOCULTURE,
    NUTRIENT_PRESSURE_HIGH_FEADER_PENALTY_LOW_NPK,
    NUTRIENT_PRESSURE_HIGH_FEADER_PENALTY_MED_NPK,
    NUTRIENT_PRESSURE_HIGH_FEADER_PENALTY_HIGH_NPK,
    RESTORATIVE_LIGHT_FEEDER_BONUS,
    BONUS_FAMILY_DIVERSIFICATION,
    BONUS_ROOT_DEPTH_ALTERNATION,
    BONUS_LEGUME_AFTER_HEAVY_FEEDER,
    BONUS_HEAVY_FEEDER_AFTER_LEGUME,
    PENALTY_LEGUME_AFTER_LEGUME,
    BONUS_RECOMMENDED_SUCCESSOR,
    PENALTY_AVOID_SUCCESSOR,
)


class HistoryRotationScorer:
    """Independent, rule-based rotation and nutrient-pressure scoring layer.

    IMPORTANT: Crop history is NOT treated as proof of nutrient deficiency.
    Current soil-test N/P/K values remain the primary indicator of nutrient status.
    """

    def __init__(self, knowledge_base: Optional[KnowledgeBase] = None):
        self.kb = knowledge_base or get_default_knowledge_base()

    def score(
        self,
        candidate_crop_name: str,
        history: CropHistoryInput,
        soil_climate: Optional[SoilClimateData] = None,
    ) -> Tuple[float, str, Dict[str, Any]]:
        """Calculate the History/Rotation Score for a candidate crop.

        Args:
            candidate_crop_name: Name of crop being evaluated.
            history: Crop history (current crop, prev 1, 2, 3 crops).
            soil_climate: Current soil test and climate data (used for nutrient pressure check).

        Returns:
            Tuple of:
              - history_rotation_score: float in [0.05, 1.00]
              - reason: Clear textual agronomic rationale
              - factors: Structured dictionary of applied rules, bonuses, and penalties
        """
        candidate = self.kb.get_or_default(candidate_crop_name)
        history_list = history.get_ordered_history()

        # If no history is provided by the farmer, return neutral baseline score
        if not history_list:
            return (
                round(BASE_HISTORY_SCORE, 4),
                "No prior crop history specified; assigned neutral baseline rotation score.",
                {"base_score": BASE_HISTORY_SCORE, "adjustments": []}
            )

        current_crop_name = history.current_crop.strip().lower() if history.current_crop else (history_list[0] if history_list else None)
        immediate_preceding = current_crop_name or (history_list[0] if history_list else None)
        prev_crop_1_name = history.prev_crop_1.strip().lower() if history.prev_crop_1 else (history_list[1] if len(history_list) > 1 else None)

        score = BASE_HISTORY_SCORE
        adjustments: List[Dict[str, Any]] = []
        positive_reasons: List[str] = []
        negative_reasons: List[str] = []
        neutral_notes: List[str] = []

        cand_canonical = candidate.name.lower()

        # =========================================================================
        # 1. REPEATED CULTIVATION OF THE SAME CROP (MONOCULTURE)
        # =========================================================================
        # Immediate consecutive monoculture (Candidate == current_crop)
        if immediate_preceding and self._is_same_crop(cand_canonical, immediate_preceding):
            deduction = PENALTY_CONSECUTIVE_CURRENT
            score -= deduction
            adjustments.append({"rule": "monoculture_current", "delta": -deduction})
            negative_reasons.append(
                f"Severe monoculture penalty: Cultivating {candidate.name.capitalize()} directly after itself "
                f"multiplies soil-borne pests, weed resistance, and depletes specialized root-zone niches."
            )
        elif prev_crop_1_name and self._is_same_crop(cand_canonical, prev_crop_1_name):
            deduction = PENALTY_CONSECUTIVE_PREV1
            score -= deduction
            adjustments.append({"rule": "monoculture_prev1", "delta": -deduction})
            negative_reasons.append(
                f"Recent repetition: {candidate.name.capitalize()} was cultivated in season T-1; "
                f"recommend wider rotation interval to break pathogen cycles."
            )

        # Recurrent cultivation (cultivated >= 2 times in recent history)
        repeat_count = sum(1 for c in history_list if self._is_same_crop(cand_canonical, c))
        if repeat_count >= 2:
            deduction = PENALTY_RECURRENT_MONOCULTURE
            score -= deduction
            adjustments.append({"rule": "recurrent_monoculture", "delta": -deduction})
            negative_reasons.append(
                f"Repetitive cultivation: {candidate.name.capitalize()} appeared {repeat_count} times "
                f"in recent seasons; rotation break strongly indicated."
            )
        elif repeat_count == 0:
            # Crop not grown in recent history gets clean rotation status
            neutral_notes.append(f"Not cultivated in the last {len(history_list)} seasons (clean break).")

        # =========================================================================
        # 2. RECENT NUTRIENT-DEMANDING CROPS & SOIL-TEST PRIMACY
        # =========================================================================
        # Identify heavy feeder history
        recent_crops = [self.kb.get_crop(c) for c in history_list[:2]]
        recent_heavy_feeders = [
            c.name.capitalize() for c in recent_crops
            if c and (c.feeder_type == "Heavy Feeder" or c.n_demand in ("High", "Very High"))
        ]

        if recent_heavy_feeders:
            if candidate.feeder_type == "Heavy Feeder" or candidate.n_demand in ("High", "Very High"):
                # Candidate is also heavy feeder.
                # Check Soil-Test Primacy:
                # Crop history must NOT be treated as proof of nutrient deficiency!
                # Current soil test N/P/K is the primary indicator.
                if soil_climate is not None:
                    npk_status = soil_climate.get_npk_adequacy()
                    n_status = npk_status.get("N", "Medium")
                    p_status = npk_status.get("P", "Medium")
                    k_status = npk_status.get("K", "Medium")

                    if n_status == "High" and (p_status == "High" or k_status == "High"):
                        # Soil test confirms high nutrient status! NO penalty!
                        adjustments.append({"rule": "nutrient_pressure_soil_test_high", "delta": 0.0})
                        positive_reasons.append(
                            f"Soil-test confirmation: Available nutrients are High (N:{soil_climate.N}, P:{soil_climate.P}, K:{soil_climate.K}). "
                            f"Adequate fertility is verified, safely supporting {candidate.name.capitalize()} despite exhaustive recent crops ({', '.join(recent_heavy_feeders)})."
                        )
                    elif n_status == "Medium":
                        deduction = NUTRIENT_PRESSURE_HIGH_FEADER_PENALTY_MED_NPK
                        score -= deduction
                        adjustments.append({"rule": "nutrient_pressure_med", "delta": -deduction})
                        negative_reasons.append(
                            f"Nutrient fatigue caution: Recent crops ({', '.join(recent_heavy_feeders)}) were heavy feeders and soil test N is moderate ({soil_climate.N} kg/ha); "
                            f"successive heavy feeder demands supplemental fertilizer or legume rest."
                        )
                    else:  # n_status == "Low"
                        deduction = NUTRIENT_PRESSURE_HIGH_FEADER_PENALTY_LOW_NPK
                        score -= deduction
                        adjustments.append({"rule": "nutrient_pressure_low", "delta": -deduction})
                        negative_reasons.append(
                            f"Nutrient exhaustion risk: Preceded by heavy feeders ({', '.join(recent_heavy_feeders)}) and current soil test indicates Low N ({soil_climate.N} kg/ha); "
                            f"planting another heavy feeder increases nutrient depletion risk."
                        )
                else:
                    # No soil test provided, apply mild caution
                    deduction = NUTRIENT_PRESSURE_HIGH_FEADER_PENALTY_MED_NPK
                    score -= deduction
                    adjustments.append({"rule": "nutrient_pressure_default", "delta": -deduction})
                    negative_reasons.append(
                        f"Cumulative nutrient demand: Successive heavy feeders ({', '.join(recent_heavy_feeders)}); "
                        f"soil test recommended to verify nutrient sufficiency."
                    )
            elif candidate.feeder_type in ("Light Feeder", "Soil Builder (Legume)"):
                bonus = RESTORATIVE_LIGHT_FEEDER_BONUS
                score += bonus
                adjustments.append({"rule": "restorative_crop_bonus", "delta": bonus})
                positive_reasons.append(
                    f"Restorative crop: As a {candidate.feeder_type.lower()}, {candidate.name.capitalize()} provides essential "
                    f"soil recovery following heavy nutrient-extracting crops ({', '.join(recent_heavy_feeders)})."
                )

        # =========================================================================
        # 3. BENEFITS OF CROP DIVERSIFICATION
        # =========================================================================
        # Family diversification
        recent_families = {
            self.kb.get_crop(c).crop_family for c in history_list
            if self.kb.get_crop(c) is not None
        }
        if candidate.crop_family and candidate.crop_family != "Unknown":
            if candidate.crop_family not in recent_families:
                bonus = BONUS_FAMILY_DIVERSIFICATION
                score += bonus
                adjustments.append({"rule": "family_diversification", "delta": bonus})
                positive_reasons.append(
                    f"Botanical family diversification: Introduces {candidate.crop_family} into a sequence dominated by "
                    f"{', '.join(recent_families) if recent_families else 'monoculture'}, suppressing specialized pathogens."
                )
            elif immediate_preceding:
                prev_crop_obj = self.kb.get_crop(immediate_preceding)
                if (
                    prev_crop_obj
                    and prev_crop_obj.crop_family == candidate.crop_family
                    and not candidate.is_legume
                    and not self._is_same_crop(cand_canonical, immediate_preceding)
                ):
                    # Same family but different crop (e.g. Potato -> Tomato, or Rice -> Wheat)
                    deduction = 0.08
                    score -= deduction
                    adjustments.append({"rule": "same_family_succession", "delta": -deduction})
                    negative_reasons.append(
                        f"Family continuity caution: Consecutive {candidate.crop_family} crops ({prev_crop_obj.name.capitalize()} -> {candidate.name.capitalize()}) "
                        f"share common root-zone pests and disease vectors."
                    )

        # Root depth alternation
        if immediate_preceding:
            prev_crop_obj = self.kb.get_crop(immediate_preceding)
            if prev_crop_obj:
                if prev_crop_obj.root_depth == "Shallow" and candidate.root_depth == "Deep":
                    bonus = BONUS_ROOT_DEPTH_ALTERNATION
                    score += bonus
                    adjustments.append({"rule": "root_depth_alternation_deep", "delta": bonus})
                    positive_reasons.append(
                        f"Root stratification synergy: Deep taproots ({candidate.name.capitalize()}) penetrate "
                        f"plow pans and access subsoil nutrients after shallow-rooted {prev_crop_obj.name.capitalize()}."
                    )
                elif prev_crop_obj.root_depth == "Deep" and candidate.root_depth == "Shallow":
                    bonus = round(BONUS_ROOT_DEPTH_ALTERNATION * 0.75, 4)
                    score += bonus
                    adjustments.append({"rule": "root_depth_alternation_shallow", "delta": bonus})
                    positive_reasons.append(
                        f"Root depth alternation: Shallow root feeder explores topsoil following deep-rooted {prev_crop_obj.name.capitalize()}."
                    )

        # =========================================================================
        # 4. LEGUME ROTATION DYNAMICS
        # =========================================================================
        prev_crop_obj = self.kb.get_crop(immediate_preceding) if immediate_preceding else None

        if candidate.is_legume:
            # Candidate is a legume
            if prev_crop_obj and prev_crop_obj.is_legume:
                # Legume immediately after legume
                deduction = PENALTY_LEGUME_AFTER_LEGUME
                score -= deduction
                adjustments.append({"rule": "legume_after_legume", "delta": -deduction})
                negative_reasons.append(
                    f"Pulse-on-pulse caution: Successive legumes ({prev_crop_obj.name.capitalize()} -> {candidate.name.capitalize()}) "
                    f"increase susceptibility to Fusarium wilt, Rhizoctonia root rot, and root-knot nematodes."
                )
            else:
                # Legume after non-legume (especially cereals or heavy feeders)
                bonus = BONUS_LEGUME_AFTER_HEAVY_FEEDER
                score += bonus
                adjustments.append({"rule": "legume_after_non_legume", "delta": bonus})
                preceding_desc = prev_crop_obj.name.capitalize() if prev_crop_obj else "non-legume crops"
                positive_reasons.append(
                    f"Legume rotation benefit: Biologically fixes atmospheric nitrogen (30-60 kg N/ha credit), "
                    f"replenishes soil organic carbon, and interrupts pest cycles after {preceding_desc}."
                )
        else:
            # Candidate is NOT a legume (e.g. cereal, fiber, tuber)
            # Check if immediately preceded by a legume
            preceding_was_legume = False
            preceding_legume_name = ""
            if prev_crop_obj and prev_crop_obj.is_legume:
                preceding_was_legume = True
                preceding_legume_name = prev_crop_obj.name.capitalize()
            elif prev_crop_1_name and self.kb.is_legume(prev_crop_1_name):
                preceding_was_legume = True
                preceding_legume_name = prev_crop_1_name.capitalize()

            if preceding_was_legume:
                bonus = BONUS_HEAVY_FEEDER_AFTER_LEGUME
                score += bonus
                adjustments.append({"rule": "cereal_after_legume_bonus", "delta": bonus})
                positive_reasons.append(
                    f"Legume residual synergy: {candidate.name.capitalize()} capitalizes directly on biologically fixed nitrogen "
                    f"and enhanced microbial tilth left by preceding legume ({preceding_legume_name})."
                )

        # =========================================================================
        # 5. CROP SEQUENCE COMPATIBILITY (EXPLICIT KNOWLEDGE BASE MATRIX)
        # =========================================================================
        if immediate_preceding:
            seq_check = self.kb.check_sequence_compatibility(immediate_preceding, cand_canonical)
            if seq_check["recommended"]:
                bonus = BONUS_RECOMMENDED_SUCCESSOR
                score += bonus
                adjustments.append({"rule": "recommended_successor", "delta": bonus})
                positive_reasons.append(
                    f"Proven sequence synergy: {candidate.name.capitalize()} is an agronomically recommended successor after {immediate_preceding.capitalize()}."
                )
            if seq_check["avoid"]:
                deduction = PENALTY_AVOID_SUCCESSOR
                score -= deduction
                adjustments.append({"rule": "avoid_successor", "delta": -deduction})
                negative_reasons.append(
                    f"Incompatible sequence warning: High agronomic risk (antagonistic root exudates or shared disease host) following {immediate_preceding.capitalize()}."
                )

        # =========================================================================
        # FINALIZE SCORE AND REASONING STRING
        # =========================================================================
        clamped_score = max(MIN_HISTORY_SCORE, min(MAX_HISTORY_SCORE, round(score, 4)))

        # Construct concise, human-readable reason
        reason_parts = []
        if positive_reasons:
            reason_parts.append("; ".join(positive_reasons))
        if negative_reasons:
            reason_parts.append("; ".join(negative_reasons))
        if not reason_parts and neutral_notes:
            reason_parts.append("; ".join(neutral_notes))
        elif not reason_parts:
            reason_parts.append("Balanced rotational fit with no specific agronomic conflicts.")

        full_reason = ". ".join(reason_parts)
        if not full_reason.endswith("."):
            full_reason += "."

        detailed_factors = {
            "base_score": BASE_HISTORY_SCORE,
            "raw_calculated_score": round(score, 4),
            "final_rotation_score": clamped_score,
            "adjustments": adjustments,
            "positive_points": positive_reasons,
            "penalties": negative_reasons,
            "history_considered": history_list,
        }

        return clamped_score, full_reason, detailed_factors

    def _is_same_crop(self, crop_a: str, crop_b: str) -> bool:
        """Check if two crop names refer to the same crop entity."""
        if not crop_a or not crop_b:
            return False
        clean_a = crop_a.strip().lower()
        clean_b = crop_b.strip().lower()
        if clean_a == clean_b:
            return True
        obj_a = self.kb.get_crop(clean_a)
        obj_b = self.kb.get_crop(clean_b)
        if obj_a and obj_b:
            return obj_a.name.lower() == obj_b.name.lower()
        return False
