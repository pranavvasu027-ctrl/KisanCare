"""
Document OCR Engine Interface & Multi-Pass Service
==================================================
Provides modern document OCR via RapidOCR (PaddleOCR ONNX runtime) with
spatial table layout reconstruction, multi-pass preprocessing retries,
and fallback to Windows Media OCR / Tesseract.
"""

from __future__ import annotations
import io
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from PIL import Image

from .preprocessor import ImageEnhancementPipeline

logger = logging.getLogger("kisancare.ocr.engine")


@dataclass
class OCRLine:
    text: str
    confidence: float
    bbox: List[float] = field(default_factory=list)  # [x1, y1, x2, y2]
    cy: float = 0.0
    h: float = 0.0
    x1: float = 0.0


@dataclass
class OCRDocumentResult:
    raw_text: str
    reconstructed_text: str
    confidence: float
    lines: List[OCRLine] = field(default_factory=list)
    engine_name: str = "unknown"
    variant_name: str = "default"
    nutrients_detected: List[str] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return len(self.reconstructed_text.strip()) == 0


class BaseOCREngine(ABC):
    """Abstract interface for document OCR engines."""

    @abstractmethod
    def is_available(self) -> bool:
        """Returns True if the engine's dependencies are installed and operational."""
        pass

    @abstractmethod
    def recognize_image_array(self, img_arr: np.ndarray) -> Tuple[List[OCRLine], float]:
        """Runs OCR on a numpy image array (grayscale, BGR, or RGB)."""
        pass


class RapidDocumentOCREngine(BaseOCREngine):
    """Primary document OCR engine using PaddleOCR's ONNX runtime (RapidOCR)."""

    def __init__(self):
        self._ocr = None
        self._init_error = None

    def _get_ocr(self):
        if self._ocr is None and self._init_error is None:
            try:
                from rapidocr_onnxruntime import RapidOCR
                self._ocr = RapidOCR()
            except Exception as e:
                self._init_error = str(e)
                logger.warning("RapidOCR initialization failed: %s", e)
        return self._ocr

    def is_available(self) -> bool:
        return self._get_ocr() is not None

    def recognize_image_array(self, img_arr: np.ndarray) -> Tuple[List[OCRLine], float]:
        ocr = self._get_ocr()
        if ocr is None:
            return [], 0.0

        try:
            results, elapse = ocr(img_arr)
            if not results:
                return [], 0.0

            lines: List[OCRLine] = []
            scores: List[float] = []

            for item in results:
                box, text, score = item[0], item[1], float(item[2])
                text_clean = text.strip()
                if not text_clean:
                    continue

                ys = [p[1] for p in box]
                xs = [p[0] for p in box]
                cy = sum(ys) / len(ys)
                h = max(ys) - min(ys)
                x1 = min(xs)
                x2 = max(xs)
                y1 = min(ys)
                y2 = max(ys)

                lines.append(OCRLine(
                    text=text_clean,
                    confidence=score,
                    bbox=[x1, y1, x2, y2],
                    cy=cy,
                    h=h,
                    x1=x1
                ))
                scores.append(score)

            mean_conf = float(np.mean(scores)) if scores else 0.0
            return lines, mean_conf

        except Exception as exc:
            logger.error("RapidOCR execution error: %s", exc)
            return [], 0.0


