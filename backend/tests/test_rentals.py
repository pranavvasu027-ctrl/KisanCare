"""Tests for KisanCare Agricultural Rental Marketplace backend engine and API."""

import os
os.environ["TESTING"] = "1"
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

root_dir = backend_dir.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

try:
    from app.main import app
    from app.rentals.service import rental_service
    from app.rentals.schemas import PriceCalculationRequest
except ModuleNotFoundError:
    from backend.app.main import app
    from backend.app.rentals.service import rental_service
    from backend.app.rentals.schemas import PriceCalculationRequest

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_test_bookings():
    """Ensure clean isolated in-memory state before each test run."""
    with rental_service._lock:
        try:
            from app.rentals.seed_data import SEED_INITIAL_BOOKINGS, SEED_LISTINGS, SEED_MARKET_BENCHMARKS, SEED_PROVIDERS
        except ModuleNotFoundError:
            from backend.app.rentals.seed_data import SEED_INITIAL_BOOKINGS, SEED_LISTINGS, SEED_MARKET_BENCHMARKS, SEED_PROVIDERS
        rental_service._bookings = {b["id"]: dict(b) for b in SEED_INITIAL_BOOKINGS}
        rental_service._listings = {l["id"]: dict(l) for l in SEED_LISTINGS}
        rental_service._benchmarks = [dict(b) for b in SEED_MARKET_BENCHMARKS]
        rental_service._providers = {p["id"]: dict(p) for p in SEED_PROVIDERS}
    yield


def test_list_listings_discovery():
    """Verify listing discovery, filtering, and provider summary attachment."""
    res = client.get("/api/v1/rentals/listings")
    assert res.status_code == 200
    listings = res.json()
    assert len(listings) >= 10
    
    # Check fields in first listing
    item = listings[0]
    assert "id" in item
    assert "title" in item
    assert "category" in item
    assert "billing_unit" in item
    assert "price" in item
    assert "provider" in item
    assert "business_name" in item["provider"]
    assert item["district"] == "Akola"


def test_filter_by_category():
    """Verify category filtering for tractors, equipment, transport, labour."""
    res_trac = client.get("/api/v1/rentals/listings?category=tractor")
    assert res_trac.status_code == 200
    for l in res_trac.json():
        assert l["category"] == "tractor"

    res_eqp = client.get("/api/v1/rentals/listings?category=equipment")
    assert res_eqp.status_code == 200
    for l in res_eqp.json():
        assert l["category"] == "equipment"

    res_lbr = client.get("/api/v1/rentals/listings?category=labour")
    assert res_lbr.status_code == 200
    for l in res_lbr.json():
        assert l["category"] == "labour"


def test_get_listing_details_and_not_found():
    """Verify single listing fetch and 404 behavior."""
    res = client.get("/api/v1/rentals/listings/LIST_TRAC_01")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == "LIST_TRAC_01"
    assert data["specs"]["horsepower"] == 45
    assert "Rotavator" in data["specs"]["implement_compatibility"]

    res_404 = client.get("/api/v1/rentals/listings/NON_EXISTENT_LISTING")
    assert res_404.status_code == 404


def test_server_side_price_calculation_transparent_breakdown():
    """Verify transparent price calculation with minimum billable duration and fees."""
    # Mahindra 575 DI is ₹850/hr with min 2 hours (min charge ₹1700)
    req = {
        "listing_id": "LIST_TRAC_01",
        "duration": 3.0,
        "acreage": 4.5,
        "quantity": 1,
        "include_operator": False,
        "include_delivery": True,
        "distance_km": 8.0  # Included 5km, extra 3km @ ₹30/km = ₹90, delivery fee ₹150 -> ₹240
    }
    res = client.post("/api/v1/rentals/calculate-price", json=req)
    assert res.status_code == 200
    data = res.json()
    
    assert data["billing_unit"] == "per_operating_hour"
    assert data["unit_price"] == 850.0
    assert data["duration"] == 3.0
    assert data["base_rental_charge"] == 850.0 * 3.0  # 2550
    assert data["platform_fee"] == 50.0
    assert data["taxes"] == 0.0  # Exempt under GST
    
    # Expected total = 2550 + transport(150 + 3*30 = 240) + 50 platform = 2840
    expected = 2550.0 + 240.0 + 50.0
    assert data["estimated_total"] == expected
    assert len(data["breakdown"]) >= 3


