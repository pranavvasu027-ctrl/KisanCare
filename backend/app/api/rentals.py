"""FastAPI router for KisanCare Agricultural Rental Marketplace."""

from __future__ import annotations
import logging
from typing import Dict, List, Optional, Any
import os
from fastapi import APIRouter, HTTPException, Query, Header, status

try:
    from app.rentals.schemas import (
        RentalListingCreate,
        PriceCalculationRequest,
        PriceCalculationResponse,
        AvailabilityCheckRequest,
        AvailabilityCheckResponse,
        BookingCreateRequest,
        BookingRecord,
        RentalReviewCreate,
        RecordExpenseRequest,
        DispatchStatus
    )
    from app.rentals.service import rental_service
    from app.rentals.geography import MAHARASHTRA_DIVISIONS
except ModuleNotFoundError:
    from backend.app.rentals.schemas import (
        RentalListingCreate,
        PriceCalculationRequest,
        PriceCalculationResponse,
        AvailabilityCheckRequest,
        AvailabilityCheckResponse,
        BookingCreateRequest,
        BookingRecord,
        RentalReviewCreate,
        RecordExpenseRequest,
        DispatchStatus
    )
    from backend.app.rentals.service import rental_service
    from backend.app.rentals.geography import MAHARASHTRA_DIVISIONS

logger = logging.getLogger("kisancare.api.rentals")
router = APIRouter(prefix="/rentals", tags=["Rental Marketplace"])


