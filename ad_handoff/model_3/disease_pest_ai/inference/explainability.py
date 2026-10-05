"""
Explainability Module for Disease & Pest AI (Phase 4, Section 14).

Provides:
1. Grad-CAM (Gradient-weighted Class Activation Mapping) for EfficientNetV2-S disease classification.
2. Spatial bounding-box localization for YOLO11s pest detection.
3. Unified visual explanation combining disease attention heatmaps and pest bounding boxes.
"""

import base64
import io
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import cv2
import numpy as np
from PIL import Image
import torch
import torch.nn as nn
import torch.nn.functional as F

from disease_pest_ai.models.base import load_image_to_pil
from disease_pest_ai.schemas.final_output import ExplainabilityOutputs

logger = logging.getLogger(__name__)


class GradCAM:
    """
    Grad-CAM implementation for PyTorch convolutional vision backbones.
    Extracts gradient-weighted feature activation maps for model explainability.
    """

    def __init__(self, model: nn.Module, target_layer: Optional[nn.Module] = None):
        self.model = model
        # Default to features[-1] for torchvision EfficientNetV2 models
        if target_layer is None:
            if hasattr(model, "features"):
                target_layer = model.features[-1]
            else:
                raise ValueError("Target layer must be specified for custom model architectures.")
        self.target_layer = target_layer

        self.activations: Optional[torch.Tensor] = None
        self.gradients: Optional[torch.Tensor] = None
        self._handles: List[Any] = []

    def _register_hooks(self) -> None:
        """Register forward and backward hooks."""
        self._remove_hooks()

        def forward_hook(module, input, output):
            self.activations = output.detach()

        def backward_hook(module, grad_input, grad_output):
            self.gradients = grad_output[0].detach()

        h1 = self.target_layer.register_forward_hook(forward_hook)
        h2 = self.target_layer.register_full_backward_hook(backward_hook)
        self._handles = [h1, h2]

    def _remove_hooks(self) -> None:
        """Clean up hooks to prevent memory leaks."""
        for h in self._handles:
            h.remove()
        self._handles = []

    def generate(
        self,
        input_tensor: torch.Tensor,
        class_idx: Optional[int] = None,
    ) -> np.ndarray:
        """
        Generate a normalized 2D Grad-CAM heatmap for the given input and class index.

        Args:
            input_tensor: Tensor of shape (1, C, H, W).
            class_idx: Target class index. If None, top-1 predicted class is used.

        Returns:
            2D numpy array of shape (H_feat, W_feat) with values in [0.0, 1.0].
        """
        self.model.eval()
        self._register_hooks()

        try:
            # Enable gradients for backward pass
            input_tensor = input_tensor.clone().requires_grad_(True)
            output = self.model(input_tensor)

            if class_idx is None:
                class_idx = int(torch.argmax(output, dim=1).item())

            self.model.zero_grad()
            score = output[0, class_idx]
            score.backward(retain_graph=False)

            if self.gradients is None or self.activations is None:
                raise RuntimeError("Failed to capture gradients or activations during Grad-CAM backward pass.")

            # Global average pooling of gradients: weights alpha_k = (1/Z) * sum(grad_k)
            pooled_gradients = torch.mean(self.gradients, dim=[0, 2, 3])  # (C,)

            # Weighted combination of activation maps
            for i in range(self.activations.shape[1]):
                self.activations[:, i, :, :] *= pooled_gradients[i]

            heatmap = torch.mean(self.activations, dim=1).squeeze()  # (H, W)
            heatmap = F.relu(heatmap)

            heatmap_np = heatmap.cpu().numpy()
            max_val = np.max(heatmap_np)
            if max_val > 1e-8:
                heatmap_np = heatmap_np / max_val
            else:
                heatmap_np = np.zeros_like(heatmap_np)

            return heatmap_np.astype(np.float32)

        finally:
            self._remove_hooks()


def overlay_heatmap_on_image(
    image: Image.Image,
    heatmap: np.ndarray,
    alpha: float = 0.45,
    colormap: int = cv2.COLORMAP_JET,
) -> Image.Image:
    """
    Overlay a 2D Grad-CAM heatmap onto a PIL image.
    """
    orig_rgb = np.array(image.convert("RGB"))
    h, w = orig_rgb.shape[:2]

    # Resize heatmap to match image dimensions
    resized_heatmap = cv2.resize(heatmap, (w, h), interpolation=cv2.INTER_LINEAR)
    heatmap_uint8 = np.uint8(255 * np.clip(resized_heatmap, 0.0, 1.0))

    # Apply colormap
    heatmap_color = cv2.applyColorMap(heatmap_uint8, colormap)
    heatmap_color_rgb = cv2.cvtColor(heatmap_color, cv2.COLOR_BGR2RGB)

    # Blend
    blended = cv2.addWeighted(orig_rgb, 1.0 - alpha, heatmap_color_rgb, alpha, 0)
    return Image.fromarray(blended)