def test_price_calculation_enforces_minimum_duration():
    """Requesting 0.5 hours on an implement with min_duration=2 should bill min 2 hours."""
    req = {
        "listing_id": "LIST_TRAC_01",
        "duration": 0.5,
        "include_delivery": False
    }
    res = client.post("/api/v1/rentals/calculate-price", json=req)
    assert res.status_code == 200
    data = res.json()
    assert data["duration"] == 2.0
    assert data["base_rental_charge"] == 1700.0


def test_concurrency_availability_and_overlap_rejection():
    """Verify overlapping confirmed booking for same resource is rejected with 409 Conflict."""
    # Check availability for rotavator package
    check_req = {
        "listing_id": "LIST_TRAC_03",
        "start_date": "2026-11-10",
        "end_date": "2026-11-12",
        "duration": 2.0
    }
    res_avail = client.post("/api/v1/rentals/check-availability", json=check_req)
    assert res_avail.status_code == 200
    assert res_avail.json()["is_available"] is True

    # Farmer 1 creates booking
    booking_req = {
        "listing_id": "LIST_TRAC_03",
        "farmer_name": "Ramesh Patil",
        "farmer_phone": "+91 98220 12345",
        "farm_id": "FARM_001",
        "field_id": "FLD_01",
        "field_name": "Field 1 - South",
        "crop_name": "Cotton",
        "start_date": "2026-11-10",
        "end_date": "2026-11-12",
        "duration": 2.0,
        "acreage": 3.0,
        "payment_method": "pay_on_service"
    }
    res_bkg1 = client.post("/api/v1/rentals/bookings", json=booking_req)
    assert res_bkg1.status_code == 201
    bkg1 = res_bkg1.json()
    bkg1_id = bkg1["id"]
    assert bkg1["booking_reference"].startswith("KCR-BKG-")
    assert bkg1["status"] == "pending_confirmation"

    # Owner confirms Farmer 1's booking
    res_confirm = client.post(f"/api/v1/rentals/owner/bookings/{bkg1_id}/respond", json={"action": "confirm"})
    assert res_confirm.status_code == 200
    assert res_confirm.json()["status"] == "confirmed"

    # Farmer 2 tries to book the EXACT overlapping dates
    res_bkg2 = client.post("/api/v1/rentals/bookings", json=booking_req)
    assert res_bkg2.status_code == 409
    assert "already reserved" in res_bkg2.json()["detail"].lower() or "conflict" in res_bkg2.json()["detail"].lower()


def test_invalid_booking_date_validation():
    """End date earlier than start date must be rejected with 400 Bad Request."""
    invalid_req = {
        "listing_id": "LIST_EQP_01",
        "farmer_name": "Ramesh Patil",
        "farmer_phone": "+91 98220 12345",
        "start_date": "2026-11-15",
        "end_date": "2026-11-10",  # Invalid
        "duration": 1.0
    }
    res = client.post("/api/v1/rentals/bookings", json=invalid_req)
    assert res.status_code == 400
    assert "end date" in res.json()["detail"].lower()


def test_booking_lifecycle_state_machine():
    """Verify pending -> confirmed -> dispatched -> completed state transitions."""
    # Create booking for combine harvester
    booking_req = {
        "listing_id": "LIST_EQP_04",
        "farmer_name": "Suresh Deshmukh",
        "farmer_phone": "+91 94221 99887",
        "start_date": "2026-11-20",
        "end_date": "2026-11-20",
        "duration": 4.0,
        "acreage": 4.0,
        "payment_method": "pay_on_service"
    }
    res_create = client.post("/api/v1/rentals/bookings", json=booking_req)
    assert res_create.status_code == 201
    bkg = res_create.json()
    bkg_id = bkg["id"]

    # 1. Owner confirms
    res_confirm = client.post(f"/api/v1/rentals/owner/bookings/{bkg_id}/respond", json={"action": "confirm"})
    assert res_confirm.status_code == 200
    assert res_confirm.json()["status"] == "confirmed"

    # 2. Owner dispatches machine
    res_dispatch = client.post(f"/api/v1/rentals/owner/bookings/{bkg_id}/dispatch", json={"dispatch_status": "dispatched"})
    assert res_dispatch.status_code == 200
    assert res_dispatch.json()["status"] == "in_progress"
    assert res_dispatch.json()["dispatch_status"] == "dispatched"

    # 3. Complete rental
    res_complete = client.post(f"/api/v1/rentals/owner/bookings/{bkg_id}/dispatch", json={"dispatch_status": "completed"})
    assert res_complete.status_code == 200
    assert res_complete.json()["status"] == "completed"
    assert res_complete.json()["payment_status"] == "paid"

    # 4. Link completed expense to Farm Economics
    exp_req = {
        "farm_id": "FARM_001",
        "field_id": "FLD_01",
        "season": "Kharif 2026",
        "crop": "Soybean",
        "expense_category": "machinery_rental"
    }
    res_exp = client.post(f"/api/v1/rentals/bookings/{bkg_id}/record-expense", json=exp_req)
    assert res_exp.status_code == 200
    exp_data = res_exp.json()
    assert exp_data["status"] == "recorded"
    assert exp_data["amount"] > 0
    assert exp_data["crop"] == "Soybean"


