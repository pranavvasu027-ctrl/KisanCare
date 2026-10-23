export type Language = 'en' | 'mr' | 'hi';

export interface FarmerProfile {
  id: string;
  name: string;
  phone: string;
  email: string;
  state: string;
  district: string;
  village: string;
  preferredLanguage: Language;
  avatarUrl?: string;
  activeFarmId: string;
}

export interface Field {
  id: string;
  farmId: string;
  name: string;
  areaAcres: number;
  areaHectares: number;
  soilType: 'Alluvial' | 'Black' | 'Clay' | 'Laterite' | 'Red' | 'Loam' | 'Sandy Loam';
  soilPh: number;
  nitrogenKgHa: number;
  phosphorusKgHa: number;
  potassiumKgHa: number;
  currentCrop: string;
  sowingDate: string;
  cropStage: 'sowing' | 'vegetative' | 'flowering' | 'grain_filling' | 'maturity' | 'harvesting';
  irrigationMethod: 'Drip' | 'Sprinkler' | 'Canal/Flood' | 'Rainfed';
  soilMoistureFraction: number; // e.g. 0.22
  healthScore: number; // 0-100
  riskLevel: 'Low' | 'Moderate' | 'High';
  coordinates?: [number, number][];
}

export interface Farm {
  id: string;
  farmerId: string;
  name: string;
  state: string;
  district: string;
  village: string;
  totalAreaAcres: number;
  primaryCrops: string[];
  irrigationAvailability: 'Year-round Borewell' | 'Seasonal Canal' | 'Farm Pond + Drip' | 'Rainfed';
  fields: Field[];
}

export interface HistoricalRecord {
  id: string;
  year: number;
  season: 'Kharif' | 'Rabi' | 'Zaid/Summer';
  fieldId: string;
  fieldName: string;
  crop: string;
  cropImage: string;
  areaAcres: number;
  yieldQuintalsPerAcre: number;
  totalProductionQuintals: number;
  sellingPricePerQuintal: number;
  totalCostInr: number;
  totalRevenueInr: number;
  netProfitInr: number;
  majorEvents: string[];
  issues: string[];
  outcomeNotes: string;
  decisionNotes: string;
  soilTestSummary?: string;
}

export interface IrrigationAdvisoryResult {
  irrigation_required: boolean;
  irrigation_quantity_mm: number;
  irrigation_timing: 'today' | 'within_24h' | 'none';
  decision_date: string;
  crop: string;
  crop_stage: string;
  soil_type: string;
  soil_moisture: number;
  rainfall_mm: number;
  water_balance: {
    soil_water_depletion_mm: number;
    total_available_water_mm: number;
    readily_available_water_mm: number;
    crop_evapotranspiration_mm: number;
    reference_eto_mm: number;
    net_irrigation_requirement_mm: number;
  };
  decision_reason_codes: string[];
  warnings: string[];
  model_source: string;
}

export interface YieldPredictionResult {
  predicted_yield: number;
  yield_unit: string;
  estimated_production: number;
  production_unit: string;
  cultivated_area_hectares: number;
  model_source: string;
  input_summary: Record<string, any>;
  confidence_range?: { min: number; max: number };
  contributing_factors?: { factor: string; impact: string }[];
}

export interface CropRecommendationItem {
  crop: string;
  cropHindi: string;
  cropMarathi: string;
  image: string;
  suitabilityScore: number; // 0-100
  expectedYieldQuintalAcre: number;
  estimatedCostPerAcre: number;
  waterRequirementMm: number;
  riskLevel: 'Low' | 'Moderate' | 'High';
  estimatedNetProfitPerAcre: number;
  confidenceScore: number;
  reasoning: string;
  soilSuitability: string;
  climateSuitability: string;
  rotationBenefit: string;
}

export interface DiseaseDiagnosisResult {
  id: string;
  timestamp: string;
  fieldId: string;
  crop: string;
  imageUrl: string;
  detectedCondition: string;
  conditionType: 'Disease' | 'Pest' | 'Healthy' | 'Nutrient Deficiency';
  confidence: number;
  severity: 'Low' | 'Moderate' | 'Severe' | 'None';
  evidenceSummary: string;
  safeNextSteps: string[];
  ipmAdvisory: string[];
  expertReviewRecommended: boolean;
  modelProvenance: string;
}

export interface FarmRiskFactor {
  category: 'Climate' | 'Water' | 'Disease & Pest' | 'Yield' | 'Market' | 'Financial';
  score: number; // 0-100
  level: 'Low' | 'Moderate' | 'High' | 'Critical';
  factors: string[];
  impact: string;
  action: string;
  trend: 'up' | 'down' | 'stable';
}

