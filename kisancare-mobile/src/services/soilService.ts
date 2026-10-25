/**
 * KisanCare Soil Intelligence Service
 * Connects to live /api/v1/soil-assessment endpoint.
 * Evaluates soil NPK and pH via agronomic heuristic rules.
 */

import { apiClient } from './apiClient';
import { ENDPOINTS } from './endpoints';
import { SoilAssessmentRequest, SoilAssessmentResponse } from '@/types';

export interface SoilNutrientStatus {
  name: string;
  chemicalSymbol: string;
  value: number;
  unit: string;
  rating: 'Low' | 'Medium' | 'High' | 'Optimal' | 'Acidic' | 'Alkaline';
  benchmark: string;
  description: string;
}

export function validateSoilInputs(payload: SoilAssessmentRequest): { isValid: boolean; error?: string } {
  if (typeof payload.n !== 'number' || isNaN(payload.n) || payload.n < 0) {
    return { isValid: false, error: 'Nitrogen (N) must be a non-negative number' };
  }
  if (typeof payload.p !== 'number' || isNaN(payload.p) || payload.p < 0) {
    return { isValid: false, error: 'Phosphorus (P) must be a non-negative number' };
  }
  if (typeof payload.k !== 'number' || isNaN(payload.k) || payload.k < 0) {
    return { isValid: false, error: 'Potassium (K) must be a non-negative number' };
  }
  if (typeof payload.ph !== 'number' || isNaN(payload.ph) || payload.ph < 0 || payload.ph > 14) {
    return { isValid: false, error: 'Soil pH must be between 0 and 14' };
  }
  return { isValid: true };
}

export function computeNutrientBreakdown(payload: SoilAssessmentRequest): SoilNutrientStatus[] {
  // ICAR agronomic reference ratings
  const nRating: SoilNutrientStatus['rating'] = payload.n < 20 ? 'Low' : payload.n > 50 ? 'High' : 'Optimal';
  const pRating: SoilNutrientStatus['rating'] = payload.p < 10 ? 'Low' : 'Optimal';
  const kRating: SoilNutrientStatus['rating'] = payload.k < 150 ? 'Low' : 'Optimal';

  let phRating: SoilNutrientStatus['rating'] = 'Optimal';
  if (payload.ph < 5.5) phRating = 'Acidic';
  else if (payload.ph > 7.5) phRating = 'Alkaline';

  return [
    {
      name: 'Available Nitrogen',
      chemicalSymbol: 'N',
      value: payload.n,
      unit: 'kg/ha',
      rating: nRating,
      benchmark: '20 - 50 kg/ha',
      description: 'Crucial for vegetative growth, green foliage, and photosynthesis.',
    },
    {
      name: 'Available Phosphorus',
      chemicalSymbol: 'P',
      value: payload.p,
      unit: 'kg/ha',
      rating: pRating,
      benchmark: '≥ 10 kg/ha',
      description: 'Essential for root development, flowering, and energy transfer.',
    },
    {
      name: 'Available Potassium',
      chemicalSymbol: 'K',
      value: payload.k,
      unit: 'kg/ha',
      rating: kRating,
      benchmark: '≥ 150 kg/ha',
      description: 'Enhances drought tolerance, disease resistance, and grain filling.',
    },
    {
      name: 'Soil Reaction',
      chemicalSymbol: 'pH',
      value: payload.ph,
      unit: 'pH scale',
      rating: phRating,
      benchmark: '5.5 - 7.5',
      description: 'Controls nutrient availability and soil microbial activity.',
    },
  ];
}

export async function assessSoilNutrients(
  payload: SoilAssessmentRequest
): Promise<SoilAssessmentResponse> {
  const validation = validateSoilInputs(payload);
  if (!validation.isValid) {
    throw new Error(validation.error);
  }

  return apiClient.post<SoilAssessmentResponse>(
    ENDPOINTS.SOIL_ASSESSMENT,
    payload,
    { timeoutMs: 15_000 }
  );
}
