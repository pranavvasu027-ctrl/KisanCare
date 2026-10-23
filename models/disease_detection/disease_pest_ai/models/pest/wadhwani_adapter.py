"""
WadhwaniAI Pest Monitoring Adapter.

Upstream Repository: WadhwaniAI/pest-monitoring (GitHub)
Architecture: Single Shot MultiBox Detector (SSD) / TorchScript JIT
Pests Targeted: American Bollworm (ABW), Pink Bollworm (PBW) in Cotton Pheromone Traps
License: Apache-2.0

Audit Finding:
No pretrained model weights / checkpoints (.pt, .jit, .ckpt) are published in the
upstream repository or Hugging Face. Per integration instructions: "If no usable
checkpoint exists: do not invent one."

This adapter implements the standard interface, handles optional custom checkpoint
loading via TorchScript if supplied, and gracefully reports checkpoint unavailability
without inventing synthetic weights.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from PIL import Image

import torch

from disease_pest_ai.models.base import (
    BaseModelAdapter,
    check_crop_consistency,
    load_image_to_pil,
)
from disease_pest_ai.schemas.outputs import (
    BoundingBox,
    ConditionType,
    PredictionResult,
    TopPrediction,
)

logger = logging.getLogger(__name__)


class WadhwaniPestAdapter(BaseModelAdapter):
    """
    Adapter for WadhwaniAI/pest-monitoring trap detection model.
    """

    model_name: str = "WadhwaniAI/pest-monitoring"
    model_version: str = "SSD-300 Cotton Trap (Unpublished Checkpoint)"

    def __init__(
        self,
        checkpoint_path: Optional[Union[str, Path]] = None,
        metadata_path: Optional[Union[str, Path]] = None,
        device: Optional[str] = None,
    ):
        self.device = torch.device(
            device if device else ("cuda" if torch.cuda.is_available() else "cpu")
        )
        self.checkpoint_path = Path(checkpoint_path) if checkpoint_path else None
        self.metadata_path = Path(metadata_path) if metadata_path else None
        self.model = None

        if self.checkpoint_path and self.checkpoint_path.exists():
            try:
                self.model = torch.jit.load(str(self.checkpoint_path), map_location=self.device)
                self.model.eval()
                logger.info(f"Loaded Wadhwani JIT model from {self.checkpoint_path}")
            except Exception as e:
                logger.error(f"Failed loading JIT checkpoint {self.checkpoint_path}: {e}")
                self.model = None

    def is_available(self) -> bool:
        """
        Check if a usable pretrained checkpoint is loaded.
        Returns False when no checkpoint is published or found.
        """
        return self.model is not None

    def predict(
        self,
        image: Union[str, Path, bytes, Image.Image],
        crop_name: Optional[str] = None,
        location_state: Optional[str] = None,
        growth_stage: Optional[str] = None,
        image_type: Optional[str] = None,
    ) -> PredictionResult:
        """
        Execute pest detection on cotton trap image.
        Raises RuntimeError if no pretrained checkpoint is available.
        """
        if not self.is_available():
            raise RuntimeError(
                "Pretrained checkpoint for WadhwaniAI/pest-monitoring is unavailable. "
                "The upstream repository (https://github.com/WadhwaniAI/pest-monitoring) "
                "provides training code and deployment scripts, but does NOT distribute "
                "pretrained weights (.pt / .jit / .ckpt). Per audit specifications, "
                "no synthetic weights were invented. Provide a trained checkpoint_path to proceed."
            )

        # Standard execution if checkpoint is available:
        pil_img = load_image_to_pil(image)
        w, h = pil_img.size

        # Preprocess to 300x300 as specified in deployment/README.md
        resized = pil_img.resize((300, 300), Image.Resampling.BILINEAR)
        # Convert to tensor
        import numpy as np
        arr = np.array(resized, dtype=np.float32) / 255.0
        arr = np.transpose(arr, (2, 0, 1))
        tensor = torch.from_numpy(np.expand_dims(arr, 0)).to(self.device)

        with torch.no_grad():
            # Output tuple: (validation_out, abw_boxes, pbw_boxes, abw_scores, pbw_scores)
            out = self.model(tensor)
            val_out, abw_boxes, pbw_boxes, abw_scores, pbw_scores = out

        boxes_out: List[BoundingBox] = []
        top_predictions: List[TopPrediction] = []

        # Parse ABW (American Bollworm)
        for i, box in enumerate(abw_boxes.cpu().numpy()):
            score = float(abw_scores[i])
            if score >= 0.2:
                boxes_out.append(
                    BoundingBox(
                        box=[float(x) for x in box],
                        label="American Bollworm (ABW)",
                        score=score,
                        crop="Cotton",
                        is_normalized=True,
                    )
                )

        # Parse PBW (Pink Bollworm)
        for i, box in enumerate(pbw_boxes.cpu().numpy()):
            score = float(pbw_scores[i])
            if score >= 0.2:
                boxes_out.append(
                    BoundingBox(
                        box=[float(x) for x in box],
                        label="Pink Bollworm (PBW)",
                        score=score,
                        crop="Cotton",
                        is_normalized=True,
                    )
                )

        condition = "Cotton Bollworm Infestation" if boxes_out else "No Bollworms Detected"
        c_type = ConditionType.PEST if boxes_out else ConditionType.HEALTHY
        pred_crop = "Cotton"

        crop_mismatch, warnings = check_crop_consistency(crop_name, pred_crop)

        return PredictionResult(
            condition=condition,
            condition_type=c_type,
            score=max([b.score for b in boxes_out], default=1.0),
            top_predictions=top_predictions,
            bounding_boxes=boxes_out,
            crop=pred_crop,
            user_crop=crop_name,
            crop_mismatch=crop_mismatch,
            model_name=self.model_name,
            model_version=self.model_version,
            warnings=warnings,
            provenance={"backend": "torchscript_jit"},
        )
