"""Model loader for Irrigation Intelligence System.

Loads and caches the FAO-56 crop coefficients, base configuration,
and pretrained PyTorch ETo LSTM with attention.
"""

from __future__ import annotations

import json
import os
import pickle
from pathlib import Path
from typing import Any, Dict, Optional
import torch

from models.irrigation.eto.lstm_attention import EToLSTMAttention

CURRENT_DIR = Path(__file__).resolve().parent

_IRRIGATION_ARTIFACTS: Optional[Dict[str, Any]] = None


def load_irrigation_model(force_reload: bool = False) -> Dict[str, Any]:
    """Load irrigation artifacts once and cache in memory.

    Returns:
        Dict containing:
            - 'crop_coefficients': dict of crops, stages, kcb, root_depth
            - 'base_config': system configuration
            - 'eto_model': PyTorch EToLSTMAttention model in eval mode
            - 'eto_scaler': MinMaxScaler for weather features and ETo
            - 'eto_model_config': architecture parameters dict
    """
    global _IRRIGATION_ARTIFACTS
    if _IRRIGATION_ARTIFACTS is not None and not force_reload:
        return _IRRIGATION_ARTIFACTS

    # 1. Load Crop Coefficients
    crop_coeff_path = CURRENT_DIR / "configs" / "crop_coefficients.json"
    with open(crop_coeff_path, "r", encoding="utf-8") as f:
        crop_coefficients = json.load(f)

    # 2. Load Base Configuration
    base_config_path = CURRENT_DIR / "configs" / "base_config.json"
    with open(base_config_path, "r", encoding="utf-8") as f:
        base_config = json.load(f)

    # 3. Load ETo LSTM Attention model & weights
    eto_dir = CURRENT_DIR / "eto"
    config_path = eto_dir / "eto_model_config.pkl"
    with open(config_path, "rb") as f:
        eto_model_config = pickle.load(f)

    device = torch.device("cpu")
    eto_model = EToLSTMAttention(
        input_size=12,
        hidden_size=eto_model_config["hidden_size"],
        num_layers=eto_model_config["num_layers"],
        dropout=eto_model_config["dropout"],
    )

    weights_path = eto_dir / "eto_punjab_best.pth"
    eto_model.load_state_dict(torch.load(weights_path, map_location=device, weights_only=False))
    eto_model.eval()

    # 4. Load Scaler
    scaler_path = eto_dir / "eto_punjab_scaler.pkl"
    with open(scaler_path, "rb") as f:
        eto_scaler = pickle.load(f)

    _IRRIGATION_ARTIFACTS = {
        "crop_coefficients": crop_coefficients,
        "base_config": base_config,
        "eto_model": eto_model,
        "eto_scaler": eto_scaler,
        "eto_model_config": eto_model_config,
        "device": device,
    }
    return _IRRIGATION_ARTIFACTS
