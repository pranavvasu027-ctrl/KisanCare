/**
 * KisanCare Crop Disease & Pest Detection Service
 * Connects to live /api/v1/disease-detection and /api/v1/pest-detection endpoints.
 * Explicitly powered by an Agronomic Rule-Based Expert System on the central backend.
 */

import { apiClient } from './apiClient';
import { ENDPOINTS } from './endpoints';
import {
  CropImageMetadata,
  DiseaseDetectionRequest,
  DiseaseDetectionResponse,
  PestDetectionRequest,
  PestDetectionResponse,
} from '@/types';

export const SUPPORTED_CROPS = [
  'Soybean',
  'Cotton',
  'Tomato',
  'Wheat',
  'Rice',
  'Corn',
  'Onion',
] as const;

export const COMMON_DISEASE_SYMPTOMS = [
  { id: 'yellow_leaves', label: 'Yellow leaves', keyword: 'yellow leaves' },
  { id: 'stunted_growth', label: 'Stunted growth', keyword: 'stunted growth' },
  { id: 'white_powdery_spots', label: 'White powdery spots', keyword: 'white powdery spots' },
  { id: 'black_spots', label: 'Black spots / lesions', keyword: 'black spots' },
  { id: 'wilting', label: 'Wilting / Drooping', keyword: 'wilting' },
] as const;

export const COMMON_PEST_SYMPTOMS = [
  { id: 'holes_in_leaves', label: 'Holes in leaves / chewed foliage', keyword: 'holes in leaves' },
  { id: 'sticky_residue', label: 'Sticky residue / honeydew', keyword: 'sticky residue' },
  { id: 'curled_leaves', label: 'Curled / distorted leaves', keyword: 'curled leaves' },
  { id: 'webbing', label: 'Fine silk webbing', keyword: 'webbing' },
] as const;

export const MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024; // 5 MB

export function validateSymptomsRequest(payload: DiseaseDetectionRequest): {
  isValid: boolean;
  error?: string;
} {
  if (!payload.crop || payload.crop.trim().length === 0) {
    return { isValid: false, error: 'Host crop is required' };
  }
  if (!Array.isArray(payload.symptoms) || payload.symptoms.length === 0) {
    return { isValid: false, error: 'At least one observed symptom must be selected' };
  }
  return { isValid: true };
}

export function validateImageMetadata(metadata?: CropImageMetadata | null): {
  isValid: boolean;
  error?: string;
} {
  if (!metadata) {
    return { isValid: true }; // Image is optional documentation for rule-based engine
  }

  if (metadata.fileSize && metadata.fileSize > MAX_IMAGE_SIZE_BYTES) {
    return {
      isValid: false,
      error: `Image file exceeds maximum allowable size of 5 MB (${(metadata.fileSize / (1024 * 1024)).toFixed(1)} MB)`,
    };
  }

  if (metadata.mimeType) {
    const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
    if (!validTypes.includes(metadata.mimeType.toLowerCase())) {
      return {
        isValid: false,
        error: `Unsupported image format (${metadata.mimeType}). Accepted: JPEG, PNG, WEBP.`,
      };
    }
  }

  return { isValid: true };
}

/**
 * Executes foliar disease detection against the central backend rule-based engine.
 * Sends JSON symptoms payload (images are not uploaded to this JSON endpoint).
 */
export async function detectDisease(
  payload: DiseaseDetectionRequest
): Promise<DiseaseDetectionResponse> {
  const validation = validateSymptomsRequest(payload);
  if (!validation.isValid) {
    throw new Error(validation.error);
  }

  return apiClient.post<DiseaseDetectionResponse>(
    ENDPOINTS.DISEASE_DETECTION,
    {
      crop: payload.crop.trim(),
      symptoms: payload.symptoms,
    },
    { timeoutMs: 15_000 }
  );
}

/**
 * Executes pest detection against the central backend rule-based engine.
 * Sends JSON symptoms payload.
 */
export async function detectPest(
  payload: PestDetectionRequest
): Promise<PestDetectionResponse> {
  const validation = validateSymptomsRequest(payload);
  if (!validation.isValid) {
    throw new Error(validation.error);
  }

  return apiClient.post<PestDetectionResponse>(
    ENDPOINTS.PEST_DETECTION,
    {
      crop: payload.crop.trim(),
      symptoms: payload.symptoms,
    },
    { timeoutMs: 15_000 }
  );
}
