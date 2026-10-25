"""Tests for KisanCare Nearby Google Maps Discovery, UPI Settlement, and Shopkeeper Subscriptions."""

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
    from app.rentals.schemas import (
        BookingCreateRequest,
        BookingUPIPaymentSubmit,
        SubscriptionUpgradeRequest
    )
    from app.rentals.seed_data import SEED_INITIAL_BOOKINGS, SEED_LISTINGS, SEED_MARKET_BENCHMARKS, SEED_PROVIDERS
except ModuleNotFoundError:
    from backend.app.main import app
    from backend.app.rentals.service import rental_service
    from backend.app.rentals.schemas import (
        BookingCreateRequest,
        BookingUPIPaymentSubmit,
        SubscriptionUpgradeRequest
    )
    from backend.app.rentals.seed_data import SEED_INITIAL_BOOKINGS, SEED_LISTINGS, SEED_MARKET_BENCHMARKS, SEED_PROVIDERS

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_test_bookings():
    """Ensure clean isolated in-memory state before and after each test run."""
    with rental_service._lock:
        rental_service._bookings = {b["id"]: dict(b) for b in SEED_INITIAL_BOOKINGS}
        rental_service._listings = {l["id"]: dict(l) for l in SEED_LISTINGS}
        rental_service._benchmarks = [dict(b) for b in SEED_MARKET_BENCHMARKS]
        rental_service._notifications = {}
    yield
    with rental_service._lock:
        rental_service._bookings = {b["id"]: dict(b) for b in SEED_INITIAL_BOOKINGS}
        rental_service._notifications = {}


def test_discover_nearby_50km_radius():
    """Verify nearby equipment discovery returns Google Places shops within 50km sorted strictly nearest first."""
    # Shioni, Akola coordinates: 20.7002, 77.0082
    resp = client.get("/api/v1/rentals/nearby?lat=20.7002&lon=77.0082&radius_km=50.0&location_name=Shioni,%20Akola")
    assert resp.status_code == 200
    data = resp.json()
    assert data["radius_km"] == 50.0
    assert "google_places_shops" in data
    shops = data["google_places_shops"]
    assert len(shops) >= 3

    # Ensure Google Places shops have distance, rating, phone, accessories
    first_shop = shops[0]
    assert "name" in first_shop
    assert "distance_km" in first_shop
    assert "rental_accessories" in first_shop
    assert len(first_shop["rental_accessories"]) > 0

    # Verify nearest-first ordering: each shop must have distance >= previous shop
    for i in range(len(shops) - 1):
        assert shops[i]["distance_km"] <= shops[i + 1]["distance_km"]

    # Verify registered platform listings
    assert "registered_listings" in data
    assert len(data["registered_listings"]) > 0


def test_subscription_priority_ranking():
    """Verify subscribed Gold/Pro shopkeepers are prioritized at the top of results."""
    # Ensure PROV_AKOLA_01 has Gold Merchant subscription
    sub_upgrade = SubscriptionUpgradeRequest(
        provider_id="PROV_AKOLA_01",
        plan_id="gold_merchant",
        duration_months=1,
        upi_transaction_ref="UTR-TEST-123456"
    )
    rental_service.upgrade_owner_subscription(sub_upgrade, provider_id="PROV_AKOLA_01")

    resp = client.get("/api/v1/rentals/nearby?lat=20.7002&lon=77.0082&radius_km=15.0")
    assert resp.status_code == 200
    data = resp.json()
    listings = data["registered_listings"]
    assert len(listings) > 0

    # First listing must be priority partner
    assert listings[0]["is_priority"] is True
    assert listings[0]["provider"]["is_priority"] is True
    assert listings[0]["provider"]["subscription_tier"] == "gold_merchant"


def test_booking_creates_shopkeeper_notification():
    """Verify booking creation generates an unread notification for the equipment owner."""
    req = {
        "listing_id": "LIST_TRAC_01",
        "farmer_name": "Suresh Gite",
        "farmer_phone": "+91 94221 99887",
        "farm_location": "Takli Bu, Akola",
        "start_date": "2026-11-01",
        "end_date": "2026-11-01",
        "start_time": "08:00",
        "duration": 2.0,
        "payment_method": "online_upi"
    }
    resp = client.post("/api/v1/rentals/bookings", json=req)
    assert resp.status_code == 201
    booking = resp.json()
    b_id = booking["id"]
    prov_id = booking["provider_id"]

    # Check notification for provider
    notif_resp = client.get(f"/api/v1/rentals/owner/notifications?provider_id={prov_id}")
    assert notif_resp.status_code == 200
    notifs = notif_resp.json()
    matching = [n for n in notifs if n["booking_id"] == b_id]
    assert len(matching) > 0
    assert matching[0]["farmer_name"] == "Suresh Gite"
    assert matching[0]["status"] == "unread"

    # Mark as read
    read_resp = client.post(f"/api/v1/rentals/owner/notifications/{matching[0]['id']}/read?provider_id={prov_id}")
    assert read_resp.status_code == 200
    assert read_resp.json()["status"] == "read"


def test_real_upi_payment_submission():
    """Verify submitting UPI payment reference marks booking as paid and links transaction ID."""
    # Create booking
    req = {
        "listing_id": "LIST_EQP_01",
        "farmer_name": "Kailas Deshmukh",
        "farmer_phone": "+91 98220 54321",
        "farm_location": "Borgaon Manju, Akola",
        "start_date": "2026-11-05",
        "end_date": "2026-11-05",
        "start_time": "09:00",
        "duration": 2.0,
        "payment_method": "online_upi"
    }
    resp = client.post("/api/v1/rentals/bookings", json=req)
    assert resp.status_code == 201
    b_id = resp.json()["id"]

    # Submit UPI Payment UTR
    upi_payload = {
        "upi_transaction_ref": "UTR429188492019",
        "paid_amount": resp.json()["total_amount"]
    }
    pay_resp = client.post(f"/api/v1/rentals/bookings/{b_id}/pay-upi", json=upi_payload)
    assert pay_resp.status_code == 200
    updated = pay_resp.json()
    assert updated["payment_status"] == "paid"
    assert updated["upi_transaction_ref"] == "UTR429188492019"
    assert updated["upi_paid_at"] is not None


def test_subscription_plans_endpoint():
    """Verify subscription plans retrieval for shopkeepers."""
    resp = client.get("/api/v1/rentals/owner/subscription/plans")
    assert resp.status_code == 200
    plans = resp.json()
    assert len(plans) >= 3
    plan_ids = [p["plan_id"] for p in plans]
    assert "free" in plan_ids
    assert "gold_merchant" in plan_ids
    assert "pro_partner" in plan_ids
