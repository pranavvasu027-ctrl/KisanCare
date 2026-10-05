"""Regional Suitability Scoring Layer.

Evaluates candidate crops based on regional agro-climatic zones, state-level
cropping patterns, and geographical adaptation.
"""

from typing import Dict, List, Optional, Set

# Major crop adaptations by Indian State / Region
REGIONAL_CROP_MAPPINGS: Dict[str, Set[str]] = {
    "punjab": {"wheat", "rice", "cotton", "maize", "mustard", "potato", "sugarcane", "mungbean"},
    "haryana": {"wheat", "rice", "cotton", "mustard", "bajra", "chickpea", "sugarcane"},
    "uttar pradesh": {"wheat", "rice", "sugarcane", "potato", "mustard", "maize", "chickpea", "pigeonpeas", "lentil", "mango"},
    "madhya pradesh": {"soybean", "wheat", "chickpea", "lentil", "mustard", "cotton", "maize", "pigeonpeas", "orange"},
    "maharashtra": {"cotton", "soybean", "sugarcane", "pigeonpeas", "chickpea", "jowar", "bajra", "pomegranate", "grapes", "banana", "onion"},
    "gujarat": {"cotton", "groundnut", "bajra", "wheat", "castor", "mustard", "tobacco", "pomegranate", "banana"},
    "rajasthan": {"bajra", "mustard", "mothbeans", "chickpea", "wheat", "clusterbean", "jowar", "pomegranate"},
    "karnataka": {"coffee", "maize", "cotton", "pigeonpeas", "rice", "groundnut", "sugarcane", "ragi", "coconut", "banana"},
    "tamil nadu": {"rice", "banana", "coconut", "sugarcane", "groundnut", "cotton", "blackgram", "mungbean"},
    "andhra pradesh": {"rice", "cotton", "chilli", "maize", "groundnut", "tobacco", "mango", "pigeonpeas", "blackgram"},
    "telangana": {"cotton", "rice", "maize", "soybean", "pigeonpeas", "chilli", "chickpea"},
    "west bengal": {"rice", "jute", "potato", "mustard", "maize", "mango"},
    "bihar": {"rice", "wheat", "maize", "potato", "lentil", "mustard", "jute", "mango"},
    "kerala": {"coconut", "rubber", "coffee", "tea", "pepper", "cardamom", "banana", "rice"},
    "himachal pradesh": {"apple", "maize", "wheat", "potato", "barley"},
    "jammu and kashmir": {"apple", "saffron", "walnut", "rice", "maize", "mustard"},
    "assam": {"tea", "rice", "jute", "mustard", "blackgram"},
    "odisha": {"rice", "blackgram", "greengram", "groundnut", "mustard", "jute"},
}


class RegionalScorer:
    """Computes RegionalScore in [0.0, 1.0] based on state or district agro-climatic alignment."""

    def __init__(self, custom_regional_map: Optional[Dict[str, Set[str]]] = None):
        self.regional_map = custom_regional_map or REGIONAL_CROP_MAPPINGS

    def score(self, candidate_crop: str, state: Optional[str] = None, district: Optional[str] = None) -> float:
        """Calculate regional suitability score."""
        if not state or not state.strip():
            # If no regional context is supplied, return neutral baseline
            return 0.70

        clean_state = state.strip().lower()
        clean_crop = candidate_crop.strip().lower()

        adapted_crops = self.regional_map.get(clean_state)
        if adapted_crops is None:
            # Check for partial state name match
            for known_state, crops in self.regional_map.items():
                if known_state in clean_state or clean_state in known_state:
                    adapted_crops = crops
                    break

        if adapted_crops is None:
            return 0.70  # Unknown state, neutral score

        if clean_crop in adapted_crops:
            return 0.90  # Prime regional crop
        else:
            return 0.55  # Secondary or non-traditional crop for the region