def test_market_rate_references():
    """Verify Akola / Vidarbha CHC benchmark rate reference data."""
    res = client.get("/api/v1/rentals/market-rates")
    assert res.status_code == 200
    benchmarks = res.json()
    assert len(benchmarks) >= 5
    
    tractor_bench = next(b for b in benchmarks if b["category"] == "tractor")
    assert "PDKV Akola" in tractor_bench["source_name"]
    assert tractor_bench["indicative_rate_min"] >= 700
    assert tractor_bench["district"] == "Akola"


def test_smart_agricultural_recommendations():
    """Verify agronomic equipment package recommendation for Cotton in Akola."""
    res = client.get("/api/v1/rentals/recommendations?crop=Cotton&acreage=4.5")
    assert res.status_code == 200
    data = res.json()
    assert data["crop"] == "Cotton"
    assert data["acreage"] == 4.5
    assert len(data["recommendations"]) >= 1
    assert "Weeding" in data["recommendations"][0]["task"]


def test_statewide_geography_endpoint():
    """Verify Maharashtra geography API exposes all 6 divisions and major agricultural districts."""
    res = client.get("/api/v1/rentals/geography")
    assert res.status_code == 200
    divisions = res.json()
    expected_divs = ["Amravati", "Nagpur", "Pune", "Nashik", "Chhatrapati Sambhajinagar", "Konkan"]
    for div in expected_divs:
        assert div in divisions
        assert "districts" in divisions[div]
        assert len(divisions[div]["districts"]) >= 2

    # Check key agricultural districts
    assert "Akola" in divisions["Amravati"]["districts"]
    assert "Pune" in divisions["Pune"]["districts"]
    assert "Nashik" in divisions["Nashik"]["districts"]
    assert "Ratnagiri" in divisions["Konkan"]["districts"]


def test_statewide_division_filtering():
    """Verify listings are present and discoverable across all 6 administrative divisions."""
    expected_divs = ["Amravati", "Nagpur", "Pune", "Nashik", "Chhatrapati Sambhajinagar", "Konkan"]
    for div in expected_divs:
        res = client.get(f"/api/v1/rentals/listings?division={div}")
        assert res.status_code == 200
        listings = res.json()
        assert len(listings) >= 3, f"Expected at least 3 listings for {div}"
        for l in listings:
            assert l["division"] == div


def test_specialist_category_and_pricing():
    """Verify specialist services (soil testing, drone spraying, viticulture) discovery and transparent billing."""
    res_spec = client.get("/api/v1/rentals/listings?category=specialist")
    assert res_spec.status_code == 200
    specs = res_spec.json()
    assert len(specs) >= 5
    for s in specs:
        assert s["category"] == "specialist"
        assert s["is_demo"] is True

    # Soil sample pricing test (per_sample)
    soil_test = next(s for s in specs if s["billing_unit"] == "per_sample")
    price_req = {
        "listing_id": soil_test["id"],
        "duration": 1.0,
        "quantity": 3  # 3 soil samples
    }
    res_price = client.post("/api/v1/rentals/calculate-price", json=price_req)
    assert res_price.status_code == 200
    pdata = res_price.json()
    assert pdata["base_rental_charge"] == soil_test["price"] * 3
    assert pdata["platform_fee"] == 50.0
    assert pdata["taxes"] == 0.0


