"""
KISANcare Soil Intelligence V1 - OCR Ingestion & Lab Report Parser
===================================================================
Handles ingestion of PDF, JPG, and PNG laboratory soil test reports,
field validation, unit normalization, confidence scoring, and human-in-the-loop review.
"""

__all__ = ["extractor", "normalizer", "review_manager"]
