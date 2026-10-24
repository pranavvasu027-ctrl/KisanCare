/**
 * Soil Intelligence API Client
 * =============================
 * Communicates with the FastAPI Soil Intelligence backend (/api/v1/soil/*).
 * Completely decouples frontend presentation from domain backend mechanics.
 */

const API_BASE = (import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || '').replace(/\/$/, '');

// ---------------------------------------------------------------------------
// Type Definitions
// ---------------------------------------------------------------------------

export interface ValidationIssue {
  field: string;
  issue_code: string;
  message: string;
  severity: string;
}

export interface ExtractedNutrient {
  nutrient: string;
  reported_value?: number;
  reported_unit?: string;
  reported_form?: string;
  normalized_value_kg_ha?: number;
  conversion_applied?: string;
  test_method?: string;
}

export interface ParseReportRequest {
  report_text: string;
  plot_id?: string;
  farm_id?: string;
}

export interface ParseReportResponse {
  success: boolean;
  report_id?: string;
  plot_id?: string;
  sample_date?: string;
  ph?: number;
  ec_ds_m?: number;
  organic_carbon_pct?: number;
  nitrogen?: ExtractedNutrient;
  phosphorus?: ExtractedNutrient;
  potassium?: ExtractedNutrient;
  confidence_score: number;
  requires_human_review: boolean;
  validation_issues: ValidationIssue[];
  review_token?: string;
  raw_ocr_text?: string;
}

export interface ManualCorrectionRequest {
  review_token: string;
  reviewer_id: string;
  corrections: Record<string, string>;
  notes?: string;
}

export interface ConfirmBaselineReportRequest {
  plot_id: string;
  farm_id?: string;
  report_id?: string;
  sample_date: string;
  lab_name: string;
  lab_certificate_no?: string;
  lab_accreditation_id?: string;
  accreditation_verified: boolean;
  accreditation_source?: string;
  nitrogen_kg_ha: number;
  phosphorus_kg_ha: number;
  potassium_kg_ha: number;
  ph: number;
  ec_ds_m?: number;
  organic_carbon_pct?: number;
  notes?: string;
}

export interface FertilizerEventRequest {
  fertilizer_grade: string;
  quantity_kg_ha: number;
  application_date: string;
  event_id?: string;
  notes?: string;
}

export interface HarvestEventRequest {
  crop_name: string;
  yield_tonnes_ha: number;
  harvest_date: string;
  residue_retained?: boolean;
  event_id?: string;
  notes?: string;
}

export interface AgronomicEventResponse {
  event_id: string;
  event_type: string;
  event_date: string;
  description: string;
  n_flux_kg_ha: number;
  p_flux_kg_ha: number;
  k_flux_kg_ha: number;
  source_citation: string;
}

export interface AdvisoryItem {
  parameter: string;
  status_tier: string;
  status_label?: string;
  reported_value?: number;
  reported_unit: string;
  educational_interpretation: string;
  management_considerations: string[];
  scientific_reference: string;
}

export interface MassBalanceLedgerDto {
  start_date: string;
  end_date: string;
  days_elapsed: number;
  gross_n_added_kg_ha: number;
  gross_p_added_kg_ha: number;
  gross_k_added_kg_ha: number;
  gross_n_removed_kg_ha: number;
  gross_p_removed_kg_ha: number;
  gross_k_removed_kg_ha: number;
  net_balance_n_kg_ha: number;
  net_balance_p_kg_ha: number;
  net_balance_k_kg_ha: number;
  balance_uncertainty_n_kg_ha: number;
  balance_uncertainty_p_kg_ha: number;
  balance_uncertainty_k_kg_ha: number;
  unrecorded_days_estimate: number;
}