def test_labour_team_pricing_calculation():
    """Verify distinct price calculation for whole-team rates (per_team_day) vs per-worker rates (per_worker_day)."""
    # 1. Whole team rate
    team_req = {
        "listing_id": "LIST_PUN_LAB_01",  # Sugarcane Harvesting Toli (per_team_day)
        "duration": 2.0,  # 2 days
        "quantity": 1  # 1 team
    }
    res_team = client.post("/api/v1/rentals/calculate-price", json=team_req)
    assert res_team.status_code == 200
    t_data = res_team.json()
    assert t_data["billing_unit"] == "per_team_day"
    assert t_data["base_rental_charge"] == 4200.0 * 2.0  # 8400

    # 2. Per-worker rate
    worker_req = {
        "listing_id": "LIST_AMR_LAB_01",  # Cotton Picking (per_worker_day)
        "duration": 3.0,  # 3 days
        "quantity": 8   # 8 workers
    }
    res_worker = client.post("/api/v1/rentals/calculate-price", json=worker_req)
    assert res_worker.status_code == 200
    w_data = res_worker.json()
    assert w_data["billing_unit"] == "per_worker_day"
    assert w_data["base_rental_charge"] == 380.0 * 3.0 * 8.0  # 9120


def test_demo_listings_transparency():
    """Verify all mock seed listings carry explicit is_demo=True transparency flags."""
    res = client.get("/api/v1/rentals/listings")
    assert res.status_code == 200
    listings = res.json()
    assert len(listings) >= 40
    for l in listings:
        assert l["is_demo"] is True



# -----------------------------------------------------------------------------
# Security & Authorization Tests: Multi-tenant and Cross-user Protections
# -----------------------------------------------------------------------------
import jwt

TEST_SECRET_KEY = "kisancare-super-secure-test-jwt-secret-key-32chars"

def _make_auth_header(user_id: str) -> dict:
    token = jwt.encode({"sub": user_id}, TEST_SECRET_KEY, algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}


def test_cross_user_cancellation_prevention():
    """Verify Farmer A's booking cannot be cancelled by Farmer B."""
    # 1. Create booking by farmer_alice
    b_req = {
        "listing_id": "LIST_TRAC_01",
        "farmer_name": "Alice Farmer",
        "farmer_phone": "+91 98000 11111",
        "start_date": "2026-11-15",
        "end_date": "2026-11-16",
        "duration": 4.0,
        "delivery_address": "Field 3, Akola",
        "notes": "Urgent tilling"
    }
    res = client.post("/api/v1/rentals/bookings", json=b_req, headers=_make_auth_header("farmer_alice"))
    assert res.status_code == 201
    booking_id = res.json()["id"]
    assert res.json()["farmer_id"] == "farmer_alice"

    # 2. farmer_bob attempts to cancel farmer_alice's booking
    cancel_payload = {"reason": "Malicious cancellation attempt", "cancelled_by": "farmer"}
    res_cancel_bob = client.post(
        f"/api/v1/rentals/bookings/{booking_id}/cancel",
        json=cancel_payload,
        headers=_make_auth_header("farmer_bob")
    )
    assert res_cancel_bob.status_code == 403
    assert "Access denied" in res_cancel_bob.json()["detail"]

    # 3. farmer_alice cancels her own booking
    res_cancel_alice = client.post(
        f"/api/v1/rentals/bookings/{booking_id}/cancel",
        json=cancel_payload,
        headers=_make_auth_header("farmer_alice")
    )
    assert res_cancel_alice.status_code == 200
    assert res_cancel_alice.json()["status"] == "cancelled"


