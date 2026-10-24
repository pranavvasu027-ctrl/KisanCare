"""Pydantic schemas for KisanCare Agricultural Rental Marketplace."""

from __future__ import annotations
from typing import Dict, List, Optional, Any, Literal
from datetime import date, time, datetime
from pydantic import BaseModel, Field, field_validator


RentalCategory = Literal["equipment", "tractor", "transport", "labour", "specialist"]
BillingUnit = Literal[
    "per_hour",
    "per_operating_hour",
    "per_half_day",
    "per_day",
    "per_acre",
    "per_worker_day",
    "per_worker_hour",
    "per_job",
    "per_trip",
    "per_km",
    "per_sample",
    "per_visit",
    "per_consultation",
    "per_team_day"
]
BookingStatus = Literal[
    "draft",
    "pending_confirmation",
    "confirmed",
    "rejected",
    "cancelled",
    "in_progress",
    "completed",
    "disputed"
]
DispatchStatus = Literal["ready", "dispatched", "arrived", "working", "completed"]


class ProviderSummary(BaseModel):
    id: str
    business_name: str
    contact_name: str
    phone: str
    division: Optional[str] = "Amravati"
    district: str
    taluka: str
    village: Optional[str] = None
    verified: bool = False
    verification_badge: str = "unverified"
    rating: float = 0.0
    review_count: int = 0
    credentials: Optional[str] = None


class RentalListingCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    category: RentalCategory
    subcategory: str
    description: str = Field(..., min_length=10)
    image_url: Optional[str] = None
    billing_unit: BillingUnit
    price: float = Field(..., ge=0)
    currency: str = "INR"
    min_duration: int = Field(default=1, ge=1)
    min_charge: float = Field(default=0.0, ge=0)
    division: Optional[str] = "Amravati"
    district: str = "Akola"
    taluka: str
    village: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    service_radius_km: float = Field(default=25.0, gt=0)
    specs: Dict[str, Any] = Field(default_factory=dict)
    terms: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    is_demo: bool = True


class RentalListing(RentalListingCreate):
    id: str
    provider_id: str
    provider: ProviderSummary
    created_at: str
    updated_at: str
    rating: float = 0.0
    review_count: int = 0


class PriceCalculationRequest(BaseModel):
    listing_id: str
    duration: float = Field(..., gt=0, description="Duration in hours, days, or trips depending on unit")
    acreage: Optional[float] = Field(default=0.0, ge=0)
    quantity: int = Field(default=1, ge=1, description="Quantity of workers or implements")
    distance_km: Optional[float] = Field(default=0.0, ge=0)
    include_operator: bool = False
    operator_daily_fee: Optional[float] = Field(default=0.0, ge=0)
    include_delivery: bool = False
    delivery_address: Optional[str] = None
    add_ons: List[Dict[str, Any]] = Field(default_factory=list)


class PriceItemBreakdown(BaseModel):
    label: str
    amount: float
    description: str


class PriceCalculationResponse(BaseModel):
    listing_id: str
    billing_unit: BillingUnit
    unit_price: float
    duration: float
    acreage: float
    quantity: int
    base_rental_charge: float
    operator_charge: float
    transport_charge: float
    add_ons_charge: float
    platform_fee: float
    taxes: float
    discounts: float
    estimated_total: float
    breakdown: List[PriceItemBreakdown]
    currency: str = "INR"
    pdkv_benchmark_comparison: Optional[str] = None


class AvailabilityCheckRequest(BaseModel):
    listing_id: str
    start_date: str  # YYYY-MM-DD
    end_date: str    # YYYY-MM-DD
    start_time: Optional[str] = "08:00"
    duration: float = Field(default=1.0, gt=0)
    quantity: int = Field(default=1, ge=1)


class AvailabilityCheckResponse(BaseModel):
    listing_id: str
    is_available: bool
    conflict_count: int
    message: str
    next_available_slot: Optional[str] = None


class BookingCreateRequest(BaseModel):
    listing_id: str
    farmer_id: Optional[str] = None
    farmer_name: str
    farmer_phone: str
    
    # Farm digital twin integration
    farm_id: Optional[str] = "FARM_001"
    field_id: Optional[str] = "FLD_01"
    field_name: Optional[str] = "Field 1 - South"
    crop_name: Optional[str] = "Cotton"
    farm_location: Optional[str] = "Akola, Murtizapur Rd"
    farm_latitude: Optional[float] = 20.7002
    farm_longitude: Optional[float] = 77.0082
    
    start_date: str
    end_date: str
    start_time: str = "08:00"
    duration: float = Field(..., gt=0)
    acreage: float = Field(default=0.0, ge=0)
    quantity: int = Field(default=1, ge=1)
    
    include_operator: bool = False
    include_delivery: bool = False
    delivery_address: Optional[str] = None
    notes: Optional[str] = None
    payment_method: Literal["pay_on_service", "online_upi", "escrow_advance"] = "pay_on_service"


class BookingRecord(BaseModel):
    id: str
    booking_reference: str
    listing_id: str
    listing_title: str
    category: RentalCategory
    provider_id: str
    provider_name: str
    provider_phone: str
    farmer_id: str
    farmer_name: str
    farmer_phone: str
    
    farm_id: Optional[str] = None
    field_id: Optional[str] = None
    field_name: Optional[str] = None
    crop_name: Optional[str] = None
    farm_location: Optional[str] = None
    
    start_date: str
    end_date: str
    start_time: str
    duration: float
    billing_unit: BillingUnit
    acreage: float
    quantity: int
    
    unit_price: float
    base_rental_charge: float
    operator_charge: float
    transport_charge: float
    add_ons_charge: float
    platform_fee: float
    taxes: float
    discounts: float
    total_amount: float
    
    payment_method: str
    payment_status: str
    status: BookingStatus
    dispatch_status: DispatchStatus
    
    cancellation_reason: Optional[str] = None
    rejection_reason: Optional[str] = None
    cancelled_by: Optional[str] = None
    
    recorded_in_economics: bool = False
    farm_expense_id: Optional[str] = None
    is_demo: bool = True
    notes: Optional[str] = None
    
    created_at: str
    updated_at: str


class BookingStatusUpdateRequest(BaseModel):
    status: Optional[BookingStatus] = None
    dispatch_status: Optional[DispatchStatus] = None
    rejection_reason: Optional[str] = None
    cancellation_reason: Optional[str] = None
    actual_hours: Optional[float] = None
    actual_acreage: Optional[float] = None


class MarketRateReference(BaseModel):
    id: str
    category: str
    subcategory: str
    item_name: str
    region: str = "Vidarbha"
    district: str = "Akola"
    source_name: str
    source_url: Optional[str] = None
    indicative_rate_min: float
    indicative_rate_max: float
    billing_unit: str
    fuel_included: bool
    operator_included: bool
    last_verified: str
    notes: str


class RentalReviewCreate(BaseModel):
    booking_id: str
    listing_id: str
    farmer_id: Optional[str] = None
    farmer_name: str
    rating: int = Field(..., ge=1, le=5)
    review_text: str = Field(..., min_length=3)


class RentalReview(RentalReviewCreate):
    id: str
    created_at: str


class RecordExpenseRequest(BaseModel):
    farm_id: str
    field_id: str
    season: str = "Kharif 2026"
    crop: str = "Cotton"
    expense_category: Literal["machinery_rental", "labour_hire", "transport"] = "machinery_rental"
