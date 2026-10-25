/**
 * KisanCare Mobile Type Definitions
 * Strict TypeScript models for UI components, Farm Management, Profile, and API sync.
 */

export interface WeatherData {
  temperature: number;
  condition: string;
  humidity: number;
  windSpeed: number;
  rainfallMm?: number;
  location: string;
  riskLevel: 'low' | 'moderate' | 'high';
  riskMessage: string;
}

export interface FarmOverview {
  farmName: string;
  farmerName: string;
  location: string;
  totalAcres: number;
  soilType: string;
  waterSource: string;
  activeCrops: string[];
}

export interface BackendFarmRecord {
  id: string;
  farm_name: string;
  location: string;
  latitude?: number | null;
  longitude?: number | null;
  has_precise_coordinates?: boolean;
  total_area: number;
  area_unit: string;
  status: string;
  crops?: string[];
  active_crop?: string;
  sowing_date?: string;
  created_at?: string;
}

export interface BackendFarmsResponse {
  farms: BackendFarmRecord[];
  count: number;
  is_mock: boolean;
}

export interface FarmCreatePayload {
  farmer_id: string;
  location: string;
  area: number;
  farm_name?: string;
  latitude?: number;
  longitude?: number;
  crops?: string[];
}

export interface FarmCreateResponse {
  farm_id: string;
  status: string;
  data: FarmCreatePayload;
  is_mock: boolean;
}

export interface FieldItem {
  id: string;
  name: string;
  crop: string;
  acres: number;
  sowingDate: string;
  expectedHarvest: string;
  growthStage: string;
  healthScore: number;
  soilMoisturePct: number;
}

export interface AdvisoryItem {
  id: string;
  category: 'irrigation' | 'pest' | 'fertilizer' | 'market' | 'weather' | 'soil';
  title: string;
  description: string;
  priority: 'urgent' | 'recommended' | 'info';
  timestamp: string;
  actionText?: string;
  actionRoute?: string;
  modelType?: 'RULE_BASED' | 'AI_COPILOT' | 'METEOROLOGICAL' | 'RANDOM_FOREST' | 'HEURISTIC';
  source?: string;
}

// --- Crop Recommendation ---
export type CropSeason = 'Kharif' | 'Rabi' | 'Summer' | 'Whole Year';
export type WaterAvailability = 'Low' | 'Medium' | 'High';

export interface CropRecommendationRequest {
  district: string;
  season: CropSeason;
  water_availability: WaterAvailability;
  top_k?: number;
}

export interface CropRecommendationItem {
  crop: string;
  predicted_area_frequency: number;
  rank: number;
}

export interface CropFilteredCandidate {
  crop: string;
  model_score: number;
  eligible: boolean;
  filter_reason: string;
}

export interface CropRecommendationResponse {
  model_version: string;
  district: string;
  season: string;
  water_availability: string;
  status: 'SUCCESS' | 'NO_ELIGIBLE_CROP' | 'ERROR';
  recommendations: CropRecommendationItem[];
  filtered_candidates?: CropFilteredCandidate[];
  data_source: string;
  score_interpretation: string;
  latency_ms: number;
  is_mock?: boolean;
}

// --- Soil Assessment ---
export interface SoilAssessmentRequest {
  n: number;
  p: number;
  k: number;
  ph: number;
}

export interface SoilAssessmentResponse {
  model_type: string;
  overall_status: 'Healthy' | 'Deficient/Imbalanced' | string;
  issues: string[];
  recommendation: string;
}

// --- Irrigation & Weather Risk ---
export interface IrrigationRequest {
  crop: string;
  soil_moisture: number;
  days_since_rain: number;
}

export interface IrrigationResponse {
  model_type: string;
  irrigation_required: boolean;
  recommended_amount_liters_per_acre: number;
  reasoning: string;
}

export interface WeatherRiskRequest {
  temperature: number;
  humidity: number;
  rainfall_forecast: number;
}

export interface WeatherRiskResponse {
  model_type: string;
  overall_risk: 'High' | 'Medium' | 'Low' | string;
  identified_risks: string[];
  mitigation: string;
}

// --- Disease & Pest Detection ---
export interface SymptomsRequest {
  crop: string;
  symptoms: string[];
}

export type DiseaseDetectionRequest = SymptomsRequest;
export type PestDetectionRequest = SymptomsRequest;

export interface DetectionResponse {
  model_type: string;
  prediction: string;
  confidence: number;
  treatment: string;
}

export type DiseaseDetectionResponse = DetectionResponse;
export type PestDetectionResponse = DetectionResponse;

export interface CropImageMetadata {
  uri: string;
  width?: number;
  height?: number;
  fileSize?: number;
  fileName?: string;
  mimeType?: string;
}

export interface MarketPriceItem {
  id: string;
  cropName: string;
  variety?: string;
  marketName: string;
  currentPrice: number;
  previousPrice: number;
  unit: string;
  trend: 'up' | 'down' | 'stable';
  changeAmount: number;
  changePercentage: number;
  updatedAt: string;
}

export interface QuickActionItem {
  id: string;
  title: string;
  subtitle: string;
  icon: string;
  route: string;
  badge?: string;
}

export interface FarmerProfile {
  id: string;
  fullName: string;
  phone: string;
  email?: string;
  village: string;
  taluka?: string;
  district: string;
  state: string;
  isVerified: boolean;
  registeredDate: string;
  preferredLanguage: 'en' | 'hi' | 'mr';
  totalLandAcres?: number;
  primaryCrops?: string[];
}

export interface AuthUser {
  id: string;
  phone?: string;
  email?: string;
  role: 'farmer' | 'expert' | 'admin';
  createdAt: string;
}

export interface AuthSession {
  accessToken: string;
  refreshToken?: string;
  user: AuthUser;
  expiresAt?: number;
}
