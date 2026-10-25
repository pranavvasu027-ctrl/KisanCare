/**
 * KisanCare Equipment Rental Service
 * Connects to live /api/v1/rentals/listings backend endpoint.
 */

import { apiClient } from './apiClient';
import { ENDPOINTS } from './endpoints';

export interface RentalProvider {
  id?: string;
  business_name?: string;
  contact_name?: string;
  phone?: string;
  verified?: boolean;
}

export interface RentalListing {
  id: string;
  title: string;
  category: 'tractor' | 'equipment' | 'transport' | 'labour' | 'specialist' | string;
  subcategory?: string;
  price?: number;
  daily_rate?: number;
  hourly_rate?: number;
  billing_unit?: string;
  currency?: string;
  district: string;
  taluka?: string;
  village?: string;
  status?: 'available' | 'rented' | 'maintenance' | string;
  is_active?: boolean;
  rating?: number;
  provider?: RentalProvider;
  owner_name?: string;
}

export interface RentalFilterParams {
  category?: string;
  district?: string;
  query?: string;
  max_price?: number;
}

export interface BookingCreatePayload {
  listing_id: string;
  farmer_name: string;
  farmer_phone: string;
  start_date: string; // YYYY-MM-DD
  end_date: string;   // YYYY-MM-DD
  start_time?: string;
  duration: number;
  payment_method?: 'pay_on_service' | 'online_upi' | 'escrow_advance';
  notes?: string;
}

export interface BookingRecord {
  id: string;
  booking_reference: string;
  listing_id: string;
  listing_title: string;
  category: string;
  provider_id: string;
  provider_name?: string;
  provider_phone?: string;
  farmer_id?: string;
  farmer_name: string;
  farmer_phone: string;
  start_date: string;
  end_date: string;
  duration: number;
  total_amount: number;
  status: string;
  payment_method: string;
  payment_status: string;
  created_at: string;
}

export interface PriceCalculationPayload {
  listing_id: string;
  duration: number;
  acreage?: number;
  quantity?: number;
  include_operator?: boolean;
  include_delivery?: boolean;
}

export interface PriceCalculationResult {
  listing_id: string;
  billing_unit: string;
  unit_price: number;
  duration: number;
  base_rental_charge: number;
  operator_charge: number;
  transport_charge: number;
  platform_fee: number;
  estimated_total: number;
  currency?: string;
}

export async function fetchRentalListings(
  params?: RentalFilterParams
): Promise<RentalListing[]> {
  return apiClient.get<RentalListing[]>(ENDPOINTS.RENTALS_LISTINGS, {
    params: {
      category: params?.category,
      district: params?.district,
      query: params?.query,
      max_price: params?.max_price,
    },
  });
}

export async function calculateRentalPrice(
  payload: PriceCalculationPayload
): Promise<PriceCalculationResult> {
  return apiClient.post<PriceCalculationResult>(
    ENDPOINTS.RENTALS_CALCULATE_PRICE,
    payload
  );
}

export async function createRentalBooking(
  payload: BookingCreatePayload
): Promise<BookingRecord> {
  return apiClient.post<BookingRecord>(ENDPOINTS.RENTALS_BOOKINGS, {
    listing_id: payload.listing_id,
    farmer_name: payload.farmer_name,
    farmer_phone: payload.farmer_phone,
    start_date: payload.start_date,
    end_date: payload.end_date,
    duration: payload.duration,
    start_time: payload.start_time || '08:00',
    payment_method: payload.payment_method || 'pay_on_service',
    notes: payload.notes,
  });
}

export async function fetchFarmerBookings(
  farmerId?: string
): Promise<BookingRecord[]> {
  return apiClient.get<BookingRecord[]>(ENDPOINTS.RENTALS_BOOKINGS, {
    params: farmerId ? { farmer_id: farmerId } : undefined,
  });
}
