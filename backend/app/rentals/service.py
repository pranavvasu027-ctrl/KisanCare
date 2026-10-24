"""Agricultural Rental Marketplace Service Engine.

Implements concurrency-safe availability validation, rigorous server-side price calculation,
booking lifecycle management, owner dispatch controls, and farm economics synchronization.
"""

from __future__ import annotations
import json
import logging
import os
import threading
import uuid
from datetime import datetime, date, time, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

try:
    from app.rentals.schemas import (
        PriceCalculationRequest,
        PriceCalculationResponse,
        PriceItemBreakdown,
        AvailabilityCheckRequest,
        AvailabilityCheckResponse,
        BookingCreateRequest,
        BookingRecord,
        BookingStatus,
        DispatchStatus,
        RentalListingCreate,
        RentalReviewCreate,
        RecordExpenseRequest
    )
    from app.rentals.seed_data import (
        SEED_PROVIDERS,
        SEED_LISTINGS,
        SEED_MARKET_BENCHMARKS,
        SEED_INITIAL_BOOKINGS
    )
except ModuleNotFoundError:
    from backend.app.rentals.schemas import (
        PriceCalculationRequest,
        PriceCalculationResponse,
        PriceItemBreakdown,
        AvailabilityCheckRequest,
        AvailabilityCheckResponse,
        BookingCreateRequest,
        BookingRecord,
        BookingStatus,
        DispatchStatus,
        RentalListingCreate,
        RentalReviewCreate,
        RecordExpenseRequest
    )
    from backend.app.rentals.seed_data import (
        SEED_PROVIDERS,
        SEED_LISTINGS,
        SEED_MARKET_BENCHMARKS,
        SEED_INITIAL_BOOKINGS
    )

logger = logging.getLogger("kisancare.rentals.service")

# Storage directory for local JSON persistence
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
RENTALS_FILE = DATA_DIR / "rentals_store.json"


