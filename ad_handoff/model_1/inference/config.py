"""Configuration constants and default weights for Crop Recommendation System."""

from pathlib import Path
from crop_recommendation.models import ScoringWeights

# Base paths
MODULE_DIR = Path(__file__).resolve().parent
KNOWLEDGE_BASE_PATH = MODULE_DIR / "knowledge_base.json"

# Configurable Weights Constants (User Requirement)
# Final Score = 0.50 * SoilClimateScore + 0.30 * RegionalScore + 0.20 * HistoryRotationScore
DEFAULT_SOIL_CLIMATE_WEIGHT: float = 0.50
DEFAULT_REGIONAL_WEIGHT: float = 0.30
DEFAULT_HISTORY_ROTATION_WEIGHT: float = 0.20

DEFAULT_SCORING_WEIGHTS = ScoringWeights(
    soil_climate=DEFAULT_SOIL_CLIMATE_WEIGHT,
    regional=DEFAULT_REGIONAL_WEIGHT,
    history_rotation=DEFAULT_HISTORY_ROTATION_WEIGHT,
)

# Rotation and History Scoring Constants
BASE_HISTORY_SCORE: float = 0.70
MIN_HISTORY_SCORE: float = 0.05
MAX_HISTORY_SCORE: float = 1.00

# Rule 1: Monoculture Penalties
PENALTY_CONSECUTIVE_CURRENT: float = 0.40      # Candidate == current_crop (immediate repeat)
PENALTY_CONSECUTIVE_PREV1: float = 0.25        # Candidate == prev_crop_1
PENALTY_RECURRENT_MONOCULTURE: float = 0.20    # Candidate appeared >= 2 times in recent 3 seasons

# Rule 2: Nutrient-Pressure Parameters
# NOTE: History is NOT proof of nutrient deficiency. Soil test NPK is primary!
NUTRIENT_PRESSURE_HIGH_FEADER_PENALTY_LOW_NPK: float = 0.18   # Heavy feeder after heavy feeders WITH low soil test
NUTRIENT_PRESSURE_HIGH_FEADER_PENALTY_MED_NPK: float = 0.08   # Heavy feeder after heavy feeders WITH med soil test
NUTRIENT_PRESSURE_HIGH_FEADER_PENALTY_HIGH_NPK: float = 0.00  # NO penalty if soil test confirms high nutrients!
RESTORATIVE_LIGHT_FEEDER_BONUS: float = 0.12                  # Growing light/moderate feeder after heavy feeders

# Rule 3: Diversification Bonuses
BONUS_FAMILY_DIVERSIFICATION: float = 0.12     # Candidate family differs from all recent crop families
BONUS_ROOT_DEPTH_ALTERNATION: float = 0.08     # Alternating shallow and deep root systems

# Rule 4: Legume Rotation Dynamics
BONUS_LEGUME_AFTER_HEAVY_FEEDER: float = 0.25  # Legume planted after exhaustive non-legume
BONUS_HEAVY_FEEDER_AFTER_LEGUME: float = 0.20  # Heavy cereal/cash crop capitalizing on legume N-fixation
PENALTY_LEGUME_AFTER_LEGUME: float = 0.20      # Pulse-on-pulse disease risk (Fusarium, Rhizoctonia, nematodes)

# Rule 5: Sequence Compatibility
BONUS_RECOMMENDED_SUCCESSOR: float = 0.15      # Explicitly recommended successor pair
PENALTY_AVOID_SUCCESSOR: float = 0.30          # Explicitly warned antagonistic sequence
