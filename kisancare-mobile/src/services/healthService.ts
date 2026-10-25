/**
 * KisanCare Health & Diagnostic Service
 * Calls live backend /health endpoint to verify server status, uptime, and AI Copilot readiness.
 */

import { apiClient } from './apiClient';
import { ENDPOINTS } from './endpoints';

export interface CopilotStatus {
  status: 'ready' | 'unconfigured' | string;
  model: string;
  configured: boolean;
}

export interface HealthResponse {
  status: 'ok' | 'healthy' | string;
  service: string;
  copilot?: CopilotStatus;
}

export interface HealthCheckResult {
  isHealthy: boolean;
  statusText: string;
  serviceName: string;
  copilotModel?: string;
  copilotReady: boolean;
  latencyMs: number;
  timestamp: string;
  baseUrl: string;
}

export async function checkBackendHealth(): Promise<HealthCheckResult> {
  const startTime = Date.now();
  const baseUrl = apiClient.getBaseUrl();

  try {
    const data = await apiClient.get<HealthResponse>(ENDPOINTS.HEALTH, {
      timeoutMs: 5000, // Quick 5s diagnostic timeout
    });
    const latencyMs = Date.now() - startTime;

    const isHealthy = data.status === 'ok' || data.status === 'healthy';

    return {
      isHealthy,
      statusText: isHealthy ? 'Connected' : 'Degraded',
      serviceName: data.service || 'KisanCare API',
      copilotModel: data.copilot?.model,
      copilotReady: data.copilot?.configured ?? false,
      latencyMs,
      timestamp: new Date().toLocaleTimeString(),
      baseUrl,
    };
  } catch (error) {
    const latencyMs = Date.now() - startTime;
    throw error;
  }
}
