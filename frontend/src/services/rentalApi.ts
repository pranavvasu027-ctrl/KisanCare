/**
 * API client service for KisanCare Agricultural Rental Marketplace.
 * Connects with FastAPI backend (/api/v1/rentals/...) with automatic token injection.
 */

import { supabase } from './supabase';
import {
  RentalListing,
  RentalBooking,
  PriceCalculationRequest,
  PriceCalculationResult,
  AvailabilityCheckRequest,
  AvailabilityCheckResult,
  BookingCreatePayload,
  MarketRateBenchmark,
  SmartRecommendationsResponse,
  RentalReview
} from '../types/rental';

async function fetchWithAuth(url: string, options: RequestInit = {}): Promise<any> {
  const headers = new Headers(options.headers || {});
  if (!headers.has('Content-Type') && options.body && typeof options.body === 'string') {
    headers.set('Content-Type', 'application/json');
  }

  try {
    const { data: { session } } = await supabase.auth.getSession();
    if (session?.access_token && !headers.has('Authorization')) {
      headers.set('Authorization', `Bearer ${session.access_token}`);
    }
  } catch {
    // Supabase auth bypass/offline
  }

  const response = await fetch(url, { ...options, headers });
  if (!response.ok) {
    let message = `API request failed: ${response.status} ${response.statusText}`;
    try {
      const err = await response.json();
      if (typeof err.detail === 'string') {
        message = err.detail;
      } else if (err.message) {
        message = err.message;
      }
    } catch {
      // Non-JSON error
    }
    throw new Error(message);
  }
  return await response.json();
}

