"""
Soil Intelligence FastAPI Router
================================
Provides REST endpoints for soil report OCR ingestion, baseline confirmation,
multi-year agronomic event logging, depletion tracking, advisory generation,
ISO 32000-1 PDF report streaming, and continuous re-test evaluation.
"""

from __future__ import annotations
import os
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Header, Response, status, File, UploadFile, Form

from .schemas import (
    ParseReportRequest,
    ParseReportResponse,
    ManualCorrectionRequest,
    ConfirmBaselineReportRequest,
    FertilizerEventRequest,
    HarvestEventRequest,
    AgronomicEventResponse,
    PlotStatusResponse,
    CompareRetestRequest,
    ComparisonResponse,
    BenchmarksResponse,
    GenericMessageResponse
)
from .service import SoilIntelligenceService

soil_router = APIRouter(prefix="/soil", tags=["Soil Intelligence"])
_service = SoilIntelligenceService()

def _extract_user_id(authorization: Optional[str] = Header(None)) -> Optional[str]:
    """Extract authenticated and cryptographically verified user_id from Bearer token."""
    from backend.app.core.auth import extract_verified_user_id
    return extract_verified_user_id(authorization, required=False)



# ---------------------------------------------------------------------------
# Benchmarks & Metadata
# ---------------------------------------------------------------------------

@soil_router.get(
    "/benchmarks",
    response_model=BenchmarksResponse,
    summary="Get supported agronomic benchmarks and provisional tolerances"
)
def get_benchmarks():
    """Returns supported crops, fertilizer grades, provenance classifications, and tolerance targets."""
    return _service.get_benchmarks()


# ---------------------------------------------------------------------------
# Report Ingestion & Review
# ---------------------------------------------------------------------------

@soil_router.post(
    "/reports/parse",
    response_model=ParseReportResponse,
    summary="Parse raw soil test report text or OCR text stream"
)
def parse_soil_report(request: ParseReportRequest):
    """
    Parses unstructured Soil Health Card or laboratory certificate text,
    normalizes chemical forms (e.g. P2O5 to elemental P), checks agronomic
    bounds, and flags out-of-bounds fields for human review.
    """
    try:
        return _service.parse_report_text(request)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to parse report: {str(exc)}"
        )


@soil_router.post(
    "/reports/upload",
    response_model=ParseReportResponse,
    summary="Upload and parse a real Soil Health Card or laboratory test document (PDF, JPG, PNG)"
)
def upload_soil_report(
    file: UploadFile = File(..., description="Soil report file (.pdf, .jpg, .jpeg, .png)"),
    plot_id: Optional[str] = Form(None, description="Optional plot identifier to link"),
    farm_id: Optional[str] = Form(None, description="Optional farm identifier")
):
    """
    Accepts real Soil Health Card documents (PDF, JPG, PNG).
    Extracts text using pypdf / Windows native OCR, normalizes nutrients,
    and returns field-level confidence and review flags.
    """
    filename = file.filename or "unknown"
    ext = os.path.splitext(filename)[1].lower()
    if ext not in [".pdf", ".jpg", ".jpeg", ".png"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Accepted formats: PDF, JPG, JPEG, PNG."
        )

    # Server-side maximum file size limit: 5MB
    MAX_FILE_SIZE = 5 * 1024 * 1024
    try:
        contents = file.file.read()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read uploaded file: {str(exc)}"
        )

    if len(contents) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is empty (0 bytes)."
        )

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size ({len(contents) / (1024 * 1024):.2f} MB) exceeds the 5MB maximum limit."
        )

    try:
        return _service.parse_uploaded_file(
            file_bytes=contents,
            filename=filename,
            plot_id=plot_id,
            farm_id=farm_id
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to process uploaded report: {str(exc)}"
        )


@soil_router.post(
    "/reports/review/correct",
    response_model=GenericMessageResponse,
    summary="Submit agronomist correction for queued report"
)
def submit_manual_correction(request: ManualCorrectionRequest):
    """Submits manual correction for a report flagged for review and logs an immutable audit trail."""
    try:
        return _service.submit_manual_correction(request)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@soil_router.post(
    "/reports/confirm",
    response_model=GenericMessageResponse,
    summary="Confirm or register a physical laboratory baseline report"
)
def confirm_baseline_report(request: ConfirmBaselineReportRequest, authorization: Optional[str] = Header(None)):
    """
    Directly registers a verified laboratory baseline for a plot.
    Enforces MEASURED provenance and strict stoichiometric normalization.
    """
    user_id = _extract_user_id(authorization)
    try:
        return _service.confirm_baseline_report(request, owner_id=user_id)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


# ---------------------------------------------------------------------------
# Agronomic Events (Timeline Ledger)
# ---------------------------------------------------------------------------

