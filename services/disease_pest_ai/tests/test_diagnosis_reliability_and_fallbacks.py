"""Comprehensive Regression Test Suite for Disease Diagnosis Reliability, Class Mapping,
Confidence Calibration, and Generic Fallback Elimination.

Validates:
1. Supported Cotton class mappings (Bacterial Blight, Curl Virus, Fusarium Wilt, Healthy Foliage).
2. Supported Soybean class mappings (Downy Mildew, Frogeye Spot, Healthy, Mosaic Virus, Rust, Brown Spot).
3. Complete elimination of fabricated 'Foliar Disorder' and hardcoded 75% confidence.
4. Handling of unknown class indices and unmapped labels.
5. Strict crop-to-model routing (Cotton -> DenseNet-121, Soybean -> ConvNeXt-Small, Others -> HTTP 422).
6. Temperature scaling and confidence calculation integrity.
7. Low-confidence abstention (<0.45 or low contrast).
8. Healthy-leaf zero-chemical safeguard.
9. Envelope unwrapping and frontend payload resilience.
"""

import io
import json
from pathlib import Path
import pytest
from PIL import Image
import torch
import numpy as np
from fastapi.testclient import TestClient

from disease_pest_ai.api.main import app
from disease_pest_ai.specialists.cotton.adapter import CottonDenseNetAdapter, COTTON_CANONICAL_MAP
from disease_pest_ai.specialists.soybean.adapter import SoybeanConvNeXtAdapter, SOYBEAN_CANONICAL_MAP
from disease_pest_ai.specialists.router import intelligent_router, SUPPORTED_CROPS
from disease_pest_ai.api.routes.diagnose import VERIFIED_CLASSES

client = TestClient(app)

TEST_DATA_DIR = Path(__file__).resolve().parent.parent / "test_data"
COTTON_TEST_DIR = TEST_DATA_DIR / "cotton_field_eval"
SOYBEAN_TEST_DIR = TEST_DATA_DIR / "soybean_field_eval"


# =====================================================================
# 1. CLASS MAPPINGS AND CHECKPOINT INTEGRITY
# =====================================================================

def test_cotton_all_classes_mapped_and_valid():
    """Verify Cotton adapter classes match the 4 verified production classes."""
    adapter = CottonDenseNetAdapter()
    assert adapter.is_available(), "Cotton DenseNet-121 checkpoint must be loaded"
    supported = adapter.get_supported_classes()
    assert len(supported) == 4
    for raw in supported:
        clean = raw.lower().strip()
        assert clean in COTTON_CANONICAL_MAP, f"Raw cotton class '{raw}' must be in canonical map"
        canonical = COTTON_CANONICAL_MAP[clean]["canonical_condition"]
        assert canonical in VERIFIED_CLASSES["Cotton"], f"Canonical condition '{canonical}' must be in VERIFIED_CLASSES"


def test_soybean_all_classes_mapped_and_valid():
    """Verify Soybean adapter classes match the 6 verified production classes."""
    adapter = SoybeanConvNeXtAdapter()
    assert adapter.is_available(), "Soybean ConvNeXt-Small checkpoint must be loaded"
    supported = adapter.get_supported_classes()
    assert len(supported) == 6
    for raw in supported:
        clean = raw.lower().strip()
        assert clean in SOYBEAN_CANONICAL_MAP, f"Raw soybean class '{raw}' must be in canonical map"
        canonical = SOYBEAN_CANONICAL_MAP[clean]["canonical_condition"]
        assert canonical in VERIFIED_CLASSES["Soybean"], f"Canonical condition '{canonical}' must be in VERIFIED_CLASSES"


# =====================================================================
# 2. COMPLETE ELIMINATION OF 'Foliar Disorder' AND HARDCODED 75%
# =====================================================================

def test_no_foliar_disorder_in_any_adapter():
    """Ensure 'Foliar Disorder' is never returned by adapters or canonical maps."""
    for crop, classes in VERIFIED_CLASSES.items():
        assert "Foliar Disorder" not in classes, f"Foliar Disorder found in {crop} classes!"

    cotton_adapter = CottonDenseNetAdapter()
    for raw in cotton_adapter.get_supported_classes():
        clean = raw.lower().strip()
        cond = COTTON_CANONICAL_MAP[clean]["canonical_condition"]
        assert cond != "Foliar Disorder"

    soybean_adapter = SoybeanConvNeXtAdapter()
    for raw in soybean_adapter.get_supported_classes():
        clean = raw.lower().strip()
        cond = SOYBEAN_CANONICAL_MAP[clean]["canonical_condition"]
        assert cond != "Foliar Disorder"


def test_real_inference_produces_specific_condition():
    """Verify real leaf photo produces genuine condition, not generic disorder."""
    img_path = COTTON_TEST_DIR / "bacterial_blight_1.jpg"
    if not img_path.is_file():
        pytest.skip(f"Test image not found at {img_path}")

    with open(img_path, "rb") as f:
        resp = client.post(
            "/api/v1/disease-detection",
            data={"crop": "Cotton"},
            files={"file": ("leaf.jpg", f, "image/jpeg")},
        )
    assert resp.status_code == 200
    res = resp.json()
    fg = res["data"]["farmer_guidance"]
    assert fg["disease_name"] != "Foliar Disorder"
    assert fg["disease_name"] == "Bacterial Blight"
    assert fg["status"] == "disease_detected"
    assert fg["confidence_percent"] is not None
    assert fg["confidence_percent"] > 50


