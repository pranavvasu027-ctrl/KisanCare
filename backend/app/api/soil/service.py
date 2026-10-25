"""
Soil Intelligence Application Service
====================================
Integrates the ml.soil_intelligence core domain logic with the API layer.
Decouples domain components from FastAPI routers, handling data transformations,
provenance guarantees, and error handling.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Any
from datetime import datetime, date
import os
import io
import re
import logging
import base64
import zlib

logger = logging.getLogger(__name__)


from ml.soil_intelligence.ocr.engine import DocumentOCREngine

_global_ocr_engine = DocumentOCREngine()


def _extract_text_from_pdf_bytes(file_bytes: bytes) -> str:
    """Robust extraction of digital and scanned PDF reports with multi-pass OCR and stream decompression fallback."""
    try:
        res = _global_ocr_engine.extract_pdf_with_ocr_fallback(file_bytes)
        text = res.reconstructed_text or res.raw_text
        if text and len(text.strip()) >= 10:
            return text
    except Exception as exc:
        logger.debug("Primary PDF extraction failed: %s", exc)

    extracted_lines: List[str] = []
    try:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        for page in reader.pages:
            t = page.extract_text()
            if t:
                extracted_lines.append(t)
    except Exception:
        pass

    if not extracted_lines:
        uncomp = re.findall(rb"\(((?:\\.|[^\\()])*)\)\s*Tj", file_bytes)
        if uncomp:
            for s in uncomp:
                clean = s.replace(b"\\(", b"(").replace(b"\\)", b")").decode("latin1", errors="ignore").strip()
                if clean:
                    extracted_lines.append(clean)

        for m in re.finditer(rb"<<(?P<dict>.*?)>>\s*stream[\r\n]*(?P<body>.*?)[\r\n]*endstream", file_bytes, re.DOTALL):
            d_meta = m.group("dict")
            body = m.group("body").strip()
            data = body
            if b"ASCII85Decode" in d_meta:
                try:
                    data = base64.a85decode(data, adobe=True)
                except Exception:
                    pass
            if b"FlateDecode" in d_meta:
                try:
                    data = zlib.decompress(data)
                except Exception:
                    try:
                        data = zlib.decompress(data, -zlib.MAX_WBITS)
                    except Exception:
                        pass
            matches = re.findall(rb"\(((?:\\.|[^\\()])*)\)\s*Tj", data)
            if matches:
                for s in matches:
                    clean = s.replace(b"\\(", b"(").replace(b"\\)", b")").decode("latin1", errors="ignore").strip()
                    if clean:
                        extracted_lines.append(clean)

    return "\n".join(extracted_lines)


def _extract_text_from_image_bytes(file_bytes: bytes) -> str:
    """Extracts text from faint, blurry, rotated, or low-contrast images using multi-variant enhancement and OCR."""
    res = _global_ocr_engine.recognize_image_bytes(file_bytes)
    return res.reconstructed_text or res.raw_text

from ml.soil_intelligence.schemas import (
    ProvenanceType,
    NutrientUnit,
    ChemicalForm,
    TestMethod,
    NutrientMeasurement,
    MeasuredLaboratoryReport,
    AgronomicTolerances,
    EvaluationComparisonRecord
)
from ml.soil_intelligence.ocr.extractor import LabReportExtractor, ExtractedReportDocument
from ml.soil_intelligence.ocr.review_manager import ReviewStatus
from ml.soil_intelligence.timeline.timeline_manager import PlotTimelineManager
from ml.soil_intelligence.timeline.agronomic_depletion import (
    AgronomicDepletionEngine,
    FERTILIZER_GRADE_BENCHMARKS,
    CROP_REMOVAL_BENCHMARKS
)
from ml.soil_intelligence.model.predictor import SoilIntelligencePredictor
from ml.soil_intelligence.reporting.report_builder import SoilReportBuilder
from ml.soil_intelligence.reporting.pdf_generator import SoilIntelligencePDFGenerator
from ml.soil_intelligence.reporting.advisory import AgronomicAdvisoryEngine, SoilAdvisoryBundle
from ml.soil_intelligence.evaluation.comparator import SoilContinuousComparator

from .store import SoilPlotStore
from .schemas import (
    ParseReportRequest,
    ParseReportResponse,
    ValidationIssueResponse,
    ExtractedNutrientResponse,
    ManualCorrectionRequest,
    ConfirmBaselineReportRequest,
    FertilizerEventRequest,
    HarvestEventRequest,
    AgronomicEventResponse,
    PlotStatusResponse,
    AdvisoryItemResponse,
    CompareRetestRequest,
    ComparisonResponse,
    SingleNutrientComparisonResponse,
    BenchmarksResponse,
    GenericMessageResponse
)


class SoilIntelligenceService:
    """Service adapter bridging FastAPI routes to ml.soil_intelligence engine."""

    def __init__(self, store: Optional[SoilPlotStore] = None):
        self.store = store or SoilPlotStore.get_instance()
        self.predictor = SoilIntelligencePredictor()
        self.pdf_generator = SoilIntelligencePDFGenerator()

    # -----------------------------------------------------------------------
    # 1. OCR Report Parsing & Human Review
    # -----------------------------------------------------------------------

    def parse_report_text(self, request: ParseReportRequest) -> ParseReportResponse:
        """Parses raw text from a Soil Health Card or lab certificate."""
        doc = LabReportExtractor.extract_from_text(request.report_text)
        review_token = None

        if doc.requires_human_review:
            review_token = self.store.get_review_manager().queue_for_review(doc)

        issues = [
            ValidationIssueResponse(
                field=iss.field_name,
                issue_code=iss.issue_code,
                message=iss.message,
                severity=iss.severity
            )
            for iss in doc.validation_issues
        ]

        def _nutrient_dto(nm: Optional[NutrientMeasurement]) -> Optional[ExtractedNutrientResponse]:
            if not nm:
                return None
            return ExtractedNutrientResponse(
                nutrient=nm.nutrient,
                reported_value=nm.reported_value,
                reported_unit=nm.reported_unit.value if hasattr(nm.reported_unit, "value") else str(nm.reported_unit),
                reported_form=nm.reported_form.value if hasattr(nm.reported_form, "value") else str(nm.reported_form),
                normalized_value_kg_ha=nm.normalized_value_kg_ha,
                conversion_applied=nm.conversion_applied,
                test_method=nm.test_method.value if hasattr(nm.test_method, "value") else str(nm.test_method)
            )

        rep = doc.extracted_report
        return ParseReportResponse(
            success=True,
            report_id=rep.report_id if rep else None,
            plot_id=request.plot_id or (rep.plot_id if rep else None),
            sample_date=rep.sample_date if rep else None,
            ph=rep.ph if rep else None,
            ec_ds_m=rep.ec_ds_m if rep else None,
            organic_carbon_pct=rep.organic_carbon_pct if rep else None,
            nitrogen=_nutrient_dto(rep.nitrogen) if rep else None,
            phosphorus=_nutrient_dto(rep.phosphorus) if rep else None,
            potassium=_nutrient_dto(rep.potassium) if rep else None,
            confidence_score=doc.overall_confidence,
            requires_human_review=doc.requires_human_review,
            validation_issues=issues,
            review_token=review_token,
            raw_ocr_text=request.report_text
        )

    def parse_uploaded_file(
        self,
        file_bytes: bytes,
        filename: str,
        plot_id: Optional[str] = None,
        farm_id: Optional[str] = None
    ) -> ParseReportResponse:
        """
        Ingests a real uploaded file (PDF, JPG, JPEG, PNG), extracts document text using
        pure-Python stream decompression (for PDFs) or Pillow/winocr with spatial layout
        reconstruction (for images), and normalizes report fields.
        """
        ext = os.path.splitext(filename)[1].lower()
        raw_text = ""

        if ext == ".pdf":
            raw_text = _extract_text_from_pdf_bytes(file_bytes)
        elif ext in [".jpg", ".jpeg", ".png"]:
            raw_text = _extract_text_from_image_bytes(file_bytes)

        # Safe development/debug logging of raw OCR text with ASCII replacement for Windows consoles
        safe_preview = raw_text.encode("ascii", errors="replace").decode("ascii")
        logger.info("Extracted %d characters of OCR text from %s", len(raw_text), filename)
        logger.debug(
            "\n================ RAW OCR TEXT [%s] ================\n%s\n===================================================",
            filename,
            safe_preview
        )

        # If extracted text is insufficient or unreadable, return graceful review-queued response
        if len(raw_text.strip()) < 10:
            review_token = "REV_SCAN_" + datetime.utcnow().strftime("%Y%m%d%H%M%S")
            return ParseReportResponse(
                success=True,
                report_id=f"SCANNED_{os.path.splitext(filename)[0][:16]}",
                plot_id=plot_id,
                confidence_score=0.10,
                requires_human_review=True,
                validation_issues=[
                    ValidationIssueResponse(
                        field="document_text",
                        issue_code="LOW_LEGIBILITY",
                        message=f"Text extracted from '{filename}' was unreadable or too faint. Please review and enter values manually.",
                        severity="WARNING"
                    )
                ],
                review_token=review_token,
                raw_ocr_text=raw_text
            )

        return self.parse_report_text(ParseReportRequest(
            report_text=raw_text,
            plot_id=plot_id,
            farm_id=farm_id
        ))

    def submit_manual_correction(self, request: ManualCorrectionRequest) -> GenericMessageResponse:
        """Applies human agronomist correction to an uncertain report."""
        record = self.store.get_review_manager().submit_manual_correction(
            report_id=request.review_token,
            reviewer_id=request.reviewer_id,
            corrections=request.corrections,
            notes=request.notes or "Manual agronomist review."
        )
        return GenericMessageResponse(
            status="corrected",
            message=f"Report {request.review_token} successfully re-normalized by reviewer {request.reviewer_id}."
        )

    # -----------------------------------------------------------------------
    # 2. Baseline Laboratory Record Confirmation
    # -----------------------------------------------------------------------

    def confirm_baseline_report(self, req: ConfirmBaselineReportRequest, owner_id: Optional[str] = None) -> GenericMessageResponse:
        """Directly confirms or inputs a verified laboratory baseline for a plot."""
        timeline = self.store.get_or_create_timeline(plot_id=req.plot_id, farm_id=req.farm_id, owner_id=owner_id)

        report_id = req.report_id or f"LAB_{req.plot_id}_{req.sample_date.replace('-', '')}"
        lab_report = MeasuredLaboratoryReport(
            report_id=report_id,
            plot_id=req.plot_id,
            sample_date=req.sample_date,
            lab_name=req.lab_name,
            lab_certificate_no=req.lab_certificate_no,
            lab_accreditation_id=req.lab_accreditation_id,
            accreditation_verified=req.accreditation_verified,
            accreditation_source=req.accreditation_source,
            provenance=ProvenanceType.MEASURED,
            nitrogen=NutrientMeasurement(
                nutrient="N",
                reported_value=req.nitrogen_kg_ha,
                reported_unit=NutrientUnit.KG_PER_HA,
                reported_form=ChemicalForm.ELEMENTAL_N,
                normalized_value_kg_ha=req.nitrogen_kg_ha,
                conversion_applied="reported directly in kg/ha",
                conversion_verified=True,
                test_method=TestMethod.ALKALINE_PERMANGANATE
            ),
            phosphorus=NutrientMeasurement(
                nutrient="P",
                reported_value=req.phosphorus_kg_ha,
                reported_unit=NutrientUnit.KG_PER_HA,
                reported_form=ChemicalForm.ELEMENTAL_P,
                normalized_value_kg_ha=req.phosphorus_kg_ha,
                conversion_applied="reported directly in kg/ha",
                conversion_verified=True,
                test_method=TestMethod.OLSEN_SODIUM_BICARBONATE
            ),
            potassium=NutrientMeasurement(
                nutrient="K",
                reported_value=req.potassium_kg_ha,
                reported_unit=NutrientUnit.KG_PER_HA,
                reported_form=ChemicalForm.ELEMENTAL_K,
                normalized_value_kg_ha=req.potassium_kg_ha,
                conversion_applied="reported directly in kg/ha",
                conversion_verified=True,
                test_method=TestMethod.AMMONIUM_ACETATE_FLAME
            ),
            ph=req.ph,
            ec_ds_m=req.ec_ds_m,
            organic_carbon_pct=req.organic_carbon_pct,
            notes=req.notes
        )

        timeline.add_lab_report(lab_report)
        self.store.save()
        return GenericMessageResponse(
            status="confirmed",
            message=f"Laboratory baseline {report_id} registered for plot {req.plot_id}.",
            plot_id=req.plot_id
        )

    # -----------------------------------------------------------------------
    # 3. Agronomic Management Events
    # -----------------------------------------------------------------------

    def record_fertilizer_event(self, plot_id: str, req: FertilizerEventRequest, user_id: Optional[str] = None) -> AgronomicEventResponse:
        timeline = self.store.get_timeline(plot_id, user_id=user_id)
        if not timeline:
            raise KeyError(f"Plot '{plot_id}' not found. Please establish a baseline first.")

        flux = timeline.record_fertilizer_application(
            fertilizer_name=req.fertilizer_grade,
            application_rate_kg_ha=req.quantity_kg_ha,
            application_date=req.application_date,
            event_id=req.event_id
        )
        self.store.save()

        return AgronomicEventResponse(
            event_id=flux.event_id,
            event_type="FERTILIZER_APPLICATION",
            event_date=flux.event_date,
            description=flux.description,
            n_flux_kg_ha=flux.delta_n_kg_ha,
            p_flux_kg_ha=flux.delta_p_elemental_kg_ha,
            k_flux_kg_ha=flux.delta_k_elemental_kg_ha,
            source_citation=flux.source_citation
        )

    def record_harvest_event(self, plot_id: str, req: HarvestEventRequest, user_id: Optional[str] = None) -> AgronomicEventResponse:
        timeline = self.store.get_timeline(plot_id, user_id=user_id)
        if not timeline:
            raise KeyError(f"Plot '{plot_id}' not found. Please establish a baseline first.")

        flux = timeline.record_crop_harvest(
            crop_name=req.crop_name,
            yield_tons_ha=req.yield_tonnes_ha,
            harvest_date=req.harvest_date,
            residue_retained=req.residue_retained,
            event_id=req.event_id
        )
        self.store.save()

        return AgronomicEventResponse(
            event_id=flux.event_id,
            event_type="CROP_HARVEST_REMOVAL",
            event_date=flux.event_date,
            description=flux.description,
            n_flux_kg_ha=flux.delta_n_kg_ha,
            p_flux_kg_ha=flux.delta_p_elemental_kg_ha,
            k_flux_kg_ha=flux.delta_k_elemental_kg_ha,
            source_citation=flux.source_citation
        )

    def list_plot_events(self, plot_id: str, user_id: Optional[str] = None) -> List[AgronomicEventResponse]:
        timeline = self.store.get_timeline(plot_id, user_id=user_id)
        if not timeline:
            raise KeyError(f"Plot '{plot_id}' not found.")

        result = []
        for e in timeline.flux_events:
            result.append(AgronomicEventResponse(
                event_id=e.event_id,
                event_type="CROP_HARVEST_REMOVAL" if e.delta_n_kg_ha < 0 or e.delta_p_elemental_kg_ha < 0 or e.delta_k_elemental_kg_ha < 0 else "FERTILIZER_APPLICATION",
                event_date=e.event_date,
                description=e.description,
                n_flux_kg_ha=e.delta_n_kg_ha,
                p_flux_kg_ha=e.delta_p_elemental_kg_ha,
                k_flux_kg_ha=e.delta_k_elemental_kg_ha,
                source_citation=e.source_citation
            ))
        return result

    # -----------------------------------------------------------------------
    # 4. Status, Balance & Advisory
    # -----------------------------------------------------------------------

    def get_plot_status(self, plot_id: str, as_of_date: Optional[str] = None, user_id: Optional[str] = None) -> PlotStatusResponse:
        timeline = self.store.get_timeline(plot_id, user_id=user_id)
        if not timeline:
            raise KeyError(f"Plot '{plot_id}' not found.")

        target = as_of_date or date.today().isoformat()
        intel_report = self.predictor.evaluate_plot(timeline, target_date=target)
        latest_base = timeline.get_latest_baseline_report(target_date=target)

        # Build advisory bundle
        advisories: List[AdvisoryItemResponse] = []
        gen_recs: List[str] = []
        disclaimer = "Educational agronomic guidance based on ICAR/Tandon benchmarks."

        if latest_base:
            adv_bundle = AgronomicAdvisoryEngine.generate_plot_advisory_bundle(
                plot_id=plot_id,
                n_kg_ha=latest_base.nitrogen.normalized_value_kg_ha if latest_base.nitrogen else None,
                p_kg_ha=latest_base.phosphorus.normalized_value_kg_ha if latest_base.phosphorus else None,
                k_kg_ha=latest_base.potassium.normalized_value_kg_ha if latest_base.potassium else None,
                ph=latest_base.ph,
                ec_ds_m=latest_base.ec_ds_m,
                oc_pct=latest_base.organic_carbon_pct
            )
            disclaimer = adv_bundle.agronomic_disclaimer
            gen_recs = adv_bundle.general_recommendations

            for item in [
                adv_bundle.nitrogen_advisory,
                adv_bundle.phosphorus_advisory,
                adv_bundle.potassium_advisory,
                adv_bundle.reaction_advisory,
                adv_bundle.salinity_advisory,
                adv_bundle.organic_carbon_advisory
            ]:
                if item:
                    advisories.append(AdvisoryItemResponse(
                        parameter=item.parameter,
                        status_tier=item.tier.value if hasattr(item.tier, "value") else str(item.tier),
                        status_label=item.status_label,
                        reported_value=item.reported_value,
                        reported_unit=item.reported_unit,
                        educational_interpretation=item.educational_interpretation,
                        management_considerations=item.management_considerations,
                        scientific_reference=item.scientific_reference
                    ))

        # Mass balance summary
        ledger_dto = None
        if intel_report.mass_balance_ledger:
            m = intel_report.mass_balance_ledger
            ledger_dto = {
                "start_date": m.start_date,
                "end_date": m.end_date,
                "days_elapsed": m.days_elapsed,
                "gross_n_added_kg_ha": m.gross_n_added_kg_ha,
                "gross_p_added_kg_ha": m.gross_p_added_kg_ha,
                "gross_k_added_kg_ha": m.gross_k_added_kg_ha,
                "gross_n_removed_kg_ha": m.gross_n_removed_kg_ha,
                "gross_p_removed_kg_ha": m.gross_p_removed_kg_ha,
                "gross_k_removed_kg_ha": m.gross_k_removed_kg_ha,
                "net_balance_n_kg_ha": m.net_balance_n_kg_ha,
                "net_balance_p_kg_ha": m.net_balance_p_kg_ha,
                "net_balance_k_kg_ha": m.net_balance_k_kg_ha,
                "balance_uncertainty_n_kg_ha": m.balance_uncertainty_n_kg_ha,
                "balance_uncertainty_p_kg_ha": m.balance_uncertainty_p_kg_ha,
                "balance_uncertainty_k_kg_ha": m.balance_uncertainty_k_kg_ha,
                "unrecorded_days_estimate": m.unrecorded_days_estimate
            }

        abstain_reason = None
        abstain_rec = None
        if intel_report.abstention_decision and intel_report.abstention_decision.should_abstain:
            dec = intel_report.abstention_decision
            abstain_reason = dec.primary_reason
            abstain_rec = "; ".join(dec.actionable_recommendations) if dec.actionable_recommendations else None

        baseline_npk = None
        if latest_base:
            baseline_npk = {
                "N": latest_base.nitrogen.normalized_value_kg_ha if latest_base.nitrogen else 0.0,
                "P": latest_base.phosphorus.normalized_value_kg_ha if latest_base.phosphorus else 0.0,
                "K": latest_base.potassium.normalized_value_kg_ha if latest_base.potassium else 0.0,
            }

        return PlotStatusResponse(
            plot_id=plot_id,
            farm_id=timeline.farm_id,
            as_of_date=target,
            has_baseline_lab_test=latest_base is not None,
            baseline_date=latest_base.sample_date if latest_base else None,
            baseline_lab_name=latest_base.lab_name if latest_base else None,
            accreditation_verified=latest_base.accreditation_verified if latest_base else False,
            baseline_npk_kg_ha=baseline_npk,
            soil_ph=latest_base.ph if latest_base else None,
            organic_carbon_pct=latest_base.organic_carbon_pct if latest_base else None,
            ec_ds_m=latest_base.ec_ds_m if latest_base else None,
            recorded_events_count=len(timeline.flux_events),
            net_mass_balance_ledger=ledger_dto,
            is_operational_authorized=intel_report.is_operational_authorized,
            abstention_reason=abstain_reason,
            abstention_recommendation=abstain_rec,
            advisories=advisories,
            general_recommendations=gen_recs,
            agronomic_disclaimer=disclaimer
        )

    # -----------------------------------------------------------------------
    # 5. PDF Report Generation
    # -----------------------------------------------------------------------

    def generate_pdf_report(self, plot_id: str, target_date: Optional[str] = None, user_id: Optional[str] = None) -> bytes:
        timeline = self.store.get_timeline(plot_id, user_id=user_id)
        if not timeline:
            raise KeyError(f"Plot '{plot_id}' not found. Cannot generate report without a registered timeline.")

        target = target_date or date.today().isoformat()
        intel_report = self.predictor.evaluate_plot(timeline, target_date=target)
        vm = SoilReportBuilder.build_view_model(timeline, intel_report)
        return self.pdf_generator.generate_pdf_bytes(vm)

    # -----------------------------------------------------------------------
    # 6. Continuous Comparison Engine
    # -----------------------------------------------------------------------

    def compare_retest(self, plot_id: str, req: CompareRetestRequest, user_id: Optional[str] = None) -> ComparisonResponse:
        timeline = self.store.get_timeline(plot_id, user_id=user_id)
        if not timeline:
            raise KeyError(f"Plot '{plot_id}' not found.")

        # Evaluate model prediction / abstention at retest date
        intel_report = self.predictor.evaluate_plot(timeline, target_date=req.retest_date)
        comparator = self.store.get_comparator()

        report_id = req.retest_report_id or f"RETEST_{plot_id}_{req.retest_date.replace('-', '')}"
        actual_lab = MeasuredLaboratoryReport(
            report_id=report_id,
            plot_id=plot_id,
            sample_date=req.retest_date,
            lab_name=req.lab_name,
            lab_certificate_no=req.lab_certificate_no,
            lab_accreditation_id=req.lab_accreditation_id,
            accreditation_verified=req.accreditation_verified,
            provenance=ProvenanceType.MEASURED,
            nitrogen=NutrientMeasurement(
                nutrient="N", reported_value=req.nitrogen_kg_ha, reported_unit=NutrientUnit.KG_PER_HA,
                reported_form=ChemicalForm.ELEMENTAL_N, normalized_value_kg_ha=req.nitrogen_kg_ha,
                conversion_applied="reported directly in kg/ha", conversion_verified=True,
                test_method=TestMethod.ALKALINE_PERMANGANATE
            ),
            phosphorus=NutrientMeasurement(
                nutrient="P", reported_value=req.phosphorus_kg_ha, reported_unit=NutrientUnit.KG_PER_HA,
                reported_form=ChemicalForm.ELEMENTAL_P, normalized_value_kg_ha=req.phosphorus_kg_ha,
                conversion_applied="reported directly in kg/ha", conversion_verified=True,
                test_method=TestMethod.OLSEN_SODIUM_BICARBONATE
            ),
            potassium=NutrientMeasurement(
                nutrient="K", reported_value=req.potassium_kg_ha, reported_unit=NutrientUnit.KG_PER_HA,
                reported_form=ChemicalForm.ELEMENTAL_K, normalized_value_kg_ha=req.potassium_kg_ha,
                conversion_applied="reported directly in kg/ha", conversion_verified=True,
                test_method=TestMethod.AMMONIUM_ACETATE_FLAME
            ),
            ph=req.ph or 7.0,
            organic_carbon_pct=req.organic_carbon_pct
        )

        pred_rec = intel_report.prediction_record
        comp_rec = comparator.record_and_log_comparison(
            prediction=pred_rec,
            actual_lab_report=actual_lab,
            comparison_id=f"COMP_{plot_id}_{req.retest_date.replace('-', '')}"
        )
        history = comparator.get_comparison_history()
        drift_n = SoilContinuousComparator.detect_systematic_drift(history, "Nitrogen")
        drift_alert = drift_n.get("interpretation") if drift_n.get("drift_alert") else None

        def _nutrient_comp_dto(nc, tol_kg_ha: float, actual_val: float, nutrient_name: str) -> SingleNutrientComparisonResponse:
            if nc is None:
                return SingleNutrientComparisonResponse(
                    nutrient=nutrient_name,
                    estimated_or_predicted_kg_ha=None,
                    actual_lab_kg_ha=actual_val,
                    absolute_error_kg_ha=None,
                    relative_error_pct=None,
                    provisional_tolerance_kg_ha=tol_kg_ha,
                    within_tolerance=False,
                    directional_bias="NOT_PREDICTED_ABSTAINED"
                )

            bias = "NOT_PREDICTED"
            if nc.predicted_kg_ha is not None and nc.actual_measured_kg_ha is not None:
                if nc.predicted_kg_ha > nc.actual_measured_kg_ha:
                    bias = "OVERESTIMATION"
                elif nc.predicted_kg_ha < nc.actual_measured_kg_ha:
                    bias = "UNDERESTIMATION"
                else:
                    bias = "ZERO_ERROR"

            return SingleNutrientComparisonResponse(
                nutrient=nc.nutrient,
                estimated_or_predicted_kg_ha=nc.predicted_kg_ha,
                actual_lab_kg_ha=nc.actual_measured_kg_ha,
                absolute_error_kg_ha=nc.absolute_error_kg_ha,
                relative_error_pct=nc.relative_error_pct,
                provisional_tolerance_kg_ha=tol_kg_ha,
                within_tolerance=nc.within_tolerance,
                directional_bias=bias
            )

        self.store.save()
        return ComparisonResponse(
            comparison_id=comp_rec.comparison_id,
            plot_id=comp_rec.plot_id,
            retest_date=comp_rec.lab_sample_date,
            days_elapsed=comp_rec.days_between_pred_and_sample,
            is_operational_prediction_evaluated=False,
            nitrogen_comparison=_nutrient_comp_dto(comp_rec.nitrogen_comparison, AgronomicTolerances.NITROGEN.absolute_tolerance, req.nitrogen_kg_ha, "Nitrogen"),
            phosphorus_comparison=_nutrient_comp_dto(comp_rec.phosphorus_comparison, AgronomicTolerances.PHOSPHORUS.absolute_tolerance, req.phosphorus_kg_ha, "Phosphorus"),
            potassium_comparison=_nutrient_comp_dto(comp_rec.potassium_comparison, AgronomicTolerances.POTASSIUM.absolute_tolerance, req.potassium_kg_ha, "Potassium"),
            all_tolerances_met=comp_rec.all_tolerances_met,
            drift_alert=drift_alert
        )

    # -----------------------------------------------------------------------
    # 7. Benchmarks & Discovery
    # -----------------------------------------------------------------------

    def get_benchmarks(self) -> BenchmarksResponse:
        return BenchmarksResponse(
            supported_fertilizers=sorted(list(FERTILIZER_GRADE_BENCHMARKS.keys())),
            supported_crops=sorted(list(CROP_REMOVAL_BENCHMARKS.keys())),
            tolerances={
                "N_tolerance_kg_ha": AgronomicTolerances.NITROGEN.absolute_tolerance,
                "P_tolerance_kg_ha": AgronomicTolerances.PHOSPHORUS.absolute_tolerance,
                "K_tolerance_kg_ha": AgronomicTolerances.POTASSIUM.absolute_tolerance,
                "target_pass_rate_pct": 80.0
            },
            provenance_types=[p.value for p in ProvenanceType]
        )
