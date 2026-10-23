/**
 * KisanCare Typed Frontend API Client
 *
 * Robust, production-grade HTTP client connecting the React frontend to the
 * KisanCare FastAPI Backend & Inference Services.
 *
 * Requirements met:
 * - Single configurable API base URL via VITE_API_BASE_URL.
 * - Vite proxy compatibility for Docker Compose and local development.
 * - Strict response.ok validation, timeout aborts, and JSON error parsing.
 * - No silent fallback returning fake predictions.
 * - Typed error diagnostics.
 */

import {
  IrrigationAdvisoryResult,
  YieldPredictionResult,
  DigitalTwinResponse,
  SimulationResponse,
  EconomicsRequest,
  EconomicsResponse,
  CropPredictionResponse,
  SimulatorScenario,
} from '../types';

// In Vite dev / Docker, empty base URL uses current origin and delegates to the Vite proxy (/api -> backend:8000).
// In production or custom setups, VITE_API_BASE_URL can provide the full origin (e.g. http://localhost:8000).
const rawBaseUrl = (import.meta as any).env?.VITE_API_BASE_URL || '';
export const API_BASE_URL = rawBaseUrl.endsWith('/') ? rawBaseUrl.slice(0, -1) : rawBaseUrl;

export class ApiError extends Error {
  status: number;
  statusText: string;
  detail: string;
  endpoint: string;
  isNetworkError: boolean;

  constructor(
    message: string,
    options: {
      status?: number;
      statusText?: string;
      detail?: string;
      endpoint?: string;
      isNetworkError?: boolean;
    } = {}
  ) {
    super(message);
    this.name = 'ApiError';
    this.status = options.status || 0;
    this.statusText = options.statusText || '';
    this.detail = options.detail || message;
    this.endpoint = options.endpoint || '';
    this.isNetworkError = options.isNetworkError || false;
  }
}

const DEFAULT_TIMEOUT_MS = 10000;

/**
 * Universal JSON fetch helper with timeout and comprehensive error extraction.
 */
async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {},
  timeoutMs: number = DEFAULT_TIMEOUT_MS
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
        ...(options.headers || {}),
      },
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    // Extract body if possible
    let responseData: any = null;
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      try {
        responseData = await response.json();
      } catch (parseErr) {
        throw new ApiError(`Invalid JSON returned from ${endpoint}`, {
          status: response.status,
          statusText: response.statusText,
          endpoint,
          detail: 'Failed to parse JSON response from server.',
        });
      }
    } else {
      const text = await response.text();
      responseData = text ? { detail: text } : null;
    }

    if (!response.ok) {
      const detailMsg =
        (responseData && (responseData.detail || responseData.message || responseData.error)) ||
        `HTTP ${response.status}: ${response.statusText}`;

      throw new ApiError(
        typeof detailMsg === 'string' ? detailMsg : JSON.stringify(detailMsg),
        {
          status: response.status,
          statusText: response.statusText,
          detail: typeof detailMsg === 'string' ? detailMsg : JSON.stringify(detailMsg),
          endpoint,
        }
      );
    }

    return responseData as T;
  } catch (error: any) {
    clearTimeout(timeoutId);

    if (error instanceof ApiError) {
      throw error;
    }

    if (error.name === 'AbortError') {
      throw new ApiError(`Request timeout after ${timeoutMs}ms`, {
        status: 408,
        statusText: 'Request Timeout',
        endpoint,
        detail: `The server took longer than ${timeoutMs}ms to respond. Please check backend connectivity.`,
        isNetworkError: true,
      });
    }

    throw new ApiError(error.message || 'Network connection failed', {
      endpoint,
      detail: `Could not reach ${url}. Ensure the backend service is running and CORS is configured.`,
      isNetworkError: true,
    });
  }
}

export interface IrrigationRequestParams {
  crop: string;
  crop_stage: string;
  soil_type: string;
  soil_moisture: number;
  rainfall: number;
  decision_date?: string;
}

export interface YieldRequestParams {
  state: string;
  crop: string;
  season: string;
  soil_type: string;
  area: number;
  rainfall: number;
  temperature: number;
  humidity: number;
  nitrogen: number;
  phosphorus: number;
  potassium: number;
}