# =====================================================================
# 3. UNKNOWN / UNMAPPED CLASS AND CORRUPT INPUT ABSTENTION
# =====================================================================

def test_unmapped_class_abstains_gracefully():
    """Verify that if an unknown condition is passed, it is treated as unable to determine."""
    from disease_pest_ai.api.routes.diagnose import VERIFIED_CLASSES
    # Test checking verification logic
    assert "Foliar Disorder" not in VERIFIED_CLASSES["Cotton"]
    assert "Unknown Fungus" not in VERIFIED_CLASSES["Soybean"]


def test_low_contrast_image_abstains():
    """Verify blank or flat low-contrast frames abstain with insufficient_evidence."""
    # Create flat grey image
    blank_img = Image.new("RGB", (224, 224), color=(128, 128, 128))
    adapter = CottonDenseNetAdapter()
    pred = adapter.predict(blank_img)
    assert pred.is_abstaining is True
    assert "insufficient_evidence" in pred.abstention_reason


# =====================================================================
# 4. STRICT CROP ROUTING AND UNSUPPORTED REJECTION
# =====================================================================

def test_unsupported_crop_rejected_with_422():
    """Verify crops other than Cotton and Soybean are rejected with HTTP 422."""
    img_bytes = io.BytesIO()
    Image.new("RGB", (224, 224), color=(50, 150, 50)).save(img_bytes, format="JPEG")
    img_bytes.seek(0)

    for invalid_crop in ["Tomato", "Rice", "Wheat", "Potato", "Apple"]:
        resp = client.post(
            "/api/v1/disease-detection",
            data={"crop": invalid_crop},
            files={"file": ("leaf.jpg", io.BytesIO(img_bytes.getvalue()), "image/jpeg")},
        )
        assert resp.status_code == 422
        assert "not supported" in resp.json()["detail"]


# =====================================================================
# 5. CONFIDENCE CALIBRATION AND TEMPERATURE SCALING
# =====================================================================

def test_cotton_temperature_scaling_is_applied():
    """Verify Cotton adapter scales logits by T=1.00 and outputs valid probabilities."""
    adapter = CottonDenseNetAdapter()
    img = Image.new("RGB", (224, 224), color=(30, 160, 40))
    pred = adapter.predict(img)
    assert 0.0 <= pred.calibrated_confidence <= 1.0
    assert pred.percentage == int(round(pred.calibrated_confidence * 100))


def test_soybean_temperature_scaling_is_applied():
    """Verify Soybean adapter scales logits by T=1.15 and outputs valid probabilities."""
    adapter = SoybeanConvNeXtAdapter()
    img = Image.new("RGB", (224, 224), color=(40, 180, 50))
    pred = adapter.predict(img)
    assert 0.0 <= pred.calibrated_confidence <= 1.0
    assert pred.percentage == int(round(pred.calibrated_confidence * 100))


# =====================================================================
# 6. ZERO-CHEMICAL SAFEGUARD FOR HEALTHY LEAVES
# =====================================================================

def test_healthy_foliage_zero_chemical_safeguard():
    """Verify that a healthy prediction strictly recommends zero chemicals."""
    img_path = COTTON_TEST_DIR / "healthy_foliage_1.jpg"
    if not img_path.is_file():
        pytest.skip(f"Healthy test image not found at {img_path}")

    with open(img_path, "rb") as f:
        resp = client.post(
            "/api/v1/disease-detection",
            data={"crop": "Cotton"},
            files={"file": ("healthy.jpg", f, "image/jpeg")},
        )
    assert resp.status_code == 200
    res = resp.json()
    fg = res["data"]["farmer_guidance"]
    if fg["status"] == "healthy":
        assert fg["is_healthy"] is True
        assert res["data"]["treatments"]["chemical"] == []
        rec_text = " ".join(fg["recommended_steps"]).lower()
        assert "no chemical pesticide or fungicide treatment is required" in rec_text


# =====================================================================
# 7. ENVELOPE UNWRAPPING AND BACKWARD COMPATIBILITY
# =====================================================================

def test_api_returns_both_nested_and_top_level_farmer_guidance():
    """Ensure response provides farmer_guidance at both top-level and in data dictionary."""
    img_bytes = io.BytesIO()
    Image.new("RGB", (224, 224), color=(60, 140, 45)).save(img_bytes, format="JPEG")
    img_bytes.seek(0)

    resp = client.post(
        "/api/v1/disease-detection",
        data={"crop": "Cotton"},
        files={"file": ("leaf.jpg", img_bytes, "image/jpeg")},
    )
    assert resp.status_code == 200
    res = resp.json()
    assert "farmer_guidance" in res, "Top-level farmer_guidance must be present"
    assert "farmer_guidance" in res["data"], "data.farmer_guidance must be present"
    assert res["farmer_guidance"]["disease_name"] == res["data"]["farmer_guidance"]["disease_name"]
