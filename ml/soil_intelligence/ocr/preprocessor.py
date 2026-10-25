"""
Image Preprocessing Pipeline for Soil Health Reports & Faint Scans
==================================================================
Handles low-contrast photos, faint dot-matrix print, camera rotation,
slight skew, non-uniform shadows, and digital noise before OCR extraction.
"""

from __future__ import annotations
import io
import math
import logging
from typing import List, Tuple, Optional
import numpy as np
import cv2
from PIL import Image, ImageOps

logger = logging.getLogger("kisancare.ocr.preprocessor")


class ImageEnhancementPipeline:
    """Preprocesses and enhances faint or noisy document images for OCR."""

    @staticmethod
    def correct_exif_orientation(pil_img: Image.Image) -> Image.Image:
        """Corrects camera rotation metadata from smartphone uploads."""
        try:
            return ImageOps.exif_transpose(pil_img)
        except Exception:
            return pil_img

    @classmethod
    def load_image_bytes(cls, image_bytes: bytes) -> np.ndarray:
        """Loads raw image bytes into a normalized BGR numpy array with correct EXIF orientation."""
        pil_img = Image.open(io.BytesIO(image_bytes))
        pil_img = cls.correct_exif_orientation(pil_img)
        if pil_img.mode != "RGB":
            pil_img = pil_img.convert("RGB")
        rgb_arr = np.array(pil_img)
        return cv2.cvtColor(rgb_arr, cv2.COLOR_RGB2BGR)

    @staticmethod
    def upscale_if_small(bgr_img: np.ndarray, min_dimension: int = 1800) -> np.ndarray:
        """Upscales small or low-resolution images using high-quality Lanczos interpolation."""
        h, w = bgr_img.shape[:2]
        max_dim = max(h, w)
        if max_dim < min_dimension:
            scale = min_dimension / float(max_dim)
            new_w = int(round(w * scale))
            new_h = int(round(h * scale))
            return cv2.resize(bgr_img, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
        return bgr_img

    @staticmethod
    def detect_and_correct_skew(gray_img: np.ndarray, max_angle: float = 30.0) -> np.ndarray:
        """Detects document skew angle and rotates image to upright position."""
        try:
            # Detect edges and use minAreaRect on non-zero pixels
            edges = cv2.Canny(gray_img, 50, 150, apertureSize=3)
            lines = cv2.HoughLinesP(edges, 1, np.pi / 180.0, threshold=100, minLineLength=100, maxLineGap=10)
            if lines is None or len(lines) == 0:
                return gray_img

            angles = []
            for line in lines:
                x1, y1, x2, y2 = line[0]
                dx = x2 - x1
                dy = y2 - y1
                if dx != 0:
                    ang = math.degrees(math.atan2(dy, dx))
                    # Only consider near-horizontal lines
                    if abs(ang) < max_angle:
                        angles.append(ang)

            if not angles:
                return gray_img

            median_angle = float(np.median(angles))
            if abs(median_angle) < 0.5:
                return gray_img

            # Rotate image by -median_angle
            h, w = gray_img.shape[:2]
            center = (w // 2, h // 2)
            rot_mat = cv2.getRotationMatrix2D(center, median_angle, 1.0)
            return cv2.warpAffine(
                gray_img, rot_mat, (w, h),
                flags=cv2.INTER_LINEAR,
                borderMode=cv2.BORDER_REPLICATE
            )
        except Exception as exc:
            logger.debug("Deskew failed, returning original: %s", exc)
            return gray_img

    @classmethod
    def enhance_clahe_sharpen(cls, bgr_img: np.ndarray) -> np.ndarray:
        """
        Variant 1: CLAHE contrast enhancement + mild unsharp mask.
        Best for faint, low-contrast photos with non-uniform lighting or shadow gradients.
        """
        gray = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2GRAY)
        gray = cls.detect_and_correct_skew(gray)

        # Contrast Limited Adaptive Histogram Equalization
        clahe = cv2.createCLAHE(clipLimit=2.8, tileGridSize=(8, 8))
        contrast_boost = clahe.apply(gray)

        # Mild unsharp masking to enhance character edges without over-amplifying noise
        gaussian = cv2.GaussianBlur(contrast_boost, (0, 0), sigmaX=2.0)
        sharpened = cv2.addWeighted(contrast_boost, 1.5, gaussian, -0.5, 0)
        return sharpened

    @classmethod
    def enhance_adaptive_threshold(cls, bgr_img: np.ndarray) -> np.ndarray:
        """
        Variant 2: Local adaptive Gaussian thresholding.
        Best for faint dot-matrix printer ink, washed-out paper, or low-contrast Xerox copies.
        """
        gray = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2GRAY)
        gray = cls.detect_and_correct_skew(gray)

        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        contrast_boost = clahe.apply(gray)

        # Adaptive Gaussian thresholding with block size 25
        thresh = cv2.adaptiveThreshold(
            contrast_boost, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            25, 11
        )
        return thresh

    @classmethod
    def enhance_denoised_otsu(cls, bgr_img: np.ndarray) -> np.ndarray:
        """
        Variant 3: Bilateral edge-preserving denoising + Otsu binarization.
        Best for noisy camera sensors, compression artifacts, and grainy phone pictures.
        """
        gray = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2GRAY)
        gray = cls.detect_and_correct_skew(gray)

        # Edge-preserving smoothing
        denoised = cv2.bilateralFilter(gray, d=9, sigmaColor=75, sigmaSpace=75)

        # Contrast stretch
        p2, p98 = np.percentile(denoised, (2, 98))
        stretched = np.clip((denoised - p2) * 255.0 / max(1.0, (p98 - p2)), 0, 255).astype(np.uint8)

        _, otsu = cv2.threshold(stretched, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return otsu

    @classmethod
    def generate_variants(cls, image_bytes: bytes) -> List[Tuple[str, np.ndarray]]:
        """
        Generates an ordered list of enhanced image variants for multi-pass OCR.
        Order:
        1. CLAHE + Sharpen (best general faint document enhancer)
        2. Adaptive Threshold (best for washed-out / dot-matrix print)
        3. Denoised + Otsu (best for high-noise camera shots)
        4. Normalized RGB (unaltered high-res baseline)
        """
        base_bgr = cls.load_image_bytes(image_bytes)
        scaled_bgr = cls.upscale_if_small(base_bgr)

        variants = []
        try:
            v1 = cls.enhance_clahe_sharpen(scaled_bgr)
            variants.append(("clahe_sharpen", v1))
        except Exception as e:
            logger.warning("Failed to generate clahe_sharpen variant: %s", e)

        try:
            v2 = cls.enhance_adaptive_threshold(scaled_bgr)
            variants.append(("adaptive_threshold", v2))
        except Exception as e:
            logger.warning("Failed to generate adaptive_threshold variant: %s", e)

        try:
            v3 = cls.enhance_denoised_otsu(scaled_bgr)
            variants.append(("denoised_otsu", v3))
        except Exception as e:
            logger.warning("Failed to generate denoised_otsu variant: %s", e)

        # Baseline scaled RGB
        rgb_scaled = cv2.cvtColor(scaled_bgr, cv2.COLOR_BGR2RGB)
        variants.append(("original_normalized", rgb_scaled))

        return variants