export const rentalApi = {
  // 1. Listings & Geography
  getGeography: async (): Promise<Record<string, any>> => {
    return await fetchWithAuth('/api/v1/rentals/geography');
  },

  getListings: async (filters: {
    category?: string;
    subcategory?: string;
    division?: string;
    district?: string;
    taluka?: string;
    query?: string;
    max_price?: number;
    billing_unit?: string;
    verified_only?: boolean;
    sort_by?: string;
  } = {}): Promise<RentalListing[]> => {
    const params = new URLSearchParams();
    if (filters.category) params.append('category', filters.category);
    if (filters.subcategory) params.append('subcategory', filters.subcategory);
    if (filters.division) params.append('division', filters.division);
    if (filters.district) params.append('district', filters.district);
    if (filters.taluka) params.append('taluka', filters.taluka);
    if (filters.query) params.append('query', filters.query);
    if (filters.max_price) params.append('max_price', filters.max_price.toString());
    if (filters.billing_unit) params.append('billing_unit', filters.billing_unit);
    if (filters.verified_only) params.append('verified_only', 'true');
    if (filters.sort_by) params.append('sort_by', filters.sort_by);

    const qs = params.toString() ? `?${params.toString()}` : '';
    return await fetchWithAuth(`/api/v1/rentals/listings${qs}`);
  },

  getListing: async (listingId: string): Promise<RentalListing> => {
    return await fetchWithAuth(`/api/v1/rentals/listings/${listingId}`);
  },

  // 2. Server-side price calculation
  calculatePrice: async (payload: PriceCalculationRequest): Promise<PriceCalculationResult> => {
    return await fetchWithAuth('/api/v1/rentals/calculate-price', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  // 3. Concurrency-safe availability check
  checkAvailability: async (payload: AvailabilityCheckRequest): Promise<AvailabilityCheckResult> => {
    return await fetchWithAuth('/api/v1/rentals/check-availability', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  // 4. Booking creation
  createBooking: async (payload: BookingCreatePayload): Promise<RentalBooking> => {
    return await fetchWithAuth('/api/v1/rentals/bookings', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  // 5. Bookings management
  getBookings: async (
    farmerId?: string,
    filter: 'all' | 'upcoming' | 'active' | 'history' = 'all'
  ): Promise<RentalBooking[]> => {
    const params = new URLSearchParams({ filter });
    if (farmerId) params.append('farmer_id', farmerId);
    return await fetchWithAuth(`/api/v1/rentals/bookings?${params.toString()}`);
  },

  getBooking: async (bookingId: string): Promise<RentalBooking> => {
    return await fetchWithAuth(`/api/v1/rentals/bookings/${bookingId}`);
  },

  cancelBooking: async (bookingId: string, reason: string): Promise<RentalBooking> => {
    return await fetchWithAuth(`/api/v1/rentals/bookings/${bookingId}/cancel`, {
      method: 'POST',
      body: JSON.stringify({ reason, cancelled_by: 'farmer' })
    });
  },

  // 6. Owner / Provider controls
  getOwnerListings: async (providerId?: string): Promise<RentalListing[]> => {
    const qs = providerId ? `?provider_id=${providerId}` : '';
    return await fetchWithAuth(`/api/v1/rentals/owner/listings${qs}`);
  },

  getOwnerRequests: async (providerId?: string): Promise<RentalBooking[]> => {
    const qs = providerId ? `?provider_id=${providerId}` : '';
    return await fetchWithAuth(`/api/v1/rentals/owner/requests${qs}`);
  },

  respondToBooking: async (
    bookingId: string,
    action: 'confirm' | 'reject',
    reason?: string
  ): Promise<RentalBooking> => {
    return await fetchWithAuth(`/api/v1/rentals/owner/bookings/${bookingId}/respond`, {
      method: 'POST',
      body: JSON.stringify({ action, reason })
    });
  },

  updateDispatchStatus: async (
    bookingId: string,
    dispatchStatus: string
  ): Promise<RentalBooking> => {
    return await fetchWithAuth(`/api/v1/rentals/owner/bookings/${bookingId}/dispatch`, {
      method: 'POST',
      body: JSON.stringify({ dispatch_status: dispatchStatus })
    });
  },

  createListing: async (payload: any, providerId?: string): Promise<RentalListing> => {
    const qs = providerId ? `?provider_id=${providerId}` : '';
    return await fetchWithAuth(`/api/v1/rentals/owner/listings${qs}`, {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  // 7. Farm Economics & Memory Link
  recordExpenseToFarm: async (
    bookingId: string,
    payload: {
      farm_id: string;
      field_id: string;
      season?: string;
      crop?: string;
      expense_category?: 'machinery_rental' | 'labour_hire' | 'transport';
    }
  ): Promise<any> => {
    return await fetchWithAuth(`/api/v1/rentals/bookings/${bookingId}/record-expense`, {
      method: 'POST',
      body: JSON.stringify({
        farm_id: payload.farm_id,
        field_id: payload.field_id,
        season: payload.season || 'Kharif 2026',
        crop: payload.crop || 'Cotton',
        expense_category: payload.expense_category || 'machinery_rental'
      })
    });
  },

  // 8. Benchmarks & Recommendations
  getMarketBenchmarks: async (
    category?: string,
    district: string = 'Akola'
  ): Promise<MarketRateBenchmark[]> => {
    const params = new URLSearchParams({ district });
    if (category) params.append('category', category);
    return await fetchWithAuth(`/api/v1/rentals/market-rates?${params.toString()}`);
  },

  submitReview: async (payload: {
    booking_id: string;
    listing_id: string;
    farmer_name: string;
    rating: number;
    review_text: string;
  }): Promise<RentalReview> => {
    return await fetchWithAuth('/api/v1/rentals/reviews', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  getRecommendations: async (
    crop: string = 'Cotton',
    acreage: number = 4.5,
    task?: string
  ): Promise<SmartRecommendationsResponse> => {
    const params = new URLSearchParams({ crop, acreage: acreage.toString() });
    if (task) params.append('task', task);
    return await fetchWithAuth(`/api/v1/rentals/recommendations?${params.toString()}`);
  }
};