export interface MarketPriceRecord {
  id: string;
  crop: string;
  mandi: string;
  state: string;
  date: string;
  modalPrice: number;
  minPrice: number;
  maxPrice: number;
  arrivalsTonnes: number;
  forecast7Day: number;
  volatility: 'Low' | 'Moderate' | 'High';
  trend: 'rising' | 'falling' | 'stable';
}

export interface DocumentItem {
  id: string;
  title: string;
  category: 'Soil Report' | 'Land Records (7/12)' | 'Crop Photograph' | 'Fertilizer/Pesticide Bill' | 'Market Receipt' | 'Insurance' | 'Loan Document' | 'Other';
  date: string;
  fileSize: string;
  fileType: string;
  fieldId?: string;
  season?: string;
  extractedValues?: Record<string, string | number>;
  status: 'Verified' | 'Pending Review' | 'OCR Processed';
  notes: string;
}

export interface GovernmentScheme {
  id: string;
  name: string;
  shortName: string;
  category: 'Direct Income Support' | 'Crop Insurance' | 'Irrigation Subsidy' | 'Soil Health' | 'Farm Machinery' | 'Credit Support';
  applicableStates: string[];
  benefits: string;
  maxAmountInr?: number;
  eligibilityCriteria: string[];
  documentsRequired: string[];
  applicationProcess: string;
  portalUrl: string;
  lastVerifiedDate: string;
  farmerEligible: boolean;
  matchScore: number;
}

export interface NotificationAlert {
  id: string;
  title: string;
  category: 'Weather' | 'Irrigation' | 'Crop Health' | 'Disease & Pest' | 'Yield' | 'Market' | 'Financial' | 'System';
  severity: 'Critical' | 'Warning' | 'Info';
  message: string;
  timestamp: string;
  fieldId?: string;
  fieldName?: string;
  actionLabel?: string;
  actionRoute?: string;
  isRead: boolean;
}

export interface SimulatorScenario {
  id: string;
  name: string;
  crop: string;
  areaAcres: number;
  rainfallChangePercent: number; // e.g. -20% or +15%
  irrigationAvailability: 'Full' | 'Reduced' | 'Deficit';
  fertilizerCostDeltaPercent: number;
  seedCostDeltaPercent: number;
  sellingPriceInr: number;
  harvestTimingDays: number;
  storageDurationMonths: number;
  
  // Computed metrics
  yieldQuintalAcre: number;
  waterRequirementMm: number;
  totalCostInr: number;
  totalRevenueInr: number;
  netProfitInr: number;
  riskScore: number;
  breakEvenPriceInr: number;
}

// Backend Integration Schemas
export interface DigitalTwinState {
  crop: string;
  soil_moisture: number;
  temperature: number;
  cadastral_parcels?: number;
  irrigation_source?: string;
  health_score?: number;
  last_synced?: string;
  [key: string]: any;
}

export interface DigitalTwinResponse {
  farm_id: string;
  state: DigitalTwinState;
}

export interface SimulationMetricSet {
  yield: number;
  cost: number;
  revenue: number;
  profit: number;
  risk: number;
}

export interface SimulationResponse {
  baseline: SimulationMetricSet;
  scenario: SimulationMetricSet;
  differences: {
    profit_diff: number;
    [key: string]: any;
  };
  explanation: string[];
}

export interface EconomicsRequest {
  expected_yield?: number;
  expected_price?: number;
  input_cost?: number;
  labour_cost?: number;
  irrigation_cost?: number;
}

export interface EconomicsResponse {
  total_cost: number;
  expected_revenue: number;
  expected_profit: number;
  roi_percent: number;
  break_even_price: number;
}

export interface CropRecommendationScoreBreakdown {
  crop: string;
  soil_climate_score: number;
  regional_score: number;
  region_score?: number;
  history_rotation_score: number;
  final_score: number;
  reason: string;
  rank?: number;
  combined_score?: number;
  confidence_pct?: number;
  npk_score?: number;
  region_suitability?: string;
  grown_pct_of_years?: number;
  avg_yield_t_ha?: number;
  historically_grown?: boolean;
  water_constrained?: boolean;
  soil_climate_source?: string;
  detailed_factors?: Record<string, any>;
}

export interface CropPredictionResponse {
  success?: boolean;
  model?: string;
  prediction: string;
  confidence?: number | null;
  final_score?: number;
  combined_score?: number;
  unit: string;
  factors?: string[];
  recommendations?: CropRecommendationScoreBreakdown[];
  soil_test_npk_status?: Record<string, string>;
  history_evaluated?: string[];
  weights_used?: Record<string, number>;
  input_summary?: Record<string, any>;
  warnings?: string[];
  model_source?: string;
  model_loaded?: boolean;
  limitations?: string[];
  is_demo?: boolean;
  status?: string;
}

export interface ApiClientError {
  message: string;
  status?: number;
  detail?: string;
  endpoint?: string;
  isNetworkError?: boolean;
}

