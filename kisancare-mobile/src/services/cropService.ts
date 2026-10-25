/**
 * KisanCare Crop Recommendation Service
 * Connects to live /api/v1/crop-recommendation endpoint.
 * Powered by trained Random Forest model (APY 2005-2015) & CropDecisionEngine.
 */

import { apiClient } from './apiClient';
import { ENDPOINTS } from './endpoints';
import {
  CropRecommendationRequest,
  CropRecommendationResponse,
  CropSeason,
  WaterAvailability,
} from '@/types';

export const VALID_MAHARASHTRA_DISTRICTS = [
  'AKOLA',
  'AMRAVATI',
  'AURANGABAD',
  'BEED',
  'BHANDARA',
  'BULDHANA',
  'CHANDRAPUR',
  'DHULE',
  'GADCHIROLI',
  'GONDIA',
  'HINGOLI',
  'JALGAON',
  'JALNA',
  'KOLHAPUR',
  'LATUR',
  'MUMBAI',
  'NAGPUR',
  'NANDED',
  'NANDURBAR',
  'NASHIK',
  'OSMANABAD',
  'PALGHAR',
  'PARBHANI',
  'PUNE',
  'RAIGAD',
  'RATNAGIRI',
  'SANGLI',
  'SATARA',
  'SINDHUDURG',
  'SOLAPUR',
  'THANE',
  'WARDHA',
  'WASHIM',
  'YAVATMAL',
] as const;

export const VALID_SEASONS: CropSeason[] = ['Kharif', 'Rabi', 'Summer', 'Whole Year'];
export const VALID_WATER_LEVELS: WaterAvailability[] = ['Low', 'Medium', 'High'];

export function normalizeDistrictName(rawDistrict: string): string {
  if (!rawDistrict) return 'AKOLA';
  const clean = rawDistrict.replace(/\b(district|dist\.?)\b/gi, '').trim().toUpperCase();
  const found = VALID_MAHARASHTRA_DISTRICTS.find((d) => d === clean);
  return found || clean;
}

export function validateCropInputs(payload: CropRecommendationRequest): { isValid: boolean; error?: string } {
  if (!payload.district || payload.district.trim().length === 0) {
    return { isValid: false, error: 'District is required' };
  }

  const cleanDistrict = payload.district.trim().toUpperCase();
  const districtExists = VALID_MAHARASHTRA_DISTRICTS.includes(
    cleanDistrict as (typeof VALID_MAHARASHTRA_DISTRICTS)[number]
  );
  if (!districtExists) {
    return {
      isValid: false,
      error: `Unknown district "${payload.district}". Must be a valid Maharashtra district.`,
    };
  }

  if (!VALID_SEASONS.includes(payload.season)) {
    return { isValid: false, error: `Invalid season "${payload.season}". Allowed: ${VALID_SEASONS.join(', ')}` };
  }

  if (!VALID_WATER_LEVELS.includes(payload.water_availability)) {
    return {
      isValid: false,
      error: `Invalid water availability "${payload.water_availability}". Allowed: ${VALID_WATER_LEVELS.join(', ')}`,
    };
  }

  const topK = payload.top_k ?? 5;
  if (!Number.isInteger(topK) || topK < 1 || topK > 20) {
    return { isValid: false, error: 'top_k must be an integer between 1 and 20' };
  }

  return { isValid: true };
}

export async function fetchCropRecommendations(
  payload: CropRecommendationRequest
): Promise<CropRecommendationResponse> {
  const validation = validateCropInputs(payload);
  if (!validation.isValid) {
    throw new Error(validation.error);
  }

  const formattedPayload = {
    district: payload.district.trim().toUpperCase(),
    season: payload.season,
    water_availability: payload.water_availability,
    top_k: payload.top_k ?? 5,
  };

  return apiClient.post<CropRecommendationResponse>(
    ENDPOINTS.CROP_RECOMMENDATION,
    formattedPayload,
    { timeoutMs: 15_000 }
  );
}