class WindowsMediaOCREngine(BaseOCREngine):
    """Fallback OCR engine using Windows 10/11 built-in WinRT OCR."""

    def __init__(self):
        self._available = None

    def is_available(self) -> bool:
        if self._available is None:
            try:
                import winocr
                self._available = True
            except Exception:
                self._available = False
        return self._available

    def recognize_image_array(self, img_arr: np.ndarray) -> Tuple[List[OCRLine], float]:
        if not self.is_available():
            return [], 0.0

        try:
            import winocr
            if len(img_arr.shape) == 2:
                pil_img = Image.fromarray(img_arr).convert("RGB")
            else:
                pil_img = Image.fromarray(cv2.cvtColor(img_arr, cv2.COLOR_BGR2RGB))

            res = winocr.recognize_pil_sync(pil_img, "en")
            lines: List[OCRLine] = []

            for line_obj in res.get("lines", []):
                line_text = line_obj.get("text", "").strip()
                if not line_text:
                    continue

                # Compute approximate bbox from line words
                words = line_obj.get("words", [])
                if words:
                    min_x = min(float(w.get("bounding_rect", {}).get("x", 0)) for w in words)
                    min_y = min(float(w.get("bounding_rect", {}).get("y", 0)) for w in words)
                    max_x = max(float(w.get("bounding_rect", {}).get("x", 0)) + float(w.get("bounding_rect", {}).get("width", 0)) for w in words)
                    max_y = max(float(w.get("bounding_rect", {}).get("y", 0)) + float(w.get("bounding_rect", {}).get("height", 0)) for w in words)
                    cy = (min_y + max_y) / 2.0
                    h = max_y - min_y
                else:
                    min_x, min_y, max_x, max_y, cy, h = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0

                lines.append(OCRLine(
                    text=line_text,
                    confidence=0.85,
                    bbox=[min_x, min_y, max_x, max_y],
                    cy=cy,
                    h=h,
                    x1=min_x
                ))

            return lines, 0.85 if lines else 0.0

        except Exception as exc:
            logger.debug("WindowsMediaOCR error: %s", exc)
            return [], 0.0


class TesseractOCREngine(BaseOCREngine):
    """Fallback OCR engine using pytesseract if installed and configured."""

    def __init__(self):
        self._available = None

    def is_available(self) -> bool:
        if self._available is None:
            try:
                import pytesseract
                self._available = True
            except Exception:
                self._available = False
        return self._available

    def recognize_image_array(self, img_arr: np.ndarray) -> Tuple[List[OCRLine], float]:
        if not self.is_available():
            return [], 0.0

        try:
            import pytesseract
            raw_text = pytesseract.image_to_string(img_arr)
            lines: List[OCRLine] = []
            for y_idx, l in enumerate(raw_text.splitlines()):
                l_str = l.strip()
                if l_str:
                    lines.append(OCRLine(
                        text=l_str,
                        confidence=0.75,
                        cy=float(y_idx * 20),
                        h=15.0,
                        x1=0.0
                    ))
            return lines, 0.75 if lines else 0.0
        except Exception as exc:
            logger.debug("Tesseract execution error: %s", exc)
            return [], 0.0


