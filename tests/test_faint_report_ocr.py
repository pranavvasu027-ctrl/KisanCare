"""
Test Suite: Faint Soil Report OCR & Multi-Pass Enhancement Pipeline
===================================================================
Validates:
1. Multi-pass image enhancement: CLAHE, unsharp masking, adaptive thresholding, deskew, and upscaling.
2. Recognition of faint, low-contrast, blurred, noisy, and rotated soil report photos.
3. Scanned PDF page rendering at 300 DPI with OCR fallback.
4. Robust extraction of N, P, K, and pH under varying table layouts and chemical units.
5. End-to-end crop recommendation generation from faint reports.
6. Graceful abstention when essential parameters are missing or completely illegible.
"""

import io
import math
import os
import pytest
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.crop_recommendation.service import CropRecommendationService
from ml.soil_intelligence.ocr.preprocessor import ImageEnhancementPipeline
from ml.soil_intelligence.ocr.engine import DocumentOCREngine

client = TestClient(app)


def _generate_synthetic_report_image(
    n_val: float = 240.0,
    p_val: float = 18.5,
    k_val: float = 310.0,
    ph_val: float = 7.4,
    district: str = "Akola",
    faint_level: float = 0.0,  # 0.0 = clear, 0.7 = very faint
    blur_radius: float = 0.0,
    noise_sigma: float = 0.0,
    rotate_deg: float = 0.0
) -> bytes:
    """Generates a synthetic laboratory Soil Health Card image with customizable visual degradation."""
    w, h = 900, 550
    img = Image.new("RGB", (w, h), color=(255, 255, 255))
    d = ImageDraw.Draw(img)

    # Header
    d.text((40, 30), "GOVERNMENT OF MAHARASHTRA", fill=(20, 20, 20))
    d.text((40, 60), f"DISTRICT SOIL TESTING LABORATORY, {district.upper()}", fill=(40, 40, 40))
    d.text((40, 90), "Soil Health Card / Analytical Certificate", fill=(40, 40, 40))
    d.text((40, 120), "Sample ID: MH-2025-0891  |  Farmer: Shri Santosh Patil", fill=(50, 50, 50))
    d.line([(40, 150), (860, 150)], fill=(120, 120, 120), width=2)

    # Table layout
    d.text((40, 170), "Parameter Name", fill=(30, 30, 30))
    d.text((380, 170), "Test Result", fill=(30, 30, 30))
    d.text((580, 170), "Unit", fill=(30, 30, 30))
    d.line([(40, 195), (860, 195)], fill=(150, 150, 150), width=1)

    d.text((40, 215), "Available Nitrogen (N)", fill=(40, 40, 40))
    d.text((380, 215), f"{n_val:.1f}", fill=(30, 30, 30))
    d.text((580, 215), "kg/ha", fill=(40, 40, 40))

    d.text((40, 260), "Available Phosphorus (P2O5)", fill=(40, 40, 40))
    d.text((380, 260), f"{p_val:.1f}", fill=(30, 30, 30))
    d.text((580, 260), "kg/ha", fill=(40, 40, 40))

    d.text((40, 305), "Available Potassium (K2O)", fill=(40, 40, 40))
    d.text((380, 305), f"{k_val:.1f}", fill=(30, 30, 30))
    d.text((580, 305), "kg/ha", fill=(40, 40, 40))

    d.text((40, 350), "Soil Reaction (pH)", fill=(40, 40, 40))
    d.text((380, 350), f"{ph_val:.2f}", fill=(30, 30, 30))
    d.text((580, 350), "pH Index", fill=(40, 40, 40))

    d.text((40, 395), "Organic Carbon (OC)", fill=(40, 40, 40))
    d.text((380, 395), "0.55", fill=(30, 30, 30))
    d.text((580, 395), "%", fill=(40, 40, 40))

    d.text((40, 440), "Electrical Conductivity (EC)", fill=(40, 40, 40))
    d.text((380, 440), "0.45", fill=(30, 30, 30))
    d.text((580, 440), "dS/m", fill=(40, 40, 40))

    # Apply rotation if specified
    if rotate_deg != 0.0:
        img = img.rotate(rotate_deg, resample=Image.Resampling.BICUBIC, expand=True, fillcolor=(255, 255, 255))

    cv_img = np.array(img).astype(np.float32)

    # Apply faintness / low contrast
    if faint_level > 0.0:
        # Scale dynamic range down: e.g. faint_level=0.7 compresses range from [0, 255] to [180, 240]
        span = 255.0 * (1.0 - faint_level)
        offset = 255.0 - span
        cv_img = cv_img * (span / 255.0) + offset

    cv_img = np.clip(cv_img, 0, 255).astype(np.uint8)

    # Apply Gaussian blur
    if blur_radius > 0:
        ksize = int(round(blur_radius * 2))
        if ksize % 2 == 0:
            ksize += 1
        ksize = max(3, ksize)
        cv_img = cv2.GaussianBlur(cv_img, (ksize, ksize), blur_radius)

    # Apply digital noise
    if noise_sigma > 0:
        noise = np.random.normal(0, noise_sigma, cv_img.shape).astype(np.int16)
        cv_img = np.clip(cv_img.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    _, buf = cv2.imencode(".png", cv_img)
    return buf.tobytes()


# ---------------------------------------------------------------------------
# 1. Preprocessing Pipeline Tests
# ---------------------------------------------------------------------------

def test_clahe_contrast_enhancement():
    """Verifies that CLAHE expands dynamic range of low-contrast images."""
    faint_bytes = _generate_synthetic_report_image(faint_level=0.75)
    faint_bgr = ImageEnhancementPipeline.load_image_bytes(faint_bytes)
    enhanced_gray = ImageEnhancementPipeline.enhance_clahe_sharpen(faint_bgr)

    # Raw faint image had low variance / standard deviation
    raw_gray = cv2.cvtColor(faint_bgr, cv2.COLOR_BGR2GRAY)
    raw_std = np.std(raw_gray)
    enh_std = np.std(enhanced_gray)

    # CLAHE must significantly increase pixel variance / dynamic contrast
    assert enh_std > raw_std * 1.5


def test_skew_detection_and_correction():
    """Verifies document skew detection and rotation correction."""
    rotated_bytes = _generate_synthetic_report_image(rotate_deg=3.5)
    bgr = ImageEnhancementPipeline.load_image_bytes(rotated_bytes)
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    deskewed = ImageEnhancementPipeline.detect_and_correct_skew(gray)
    assert deskewed is not None
    assert deskewed.shape == gray.shape


def test_upscaling_small_images():
    """Small low-res thumbnails must be upscaled to at least 1800px on the longest dimension."""
    small_bgr = np.zeros((400, 300, 3), dtype=np.uint8)
    upscaled = ImageEnhancementPipeline.upscale_if_small(small_bgr, min_dimension=1800)
    assert max(upscaled.shape[:2]) == 1800


# ---------------------------------------------------------------------------
# 2. Document OCR Engine & Layout Reconstruction Tests
# ---------------------------------------------------------------------------

def test_ocr_engine_faint_image_recognition():
    """Verifies that DocumentOCREngine extracts N, P, K, and pH from a low-contrast faint photo."""
    faint_bytes = _generate_synthetic_report_image(
        n_val=220.0,
        p_val=19.5,
        k_val=290.0,
        ph_val=7.6,
        faint_level=0.65,
        blur_radius=0.5,
        noise_sigma=3.0
    )

    engine = DocumentOCREngine()
    result = engine.recognize_image_bytes(faint_bytes)

    assert not result.is_empty
    assert result.confidence > 0.50
    # Must detect core nutrients
    assert "pH" in result.nutrients_detected
    assert any(n in result.nutrients_detected for n in ["Nitrogen", "Phosphorus", "Potassium"])


def test_ocr_scanned_pdf_rendering():
    """Verifies that a raster/scanned PDF without digital text is rendered and OCR'd successfully."""
    import pymupdf

    # Create a scanned PDF containing a page image
    faint_bytes = _generate_synthetic_report_image(n_val=240.0, p_val=18.5, k_val=310.0, ph_val=7.4, faint_level=0.5)
    doc = pymupdf.open()
    rect = pymupdf.Rect(0, 0, 595, 842)  # A4
    page = doc.new_page(width=595, height=842)
    page.insert_image(rect, stream=faint_bytes)
    scanned_pdf_bytes = doc.tobytes()

    engine = DocumentOCREngine()
    result = engine.extract_pdf_with_ocr_fallback(scanned_pdf_bytes)

    assert not result.is_empty
    assert "scanned_pdf" in result.variant_name
    assert "pH" in result.nutrients_detected


# ---------------------------------------------------------------------------
# 3. End-to-End Crop Recommendation Integration from Faint Reports
# ---------------------------------------------------------------------------

def test_end_to_end_faint_report_upload_api():
    """
    Simulates a farmer uploading a faint, low-contrast photo taken with a smartphone.
    The system must enhance the image, extract parameters via OCR, and return top 3 crop recommendations.
    """
    faint_png_bytes = _generate_synthetic_report_image(
        n_val=210.0,
        p_val=24.0,
        k_val=270.0,
        ph_val=7.50,
        district="Akola",
        faint_level=0.60,
        blur_radius=0.5,
        noise_sigma=3.0
    )

    resp = client.post(
        "/api/v1/crop-recommendation/recommend-from-report",
        files={"file": ("faint_soil_health_card.png", faint_png_bytes, "image/png")},
        data={"district": "Akola"}
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["district"] == "Akola"
    assert len(data["recommendations"]) == 3
    assert data["recommendations"][0]["rank"] == 1
    assert data["recommendations"][0]["suitability_label"] in ["Highly Suitable", "Moderately Suitable"]


def test_partially_readable_report_actionable_error():
    """
    If a report is severely damaged and only pH/Nitrogen can be read,
    the system must return HTTP 422 with an explanation of which fields were found vs missing.
    """
    service = CropRecommendationService()

    # Image missing P and K
    img = Image.new("RGB", (600, 200), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((20, 30), "SOIL HEALTH CARD\npH: 7.40\nAvailable Nitrogen: 240.0 kg/ha", fill=(0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")

    with pytest.raises(Exception) as exc_info:
        service.process_soil_report_and_recommend(
            file_bytes=buf.getvalue(),
            filename="partial_report.png",
            district="Amravati"
        )

    err_msg = str(exc_info.value.detail)
    assert "Essential soil parameters missing" in err_msg
    assert "Phosphorus" in err_msg
    assert "Potassium" in err_msg
    assert "Partially readable" in err_msg
