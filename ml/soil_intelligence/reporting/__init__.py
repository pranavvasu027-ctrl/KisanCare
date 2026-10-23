"""
KISANcare Soil Intelligence - Reporting & Advisory Module
==========================================================
Generates verifiable, publication-grade soil intelligence PDF reports
and ICAR-compliant educational advisory guidance.
"""

from ml.soil_intelligence.reporting.advisory import (
    AgronomicAdvisoryEngine,
    SoilAdvisoryBundle,
    AgronomicAdvisoryItem,
    NutrientTier,
    ReactionTier,
    SalinityTier,
    OrganicCarbonTier
)
from ml.soil_intelligence.reporting.report_builder import (
    SoilReportBuilder,
    SoilReportViewModel,
    MeasuredParameterRow,
    ChronologicalEventRow
)
from ml.soil_intelligence.reporting.pdf_generator import (
    SoilIntelligencePDFGenerator
)

__all__ = [
    "AgronomicAdvisoryEngine",
    "SoilAdvisoryBundle",
    "AgronomicAdvisoryItem",
    "NutrientTier",
    "ReactionTier",
    "SalinityTier",
    "OrganicCarbonTier",
    "SoilReportBuilder",
    "SoilReportViewModel",
    "MeasuredParameterRow",
    "ChronologicalEventRow",
    "SoilIntelligencePDFGenerator",
]