class DocumentOCREngine:
    """
    Facade managing document OCR with spatial layout reconstruction,
    multi-pass image preprocessing retries, and high-DPI scanned PDF rendering.
    """

    def __init__(self):
        self.engines: List[Tuple[str, BaseOCREngine]] = [
            ("RapidOCR", RapidDocumentOCREngine()),
            ("WindowsMediaOCR", WindowsMediaOCREngine()),
            ("Tesseract", TesseractOCREngine()),
        ]

    @staticmethod
    def reconstruct_table_layout(lines: List[OCRLine]) -> str:
        """
        Groups horizontally adjacent word/column bounding boxes into coherent rows.
        Calculates vertical tolerance adaptively from line heights and prevents
        horizontal overlap between different rows.
        """
        if not lines:
            return ""

        # Compute median line height across detected text boxes
        heights = [l.h for l in lines if l.h > 2.0]
        median_h = float(np.median(heights)) if heights else 14.0
        # Adaptive vertical tolerance: scaled to font height, with floor at 3.0 and ceiling at 10.0
        tol = max(3.0, min(10.0, median_h * 0.45))

        # Sort all boxes top-to-bottom by vertical center
        sorted_lines = sorted(lines, key=lambda l: l.cy)
        rows: List[List[OCRLine]] = []

        for line_item in sorted_lines:
            matched = False
            for row in rows:
                # Check horizontal overlap with any existing item in row
                # If two boxes overlap horizontally by more than 4 pixels, they cannot be on the same horizontal row
                overlaps = False
                for existing in row:
                    overlap_w = min(line_item.bbox[2], existing.bbox[2]) - max(line_item.bbox[0], existing.bbox[0])
                    if overlap_w > 4.0:
                        overlaps = True
                        break
                if overlaps:
                    continue

                avg_cy = sum(x.cy for x in row) / len(row)
                if abs(line_item.cy - avg_cy) <= tol:
                    row.append(line_item)
                    matched = True
                    break
            if not matched:
                rows.append([line_item])

        # Sort rows top-to-bottom
        rows.sort(key=lambda r: sum(x.cy for x in r) / len(r))

        output_lines = []
        for row in rows:
            # Sort items in this row left-to-right
            row.sort(key=lambda x: x.x1)
            row_text = "  ".join(x.text for x in row)
            output_lines.append(row_text)

        return "\n".join(output_lines)

    @staticmethod
    def count_soil_parameters_in_text(text: str) -> List[str]:
        """
        Detects presence of essential soil parameters in extracted text,
        robust to common OCR character confusions.
        """
        import re
        detected = []
        text_lower = text.lower()
        if re.search(r"\bph\b|soil\s+reaction|p\.h\.?|\bph\s+value\b|\bphindex\b", text_lower, re.IGNORECASE):
            detected.append("pH")
        if re.search(r"\bnitrogen\b|\bavail(?:able|oble|allable)?\s+n\b|\b(?:as|os)?\s*n\)?|\bn\s*\(?kg", text_lower, re.IGNORECASE):
            detected.append("Nitrogen")
        if re.search(r"\bphosphorus\b|\bavail(?:able|eble|oble|allable)?\s+p\b|p2[o0]5|p₂o₅|phosphate|\b(?:as|os)?\s*p\)?", text_lower, re.IGNORECASE):
            detected.append("Phosphorus")
        if re.search(r"\bpotassium\b|pot[ao]ss[il1u]um[k]?|\bavail(?:able|oble|toble|ateble)?\s+k\b|k2[o0]|k₂o|potash|\bavail(?:able)?\s+pot|\b(?:as|os)?\s*k\)?", text_lower, re.IGNORECASE):
            detected.append("Potassium")
        if re.search(r"\borganic\s+c[ao]rbon\b|\boc\b", text_lower, re.IGNORECASE):
            detected.append("Organic Carbon")
        if re.search(r"\belectrical\s+conductivity\b|\bec\b", text_lower, re.IGNORECASE):
            detected.append("EC")
        return detected

    def recognize_image_bytes(self, image_bytes: bytes) -> OCRDocumentResult:
        """
        Runs multi-pass OCR on image bytes.
        Tries multiple image enhancement variants (CLAHE, Adaptive Threshold, Denoised Otsu, Original).
        Collects results across variants and performs multi-pass pooling if essential parameters are missing in the top variant.
        """
        variants = ImageEnhancementPipeline.generate_variants(image_bytes)
        best_result: Optional[OCRDocumentResult] = None
        best_score = -1.0
        all_variant_results: List[OCRDocumentResult] = []

        for variant_name, img_arr in variants:
            for engine_name, engine in self.engines:
                if not engine.is_available():
                    continue

                lines, mean_conf = engine.recognize_image_array(img_arr)
                if not lines:
                    continue

                reconstructed = self.reconstruct_table_layout(lines)
                raw_text = "\n".join(l.text for l in lines)
                detected_nutrients = self.count_soil_parameters_in_text(reconstructed)

                nutrient_score = len(detected_nutrients) * 100.0
                char_score = min(50.0, len(reconstructed) / 10.0)
                conf_score = mean_conf * 20.0
                total_variant_score = nutrient_score + char_score + conf_score

                result = OCRDocumentResult(
                    raw_text=raw_text,
                    reconstructed_text=reconstructed,
                    confidence=mean_conf,
                    lines=lines,
                    engine_name=engine_name,
                    variant_name=variant_name,
                    nutrients_detected=detected_nutrients
                )
                all_variant_results.append(result)

                # If all 4 essential parameters (pH, N, P, K) are detected, we found an optimal enhancement!
                if {"pH", "Nitrogen", "Phosphorus", "Potassium"}.issubset(set(detected_nutrients)):
                    logger.info("Optimal OCR extraction achieved using variant '%s' with engine '%s'", variant_name, engine_name)
                    return result

                if total_variant_score > best_score:
                    best_score = total_variant_score
                    best_result = result

                # Only try the next engine if this one produced no text
                break

            # Fast early-exit: If the document is sharp and high-confidence (mean_conf >= 0.82, >= 30 lines)
            # and we have already tried 2 variants without finding the remaining parameter, stop early
            # rather than keeping the farmer waiting for redundant passes on a parameter not on the certificate.
            if len(all_variant_results) >= 2 and best_result and best_result.confidence >= 0.82 and len(best_result.lines) >= 30:
                logger.info("Terminating multi-pass OCR early after %d high-confidence passes to avoid farmer latency.", len(all_variant_results))
                break

        if best_result is not None:
            # Multi-pass intelligent pooling:
            # If best_result is missing any core nutrient, check if other variants detected it
            core_needed = {"pH", "Nitrogen", "Phosphorus", "Potassium"}
            found_in_best = set(best_result.nutrients_detected)
            missing_core = core_needed - found_in_best

            if missing_core and len(all_variant_results) > 1:
                supplementary_lines = []
                for other_res in all_variant_results:
                    if other_res is best_result:
                        continue
                    for line in other_res.reconstructed_text.splitlines():
                        line_nutrients = set(self.count_soil_parameters_in_text(line))
                        if line_nutrients & missing_core:
                            supplementary_lines.append(line)
                            missing_core -= line_nutrients
                            best_result.nutrients_detected.extend(list(line_nutrients & core_needed))

                if supplementary_lines:
                    best_result.reconstructed_text = (
                        best_result.reconstructed_text + "\n" + "\n".join(supplementary_lines)
                    )
                    logger.info("Multi-pass retry supplemented missing parameters from alternate variants: %s", supplementary_lines)

            return best_result

        return OCRDocumentResult(
            raw_text="",
            reconstructed_text="",
            confidence=0.0,
            engine_name="none",
            variant_name="none"
        )

    def extract_pdf_with_ocr_fallback(self, pdf_bytes: bytes) -> OCRDocumentResult:
        """
        Extracts document text from PDF.
        1. Checks embedded vector/digital text streams first (fastest, 100% precision).
        2. If PDF is scanned or embedded text lacks soil parameters, renders pages at 300 DPI
           and executes the multi-pass image OCR pipeline.
        """
        import pymupdf

        try:
            doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        except Exception as exc:
            logger.error("Failed to open PDF stream: %s", exc)
            return OCRDocumentResult(raw_text="", reconstructed_text="", confidence=0.0, engine_name="pymupdf_error")

        # Step 1: Check digital embedded text
        extracted_pages_text = []
        for page_idx in range(len(doc)):
            page = doc[page_idx]
            page_text = page.get_text().strip()
            if page_text:
                extracted_pages_text.append(page_text)

        full_digital_text = "\n\n".join(extracted_pages_text)
        detected_nutrients = self.count_soil_parameters_in_text(full_digital_text)

        # If digital text is rich and contains at least 2 soil parameters, use it!
        if len(full_digital_text.strip()) >= 40 and len(detected_nutrients) >= 2:
            return OCRDocumentResult(
                raw_text=full_digital_text,
                reconstructed_text=full_digital_text,
                confidence=0.99,
                engine_name="pymupdf_digital",
                variant_name="digital_embedded",
                nutrients_detected=detected_nutrients
            )

        # Step 2: PDF is scanned or embedded text was insufficient -> Render pages at 300 DPI
        logger.info("PDF contains insufficient embedded text; rendering %d page(s) at 300 DPI for image OCR.", len(doc))
        all_page_results = []

        for page_idx in range(min(5, len(doc))):  # Process up to first 5 pages of report
            page = doc[page_idx]
            pix = page.get_pixmap(dpi=300)
            img_bytes = pix.tobytes("png")

            page_ocr_res = self.recognize_image_bytes(img_bytes)
            if not page_ocr_res.is_empty:
                all_page_results.append(page_ocr_res)

        if all_page_results:
            combined_raw = "\n\n".join(r.raw_text for r in all_page_results)
            combined_reconstructed = "\n\n".join(r.reconstructed_text for r in all_page_results)
            combined_conf = float(np.mean([r.confidence for r in all_page_results]))
            all_nutrients = list(set(n for r in all_page_results for n in r.nutrients_detected))

            return OCRDocumentResult(
                raw_text=combined_raw,
                reconstructed_text=combined_reconstructed,
                confidence=combined_conf,
                engine_name=all_page_results[0].engine_name,
                variant_name=f"scanned_pdf_{all_page_results[0].variant_name}",
                nutrients_detected=all_nutrients
            )

        return OCRDocumentResult(
            raw_text="",
            reconstructed_text="",
            confidence=0.0,
            engine_name="pymupdf_ocr_fallback",
            variant_name="none"
        )