def generate_explainability(
    disease_adapter: Optional[Any],
    image: Any,
    top_class_idx: Optional[int] = None,
    pest_detections: Optional[List[Any]] = None,
    output_dir: Optional[Union[str, Path]] = None,
    file_prefix: str = "diagnostic",
) -> ExplainabilityOutputs:
    """
    Unified explainability generator creating Grad-CAM overlays and bounding box manifests.

    Args:
        disease_adapter: EfficientNetDiseaseAdapter instance (or None if bypassed).
        image: Original input PIL Image, file path, or bytes.
        top_class_idx: Target disease class index for Grad-CAM.
        pest_detections: Detected pests with bounding boxes from YOLO detector.
        output_dir: Optional directory to persist generated overlay visualizations.
        file_prefix: Filename prefix for saved images.

    Returns:
        ExplainabilityOutputs schema instance.
    """
    heatmap_path_str: Optional[str] = None
    pest_box_dicts: List[Dict[str, Any]] = []

    try:
        pil_img = load_image_to_pil(image)
    except Exception as e:
        logger.warning(f"Could not load image for explainability: {e}")
        pil_img = None

    # 1. Format pest bounding boxes
    if pest_detections:
        for p in pest_detections:
            if hasattr(p, "bounding_box"):
                box = p.bounding_box
                label = getattr(p, "pest", "Pest")
                score = getattr(p, "score", 0.0)
            elif isinstance(p, dict):
                box = p.get("bounding_box", [])
                label = p.get("pest", "Pest")
                score = p.get("score", 0.0)
            else:
                continue

            pest_box_dicts.append({
                "label": label,
                "score": round(float(score), 4),
                "box": [round(float(c), 2) for c in box],
            })

    # 2. Generate Grad-CAM if disease adapter is available
    if pil_img and disease_adapter and hasattr(disease_adapter, "model") and disease_adapter.model is not None:
        try:
            # Prepare input tensor
            if hasattr(disease_adapter, "preprocess"):
                input_tensor = disease_adapter.preprocess(pil_img)
            elif hasattr(disease_adapter, "_preprocess"):
                input_tensor = disease_adapter._preprocess(pil_img).unsqueeze(0).to(disease_adapter.device)
            else:
                input_tensor = None

            if input_tensor is None or not hasattr(disease_adapter.model, "features"):
                raise ValueError("Model does not support convolutional Grad-CAM extraction.")

            grad_cam = GradCAM(disease_adapter.model)
            heatmap = grad_cam.generate(input_tensor, class_idx=top_class_idx)

            # Generate overlay
            overlay_img = overlay_heatmap_on_image(pil_img, heatmap, alpha=0.45)

            # Draw pest bounding boxes onto overlay if present
            if pest_detections:
                from disease_pest_ai.inference.visualization import draw_pest_detections
                overlay_img = draw_pest_detections(overlay_img, pest_detections)

            # Save if output_dir specified
            if output_dir:
                out_path = Path(output_dir)
                out_path.mkdir(parents=True, exist_ok=True)
                save_file = out_path / f"{file_prefix}_gradcam_overlay.png"
                overlay_img.save(save_file, format="PNG")
                heatmap_path_str = str(save_file)
            else:
                # Store as base64 data URI for portable visualization
                buf = io.BytesIO()
                overlay_img.save(buf, format="JPEG", quality=85)
                b64_str = base64.b64encode(buf.getvalue()).decode("utf-8")
                heatmap_path_str = f"data:image/jpeg;base64,{b64_str}"

        except Exception as e:
            logger.warning(f"Grad-CAM generation failed: {e}")

    # Determine explanation type
    if heatmap_path_str and pest_box_dicts:
        exp_type = "gradcam_and_bounding_boxes"
    elif heatmap_path_str:
        exp_type = "gradcam"
    elif pest_box_dicts:
        exp_type = "bounding_box"
    else:
        exp_type = "none"

    return ExplainabilityOutputs(
        disease_heatmap=heatmap_path_str,
        pest_boxes=pest_box_dicts,
        explanation_type=exp_type,
    )