@soil_router.post(
    "/plots/{plot_id}/events/fertilizer",
    response_model=AgronomicEventResponse,
    summary="Record mineral fertilizer or manure application"
)
def record_fertilizer_event(plot_id: str, request: FertilizerEventRequest, authorization: Optional[str] = Header(None)):
    """
    Records a fertilizer application event on the plot timeline.
    Calculates nutrient flux according to official grade benchmarks.
    """
    user_id = _extract_user_id(authorization)
    try:
        return _service.record_fertilizer_event(plot_id, request, user_id=user_id)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@soil_router.post(
    "/plots/{plot_id}/events/harvest",
    response_model=AgronomicEventResponse,
    summary="Record crop harvest removal event"
)
def record_harvest_event(plot_id: str, request: HarvestEventRequest, authorization: Optional[str] = Header(None)):
    """
    Records a crop harvest removal event. Calculates nutrient depletion using
    ICAR/Tandon uptake coefficients, biological N2 fixation credits for legumes,
    and residue retention adjustments.
    """
    user_id = _extract_user_id(authorization)
    try:
        return _service.record_harvest_event(plot_id, request, user_id=user_id)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@soil_router.get(
    "/plots/{plot_id}/events",
    response_model=List[AgronomicEventResponse],
    summary="List chronological agronomic flux events for a plot"
)
def list_plot_events(plot_id: str, authorization: Optional[str] = Header(None)):
    """Returns all recorded agronomic depletion and replenishment events for the plot."""
    user_id = _extract_user_id(authorization)
    try:
        return _service.list_plot_events(plot_id, user_id=user_id)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


# ---------------------------------------------------------------------------
# Plot Status, Balance & Advisory
# ---------------------------------------------------------------------------

@soil_router.get(
    "/plots/{plot_id}/status",
    response_model=PlotStatusResponse,
    summary="Get current nutrient ledger balance, prediction state & advisory"
)
def get_plot_status(
    plot_id: str,
    as_of_date: Optional[str] = Query(None, description="Target evaluation date (YYYY-MM-DD). Defaults to today."),
    authorization: Optional[str] = Header(None)
):
    """
    Returns the comprehensive digital status of the soil plot:
    - Baseline laboratory measurements
    - Dynamic mass-balance ledger (additions vs removals)
    - Operational prediction gate status (strictly blocked if empirical data gate closed)
    - Educational agronomic advisory bundle (actionable farmer advice)
    """
    user_id = _extract_user_id(authorization)
    try:
        return _service.get_plot_status(plot_id, as_of_date=as_of_date, user_id=user_id)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


# ---------------------------------------------------------------------------
# Printable PDF Report Streaming
# ---------------------------------------------------------------------------

@soil_router.get(
    "/plots/{plot_id}/report.pdf",
    summary="Download official ISO 32000-1 printable vector PDF report",
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "Returns a pure-Python ISO 32000-1 compliant vector PDF report."
        }
    }
)
def download_soil_report_pdf(
    plot_id: str,
    target_date: Optional[str] = Query(None, description="Target evaluation date (YYYY-MM-DD)"),
    authorization: Optional[str] = Header(None)
):
    """Generates and streams an ISO 32000-1 vector PDF Soil Intelligence Report directly in memory."""
    user_id = _extract_user_id(authorization)
    try:
        pdf_bytes = _service.generate_pdf_report(plot_id, target_date=target_date, user_id=user_id)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=soil_report_{plot_id}.pdf"
            }
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


# ---------------------------------------------------------------------------
# Continuous Evaluation & Comparison
# ---------------------------------------------------------------------------

@soil_router.post(
    "/plots/{plot_id}/compare",
    response_model=ComparisonResponse,
    summary="Ingest subsequent laboratory re-test for continuous drift evaluation"
)
def compare_retest(plot_id: str, request: CompareRetestRequest, authorization: Optional[str] = Header(None)):
    """
    Ingests a subsequent ground-truth laboratory test, compares it against the prior
    estimated state, checks provisional agronomic tolerances (N +/-25, P +/-5, K +/-30 kg/ha),
    and detects directional drift.
    """
    user_id = _extract_user_id(authorization)
    try:
        return _service.compare_retest(plot_id, request, user_id=user_id)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


# ---------------------------------------------------------------------------
# Management & Cleanup
# ---------------------------------------------------------------------------

@soil_router.delete(
    "/plots/{plot_id}",
    response_model=GenericMessageResponse,
    summary="Reset and delete a plot timeline"
)
def delete_plot(plot_id: str, authorization: Optional[str] = Header(None)):
    """Deletes the plot timeline from memory and persistent storage."""
    user_id = _extract_user_id(authorization)
    try:
        deleted = _service.store.delete_plot(plot_id, user_id=user_id)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Plot '{plot_id}' not found.")
    return GenericMessageResponse(
        status="deleted",
        message=f"Plot '{plot_id}' timeline has been reset.",
        plot_id=plot_id
    )
