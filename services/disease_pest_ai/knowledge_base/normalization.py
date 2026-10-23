"""
Canonical Normalization Layer for Crops, Diseases, Pests, Active Ingredients, and Formulations.

Enforces:
1. Strict canonical mappings for case/punctuation variances (e.g., 'tomato', 'Tomato', 'TOMATO' -> 'Tomato').
2. Biological distinction — NEVER merges distinct pathologies (e.g. Early Blight vs Late Blight).
3. Verified biological synonym resolution (e.g., 'Alternaria solani' -> 'Early Blight' on Tomato).
"""

import re
from typing import Optional, Tuple
from disease_pest_ai.schemas.outputs import ConditionType


# Canonical Crops supported by the system
CANONICAL_CROPS = {
    "tomato": "Tomato",
    "tomatoes": "Tomato",
    "apple": "Apple",
    "apples": "Apple",
    "potato": "Potato",
    "potatoes": "Potato",
    "corn": "Corn",
    "maize": "Corn",
    "corn maize": "Corn",
    "corn (maize)": "Corn",
    "grape": "Grape",
    "grapes": "Grape",
    "bell pepper": "Bell Pepper",
    "pepper": "Bell Pepper",
    "pepper, bell": "Bell Pepper",
    "capsicum": "Bell Pepper",
    "chilli": "Bell Pepper",
    "peach": "Peach",
    "cherry": "Cherry",
    "sour cherry": "Cherry",
    "cherry including sour": "Cherry",
    "squash": "Squash",
    "strawberry": "Strawberry",
    "orange": "Orange",
    "citrus": "Orange",
    "cotton": "Cotton",
    "blueberry": "Blueberry",
    "raspberry": "Raspberry",
    "soybean": "Soybean",
    "soybeans": "Soybean",
}


