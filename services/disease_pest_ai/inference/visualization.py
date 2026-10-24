"""
Visualization Utility for Disease & Pest AI (Section 14).

Draws pest bounding boxes, canonical names, and confidence scores on a copy
of the input image. Never modifies the original uploaded image file or object.
"""

import logging
from pathlib import Path
from typing import Any, List, Optional, Union
from PIL import Image, ImageDraw, ImageFont

from disease_pest_ai.schemas.outputs import (
    AgricultureDiseaseResult,
    BoundingBox,
    DetectedPest,
    PestPrediction,
)

logger = logging.getLogger(__name__)

# Distinct color palette for pest bounding boxes
BOX_COLORS = [
    (0, 230, 118),    # Neon Green
    (255, 61, 0),     # Bright Orange-Red
    (41, 121, 255),   # Royal Blue
    (255, 214, 0),    # Yellow
    (213, 0, 249),    # Magenta
    (0, 229, 255),    # Cyan
]


def _load_pil_image(image: Union[str, Path, Image.Image]) -> Image.Image:
    """Load or copy PIL image safely."""
    if isinstance(image, (str, Path)):
        p = Path(image)
        if not p.exists():
            raise FileNotFoundError(f"Image not found at: {p}")
        return Image.open(p).convert("RGB")
    elif isinstance(image, Image.Image):
        return image.copy().convert("RGB")
    else:
        raise TypeError(f"Unsupported image type: {type(image)}. Expected PIL Image or file path.")


def draw_pest_detections(
    image: Union[str, Path, Image.Image],
    detections: Union[PestPrediction, List[DetectedPest], List[BoundingBox]],
    output_path: Optional[Union[str, Path]] = None,
    line_width: int = 3,
) -> Image.Image:
    """
    Render bounding boxes, pest labels, and confidence scores on a copy of the input image.
    
    Args:
        image: Original image (file path or PIL Image).
        detections: PestPrediction instance or list of DetectedPest / BoundingBox items.
        output_path: Optional path to save the visualized image.
        line_width: Pixel width of bounding box strokes.
        
    Returns:
        New PIL Image with rendered detections.
    """
    # Create fresh copy — never mutate original
    annotated = _load_pil_image(image)
    draw = ImageDraw.Draw(annotated)

    # Extract detection list
    pest_items: List[Any] = []
    if isinstance(detections, PestPrediction):
        pest_items = list(detections.pests)
    elif isinstance(detections, list):
        pest_items = detections

    if not pest_items:
        # Zero pests detected: render subtle status notice
        draw.rectangle([10, 10, 220, 36], fill=(40, 40, 40, 200))
        draw.text((16, 14), "No Pests Detected", fill=(255, 255, 255))
        if output_path:
            annotated.save(output_path)
        return annotated

    font = ImageFont.load_default()

    for idx, item in enumerate(pest_items):
        color = BOX_COLORS[idx % len(BOX_COLORS)]

        if isinstance(item, DetectedPest):
            x1, y1, x2, y2 = item.bounding_box
            label = f"{item.pest} ({item.score:.1%})"
        elif isinstance(item, BoundingBox):
            x1, y1, x2, y2 = item.box
            label = f"{item.label} ({item.score:.1%})"
        elif isinstance(item, dict):
            coords = item.get("bounding_box", item.get("box", [0, 0, 0, 0]))
            x1, y1, x2, y2 = coords
            pest_name = item.get("pest", item.get("label", "Pest"))
            score = item.get("score", 0.0)
            label = f"{pest_name} ({score:.1%})"
        else:
            continue

        # Draw bounding rectangle
        draw.rectangle([x1, y1, x2, y2], outline=color, width=line_width)

        # Draw label badge background
        badge_w = len(label) * 6 + 10
        badge_h = 16
        draw.rectangle([x1, max(0, y1 - badge_h), x1 + badge_w, max(badge_h, y1)], fill=color)

        # Draw label text
        draw.text((x1 + 4, max(2, y1 - badge_h + 2)), label, fill=(0, 0, 0), font=font)

    if output_path:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        annotated.save(out_p)
        logger.info(f"Saved pest detection visualization to: {out_p}")

    return annotated


def draw_unified_result(
    image: Union[str, Path, Image.Image],
    result: AgricultureDiseaseResult,
    output_path: Optional[Union[str, Path]] = None,
) -> Image.Image:
    """
    Render both disease diagnosis banner and pest localization bounding boxes on an image copy.
    """
    annotated = _load_pil_image(image)

    # 1. Draw pest detections if present
    if result.pest_prediction and result.pest_prediction.pests:
        annotated = draw_pest_detections(annotated, result.pest_prediction)

    draw = ImageDraw.Draw(annotated)
    font = ImageFont.load_default()

    # 2. Draw top diagnosis summary banner
    diag = result.diagnosis
    banner_text = f"DIAGNOSIS: {diag.crop} - {diag.condition} ({diag.prediction_score:.1%})"
    w, _ = annotated.size
    draw.rectangle([0, 0, w, 24], fill=(20, 20, 20))
    draw.text((10, 6), banner_text, fill=(255, 255, 255), font=font)

    if output_path:
        annotated.save(output_path)

    return annotated
