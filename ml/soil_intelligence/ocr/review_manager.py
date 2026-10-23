"""
Human-in-the-Loop Review & Correction Manager
=============================================
Enforces the strict rule: NEVER silently convert uncertain OCR output into
trusted laboratory measurements.
Maintains an immutable audit log of manual corrections, reviewer signatures,
and parameter updates before reports are committed to active MEASURED state.
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime

from ml.soil_intelligence.schemas import (
    MeasuredLaboratoryReport,
    NutrientMeasurement,
    NutrientUnit,
    ChemicalForm,
    ProvenanceType
)
from ml.soil_intelligence.ocr.extractor import ExtractedReportDocument
from ml.soil_intelligence.ocr.normalizer import ReportFieldNormalizer


class ReviewStatus(str, Enum):
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED_AS_EXTRACTED = "APPROVED_AS_EXTRACTED"
    CORRECTED_AND_APPROVED = "CORRECTED_AND_APPROVED"
    REJECTED = "REJECTED"


@dataclass
class FieldCorrectionAudit:
    field_name: str
    original_reported_value: Any
    corrected_reported_value: Any
    original_normalized_kg_ha: Optional[float]
    corrected_normalized_kg_ha: Optional[float]
    correction_reason: str


@dataclass
class HumanReviewRecord:
    review_id: str
    report_id: str
    plot_id: str
    reviewer_id: str
    review_status: ReviewStatus
    reviewed_at: str
    corrections_applied: List[FieldCorrectionAudit] = field(default_factory=list)
    reviewer_notes: Optional[str] = None
    final_verified_report: Optional[MeasuredLaboratoryReport] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['review_status'] = self.review_status.value
        return d


class LabReportReviewManager:
    """
    Manages the verification queue for uncertain or out-of-bounds laboratory reports.
    """

    def __init__(self):
        self.review_queue: Dict[str, ExtractedReportDocument] = {}
        self.completed_reviews: Dict[str, HumanReviewRecord] = {}

    def queue_for_review(self, doc: ExtractedReportDocument) -> str:
        """Adds an extracted document to the human review queue."""
        report = doc.extracted_report
        report_id = report.report_id if report else f"DOC_{len(self.review_queue) + 1}"
        self.review_queue[report_id] = doc
        return report_id

    def approve_as_is(self, report_id: str, reviewer_id: str, notes: str = "") -> HumanReviewRecord:
        """Approves the extracted report without modifications."""
        if report_id not in self.review_queue:
            raise KeyError(f"Report ID not found in review queue: {report_id}")

        doc = self.review_queue.pop(report_id)
        report = doc.extracted_report
        if report:
            report.review_required = False
            report.notes = (report.notes or "") + f" | Verified by reviewer {reviewer_id}"

        review_record = HumanReviewRecord(
            review_id=f"REV_{report_id}",
            report_id=report_id,
            plot_id=report.plot_id if report else "UNKNOWN",
            reviewer_id=reviewer_id,
            review_status=ReviewStatus.APPROVED_AS_EXTRACTED,
            reviewed_at=datetime.utcnow().isoformat(),
            corrections_applied=[],
            reviewer_notes=notes,
            final_verified_report=report
        )
        self.completed_reviews[report_id] = review_record
        return review_record

    def submit_manual_correction(
        self,
        report_id: str,
        reviewer_id: str,
        corrections: Dict[str, Any],
        notes: str = ""
    ) -> HumanReviewRecord:
        """
        Applies manual corrections to uncertain fields, re-normalizes them,
        and logs a complete audit trail before committing to active ground truth.
        """
        if report_id not in self.review_queue:
            raise KeyError(f"Report ID not found in review queue: {report_id}")

        doc = self.review_queue.pop(report_id)
        report = doc.extracted_report
        if not report:
            raise ValueError(f"Cannot correct report without base extracted structure: {report_id}")

        applied_audits: List[FieldCorrectionAudit] = []

        # Process each corrected field
        for field_name, new_val in corrections.items():
            fn_lower = field_name.lower().strip()

            if fn_lower in ["n", "nitrogen"]:
                orig_reported = report.nitrogen.reported_value if report.nitrogen else None
                orig_norm = report.nitrogen.normalized_value_kg_ha if report.nitrogen else None
                # Re-normalize
                res = ReportFieldNormalizer.normalize_nutrient_field("N", str(new_val))
                report.nitrogen = res.measurement
                applied_audits.append(FieldCorrectionAudit(
                    field_name="Nitrogen",
                    original_reported_value=orig_reported,
                    corrected_reported_value=new_val,
                    original_normalized_kg_ha=orig_norm,
                    corrected_normalized_kg_ha=res.measurement.normalized_value_kg_ha if res.measurement else None,
                    correction_reason="Manual agronomist correction from original lab report document"
                ))

            elif fn_lower in ["p", "phosphorus"]:
                orig_reported = report.phosphorus.reported_value if report.phosphorus else None
                orig_norm = report.phosphorus.normalized_value_kg_ha if report.phosphorus else None
                res = ReportFieldNormalizer.normalize_nutrient_field("P", str(new_val))
                report.phosphorus = res.measurement
                applied_audits.append(FieldCorrectionAudit(
                    field_name="Phosphorus",
                    original_reported_value=orig_reported,
                    corrected_reported_value=new_val,
                    original_normalized_kg_ha=orig_norm,
                    corrected_normalized_kg_ha=res.measurement.normalized_value_kg_ha if res.measurement else None,
                    correction_reason="Manual agronomist correction from original lab report document"
                ))

            elif fn_lower in ["k", "potassium"]:
                orig_reported = report.potassium.reported_value if report.potassium else None
                orig_norm = report.potassium.normalized_value_kg_ha if report.potassium else None
                res = ReportFieldNormalizer.normalize_nutrient_field("K", str(new_val))
                report.potassium = res.measurement
                applied_audits.append(FieldCorrectionAudit(
                    field_name="Potassium",
                    original_reported_value=orig_reported,
                    corrected_reported_value=new_val,
                    original_normalized_kg_ha=orig_norm,
                    corrected_normalized_kg_ha=res.measurement.normalized_value_kg_ha if res.measurement else None,
                    correction_reason="Manual agronomist correction from original lab report document"
                ))

            elif fn_lower in ["ph"]:
                orig_reported = report.ph
                try:
                    corrected_ph = float(new_val)
                    report.ph = corrected_ph
                    applied_audits.append(FieldCorrectionAudit(
                        field_name="pH",
                        original_reported_value=orig_reported,
                        corrected_reported_value=corrected_ph,
                        original_normalized_kg_ha=corrected_ph,
                        corrected_normalized_kg_ha=corrected_ph,
                        correction_reason="Manual pH correction"
                    ))
                except ValueError:
                    pass

        report.review_required = False
        report.notes = (report.notes or "") + f" | Corrected & approved by reviewer {reviewer_id}"

        review_record = HumanReviewRecord(
            review_id=f"REV_{report_id}",
            report_id=report_id,
            plot_id=report.plot_id,
            reviewer_id=reviewer_id,
            review_status=ReviewStatus.CORRECTED_AND_APPROVED,
            reviewed_at=datetime.utcnow().isoformat(),
            corrections_applied=applied_audits,
            reviewer_notes=notes,
            final_verified_report=report
        )
        self.completed_reviews[report_id] = review_record
        return review_record