def _extract_user_id(authorization: Optional[str] = Header(None)) -> Optional[str]:
    """Extract authenticated user_id from Bearer token."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split("Bearer ", 1)[1].strip()
    if not token:
        return None

    url = os.environ.get("SUPABASE_URL")
    anon_key = os.environ.get("SUPABASE_ANON_KEY") or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if url and anon_key:
        try:
            from supabase import create_client
            sb = create_client(url, anon_key)
            u = sb.auth.get_user(token)
            if u and u.user:
                return str(u.user.id)
        except Exception:
            pass

    try:
        import jwt
        decoded = jwt.decode(token, options={"verify_signature": False})
        return decoded.get("sub") or decoded.get("user_id")
    except Exception:
        return None



@router.get("/geography", response_model=Dict[str, Any])
def get_maharashtra_geography():
    """Retrieve complete structured dataset of Maharashtra divisions, districts, and talukas."""
    return MAHARASHTRA_DIVISIONS


@router.get("/listings", response_model=List[Dict[str, Any]])
def list_listings(
    category: Optional[str] = Query(None, description="equipment, tractor, transport, labour, specialist"),
    subcategory: Optional[str] = Query(None),
    division: Optional[str] = Query(None, description="e.g. Amravati, Nagpur, Pune, Nashik, Chhatrapati Sambhajinagar, Konkan"),
    district: Optional[str] = Query(None, description="e.g. Akola, Pune, Kolhapur, Ratnagiri"),
    taluka: Optional[str] = Query(None, description="e.g. Akola, Baramati, Niphad"),
    query: Optional[str] = Query(None, description="Search query"),
    max_price: Optional[float] = Query(None, ge=0),
    billing_unit: Optional[str] = Query(None),
    verified_only: bool = Query(False),
    sort_by: str = Query("relevance", description="relevance, price_asc, price_desc, rating")
):
    """Discover rental listings with category, geography, price, and verification filters across Maharashtra."""
    return rental_service.get_listings(
        category=category,
        subcategory=subcategory,
        division=division,
        district=district,
        taluka=taluka,
        query=query,
        max_price=max_price,
        billing_unit=billing_unit,
        verified_only=verified_only,
        sort_by=sort_by
    )


@router.get("/listings/{listing_id}", response_model=Dict[str, Any])
def get_listing(listing_id: str):
    """Retrieve detailed information and specifications for a single rental listing."""
    listing = rental_service.get_listing_by_id(listing_id)
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Listing '{listing_id}' not found."
        )
    return listing


@router.post("/calculate-price", response_model=PriceCalculationResponse)
def calculate_price(req: PriceCalculationRequest):
    """Server-side itemized price calculation enforcing transparent terms, minimums, and platform fees."""
    try:
        return rental_service.calculate_price(req)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        logger.error("Price calculation failure: %s", exc, exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.post("/check-availability", response_model=AvailabilityCheckResponse)
def check_availability(req: AvailabilityCheckRequest):
    """Check whether a machine, vehicle, or team is available for the given window."""
    return rental_service.check_availability(req)


@router.post("/bookings", response_model=BookingRecord, status_code=status.HTTP_201_CREATED)
def create_booking(req: BookingCreateRequest, authorization: Optional[str] = Header(None)):
    """Create a persistent booking request with concurrency protection and transparent pricing."""
    user_id = _extract_user_id(authorization)
    if user_id:
        req.farmer_id = user_id
    elif not req.farmer_id:
        req.farmer_id = "FARMER_DEMO_DEFAULT"
    try:
        return rental_service.create_booking(req)
    except ValueError as exc:
        # Check if it's an availability conflict
        err_msg = str(exc)
        if "conflict" in err_msg.lower() or "already reserved" in err_msg.lower():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=err_msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)
    except Exception as exc:
        logger.error("Booking creation failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get("/bookings", response_model=List[BookingRecord])
def get_bookings(
    farmer_id: Optional[str] = Query(None),
    filter: str = Query("all", description="all, upcoming, active, history"),
    authorization: Optional[str] = Header(None)
):
    """Retrieve booking records for a farmer across lifecycle stages."""
    user_id = _extract_user_id(authorization)
    if user_id:
        if farmer_id and farmer_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Cannot query bookings belonging to another farmer."
            )
        farmer_id = user_id
    return rental_service.list_bookings(farmer_id=farmer_id, filter_type=filter)


@router.get("/bookings/{booking_id}", response_model=BookingRecord)
def get_booking(booking_id: str, authorization: Optional[str] = Header(None)):
    """Retrieve a single booking record by ID or booking reference."""
    record = rental_service.get_booking_by_id(booking_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Booking '{booking_id}' not found."
        )
    user_id = _extract_user_id(authorization)
    if user_id:
        rec_dict = record.model_dump() if hasattr(record, "model_dump") else (record.dict() if hasattr(record, "dict") else dict(record))
        if rec_dict.get("farmer_id") != user_id and rec_dict.get("provider_id") != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You do not have permission to view this booking."
            )
    return record


@router.post("/bookings/{booking_id}/cancel", response_model=BookingRecord)
def cancel_booking(booking_id: str, payload: Dict[str, str], authorization: Optional[str] = Header(None)):
    """Cancel a booking adhering to disclosed cancellation policy."""
    reason = payload.get("reason", "Cancelled by farmer")
    cancelled_by = payload.get("cancelled_by", "farmer")
    user_id = _extract_user_id(authorization)
    try:
        return rental_service.cancel_booking(booking_id, reason=reason, cancelled_by=cancelled_by, user_id=user_id)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


# -----------------------------------------------------------------------------
# Owner / Provider Dashboard Endpoints
# -----------------------------------------------------------------------------
@router.get("/owner/listings", response_model=List[Dict[str, Any]])
def get_owner_listings(provider_id: Optional[str] = Query(None), authorization: Optional[str] = Header(None)):
    """Retrieve all listings owned by the provider."""
    user_id = _extract_user_id(authorization)
    if user_id:
        if provider_id and provider_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Cannot query listings of another provider."
            )
        provider_id = user_id
    return rental_service.get_owner_listings(provider_id=provider_id)


@router.post("/owner/listings", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
def create_owner_listing(req: RentalListingCreate, provider_id: Optional[str] = Query(None), authorization: Optional[str] = Header(None)):
    """Create a new rental listing for machinery, equipment, transport, or labour."""
    user_id = _extract_user_id(authorization)
    if user_id:
        provider_id = user_id
    try:
        return rental_service.create_listing(req, provider_id=provider_id)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/owner/requests", response_model=List[BookingRecord])
def get_owner_requests(provider_id: Optional[str] = Query(None), authorization: Optional[str] = Header(None)):
    """Retrieve incoming and active booking requests for the owner's listings."""
    user_id = _extract_user_id(authorization)
    if user_id:
        if provider_id and provider_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Cannot query requests of another provider."
            )
        provider_id = user_id
    return rental_service.get_owner_requests(provider_id=provider_id)