export interface PlotStatusResponse {
  plot_id: string;
  farm_id?: string;
  as_of_date: string;
  has_baseline_lab_test: boolean;
  baseline_date?: string;
  baseline_lab_name?: string;
  accreditation_verified: boolean;
  baseline_npk_kg_ha?: { N: number; P: number; K: number };
  soil_ph?: number;
  organic_carbon_pct?: number;
  ec_ds_m?: number;
  recorded_events_count: number;
  net_mass_balance_ledger?: MassBalanceLedgerDto;
  is_operational_authorized: boolean;
  abstention_reason?: string;
  abstention_recommendation?: string;
  advisories: AdvisoryItem[];
  general_recommendations: string[];
  agronomic_disclaimer: string;
}

export interface SingleNutrientComparison {
  nutrient: string;
  estimated_or_predicted_kg_ha?: number;
  actual_lab_kg_ha: number;
  absolute_error_kg_ha?: number;
  relative_error_pct?: number;
  provisional_tolerance_kg_ha: number;
  within_tolerance?: boolean;
  directional_bias: string;
}

export interface ComparisonResponse {
  comparison_id: string;
  plot_id: string;
  retest_date: string;
  days_elapsed: number;
  is_operational_prediction_evaluated: boolean;
  nitrogen_comparison: SingleNutrientComparison;
  phosphorus_comparison: SingleNutrientComparison;
  potassium_comparison: SingleNutrientComparison;
  all_tolerances_met?: boolean;
  drift_alert?: string;
}

export interface CompareRetestRequest {
  retest_date: string;
  retest_report_id?: string;
  lab_name: string;
  lab_certificate_no?: string;
  lab_accreditation_id?: string;
  accreditation_verified?: boolean;
  nitrogen_kg_ha: number;
  phosphorus_kg_ha: number;
  potassium_kg_ha: number;
  ph?: number;
  organic_carbon_pct?: number;
}

export interface BenchmarksResponse {
  supported_fertilizers: string[];
  supported_crops: string[];
  tolerances: Record<string, number>;
  provenance_types: string[];
}

export interface GenericMessageResponse {
  status: string;
  message: string;
  plot_id?: string;
}

// ---------------------------------------------------------------------------
// Helper fetch wrapper
// ---------------------------------------------------------------------------

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {})
  };

  try {
    const res = await fetch(url, { ...options, headers });
    if (!res.ok) {
      let detail = `HTTP ${res.status}: ${res.statusText}`;
      try {
        const body = await res.json();
        if (typeof body.detail === 'string') {
          detail = body.detail;
        } else if (Array.isArray(body.detail)) {
          detail = body.detail.map((d: any) => d.msg || JSON.stringify(d)).join('; ');
        } else if (body.message) {
          detail = body.message;
        }
      } catch {
        // Body was not JSON
      }
      throw new Error(detail);
    }
    return (await res.json()) as T;
  } catch (err: any) {
    console.error(`Soil API request failed [${options.method || 'GET'} ${url}]:`, err);
    throw err;
  }
}

// ---------------------------------------------------------------------------
// API Methods
// ---------------------------------------------------------------------------

