/**
 * Type definitions for KisanCare Agricultural Rental Marketplace.
 */

export type RentalCategory = 'equipment' | 'tractor' | 'transport' | 'labour' | 'specialist';

export type BillingUnit =
  | 'per_hour'
  | 'per_operating_hour'
  | 'per_half_day'
  | 'per_day'
  | 'per_acre'
  | 'per_worker_day'
  | 'per_worker_hour'
  | 'per_job'
  | 'per_trip'
  | 'per_km'
  | 'per_sample'
  | 'per_visit'
  | 'per_consultation'
  | 'per_team_day';

export type BookingStatus =
  | 'draft'
  | 'pending_confirmation'
  | 'confirmed'
  | 'rejected'
  | 'cancelled'
  | 'in_progress'
  | 'completed'
  | 'disputed';

export type DispatchStatus = 'ready' | 'dispatched' | 'arrived' | 'working' | 'completed';

export interface ProviderSummary {
  id: string;
  business_name: string;
  contact_name: string;
  phone: string;
  division?: string;
  district: string;
  taluka: string;
  village?: string;
  verified: boolean;
  verification_badge: 'verified_fpo' | 'chc_authorized' | 'verified_owner' | 'certified_expert' | 'kvk_authorized' | 'unverified';
  rating: number;
  review_count: number;
  credentials?: string;
}

export interface RentalListing {
  id: string;
  provider_id: string;
  provider: ProviderSummary;
  title: string;
  category: RentalCategory;
  subcategory: string;
  description: string;
  image_url?: string;
  images?: string[];
  billing_unit: BillingUnit;
  price: number;
  currency: string;
  min_duration: number;
  min_charge: number;
  division?: string;
  district: string;
  taluka: string;
  village?: string;
  latitude?: number;
  longitude?: number;
  service_radius_km: number;
  specs: Record<string, any>;
  terms: Record<string, any>;
  is_active: boolean;
  is_demo?: boolean;
  rating: number;
  review_count: number;
  created_at: string;
  updated_at: string;
}

export interface PriceItemBreakdown {
  label: string;
  amount: number;
  description: string;
}

export interface PriceCalculationResult {
  listing_id: string;
  billing_unit: BillingUnit;
  unit_price: number;
  duration: number;
  acreage: number;
  quantity: number;
  base_rental_charge: number;
  operator_charge: number;
  transport_charge: number;
  add_ons_charge: number;
  platform_fee: number;
  taxes: number;
  discounts: number;
  estimated_total: number;
  breakdown: PriceItemBreakdown[];
  currency: string;
  pdkv_benchmark_comparison?: string;
}

export interface PriceCalculationRequest {
  listing_id: string;
  duration: number;
  acreage?: number;
  quantity?: number;
  distance_km?: number;
  include_operator?: boolean;
  operator_daily_fee?: number;
  include_delivery?: boolean;
  delivery_address?: string;
  add_ons?: Array<{ label: string; amount: number; description?: string }>;
}

export interface AvailabilityCheckRequest {
  listing_id: string;
  start_date: string;
  end_date: string;
  start_time?: string;
  duration?: number;
  quantity?: number;
}

export interface AvailabilityCheckResult {
  listing_id: string;
  is_available: boolean;
  conflict_count: number;
  message: string;
  next_available_slot?: string;
}

export interface BookingCreatePayload {
  listing_id: string;
  farmer_id?: string;
  farmer_name: string;
  farmer_phone: string;
  farm_id?: string;
  field_id?: string;
  field_name?: string;
  crop_name?: string;
  farm_location?: string;
  farm_latitude?: number;
  farm_longitude?: number;
  start_date: string;
  end_date: string;
  start_time: string;
  duration: number;
  acreage?: number;
  quantity?: number;
  include_operator?: boolean;
  include_delivery?: boolean;
  delivery_address?: string;
  notes?: string;
  payment_method?: 'pay_on_service' | 'online_upi' | 'escrow_advance';
}

export interface RentalBooking {
  id: string;
  booking_reference: string;
  listing_id: string;
  listing_title: string;
  category: RentalCategory;
  provider_id: string;
  provider_name: string;
  provider_phone: string;
  farmer_id: string;
  farmer_name: string;
  farmer_phone: string;
  farm_id?: string;
  field_id?: string;
  field_name?: string;
  crop_name?: string;
  farm_location?: string;
  start_date: string;
  end_date: string;
  start_time: string;
  duration: number;
  billing_unit: BillingUnit;
  acreage: number;
  quantity: number;
  unit_price: number;
  base_rental_charge: number;
  operator_charge: number;
  transport_charge: number;
  add_ons_charge: number;
  platform_fee: number;
  taxes: number;
  discounts: number;
  total_amount: number;
  payment_method: string;
  payment_status: string;
  status: BookingStatus;
  dispatch_status: DispatchStatus;
  cancellation_reason?: string;
  rejection_reason?: string;
  cancelled_by?: string;
  recorded_in_economics: boolean;
  farm_expense_id?: string;
  is_demo?: boolean;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface MarketRateBenchmark {
  id: string;
  category: string;
  subcategory: string;
  item_name: string;
  region: string;
  district: string;
  source_name: string;
  source_url?: string;
  indicative_rate_min: number;
  indicative_rate_max: number;
  billing_unit: string;
  fuel_included: boolean;
  operator_included: boolean;
  last_verified: string;
  notes: string;
}

export interface SmartRecommendationItem {
  task: string;
  recommended_equipment: string;
  best_value_listing_id: string;
  rationale: string;
  estimated_machinery_cost: number;
  estimated_labour_cost: number;
  savings_percent: number;
}

export interface SmartRecommendationsResponse {
  crop: string;
  acreage: number;
  region: string;
  recommendations: SmartRecommendationItem[];
  disclaimer: string;
}

export interface RentalReview {
  id: string;
  booking_id: string;
  listing_id: string;
  farmer_name: string;
  rating: number;
  review_text: string;
  created_at: string;
}