def test_cross_user_provider_response_prevention():
    """Verify Provider A cannot confirm or reject bookings belonging to Provider B."""
    # LIST_TRAC_01 is owned by PROV_AKOLA_01
    b_req = {
        "listing_id": "LIST_TRAC_01",
        "farmer_name": "Charlie Farmer",
        "farmer_phone": "+91 98000 22222",
        "start_date": "2026-11-20",
        "end_date": "2026-11-21",
        "duration": 3.0,
        "delivery_address": "Farm 2, Akola"
    }
    res = client.post("/api/v1/rentals/bookings", json=b_req, headers=_make_auth_header("farmer_charlie"))
    assert res.status_code == 201
    booking_id = res.json()["id"]

    # Rogue provider PROV_PUNE_ROGUE tries to respond
    res_rogue = client.post(
        f"/api/v1/rentals/owner/bookings/{booking_id}/respond",
        json={"action": "confirm"},
        headers=_make_auth_header("PROV_PUNE_ROGUE")
    )
    assert res_rogue.status_code == 403
    assert "Access denied" in res_rogue.json()["detail"]

    # Legitimate owner PROV_AKOLA_01 responds
    res_owner = client.post(
        f"/api/v1/rentals/owner/bookings/{booking_id}/respond",
        json={"action": "confirm"},
        headers=_make_auth_header("PROV_AKOLA_01")
    )
    assert res_owner.status_code == 200
    assert res_owner.json()["status"] == "confirmed"


def test_cross_user_dispatch_prevention():
    """Verify unauthorized provider cannot alter dispatch workflow."""
    # BKG_2026_001 is confirmed, provider is PROV_AKOLA_01
    res = client.post(
        "/api/v1/rentals/owner/bookings/BKG_2026_001/dispatch",
        json={"dispatch_status": "arrived"},
        headers=_make_auth_header("PROV_UNAUTHORIZED")
    )
    assert res.status_code == 403
    assert "Access denied" in res.json()["detail"]


def test_cross_user_booking_inspection_prevention():
    """Verify unrelated users cannot inspect other farmers' booking details."""
    # Create booking for farmer_david
    b_req = {
        "listing_id": "LIST_TRAC_01",
        "farmer_name": "David Farmer",
        "farmer_phone": "+91 98000 33333",
        "start_date": "2026-12-01",
        "end_date": "2026-12-02",
        "duration": 5.0,
        "delivery_address": "Baramati Farm"
    }
    res = client.post("/api/v1/rentals/bookings", json=b_req, headers=_make_auth_header("farmer_david"))
    assert res.status_code == 201
    booking_id = res.json()["id"]

    # Unrelated farmer_eve attempts to inspect
    res_inspect_eve = client.get(
        f"/api/v1/rentals/bookings/{booking_id}",
        headers=_make_auth_header("farmer_eve")
    )
    assert res_inspect_eve.status_code == 403
    assert "Access denied" in res_inspect_eve.json()["detail"]

    # Owner farmer_david can inspect
    res_inspect_david = client.get(
        f"/api/v1/rentals/bookings/{booking_id}",
        headers=_make_auth_header("farmer_david")
    )
    assert res_inspect_david.status_code == 200


def test_duplicate_review_and_cross_user_review_prevention():
    """Verify duplicate reviews are blocked and non-booked users cannot review."""
    # Create and complete a booking for farmer_frank
    b_req = {
        "listing_id": "LIST_TRAC_01",
        "farmer_name": "Frank Farmer",
        "farmer_phone": "+91 98000 44444",
        "start_date": "2026-12-05",
        "end_date": "2026-12-06",
        "duration": 2.0,
        "delivery_address": "Akola North"
    }
    res = client.post("/api/v1/rentals/bookings", json=b_req, headers=_make_auth_header("farmer_frank"))
    assert res.status_code == 201
    booking_id = res.json()["id"]
    listing_id = res.json()["listing_id"]

    # Confirm and complete
    client.post(
        f"/api/v1/rentals/owner/bookings/{booking_id}/respond",
        json={"action": "confirm"},
        headers=_make_auth_header("PROV_AKOLA_01")
    )
    client.post(
        f"/api/v1/rentals/owner/bookings/{booking_id}/dispatch",
        json={"dispatch_status": "completed"},
        headers=_make_auth_header("PROV_AKOLA_01")
    )

    # 1. Non-booked farmer tries to review
    rev_payload_fake = {
        "booking_id": booking_id,
        "listing_id": listing_id,
        "farmer_name": "Imposter Farmer",
        "rating": 5,
        "review_text": "Fake review by stranger"
    }
    res_fake = client.post("/api/v1/rentals/reviews", json=rev_payload_fake, headers=_make_auth_header("farmer_imposter"))
    assert res_fake.status_code == 403
    assert "Access denied" in res_fake.json()["detail"]

    # 2. Legitimate farmer reviews
    rev_payload_legit = {
        "booking_id": booking_id,
        "listing_id": listing_id,
        "farmer_name": "Frank Farmer",
        "rating": 5,
        "review_text": "Excellent machine, timely operator!"
    }
    res_legit = client.post("/api/v1/rentals/reviews", json=rev_payload_legit, headers=_make_auth_header("farmer_frank"))
    assert res_legit.status_code == 201

    # 3. Duplicate review on same booking
    res_dup = client.post("/api/v1/rentals/reviews", json=rev_payload_legit, headers=_make_auth_header("farmer_frank"))
    assert res_dup.status_code == 400
    assert "already been submitted" in res_dup.json()["detail"]


