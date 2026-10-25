/**
 * KisanCare Farm Management Service
 * Connects to live /api/v1/farms endpoint (GET & POST).
 */

import { apiClient } from './apiClient';
import { ENDPOINTS } from './endpoints';
import {
  BackendFarmRecord,
  BackendFarmsResponse,
  FarmCreatePayload,
  FarmCreateResponse,
} from '@/types';

export interface FarmDisplayItem {
  id: string;
  name: string;
  location: string;
  areaAcres: number;
  status: string;
  isMock: boolean;
  crops: string[];
  activeCrop?: string;
  sowingDate?: string;
}

export async function fetchFarms(): Promise<{
  farms: FarmDisplayItem[];
  isMock: boolean;
  count: number;
}> {
  const response = await apiClient.get<BackendFarmsResponse>(ENDPOINTS.FARMS);

  const farms: FarmDisplayItem[] = (response.farms || []).map((farm: BackendFarmRecord) => ({
    id: farm.id,
    name: farm.farm_name || `Farm (${farm.location})`,
    location: farm.location,
    areaAcres: Number(farm.total_area) || 0,
    status: farm.status || 'ACTIVE',
    isMock: Boolean(response.is_mock),
    crops: farm.crops && farm.crops.length > 0 ? farm.crops : ['Cotton', 'Soybean'],
    activeCrop: farm.active_crop,
    sowingDate: farm.sowing_date,
  }));

  return {
    farms,
    isMock: Boolean(response.is_mock),
    count: response.count || farms.length,
  };
}

export async function createFarm(payload: FarmCreatePayload): Promise<FarmCreateResponse> {
  // Validate inputs client-side
  if (!payload.farmer_id || payload.farmer_id.trim().length === 0) {
    throw new Error('Farmer ID is required');
  }
  if (!payload.location || payload.location.trim().length === 0) {
    throw new Error('Farm location is required');
  }
  if (!payload.area || payload.area <= 0) {
    throw new Error('Farm area must be greater than 0 acres');
  }

  return apiClient.post<FarmCreateResponse>(ENDPOINTS.FARMS, {
    farmer_id: payload.farmer_id.trim(),
    location: payload.location.trim(),
    area: Number(payload.area),
    farm_name: payload.farm_name?.trim() || undefined,
    latitude: payload.latitude,
    longitude: payload.longitude,
  });
}

export interface FarmCropAssignPayload {
  crop: string;
  sowing_date?: string;
}

export interface FarmCropAssignResponse {
  status: string;
  farm_id: string;
  active_crop: string;
  sowing_date?: string;
  is_mock?: boolean;
}

export async function assignCropToFarm(
  farmId: string,
  payload: FarmCropAssignPayload
): Promise<FarmCropAssignResponse> {
  if (!farmId || farmId.trim().length === 0) {
    throw new Error('Farm ID is required');
  }
  if (!payload.crop || payload.crop.trim().length === 0) {
    throw new Error('Crop name is required');
  }

  return apiClient.put<FarmCropAssignResponse>(
    `${ENDPOINTS.FARMS}/${encodeURIComponent(farmId)}/crop`,
    {
      crop: payload.crop.trim(),
      sowing_date: payload.sowing_date?.trim(),
    }
  );
}