export const apiService = {
  /**
   * Health Check
   * Calls GET /health or /api/health
   */
  async checkHealth(): Promise<{ status: string; service?: string }> {
    return apiFetch<{ status: string; service?: string }>('/health', { method: 'GET' });
  },

  /**
   * 1. Digital Twin Dashboard State
   * Connects to GET /api/v1/farms/{farm_id}/digital-twin
   */
  async getDigitalTwin(farmId: string = 'F001'): Promise<DigitalTwinResponse> {
    return apiFetch<DigitalTwinResponse>(`/api/v1/farms/${farmId}/digital-twin`, {
      method: 'GET',
    });
  },

  /**
   * 2. What-If Simulator Engine
   * Connects to POST /api/v1/simulate
   */
  async simulateScenario(
    farmId: string = 'F001',
    changes: Record<string, any>
  ): Promise<SimulationResponse> {
    return apiFetch<SimulationResponse>('/api/v1/simulate', {
      method: 'POST',
      body: JSON.stringify({ farm_id: farmId, changes }),
    });
  },

  /**
   * 3. Economics Calculator
   * Connects to POST /api/v1/economics/calculate
   */
  async calculateEconomics(params: EconomicsRequest): Promise<EconomicsResponse> {
    return apiFetch<EconomicsResponse>('/api/v1/economics/calculate', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  },

  /**
   * 4. Precision Irrigation Intelligence Model
   * Connects to POST /api/irrigation/predict (Verified FAO-56 + PyTorch LSTM)
   */
  async predictIrrigation(params: IrrigationRequestParams): Promise<IrrigationAdvisoryResult> {
    const json = await apiFetch<any>('/api/irrigation/predict', {
      method: 'POST',
      body: JSON.stringify(params),
    });

    if (json.success && json.prediction) {
      return json.prediction;
    }
    if (json.water_balance) {
      return json;
    }
    throw new ApiError('Unexpected response format from Irrigation model', {
      endpoint: '/api/irrigation/predict',
      detail: JSON.stringify(json),
    });
  },

  /**
   * 5. Crop Yield Prediction Model
   * Connects to POST /api/yield/predict (Verified Scikit-Learn Random Forest)
   */
  async predictYield(params: YieldRequestParams): Promise<YieldPredictionResult> {
    const json = await apiFetch<any>('/api/yield/predict', {
      method: 'POST',
      body: JSON.stringify(params),
    });

    if (json.success && json.prediction) {
      return json.prediction;
    }
    if (json.predicted_yield !== undefined) {
      return json;
    }
    throw new ApiError('Unexpected response format from Yield model', {
      endpoint: '/api/yield/predict',
      detail: JSON.stringify(json),
    });
  },

  /**
   * 6. Crop Recommendation (Hugging Face Dual-Model Pipeline)
   * Connects to POST /api/v1/crop-recommendation (fallback to POST /api/v1/recommend)
   */
  async predictCrop(data: Record<string, any>): Promise<CropPredictionResponse> {
    try {
      return await apiFetch<CropPredictionResponse>('/api/v1/crop-recommendation', {
        method: 'POST',
        body: JSON.stringify(data),
      });
    } catch (err: any) {
      // If versioned endpoint returns 404, fallback to /api/v1/recommend
      if (err instanceof ApiError && err.status === 404) {
        return apiFetch<CropPredictionResponse>('/api/v1/recommend', {
          method: 'POST',
          body: JSON.stringify(data),
        });
      }
      throw err;
    }
  },

  /**
   * Client-side scenario adapter combining backend simulation with UI presentation
   */
  async runScenarioSimulation(
    farmId: string,
    areaAcres: number,
    rainfallChangePct: number,
    irrigationLevel: 'Full' | 'Reduced' | 'Deficit',
    fertilizerCostDeltaPct: number,
    seedCostDeltaPct: number,
    sellingPrice: number,
    baselineYield: number = 9.5,
    baselineCostPerAc: number = 13500
  ): Promise<{ scenario: SimulatorScenario; apiResponse: SimulationResponse }> {
    // Call real backend simulation endpoint
    const simResult = await this.simulateScenario(farmId, {
      rainfall_change_percent: rainfallChangePct,
      input_cost: Math.round(baselineCostPerAc * (1 + (fertilizerCostDeltaPct + seedCostDeltaPct) / 200)),
      irrigation_level: irrigationLevel,
    });

    const scenarioYieldAcre = simResult.scenario.yield;
    const totalProduction = Math.round(scenarioYieldAcre * areaAcres * 10) / 10;
    const totalCost = simResult.scenario.cost;
    const totalRevenue = Math.round(totalProduction * sellingPrice);
    const netProfit = totalRevenue - totalCost;
    const breakEvenPrice = totalProduction > 0 ? Math.round(totalCost / totalProduction) : 0;
    const riskScore = Math.round(simResult.scenario.risk * 100);

    const scenario: SimulatorScenario = {
      id: `SIM_${Date.now()}`,
      name: 'Simulated Scenario',
      crop: 'Soybean',
      areaAcres,
      rainfallChangePercent: rainfallChangePct,
      irrigationAvailability: irrigationLevel,
      fertilizerCostDeltaPercent: fertilizerCostDeltaPct,
      seedCostDeltaPercent: seedCostDeltaPct,
      sellingPriceInr: sellingPrice,
      harvestTimingDays: 0,
      storageDurationMonths: 0,
      yieldQuintalAcre: scenarioYieldAcre,
      waterRequirementMm: Math.round(450 * (1 + (rainfallChangePct < 0 ? 0.1 : -0.05))),
      totalCostInr: totalCost,
      totalRevenueInr: totalRevenue,
      netProfitInr: netProfit,
      riskScore,
      breakEvenPriceInr: breakEvenPrice,
    };

    return { scenario, apiResponse: simResult };
  },
};