class RentalMarketplaceService:
    """Thread-safe rental engine with local file persistence and Supabase compatibility."""

    def __init__(self):
        self._lock = threading.RLock()
        self._providers: Dict[str, Dict[str, Any]] = {}
        self._listings: Dict[str, Dict[str, Any]] = {}
        self._bookings: Dict[str, Dict[str, Any]] = {}
        self._benchmarks: List[Dict[str, Any]] = []
        self._reviews: List[Dict[str, Any]] = []
        self._load_or_seed()

    def _load_or_seed(self):
        """Load state from persistent file or initialize with authentic Akola/Vidarbha seed data."""
        with self._lock:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            if RENTALS_FILE.exists():
                try:
                    with open(RENTALS_FILE, "r", encoding="utf-8") as f:
                        payload = json.load(f)
                        self._providers = {p["id"]: p for p in payload.get("providers", [])}
                        self._listings = {l["id"]: l for l in payload.get("listings", [])}
                        self._bookings = {b["id"]: b for b in payload.get("bookings", [])}
                        self._benchmarks = payload.get("benchmarks", SEED_MARKET_BENCHMARKS)
                        self._reviews = payload.get("reviews", [])
                        logger.info("Loaded %d listings, %d bookings from %s", len(self._listings), len(self._bookings), RENTALS_FILE)
                        return
                except Exception as exc:
                    logger.warning("Failed to parse %s (%s). Re-seeding with authentic Akola data.", RENTALS_FILE, exc)

            # Initialize seed data
            self._providers = {p["id"]: dict(p) for p in SEED_PROVIDERS}
            self._listings = {l["id"]: dict(l) for l in SEED_LISTINGS}
            self._bookings = {b["id"]: dict(b) for b in SEED_INITIAL_BOOKINGS}
            self._benchmarks = [dict(b) for b in SEED_MARKET_BENCHMARKS]
            self._reviews = [
                {
                    "id": "REV_01",
                    "booking_id": "BKG_2026_002",
                    "listing_id": "LIST_EQP_02",
                    "farmer_id": "FARMER_RAMESH_PATIL",
                    "farmer_name": "Ramesh Patil",
                    "rating": 5,
                    "review_text": "Excellent seed drill. Sowed 5 acres of gram in one afternoon with accurate seed depth.",
                    "created_at": "2026-10-18T18:00:00Z"
                }
            ]
            self._save_unlocked()

    def _save_unlocked(self):
        """Write current state to file. Must be called while self._lock is acquired."""
        try:
            payload = {
                "providers": list(self._providers.values()),
                "listings": list(self._listings.values()),
                "bookings": list(self._bookings.values()),
                "benchmarks": self._benchmarks,
                "reviews": self._reviews,
                "last_persisted": datetime.now().isoformat()
            }
            with open(RENTALS_FILE, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, default=str)
        except Exception as exc:
            logger.error("Failed to persist rentals to %s: %s", RENTALS_FILE, exc)

    # -------------------------------------------------------------------------
    # Listing Discovery & Filtering
    # -------------------------------------------------------------------------
    def get_listings(
        self,
        category: Optional[str] = None,
        subcategory: Optional[str] = None,
        division: Optional[str] = None,
        district: Optional[str] = None,
        taluka: Optional[str] = None,
        query: Optional[str] = None,
        max_price: Optional[float] = None,
        billing_unit: Optional[str] = None,
        verified_only: bool = False,
        sort_by: str = "relevance"
    ) -> List[Dict[str, Any]]:
        """Filter and sort active rental listings across Maharashtra."""
        with self._lock:
            results = []
            for l in self._listings.values():
                if not l.get("is_active", True):
                    continue
                if category and l.get("category") != category:
                    continue
                if subcategory and l.get("subcategory") != subcategory:
                    continue
                if division and l.get("division", "").lower() != division.lower():
                    continue
                if district and l.get("district", "").lower() != district.lower():
                    continue
                if taluka and l.get("taluka", "").lower() != taluka.lower():
                    continue
                if max_price and float(l.get("price", 0)) > max_price:
                    continue
                if billing_unit and l.get("billing_unit") != billing_unit:
                    continue

                provider = self._providers.get(l["provider_id"], {})
                if verified_only and not provider.get("verified", False):
                    continue

                if query:
                    q = query.lower()
                    title = l.get("title", "").lower()
                    desc = l.get("description", "").lower()
                    t_name = l.get("taluka", "").lower()
                    d_name = l.get("district", "").lower()
                    prov_name = provider.get("business_name", "").lower()
                    if not (q in title or q in desc or q in t_name or q in d_name or q in prov_name):
                        continue

                # Attach provider summary
                item = dict(l)
                item["provider"] = {
                    "id": provider.get("id", l["provider_id"]),
                    "business_name": provider.get("business_name", "Local Agri Provider"),
                    "contact_name": provider.get("contact_name", "Manager"),
                    "phone": provider.get("phone", ""),
                    "division": provider.get("division", l.get("division", "Amravati")),
                    "district": provider.get("district", l.get("district", "Akola")),
                    "taluka": provider.get("taluka", l.get("taluka", "")),
                    "village": provider.get("village", l.get("village", "")),
                    "verified": provider.get("verified", False),
                    "verification_badge": provider.get("verification_badge", "unverified"),
                    "rating": provider.get("rating", 4.5),
                    "review_count": provider.get("review_count", 0),
                    "credentials": provider.get("credentials")
                }
                results.append(item)

            # Sorting
            if sort_by == "price_asc":
                results.sort(key=lambda x: x.get("price", 0))
            elif sort_by == "price_desc":
                results.sort(key=lambda x: x.get("price", 0), reverse=True)
            elif sort_by == "rating":
                results.sort(key=lambda x: x.get("rating", 0), reverse=True)

            return results

    def get_listing_by_id(self, listing_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            l = self._listings.get(listing_id)
            if not l:
                return None
            item = dict(l)
            provider = self._providers.get(l["provider_id"], {})
            item["provider"] = {
                "id": provider.get("id", l["provider_id"]),
                "business_name": provider.get("business_name", "Local Agri Provider"),
                "contact_name": provider.get("contact_name", "Manager"),
                "phone": provider.get("phone", ""),
                "division": provider.get("division", l.get("division", "Amravati")),
                "district": provider.get("district", l.get("district", "Akola")),
                "taluka": provider.get("taluka", l.get("taluka", "")),
                "village": provider.get("village", l.get("village", "")),
                "verified": provider.get("verified", False),
                "verification_badge": provider.get("verification_badge", "unverified"),
                "rating": provider.get("rating", 4.5),
                "review_count": provider.get("review_count", 0),
                "credentials": provider.get("credentials")
            }
            return item

    # -------------------------------------------------------------------------
    # Server-Side Price Calculation Engine
    # -------------------------------------------------------------------------
    def calculate_price(self, req: PriceCalculationRequest) -> PriceCalculationResponse:
        """Calculate itemized price strictly according to commercial terms and unit rules."""
        listing = self.get_listing_by_id(req.listing_id)
        if not listing:
            raise ValueError(f"Listing {req.listing_id} not found.")

        unit_price = float(listing["price"])
        billing_unit = listing["billing_unit"]
        min_duration = int(listing.get("min_duration", 1))
        min_charge = float(listing.get("min_charge", 0.0))

        # Enforce billable duration/quantity
        effective_duration = max(req.duration, float(min_duration))
        quantity = max(1, req.quantity)

        # 1. Base rental calculation
        calc_desc = f"₹{unit_price:.0f} × {effective_duration:.1f} {billing_unit.replace('per_', '')}"
        if billing_unit in ("per_hour", "per_operating_hour"):
            base_charge = unit_price * effective_duration
            calc_desc = f"₹{unit_price:.0f}/hr × {effective_duration:.1f} hrs"
        elif billing_unit in ("per_day", "per_half_day"):
            base_charge = unit_price * effective_duration
            calc_desc = f"₹{unit_price:.0f}/day × {effective_duration:.1f} days"
        elif billing_unit == "per_team_day":
            base_charge = unit_price * effective_duration * quantity
            calc_desc = f"₹{unit_price:.0f}/team-day × {effective_duration:.1f} days ({quantity} team{'s' if quantity > 1 else ''})"
        elif billing_unit == "per_acre":
            area = req.acreage if req.acreage and req.acreage > 0 else effective_duration
            base_charge = unit_price * area
            calc_desc = f"₹{unit_price:.0f}/acre × {area:.1f} acres"
        elif billing_unit in ("per_worker_day", "per_worker_hour"):
            base_charge = unit_price * effective_duration * quantity
            calc_desc = f"₹{unit_price:.0f} × {quantity} workers × {effective_duration:.1f} days"
        elif billing_unit == "per_sample":
            samples = quantity if quantity > 1 else (req.acreage if req.acreage and req.acreage > 0 else 1)
            base_charge = unit_price * samples
            calc_desc = f"₹{unit_price:.0f}/sample × {samples:.0f} soil samples"
        elif billing_unit in ("per_visit", "per_consultation"):
            base_charge = unit_price * effective_duration
            calc_desc = f"₹{unit_price:.0f}/session × {effective_duration:.0f} visit(s)"
        elif billing_unit in ("per_trip", "per_km"):
            base_charge = unit_price * effective_duration
            calc_desc = f"₹{unit_price:.0f}/trip × {effective_duration:.0f} trip(s)"
        else:
            base_charge = unit_price * effective_duration

        if base_charge < min_charge:
            base_charge = min_charge
            calc_desc += f" (Min. contract charge ₹{min_charge:.0f} applied)"

        breakdown: List[PriceItemBreakdown] = [
            PriceItemBreakdown(
                label=f"Base Rental ({billing_unit.replace('_', ' ').title()})",
                amount=round(base_charge, 2),
                description=calc_desc
            )
        ]

        # 2. Operator charge
        operator_charge = 0.0
        specs = listing.get("specs", {})
        if not specs.get("operator_included", False) and req.include_operator:
            daily_fee = req.operator_daily_fee if req.operator_daily_fee > 0 else 600.0
            operator_charge = daily_fee * max(1.0, req.duration if billing_unit == "per_day" else 1.0)
            breakdown.append(PriceItemBreakdown(
                label="Certified Operator / Driver",
                amount=round(operator_charge, 2),
                description="Daily skilled machinery driver wage"
            ))

        # 3. Transport / Mobilization
        transport_charge = 0.0
        terms = listing.get("terms", {})
        delivery_fee = float(terms.get("delivery_fee", 0.0))
        extra_km_rate = float(terms.get("extra_km_rate", 25.0))
        included_km = float(terms.get("delivery_included_km", 5.0))

        if req.include_delivery or delivery_fee > 0:
            dist = req.distance_km if req.distance_km > 0 else 5.0
            extra_dist = max(0.0, dist - included_km)
            transport_charge = delivery_fee + (extra_dist * extra_km_rate)
            breakdown.append(PriceItemBreakdown(
                label="Mobilization / Transport to Farm Gate",
                amount=round(transport_charge, 2),
                description=f"Base mobilization ₹{delivery_fee:.0f} + {extra_dist:.1f} km at ₹{extra_km_rate:.0f}/km"
            ))

        # 4. Add-ons
        add_ons_charge = 0.0
        for addon in req.add_ons:
            addon_amt = float(addon.get("amount", 0.0))
            if addon_amt > 0:
                add_ons_charge += addon_amt
                breakdown.append(PriceItemBreakdown(
                    label=addon.get("label", "Optional Implement / Tool Add-on"),
                    amount=round(addon_amt, 2),
                    description=addon.get("description", "Selected add-on service")
                ))

        # 5. Platform fee (Disclosed transparently: flat ₹50 or 2%)
        platform_fee = 50.0
        breakdown.append(PriceItemBreakdown(
            label="KisanCare Platform & Support Fee",
            amount=platform_fee,
            description="Verified provider guarantee, dispute coverage & scheduling"
        ))

        # 6. Taxes (Agri custom hiring services exempt from GST under Notification 12/2017 - Central Tax)
        taxes = 0.0
        discounts = 0.0

        estimated_total = round(base_charge + operator_charge + transport_charge + add_ons_charge + platform_fee + taxes - discounts, 2)

        # PDKV benchmark comparison text
        benchmark_note = terms.get("pdkv_benchmark_source")

        return PriceCalculationResponse(
            listing_id=req.listing_id,
            billing_unit=billing_unit,
            unit_price=unit_price,
            duration=effective_duration,
            acreage=req.acreage or 0.0,
            quantity=quantity,
            base_rental_charge=round(base_charge, 2),
            operator_charge=round(operator_charge, 2),
            transport_charge=round(transport_charge, 2),
            add_ons_charge=round(add_ons_charge, 2),
            platform_fee=round(platform_fee, 2),
            taxes=round(taxes, 2),
            discounts=round(discounts, 2),
            estimated_total=estimated_total,
            breakdown=breakdown,
            currency="INR",
            pdkv_benchmark_comparison=benchmark_note
        )

    # -------------------------------------------------------------------------
    # Concurrency-Safe Availability Check
    # -------------------------------------------------------------------------
    def check_availability(self, req: AvailabilityCheckRequest) -> AvailabilityCheckResponse:
        """Check if listing has conflicting bookings for requested date/time window."""
        listing = self.get_listing_by_id(req.listing_id)
        if not listing:
            return AvailabilityCheckResponse(
                listing_id=req.listing_id,
                is_available=False,
                conflict_count=0,
                message="Listing not found."
            )

        with self._lock:
            conflicts = []
            req_start = req.start_date
            req_end = req.end_date

            for b in self._bookings.values():
                if b["listing_id"] != req.listing_id:
                    continue
                # Active or confirmed bookings block the resource
                if b["status"] in ("confirmed", "in_progress", "pending_confirmation"):
                    b_start = b["start_date"]
                    b_end = b["end_date"]
                    # Overlap condition: startA <= endB and startB <= endA
                    if req_start <= b_end and b_start <= req_end:
                        conflicts.append(b)

            is_available = len(conflicts) == 0
            if is_available:
                msg = "Resource is available for the requested slot."
            else:
                msg = f"Resource is booked for {len(conflicts)} conflicting slot(s) between {req_start} and {req_end}."

            return AvailabilityCheckResponse(
                listing_id=req.listing_id,
                is_available=is_available,
                conflict_count=len(conflicts),
                message=msg
            )

    # -------------------------------------------------------------------------
    # Booking Engine & Concurrency Safety
    # -------------------------------------------------------------------------
    def create_booking(self, req: BookingCreateRequest) -> BookingRecord:
        """Create a booking with atomic availability check and price calculation."""
        with self._lock:
            listing = self._listings.get(req.listing_id)
            if not listing:
                raise ValueError(f"Listing {req.listing_id} not found.")

            # Validate date sequence
            if req.end_date < req.start_date:
                raise ValueError("End date cannot be earlier than start date.")

            # Check overlap concurrency safely
            for b in self._bookings.values():
                if b["listing_id"] == req.listing_id and b["status"] in ("confirmed", "in_progress", "pending_confirmation"):
                    if req.start_date <= b["end_date"] and b["start_date"] <= req.end_date:
                        raise ValueError(
                            f"Booking conflict: The resource is already reserved by confirmed booking {b['booking_reference']} from {b['start_date']} to {b['end_date']}."
                        )

            # Perform price calculation
            calc_req = PriceCalculationRequest(
                listing_id=req.listing_id,
                duration=req.duration,
                acreage=req.acreage,
                quantity=req.quantity,
                include_operator=req.include_operator,
                include_delivery=req.include_delivery,
                delivery_address=req.delivery_address
            )
            price_res = self.calculate_price(calc_req)

            # Generate persistent reference ID: KCR-BKG-YYYYMMDD-XXXX
            today_str = datetime.now().strftime("%Y%m%d")
            suffix = uuid.uuid4().hex[:4].upper()
            ref_id = f"KCR-BKG-{today_str}-{suffix}"
            booking_id = f"BKG_{uuid.uuid4().hex[:8]}"

            provider = self._providers.get(listing["provider_id"], {})

            record_dict = {
                "id": booking_id,
                "booking_reference": ref_id,
                "listing_id": req.listing_id,
                "listing_title": listing.get("title", ""),
                "category": listing.get("category", "equipment"),
                "provider_id": listing["provider_id"],
                "provider_name": provider.get("business_name", "Local Agri Provider"),
                "provider_phone": provider.get("phone", ""),
                "farmer_id": req.farmer_id or "FARMER_DEMO_DEFAULT",
                "farmer_name": req.farmer_name,
                "farmer_phone": req.farmer_phone,
                "farm_id": req.farm_id,
                "field_id": req.field_id,
                "field_name": req.field_name,
                "crop_name": req.crop_name,
                "farm_location": req.farm_location,
                "start_date": req.start_date,
                "end_date": req.end_date,
                "start_time": req.start_time,
                "duration": price_res.duration,
                "billing_unit": price_res.billing_unit,
                "acreage": price_res.acreage,
                "quantity": price_res.quantity,
                "unit_price": price_res.unit_price,
                "base_rental_charge": price_res.base_rental_charge,
                "operator_charge": price_res.operator_charge,
                "transport_charge": price_res.transport_charge,
                "add_ons_charge": price_res.add_ons_charge,
                "platform_fee": price_res.platform_fee,
                "taxes": price_res.taxes,
                "discounts": price_res.discounts,
                "total_amount": price_res.estimated_total,
                "payment_method": req.payment_method,
                "payment_status": "pay_on_delivery" if req.payment_method == "pay_on_service" else "pending",
                "status": "pending_confirmation",
                "dispatch_status": "ready",
                "cancellation_reason": None,
                "rejection_reason": None,
                "cancelled_by": None,
                "recorded_in_economics": False,
                "farm_expense_id": None,
                "is_demo": listing.get("is_demo", True),
                "notes": req.notes,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }

            self._bookings[booking_id] = record_dict
            self._save_unlocked()
            logger.info("Created booking %s (%s) for listing %s", booking_id, ref_id, req.listing_id)
            return BookingRecord(**record_dict)

    def get_booking_by_id(self, booking_id: str) -> Optional[BookingRecord]:
        with self._lock:
            b = self._bookings.get(booking_id)
            if not b:
                # Also allow lookup by booking_reference
                for item in self._bookings.values():
                    if item.get("booking_reference") == booking_id:
                        return BookingRecord(**item)
                return None
            return BookingRecord(**b)

    def list_bookings(self, farmer_id: Optional[str] = None, filter_type: str = "all") -> List[BookingRecord]:
        """List bookings filtered by state: upcoming, active, history, or all."""
        with self._lock:
            results = []
            today_str = date.today().isoformat()

            for b in self._bookings.values():
                if farmer_id and b.get("farmer_id") != farmer_id:
                    continue

                status = b.get("status")
                start = b.get("start_date")
                end = b.get("end_date")

                if filter_type == "upcoming":
                    if status in ("confirmed", "pending_confirmation") and start >= today_str:
                        results.append(BookingRecord(**b))
                elif filter_type == "active":
                    if status in ("in_progress", "confirmed") and start <= today_str <= end:
                        results.append(BookingRecord(**b))
                elif filter_type == "history":
                    if status in ("completed", "cancelled", "rejected") or (status == "confirmed" and end < today_str):
                        results.append(BookingRecord(**b))
                else:
                    results.append(BookingRecord(**b))

            results.sort(key=lambda x: x.start_date, reverse=True)
            return results

    def cancel_booking(self, booking_id: str, reason: str, cancelled_by: str = "farmer", user_id: Optional[str] = None) -> BookingRecord:
        """Authorized cancellation following fair terms with user ownership verification."""
        with self._lock:
            b = self._bookings.get(booking_id)
            if not b:
                raise ValueError(f"Booking {booking_id} not found.")

            if user_id:
                # If farmer cancelling, ensure they own the booking
                if cancelled_by == "farmer" and b.get("farmer_id") and b.get("farmer_id") != user_id:
                    raise PermissionError(f"Access denied: user {user_id} does not own booking {booking_id}.")
                # If provider cancelling, ensure they own the listing/booking
                elif cancelled_by == "provider" and b.get("provider_id") and b.get("provider_id") != user_id:
                    raise PermissionError(f"Access denied: provider {user_id} is not the owner of booking {booking_id}.")

            if b["status"] in ("completed", "cancelled", "rejected"):
                raise ValueError(f"Cannot cancel booking with status '{b['status']}'.")

            b["status"] = "cancelled"
            b["cancellation_reason"] = reason
            b["cancelled_by"] = cancelled_by
            b["updated_at"] = datetime.now().isoformat()

            self._save_unlocked()
            logger.info("Cancelled booking %s by %s. Reason: %s", booking_id, cancelled_by, reason)
            return BookingRecord(**b)

    # -------------------------------------------------------------------------
    # Owner & Provider Controls
    # -------------------------------------------------------------------------
    def get_owner_listings(self, provider_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._lock:
            prov_id = provider_id or "PROV_AKOLA_01"
            return [l for l in self._listings.values() if l.get("provider_id") == prov_id]

    def get_owner_requests(self, provider_id: Optional[str] = None) -> List[BookingRecord]:
        with self._lock:
            prov_id = provider_id or "PROV_AKOLA_01"
            return [BookingRecord(**b) for b in self._bookings.values() if b.get("provider_id") == prov_id]

    def respond_to_booking(self, booking_id: str, action: str, reason: Optional[str] = None, provider_id: Optional[str] = None) -> BookingRecord:
        """Owner confirms or rejects an incoming booking request with provider ownership check."""
        with self._lock:
            b = self._bookings.get(booking_id)
            if not b:
                raise ValueError(f"Booking {booking_id} not found.")

            if provider_id and b.get("provider_id") and b.get("provider_id") != provider_id:
                raise PermissionError(f"Access denied: provider {provider_id} does not own listing for booking {booking_id}.")

            if b["status"] != "pending_confirmation":
                raise ValueError(f"Booking is in '{b['status']}' state; only pending bookings can be confirmed/rejected.")

            if action == "confirm":
                b["status"] = "confirmed"
                b["dispatch_status"] = "ready"
            elif action == "reject":
                b["status"] = "rejected"
                b["rejection_reason"] = reason or "Provider unavailable at requested time."
            else:
                raise ValueError("Action must be 'confirm' or 'reject'.")

            b["updated_at"] = datetime.now().isoformat()
            self._save_unlocked()
            return BookingRecord(**b)

    def update_dispatch_status(self, booking_id: str, dispatch_status: DispatchStatus, provider_id: Optional[str] = None) -> BookingRecord:
        """Owner updates operational dispatch status: ready -> dispatched -> arrived -> working -> completed with provider ownership check."""
        with self._lock:
            b = self._bookings.get(booking_id)
            if not b:
                raise ValueError(f"Booking {booking_id} not found.")

            if provider_id and b.get("provider_id") and b.get("provider_id") != provider_id:
                raise PermissionError(f"Access denied: provider {provider_id} does not own listing for booking {booking_id}.")

            b["dispatch_status"] = dispatch_status
            if dispatch_status in ("dispatched", "arrived", "working"):
                b["status"] = "in_progress"
            elif dispatch_status == "completed":
                b["status"] = "completed"
                b["payment_status"] = "paid"

            b["updated_at"] = datetime.now().isoformat()
            self._save_unlocked()
            return BookingRecord(**b)

    def create_listing(self, req: RentalListingCreate, provider_id: Optional[str] = None) -> Dict[str, Any]:
        """Create new equipment/labour listing for an authorized provider."""
        with self._lock:
            prov_id = provider_id or "PROV_AKOLA_01"
            listing_id = f"LIST_{uuid.uuid4().hex[:8].upper()}"

            new_item = req.model_dump()
            new_item["id"] = listing_id
            new_item["provider_id"] = prov_id
            new_item["created_at"] = datetime.now().isoformat()
            new_item["updated_at"] = datetime.now().isoformat()
            new_item["rating"] = 5.0
            new_item["review_count"] = 0

            self._listings[listing_id] = new_item
            self._save_unlocked()
            logger.info("Provider %s created listing %s (%s)", prov_id, listing_id, req.title)
            return new_item

    # -------------------------------------------------------------------------
    # Farm Economics & Memory Synchronization
    # -------------------------------------------------------------------------
    def record_expense_to_farm(self, booking_id: str, req: RecordExpenseRequest) -> Dict[str, Any]:
        """Record completed rental cost against the farmer's Digital Twin field and season."""
        with self._lock:
            b = self._bookings.get(booking_id)
            if not b:
                raise ValueError(f"Booking {booking_id} not found.")

            if b["status"] != "completed":
                raise ValueError("Expenses can only be recorded for 'completed' rentals.")

            if b.get("recorded_in_economics"):
                raise ValueError(f"Expense for booking {booking_id} has already been recorded (Expense ID: {b.get('farm_expense_id')}).")

            expense_id = f"EXP_{uuid.uuid4().hex[:8]}"
            b["recorded_in_economics"] = True
            b["farm_expense_id"] = expense_id
            b["updated_at"] = datetime.now().isoformat()
            self._save_unlocked()

            is_demo = b.get("is_demo", True)
            return {
                "status": "recorded",
                "expense_id": expense_id,
                "booking_reference": b["booking_reference"],
                "farm_id": req.farm_id,
                "field_id": req.field_id,
                "season": req.season,
                "crop": req.crop,
                "category": req.expense_category,
                "amount": b["total_amount"],
                "item_name": b["listing_title"],
                "is_demo": is_demo,
                "isolated_from_production": is_demo,
                "timestamp": datetime.now().isoformat()
            }

    # -------------------------------------------------------------------------
    # Reference Market Rates & Smart Recommendations
    # -------------------------------------------------------------------------
    def get_market_benchmarks(self, category: Optional[str] = None, district: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._lock:
            results = self._benchmarks
            if category:
                results = [r for r in results if r.get("category") == category]
            if district:
                results = [r for r in results if r.get("district", "").lower() == district.lower()]
            return results

    def add_review(self, rev: RentalReviewCreate) -> Dict[str, Any]:
        with self._lock:
            b = self._bookings.get(rev.booking_id)
            if not b:
                raise ValueError(f"Booking {rev.booking_id} not found.")
            if b["status"] != "completed":
                raise ValueError("Reviews can only be submitted after rental completion.")

            # Check for duplicate review on same booking
            for r in self._reviews:
                if r.get("booking_id") == rev.booking_id:
                    raise ValueError(f"A review has already been submitted for booking {rev.booking_id}.")

            if rev.farmer_id and b.get("farmer_id") and b.get("farmer_id") != rev.farmer_id:
                raise PermissionError(f"Access denied: user {rev.farmer_id} is not the farmer who booked {rev.booking_id}.")

            review_id = f"REV_{uuid.uuid4().hex[:8]}"
            review_obj = {
                "id": review_id,
                "booking_id": rev.booking_id,
                "listing_id": rev.listing_id,
                "farmer_id": rev.farmer_id or b.get("farmer_id", "FARMER_RAMESH_PATIL"),
                "farmer_name": rev.farmer_name,
                "rating": rev.rating,
                "review_text": rev.review_text,
                "created_at": datetime.now().isoformat()
            }
            self._reviews.append(review_obj)

            # Update listing rating
            listing_revs = [r["rating"] for r in self._reviews if r.get("listing_id") == rev.listing_id]
            if listing_revs and rev.listing_id in self._listings:
                avg_rating = round(sum(listing_revs) / len(listing_revs), 1)
                self._listings[rev.listing_id]["rating"] = avg_rating
                self._listings[rev.listing_id]["review_count"] = len(listing_revs)

            self._save_unlocked()
            return review_obj

    def get_smart_recommendations(self, crop: str = "Cotton", acreage: float = 4.5, task: Optional[str] = None) -> Dict[str, Any]:
        """Recommend equipment packages based on authentic agronomic task and field acreage."""
        crop_lower = crop.lower()
        recs = []

        if "cotton" in crop_lower:
            recs = [
                {
                    "task": "Inter-Row Weeding & Aeration",
                    "recommended_equipment": "9-Tyne Cultivator or 4-Worker Weeding Team",
                    "best_value_listing_id": "LIST_EQP_01",
                    "rationale": f"For {acreage} acres of Cotton, tractor cultivator covers land in ~4 hours vs manual team (1-2 days).",
                    "estimated_machinery_cost": 600.0 * 1,
                    "estimated_labour_cost": 1600.0 * 2,
                    "savings_percent": 45
                },
                {
                    "task": "Protective Pest & Bollworm Spraying",
                    "recommended_equipment": "Tractor-Mounted 600L Boom Sprayer or Battery Sprayer Technician",
                    "best_value_listing_id": "LIST_EQP_03",
                    "rationale": "High-pressure boom sprayer achieves uniform canopy penetration within 1 hour.",
                    "estimated_machinery_cost": 350.0 * acreage,
                    "estimated_labour_cost": 600.0 * 2,
                    "savings_percent": 25
                }
            ]
        elif "soybean" in crop_lower:
            recs = [
                {
                    "task": "Harvesting & Threshing",
                    "recommended_equipment": "Multi-Crop Track Combine Harvester",
                    "best_value_listing_id": "LIST_EQP_04",
                    "rationale": f"Fast mechanical harvest avoids pod shattering loss in {acreage} acres.",
                    "estimated_machinery_cost": 2400.0 * acreage,
                    "estimated_labour_cost": 400.0 * 8 * 2,
                    "savings_percent": 30
                }
            ]
        else:
            recs = [
                {
                    "task": "Land Preparation & Seedbed Tillage",
                    "recommended_equipment": "45-50 HP Tractor with 7ft Rotavator",
                    "best_value_listing_id": "LIST_TRAC_03",
                    "rationale": "Single-pass fine tilth ensures optimal germination.",
                    "estimated_machinery_cost": 1150.0 * acreage,
                    "estimated_labour_cost": 3500.0,
                    "savings_percent": 20
                }
            ]

        return {
            "crop": crop,
            "acreage": acreage,
            "region": "Akola, Vidarbha",
            "recommendations": recs,
            "disclaimer": "Cost estimations based on verified Akola CHC and PDKV extension benchmarks."
        }


# Global singleton instance
rental_service = RentalMarketplaceService()