# Canonical Pathologies & Verified Biological Targets
# Key: (normalized_crop, normalized_condition_text) -> (canonical_condition, target_pathogen, ConditionType)
CANONICAL_CONDITIONS = {
    # TOMATO
    ("tomato", "early blight"): ("Early Blight", "Alternaria solani", ConditionType.DISEASE),
    ("tomato", "alternaria solani"): ("Early Blight", "Alternaria solani", ConditionType.DISEASE),
    ("tomato", "late blight"): ("Late Blight", "Phytophthora infestans", ConditionType.DISEASE),
    ("tomato", "phytophthora infestans"): ("Late Blight", "Phytophthora infestans", ConditionType.DISEASE),
    ("tomato", "bacterial spot"): ("Bacterial Spot", "Xanthomonas campestris pv. vesicatoria", ConditionType.DISEASE),
    ("tomato", "xanthomonas"): ("Bacterial Spot", "Xanthomonas campestris pv. vesicatoria", ConditionType.DISEASE),
    ("tomato", "leaf mold"): ("Leaf Mold", "Passalora fulva", ConditionType.DISEASE),
    ("tomato", "passalora fulva"): ("Leaf Mold", "Passalora fulva", ConditionType.DISEASE),
    ("tomato", "septoria leaf spot"): ("Septoria Leaf Spot", "Septoria lycopersici", ConditionType.DISEASE),
    ("tomato", "septoria lycopersici"): ("Septoria Leaf Spot", "Septoria lycopersici", ConditionType.DISEASE),
    ("tomato", "spider mites"): ("Spider Mites (Two-Spotted Spider Mite)", "Tetranychus urticae", ConditionType.PEST),
    ("tomato", "spider mites two spotted spider mite"): ("Spider Mites (Two-Spotted Spider Mite)", "Tetranychus urticae", ConditionType.PEST),
    ("tomato", "tetranychus urticae"): ("Spider Mites (Two-Spotted Spider Mite)", "Tetranychus urticae", ConditionType.PEST),
    ("tomato", "target spot"): ("Target Spot", "Corynespora cassiicola", ConditionType.DISEASE),
    ("tomato", "corynespora cassiicola"): ("Target Spot", "Corynespora cassiicola", ConditionType.DISEASE),
    ("tomato", "tomato yellow leaf curl virus"): ("Tomato Yellow Leaf Curl Virus", "Tomato yellow leaf curl virus (TYLCV)", ConditionType.DISEASE),
    ("tomato", "tylcv"): ("Tomato Yellow Leaf Curl Virus", "Tomato yellow leaf curl virus (TYLCV)", ConditionType.DISEASE),
    ("tomato", "tomato mosaic virus"): ("Tomato Mosaic Virus", "Tomato mosaic virus (ToMV)", ConditionType.DISEASE),
    ("tomato", "tomv"): ("Tomato Mosaic Virus", "Tomato mosaic virus (ToMV)", ConditionType.DISEASE),
    ("tomato", "healthy"): ("Healthy", "Normal Plant Tissue", ConditionType.HEALTHY),

    # APPLE
    ("apple", "apple scab"): ("Apple Scab", "Venturia inaequalis", ConditionType.DISEASE),
    ("apple", "scab"): ("Apple Scab", "Venturia inaequalis", ConditionType.DISEASE),
    ("apple", "venturia inaequalis"): ("Apple Scab", "Venturia inaequalis", ConditionType.DISEASE),
    ("apple", "black rot"): ("Black Rot", "Botryosphaeria obtusa", ConditionType.DISEASE),
    ("apple", "botryosphaeria obtusa"): ("Black Rot", "Botryosphaeria obtusa", ConditionType.DISEASE),
    ("apple", "cedar apple rust"): ("Cedar Apple Rust", "Gymnosporangium juniperi-virginianae", ConditionType.DISEASE),
    ("apple", "rust"): ("Cedar Apple Rust", "Gymnosporangium juniperi-virginianae", ConditionType.DISEASE),
    ("apple", "healthy"): ("Healthy", "Normal Plant Tissue", ConditionType.HEALTHY),

    # POTATO
    ("potato", "early blight"): ("Early Blight", "Alternaria solani", ConditionType.DISEASE),
    ("potato", "alternaria solani"): ("Early Blight", "Alternaria solani", ConditionType.DISEASE),
    ("potato", "late blight"): ("Late Blight", "Phytophthora infestans", ConditionType.DISEASE),
    ("potato", "phytophthora infestans"): ("Late Blight", "Phytophthora infestans", ConditionType.DISEASE),
    ("potato", "healthy"): ("Healthy", "Normal Plant Tissue", ConditionType.HEALTHY),

    # CORN
    ("corn", "common rust"): ("Common Rust", "Puccinia sorghi", ConditionType.DISEASE),
    ("corn", "puccinia sorghi"): ("Common Rust", "Puccinia sorghi", ConditionType.DISEASE),
    ("corn", "northern leaf blight"): ("Northern Leaf Blight", "Exserohilum turcicum", ConditionType.DISEASE),
    ("corn", "turcicum leaf blight"): ("Northern Leaf Blight", "Exserohilum turcicum", ConditionType.DISEASE),
    ("corn", "exserohilum turcicum"): ("Northern Leaf Blight", "Exserohilum turcicum", ConditionType.DISEASE),
    ("corn", "cercospora leaf spot gray leaf spot"): ("Cercospora Leaf Spot Gray Leaf Spot", "Cercospora zeae-maydis", ConditionType.DISEASE),
    ("corn", "gray leaf spot"): ("Cercospora Leaf Spot Gray Leaf Spot", "Cercospora zeae-maydis", ConditionType.DISEASE),
    ("corn", "healthy"): ("Healthy", "Normal Plant Tissue", ConditionType.HEALTHY),

    # GRAPE
    ("grape", "black rot"): ("Black Rot", "Guignardia bidwellii", ConditionType.DISEASE),
    ("grape", "guignardia bidwellii"): ("Black Rot", "Guignardia bidwellii", ConditionType.DISEASE),
    ("grape", "esca black measles"): ("Esca (Black Measles)", "Phaeomoniella / Phaeoacremonium complex", ConditionType.DISEASE),
    ("grape", "esca"): ("Esca (Black Measles)", "Phaeomoniella / Phaeoacremonium complex", ConditionType.DISEASE),
    ("grape", "leaf blight isariopsis leaf spot"): ("Leaf Blight (Isariopsis Leaf Spot)", "Pseudocercospora vitis", ConditionType.DISEASE),
    ("grape", "leaf blight"): ("Leaf Blight (Isariopsis Leaf Spot)", "Pseudocercospora vitis", ConditionType.DISEASE),
    ("grape", "healthy"): ("Healthy", "Normal Plant Tissue", ConditionType.HEALTHY),

    # BELL PEPPER
    ("bell pepper", "bacterial spot"): ("Bacterial Spot", "Xanthomonas campestris pv. vesicatoria", ConditionType.DISEASE),
    ("bell pepper", "healthy"): ("Healthy", "Normal Plant Tissue", ConditionType.HEALTHY),

    # PEACH
    ("peach", "bacterial spot"): ("Bacterial Spot", "Xanthomonas arboricola pv. pruni", ConditionType.DISEASE),
    ("peach", "healthy"): ("Healthy", "Normal Plant Tissue", ConditionType.HEALTHY),

    # CHERRY
    ("cherry", "powdery mildew"): ("Powdery Mildew", "Podosphaera clandestina", ConditionType.DISEASE),
    ("cherry", "healthy"): ("Healthy", "Normal Plant Tissue", ConditionType.HEALTHY),

    # SQUASH
    ("squash", "powdery mildew"): ("Powdery Mildew", "Podosphaera xanthii", ConditionType.DISEASE),

    # STRAWBERRY
    ("strawberry", "leaf scorch"): ("Leaf Scorch", "Diplocarpon earlianum", ConditionType.DISEASE),
    ("strawberry", "healthy"): ("Healthy", "Normal Plant Tissue", ConditionType.HEALTHY),

    # ORANGE / CITRUS
    ("orange", "huanglongbing citrus greening"): ("Huanglongbing (Citrus Greening)", "Candidatus Liberibacter asiaticus", ConditionType.DISEASE),
    ("orange", "citrus greening"): ("Huanglongbing (Citrus Greening)", "Candidatus Liberibacter asiaticus", ConditionType.DISEASE),

    # COTTON PEST TRAP
    ("cotton", "cotton bollworm infestation"): ("Cotton Bollworm Infestation", "Helicoverpa armigera / Pectinophora gossypiella", ConditionType.PEST),
    ("cotton", "bollworm"): ("Cotton Bollworm Infestation", "Helicoverpa armigera / Pectinophora gossypiella", ConditionType.PEST),
    ("cotton", "american bollworm"): ("Cotton Bollworm Infestation", "Helicoverpa armigera", ConditionType.PEST),
    ("cotton", "pink bollworm"): ("Cotton Bollworm Infestation", "Pectinophora gossypiella", ConditionType.PEST),

    # BASELINE HEALTHY
    ("blueberry", "healthy"): ("Healthy", "Normal Plant Tissue", ConditionType.HEALTHY),
    ("raspberry", "healthy"): ("Healthy", "Normal Plant Tissue", ConditionType.HEALTHY),
    ("soybean", "healthy"): ("Healthy", "Normal Plant Tissue", ConditionType.HEALTHY),
}