@router.post("/owner/bookings/{booking_id}/respond", response_model=BookingRecord)
def respond_booking(booking_id: str, payload: Dict[str, str], authorization: Optional[str] = Header(None)):
    """Owner accepts (confirms) or rejects an incoming booking request."""
    action = payload.get("action")  # 'confirm' or 'reject'
    reason = payload.get("reason")
    if not action:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing required field: action ('confirm' or 'reject').")
    user_id = _extract_user_id(authorization)
    try:
        return rental_service.respond_to_booking(booking_id, action=action, reason=reason, provider_id=user_id)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/owner/bookings/{booking_id}/dispatch", response_model=BookingRecord)
def update_dispatch(booking_id: str, payload: Dict[str, str], authorization: Optional[str] = Header(None)):
    """Update dispatch or execution status (ready, dispatched, arrived, working, completed)."""
    dispatch_status = payload.get("dispatch_status")
    if not dispatch_status:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing dispatch_status.")
    user_id = _extract_user_id(authorization)
    try:
        return rental_service.update_dispatch_status(booking_id, dispatch_status=dispatch_status, provider_id=user_id)  # type: ignore
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


# -----------------------------------------------------------------------------
# Farm Economics & Memory Link
# -----------------------------------------------------------------------------
@router.post("/bookings/{booking_id}/record-expense", response_model=Dict[str, Any])
def record_expense(booking_id: str, req: RecordExpenseRequest, authorization: Optional[str] = Header(None)):
    """Link completed rental expense to the farmer's Digital Twin field and season."""
    user_id = _extract_user_id(authorization)
    b = rental_service.get_booking_by_id(booking_id)
    if not b:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Booking '{booking_id}' not found.")
    rec_dict = b.model_dump() if hasattr(b, "model_dump") else (b.dict() if hasattr(b, "dict") else dict(b))
    if user_id and rec_dict.get("farmer_id") and rec_dict.get("farmer_id") != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: Cannot record expenses for a booking you do not own.")
    try:
        return rental_service.record_expense_to_farm(booking_id, req)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


# -----------------------------------------------------------------------------
# Market Rate Benchmarks & Reviews
# -----------------------------------------------------------------------------
@router.get("/market-rates", response_model=List[Dict[str, Any]])
def get_market_rates(
    category: Optional[str] = Query(None),
    district: Optional[str] = Query(None, description="e.g. Akola, Pune, Kolhapur or None for statewide")
):
    """Retrieve verified indicative custom-hiring benchmarks (Dr. PDKV Akola, MPKV, VNMKV, BSKKV & Maharashtra CHC)."""
    return rental_service.get_market_benchmarks(category=category, district=district)


@router.post("/reviews", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
def submit_review(req: RentalReviewCreate, authorization: Optional[str] = Header(None)):
    """Submit a verified rating and review for an eligible completed rental."""
    user_id = _extract_user_id(authorization)
    if user_id:
        req.farmer_id = user_id
    try:
        return rental_service.add_review(req)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/recommendations", response_model=Dict[str, Any])
def get_recommendations(
    crop: str = Query("Cotton"),
    acreage: float = Query(4.5, gt=0),
    task: Optional[str] = Query(None)
):
    """Get smart agricultural machinery and labour recommendations tailored to crop and field size."""
    return rental_service.get_smart_recommendations(crop=crop, acreage=acreage, task=task)