export const soilIntelligenceApi = {
  /**
   * Fetch list of supported fertilizers, crops, and agronomic tolerances.
   */
  async getBenchmarks(): Promise<BenchmarksResponse> {
    return request<BenchmarksResponse>('/api/v1/soil/benchmarks');
  },

  /**
   * Parse raw Soil Health Card / lab certificate text.
   */
  async parseReport(payload: ParseReportRequest): Promise<ParseReportResponse> {
    return request<ParseReportResponse>('/api/v1/soil/reports/parse', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  /**
   * Upload and parse real Soil Health Card or laboratory test file (PDF, JPG, JPEG, PNG).
   * Streams multipart/form-data directly to the FastAPI file ingestion endpoint.
   */
  async uploadSoilReport(file: File, plotId?: string, farmId?: string): Promise<ParseReportResponse> {
    const formData = new FormData();
    formData.append('file', file);
    if (plotId) formData.append('plot_id', plotId);
    if (farmId) formData.append('farm_id', farmId);

    const url = `${API_BASE}/api/v1/soil/reports/upload`;
    try {
      const res = await fetch(url, {
        method: 'POST',
        body: formData
      });
      if (!res.ok) {
        let detail = `HTTP ${res.status}: ${res.statusText}`;
        try {
          const body = await res.json();
          if (typeof body.detail === 'string') {
            detail = body.detail;
          } else if (Array.isArray(body.detail)) {
            detail = body.detail.map((d: any) => d.msg || JSON.stringify(d)).join('; ');
          } else if (body.message) {
            detail = body.message;
          }
        } catch {
          // Non-JSON error payload
        }
        throw new Error(detail);
      }
      return (await res.json()) as ParseReportResponse;
    } catch (err: any) {
      console.error(`Soil API upload failed [POST ${url}]:`, err);
      throw err;
    }
  },

  /**
   * Submit manual agronomist correction for a flagged report item.
   */
  async submitManualCorrection(payload: ManualCorrectionRequest): Promise<GenericMessageResponse> {
    return request<GenericMessageResponse>('/api/v1/soil/reports/review/correct', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  /**
   * Confirm and establish an accredited laboratory baseline test for a plot.
   */
  async confirmBaselineReport(payload: ConfirmBaselineReportRequest): Promise<GenericMessageResponse> {
    return request<GenericMessageResponse>('/api/v1/soil/reports/confirm', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  /**
   * Record a fertilizer application event on the plot timeline.
   */
  async recordFertilizerEvent(plotId: string, payload: FertilizerEventRequest): Promise<AgronomicEventResponse> {
    return request<AgronomicEventResponse>(`/api/v1/soil/plots/${encodeURIComponent(plotId)}/events/fertilizer`, {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  /**
   * Record a crop harvest removal event on the plot timeline.
   */
  async recordHarvestEvent(plotId: string, payload: HarvestEventRequest): Promise<AgronomicEventResponse> {
    return request<AgronomicEventResponse>(`/api/v1/soil/plots/${encodeURIComponent(plotId)}/events/harvest`, {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  /**
   * Retrieve all recorded events on a plot's chronological timeline.
   */
  async listPlotEvents(plotId: string): Promise<AgronomicEventResponse[]> {
    return request<AgronomicEventResponse[]>(`/api/v1/soil/plots/${encodeURIComponent(plotId)}/events`);
  },

  /**
   * Query the plot's current status: nutrient ledger, uncertainty, abstention gate, and advisory.
   */
  async getPlotStatus(plotId: string, asOfDate?: string): Promise<PlotStatusResponse> {
    const query = asOfDate ? `?as_of_date=${encodeURIComponent(asOfDate)}` : '';
    return request<PlotStatusResponse>(`/api/v1/soil/plots/${encodeURIComponent(plotId)}/status${query}`);
  },

  /**
   * Stream and download the pure-Python ISO 32000-1 vector PDF report.
   */
  async downloadReportPdf(plotId: string, targetDate?: string): Promise<Blob> {
    const query = targetDate ? `?target_date=${encodeURIComponent(targetDate)}` : '';
    const url = `${API_BASE}/api/v1/soil/plots/${encodeURIComponent(plotId)}/report.pdf${query}`;

    const res = await fetch(url);
    if (!res.ok) {
      let detail = `HTTP ${res.status}: ${res.statusText}`;
      try {
        const body = await res.json();
        detail = body.detail || detail;
      } catch {
        // Not JSON
      }
      throw new Error(detail);
    }
    return await res.blob();
  },

  /**
   * Ingest a subsequent laboratory retest for continuous comparator & drift tracking.
   */
  async compareRetest(plotId: string, payload: CompareRetestRequest): Promise<ComparisonResponse> {
    return request<ComparisonResponse>(`/api/v1/soil/plots/${encodeURIComponent(plotId)}/compare`, {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  /**
   * Reset / clear plot timeline from memory.
   */
  async deletePlot(plotId: string): Promise<GenericMessageResponse> {
    return request<GenericMessageResponse>(`/api/v1/soil/plots/${encodeURIComponent(plotId)}`, {
      method: 'DELETE'
    });
  }
};
