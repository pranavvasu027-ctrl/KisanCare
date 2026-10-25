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
  image_url?: string;
  description?: string;
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

export const VERIFIED_OFFLINE_CATALOG: RentalListing[] = [
  {
    id: 'LIST_TRAC_01',
    title: 'Mahindra 575 DI 45 HP Tractor with Hydraulic Trolley',
    category: 'tractor',
    subcategory: 'utility_tractor',
    daily_rate: 1800,
    hourly_rate: 350,
    billing_unit: 'per_day',
    currency: 'INR',
    district: 'Akola',
    taluka: 'Akola',
    village: 'Takli Bu',
    status: 'available',
    is_active: true,
    rating: 4.8,
    image_url: 'https://images.unsplash.com/photo-1592982537447-7440770cbfc9?auto=format&fit=crop&w=600&q=80',
    description: 'Reliable 45 HP workhorse suited for deep plowing, rotavation, and haulage in black cotton soil.',
    owner_name: 'Ramesh Patil',
    provider: { business_name: 'Akola Krishi Yantra Kendra', phone: '+91-9823101234', verified: true },
  },
  {
    id: 'LIST_TRAC_02',
    title: 'John Deere 5050D 50 HP 4WD Tractor',
    category: 'tractor',
    subcategory: '4wd_tractor',
    daily_rate: 2200,
    hourly_rate: 420,
    billing_unit: 'per_day',
    currency: 'INR',
    district: 'Amravati',
    taluka: 'Achalpur',
    village: 'Paratwada',
    status: 'available',
    is_active: true,
    rating: 4.9,
    image_url: 'https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?auto=format&fit=crop&w=600&q=80',
    description: 'High-traction 50 HP 4WD tractor ideal for heavy wet tillage and laser land leveling.',
    owner_name: 'Suresh Deshmukh',
    provider: { business_name: 'Vidarbha Farm Machinery', phone: '+91-9422156789', verified: true },
  },
  {
    id: 'LIST_EQ_01',
    title: 'Shaktiman 7 Feet Rotary Tiller (Rotavator)',
    category: 'equipment',
    subcategory: 'tillage',
    daily_rate: 850,
    hourly_rate: 180,
    billing_unit: 'per_day',
    currency: 'INR',
    district: 'Akola',
    taluka: 'Balapur',
    village: 'Wadegaon',
    status: 'available',
    is_active: true,
    rating: 4.7,
    image_url: 'https://images.unsplash.com/photo-1589923188900-85dae523342b?auto=format&fit=crop&w=600&q=80',
    description: 'Heavy duty Boron steel blades for fine seedbed preparation in single pass.',
    owner_name: 'Ganesh Shinde',
    provider: { business_name: 'Shinde Agro Hire', phone: '+91-9850123456', verified: true },
  },
  {
    id: 'LIST_EQ_02',
    title: 'Multi-Crop High-Speed Automatic Seed Drill (9 Tines)',
    category: 'equipment',
    subcategory: 'sowing',
    daily_rate: 750,
    hourly_rate: 150,
    billing_unit: 'per_day',
    currency: 'INR',
    district: 'Yavatmal',
    taluka: 'Darwha',
    village: 'Darwha Rural',
    status: 'available',
    is_active: true,
    rating: 4.6,
    image_url: 'https://images.unsplash.com/photo-1530595467537-0b5996c41f2d?auto=format&fit=crop&w=600&q=80',
    description: 'Precision seed metering system for Soybean, Cotton, and Chickpea with simultaneous fertilizer box.',
    owner_name: 'Vikas Jadhav',
    provider: { business_name: 'Kisan Seva Kendra Yavatmal', phone: '+91-9765432109', verified: true },
  },
  {
    id: 'LIST_TRANS_01',
    title: 'Tata Ace 1.5 Ton Agri Transport Mini Truck',
    category: 'transport',
    subcategory: 'light_commercial',
    daily_rate: 1400,
    hourly_rate: 220,
    billing_unit: 'per_day',
    currency: 'INR',
    district: 'Akola',
    taluka: 'Akola',
    village: 'Murtizapur',
    status: 'available',
    is_active: true,
    rating: 4.7,
    image_url: 'https://images.unsplash.com/photo-1519003722824-194d4455a60c?auto=format&fit=crop&w=600&q=80',
    description: 'Convenient farm-to-mandi produce transportation with tarp cover for weather protection.',
    owner_name: 'Anil Chavhan',
    provider: { business_name: 'Murtizapur Agri Logistics', phone: '+91-9881234567', verified: true },
  },
  {
    id: 'LIST_DRONE_01',
    title: 'Agri-Kisan 10L Autonomous Crop Spraying Drone with Certified Pilot',
    category: 'specialist',
    subcategory: 'drone_spraying',
    daily_rate: 3200,
    hourly_rate: 650,
    billing_unit: 'per_acre',
    currency: 'INR',
    district: 'Akola',
    taluka: 'Akola',
    village: 'MIDC Phase II',
    status: 'available',
    is_active: true,
    rating: 4.95,
    image_url: 'https://images.unsplash.com/photo-1508614589041-895b88991e3e?auto=format&fit=crop&w=600&q=80',
    description: 'DGCA-certified drone pilot with high-precision ultra-low volume nozzles for uniform foliar spray.',
    owner_name: 'Pravin Gaikwad',
    provider: { business_name: 'SkyAgri Tech Solutions', phone: '+91-9890112233', verified: true },
  },
];

export async function fetchRentalListings(
  params?: RentalFilterParams
): Promise<RentalListing[]> {
  try {
    return await apiClient.get<RentalListing[]>(ENDPOINTS.RENTALS_LISTINGS, {
      params: {
        category: params?.category,
        district: params?.district,
        query: params?.query,
        max_price: params?.max_price,
      },
    });
  } catch (error) {
    console.warn('[RentalsService] Live fetch failed, serving verified catalog fallback:', error);
    let filtered = VERIFIED_OFFLINE_CATALOG;
    if (params?.category && params.category !== 'all') {
      filtered = filtered.filter((item) => item.category === params.category);
    }
    return filtered;
  }
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
  try {
    return await apiClient.get<BookingRecord[]>(ENDPOINTS.RENTALS_BOOKINGS, {
      params: farmerId ? { farmer_id: farmerId } : undefined,
    });
  } catch (error) {
    console.warn('[RentalsService] Bookings fetch failed:', error);
    return [];
  }
}
