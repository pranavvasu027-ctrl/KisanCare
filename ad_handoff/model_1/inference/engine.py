"""Core Recommendation Engine combining Soil/Climate, Regional, and Rotation Scoring Layers."""

import logging
from typing import Dict, List, Optional
from crop_recommendation.models import (
    SoilClimateData,
    CropHistoryInput,
    ScoringWeights,
    CropScoreBreakdown,
    RecommendationResponse,
)
from crop_recommendation.config import DEFAULT_SCORING_WEIGHTS
from crop_recommendation.knowledge_base import KnowledgeBase, get_default_knowledge_base
from crop_recommendation.rotation_scorer import HistoryRotationScorer
from crop_recommendation.soil_climate_scorer import SoilClimateScorer
from crop_recommendation.regional_scorer import RegionalScorer

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Multi-layer crop recommendation engine.

    Scores candidate crops via:
      Final Score = (w_soil * SoilClimateScore)
                  + (w_reg * RegionalScore)
                  + (w_hist * HistoryRotationScore)

    All weights are configurable constants.
    """

    def __init__(
        self,
        knowledge_base: Optional[KnowledgeBase] = None,
        rotation_scorer: Optional[HistoryRotationScorer] = None,
        soil_climate_scorer: Optional[SoilClimateScorer] = None,
        regional_scorer: Optional[RegionalScorer] = None,
        default_weights: Optional[ScoringWeights] = None,
    ):
        self.kb = knowledge_base or get_default_knowledge_base()
        self.rotation_scorer = rotation_scorer or HistoryRotationScorer(self.kb)
        self.soil_climate_scorer = soil_climate_scorer or SoilClimateScorer()
        self.regional_scorer = regional_scorer or RegionalScorer()
        self.default_weights = default_weights or DEFAULT_SCORING_WEIGHTS

    def recommend(
        self,
        soil_climate: SoilClimateData,
        history: CropHistoryInput,
        candidate_crops: Optional[List[str]] = None,
        weights: Optional[ScoringWeights] = None,
        external_soil_scores: Optional[Dict[str, float]] = None,
        top_k: int = 5,
    ) -> RecommendationResponse:
        """Generate ranked crop recommendations with individual score breakdowns and explanations.

        Args:
            soil_climate: Soil test measurements (N, P, K, pH) and local climate parameters.
            history: Farmer's crop history (current crop, prev 1, prev 2, prev 3).
            candidate_crops: Optional list of crop names to evaluate. Defaults to all KB crops.
            weights: Optional custom scoring weights override.
            external_soil_scores: Optional dictionary of {crop_name: score} from an external
                Hugging Face model. If provided, used directly as SoilClimateScore.
            top_k: Number of top recommendations to return.

        Returns:
            RecommendationResponse with sorted recommendations and score breakdown.
        """
        active_weights = weights or self.default_weights

        # Determine candidate crops
        if candidate_crops and len(candidate_crops) > 0:
            target_crops = [c.strip().lower() for c in candidate_crops]
        else:
            target_crops = self.kb.list_crops()

        results: List[CropScoreBreakdown] = []

        for crop_name in target_crops:
            # 1. Soil / Climate Score (from external HF model if provided, else HF model / fallback)
            if external_soil_scores and crop_name in external_soil_scores:
                sc_score = max(0.0, min(1.0, float(external_soil_scores[crop_name])))
                sc_source = "External HF Model Probability Dictionary"
            else:
                sc_score, sc_source = self.soil_climate_scorer.score(crop_name, soil_climate)

            # 2. Regional Suitability Score
            reg_score = self.regional_scorer.score(
                crop_name, state=soil_climate.state, district=soil_climate.district
            )

            # 3. History / Rotation Score (Independent rule-based layer)
            rot_score, rot_reason, detailed_factors = self.rotation_scorer.score(
                candidate_crop_name=crop_name,
                history=history,
                soil_climate=soil_climate,
            )

            # 4. Composite Final Score
            # Final Score = 0.50 * SoilClimateScore + 0.30 * RegionalScore + 0.20 * HistoryRotationScore
            final_score = (
                (active_weights.soil_climate * sc_score)
                + (active_weights.regional * reg_score)
                + (active_weights.history_rotation * rot_score)
            )
            final_score = max(0.0, min(1.0, round(final_score, 4)))

            results.append(
                CropScoreBreakdown(
                    crop=crop_name,
                    soil_climate_score=round(sc_score, 4),
                    regional_score=round(reg_score, 4),
                    history_rotation_score=round(rot_score, 4),
                    final_score=final_score,
                    reason=rot_reason,
                    soil_climate_source=sc_source,
                    detailed_factors=detailed_factors,
                )
            )

        # Sort descending by final score
        results.sort(key=lambda x: x.final_score, reverse=True)
        top_results = results[:top_k]

        return RecommendationResponse(
            recommendations=top_results,
            weights_used=active_weights,
            soil_test_npk_status=soil_climate.get_npk_adequacy(),
            history_evaluated=history.get_ordered_history(),
            model_source=self.soil_climate_scorer.model_source,
            model_loaded=self.soil_climate_scorer.model_loaded,
        )