def clean_text(text: Optional[str]) -> str:
    """Strip punctuation and normalize whitespace to single lowercase space."""
    if not text:
        return ""
    clean = re.sub(r"[^\w\s]", " ", text.lower()).strip()
    return re.sub(r"\s+", " ", clean)


def normalize_crop(crop_name: Optional[str]) -> Tuple[str, bool]:
    """
    Map raw crop name to canonical title case.
    Returns (canonical_crop_name, is_supported).
    """
    clean = clean_text(crop_name)
    if clean in CANONICAL_CROPS:
        return CANONICAL_CROPS[clean], True
    # If not directly matched, check if any canonical key is in clean string
    for key, canon in CANONICAL_CROPS.items():
        if key == clean or f" {key} " in f" {clean} ":
            return canon, True
    return (crop_name.strip().title() if crop_name else "Unknown", False)


def normalize_condition(
    condition_name: Optional[str],
    crop_name: Optional[str] = None
) -> Tuple[str, Optional[str], ConditionType]:
    """
    Map condition text to canonical name and verified biological target.
    Returns (canonical_condition, biological_target, condition_type).
    """
    clean_cond = clean_text(condition_name)
    crop_canon, _ = normalize_crop(crop_name)
    clean_crop = clean_text(crop_canon)

    # 1. Direct dual-key match
    if (clean_crop, clean_cond) in CANONICAL_CONDITIONS:
        return CANONICAL_CONDITIONS[(clean_crop, clean_cond)]

    # 2. Check condition key across clean_cond
    for (c, d), val in CANONICAL_CONDITIONS.items():
        if c == clean_crop and (d in clean_cond or clean_cond in d):
            return val

    # 3. Fallback for healthy
    if "healthy" in clean_cond:
        return ("Healthy", "Normal Plant Tissue", ConditionType.HEALTHY)

    # 4. Unknown condition
    title_cond = condition_name.strip().title() if condition_name else "Unknown"
    return (title_cond, None, ConditionType.UNKNOWN)


def normalize_active_ingredient(ai: Optional[str]) -> Optional[str]:
    """Standardize active ingredient name."""
    if not ai:
        return None
    return ai.strip().title()


def normalize_formulation(form: Optional[str]) -> Optional[str]:
    """Standardize formulation string."""
    if not form:
        return None
    return form.strip().upper()