def test_duplicate_expense_and_cross_user_expense_prevention():
    """Verify duplicate expense recording is blocked and non-owners cannot record."""
    # Create and complete a booking for farmer_george
    b_req = {
        "listing_id": "LIST_TRAC_01",
        "farmer_name": "George Farmer",
        "farmer_phone": "+91 98000 55555",
        "start_date": "2026-12-10",
        "end_date": "2026-12-11",
        "duration": 3.0,
        "delivery_address": "Akola East"
    }
    res = client.post("/api/v1/rentals/bookings", json=b_req, headers=_make_auth_header("farmer_george"))
    assert res.status_code == 201
    booking_id = res.json()["id"]

    client.post(
        f"/api/v1/rentals/owner/bookings/{booking_id}/respond",
        json={"action": "confirm"},
        headers=_make_auth_header("PROV_AKOLA_01")
    )
    client.post(
        f"/api/v1/rentals/owner/bookings/{booking_id}/dispatch",
        json={"dispatch_status": "completed"},
        headers=_make_auth_header("PROV_AKOLA_01")
    )

    exp_req = {
        "farm_id": "farm-101",
        "field_id": "FIELD-01",
        "season": "Rabi 2026",
        "crop": "Cotton",
        "expense_category": "machinery_rental"
    }

    # 1. Imposter attempts to record expense
    res_imposter = client.post(
        f"/api/v1/rentals/bookings/{booking_id}/record-expense",
        json=exp_req,
        headers=_make_auth_header("farmer_stranger")
    )
    assert res_imposter.status_code == 403

    # 2. Legitimate farmer records expense
    res_rec = client.post(
        f"/api/v1/rentals/bookings/{booking_id}/record-expense",
        json=exp_req,
        headers=_make_auth_header("farmer_george")
    )
    assert res_rec.status_code == 200
    assert "expense_id" in res_rec.json()

    # 3. Duplicate expense recording
    res_dup = client.post(
        f"/api/v1/rentals/bookings/{booking_id}/record-expense",
        json=exp_req,
        headers=_make_auth_header("farmer_george")
    )
    assert res_dup.status_code == 400
    assert "already been recorded" in res_dup.json()["detail"]


def test_pending_confirmation_blocks_concurrent_booking():
    """Verify that a pending_confirmation booking protects against double booking."""
    req1 = {
        "listing_id": "LIST_TRAC_01",
        "farmer_name": "Farmer One",
        "farmer_phone": "+91 98000 66666",
        "start_date": "2026-12-25",
        "end_date": "2026-12-28",
        "duration": 4.0,
        "delivery_address": "Farm 9, Baramati"
    }
    # Create first booking -> status will be pending_confirmation
    res1 = client.post("/api/v1/rentals/bookings", json=req1, headers=_make_auth_header("farmer_one"))
    assert res1.status_code == 201
    assert res1.json()["status"] == "pending_confirmation"

    # Second booking overlapping with the pending booking
    req2 = {
        "listing_id": "LIST_TRAC_01",
        "farmer_name": "Farmer Two",
        "farmer_phone": "+91 98000 77777",
        "start_date": "2026-12-26",
        "end_date": "2026-12-27",
        "duration": 2.0,
        "delivery_address": "Farm 10, Baramati"
    }
    res2 = client.post("/api/v1/rentals/bookings", json=req2, headers=_make_auth_header("farmer_two"))
    assert res2.status_code == 409
    assert "already reserved" in res2.json()["detail"] or "conflict" in res2.json()["detail"]
