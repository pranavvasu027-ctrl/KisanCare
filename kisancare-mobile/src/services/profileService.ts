/**
 * KisanCare Farmer Profile Service
 * Manages farmer personal details, agricultural holdings, and language settings.
 */

import { FarmerProfile } from '@/types';
import { setLanguage, SupportedLanguage } from '@/utils/localization';

export type { FarmerProfile };

const DEFAULT_PROFILE: FarmerProfile = {
  id: 'farmer-ramesh-1',
  fullName: 'Ramesh Kumar',
  phone: '9876543210',
  email: 'ramesh.farmer@kisancare.in',
  village: 'Shioni',
  taluka: 'Baramati',
  district: 'Pune',
  state: 'Maharashtra',
  isVerified: true,
  registeredDate: '15 Jan 2026',
  preferredLanguage: 'en',
  totalLandAcres: 5.2,
  primaryCrops: ['Soybean (JS 335)', 'Onion (Bhima Super)'],
};

let activeProfile: FarmerProfile = { ...DEFAULT_PROFILE };

export function getStoredProfile(): FarmerProfile {
  return { ...activeProfile };
}

export interface ProfileValidationResult {
  isValid: boolean;
  errors: Record<string, string>;
}

export function validateProfile(data: Partial<FarmerProfile>): ProfileValidationResult {
  const errors: Record<string, string> = {};

  if (!data.fullName || data.fullName.trim().length < 2) {
    errors.fullName = 'Please enter a valid farmer name (at least 2 characters)';
  }

  if (!data.phone || !/^\d{10}$/.test(data.phone.replace(/[\s-+]/g, '').slice(-10))) {
    errors.phone = 'Please enter a valid 10-digit mobile number';
  }

  if (data.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.email.trim())) {
    errors.email = 'Please enter a valid email address';
  }

  if (!data.district || data.district.trim().length === 0) {
    errors.district = 'District is required';
  }

  if (!data.state || data.state.trim().length === 0) {
    errors.state = 'State is required';
  }

  return {
    isValid: Object.keys(errors).length === 0,
    errors,
  };
}

export async function saveProfile(updated: Partial<FarmerProfile>): Promise<FarmerProfile> {
  const validation = validateProfile({ ...activeProfile, ...updated });
  if (!validation.isValid) {
    const firstError = Object.values(validation.errors)[0];
    throw new Error(firstError);
  }

  activeProfile = {
    ...activeProfile,
    ...updated,
  };

  if (updated.preferredLanguage) {
    setLanguage(updated.preferredLanguage as SupportedLanguage);
  }

  return { ...activeProfile };
}
