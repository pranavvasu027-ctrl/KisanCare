/**
 * KisanCare AI Copilot Service
 * Connects to live /api/copilot/status and /api/v1/copilot/chat endpoints.
 * Orchestrates agricultural intelligence across Crop Recommendation,
 * Disease Detection, Market Intelligence, and Equipment Rental.
 */

import { apiClient } from './apiClient';
import { ENDPOINTS } from './endpoints';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'model';
  content: string;
  timestamp: string;
  toolProvenance?: string[];
  isError?: boolean;
}

export interface CopilotChatPayload {
  message: string;
  conversation_id?: string;
  language?: string;
  history?: Array<{ role: string; content: string }>;
  farm_id?: string;
}

export interface CopilotChatResponse {
  reply: string;
  conversation_id: string;
  grounded: boolean;
  language?: string;
  model_results?: Record<string, any>;
  evidence_references?: Array<{
    tool_name?: string;
    provenance?: string;
    result?: any;
  }>;
  missing_data_warnings?: string[];
  error?: string;
}

export interface CopilotStatusResponse {
  status: string;
  provider: string;
  model: string;
  gemini_configured: boolean;
  message?: string;
}

/**
 * Sends a message turn to the KisanCare AI Copilot backend.
 */
export async function sendCopilotMessage(
  payload: CopilotChatPayload
): Promise<CopilotChatResponse> {
  if (!payload.message || payload.message.trim().length === 0) {
    throw new Error('Message cannot be empty');
  }

  return apiClient.post<CopilotChatResponse>(
    ENDPOINTS.COPILOT_CHAT,
    {
      message: payload.message.trim(),
      conversation_id: payload.conversation_id,
      language: payload.language || 'en',
      history: payload.history || [],
      farm_id: payload.farm_id,
    },
    { timeoutMs: 25_000 }
  );
}

/**
 * Fetches operational readiness of the AI Copilot.
 */
export async function fetchCopilotStatus(): Promise<CopilotStatusResponse> {
  return apiClient.get<CopilotStatusResponse>(
    ENDPOINTS.COPILOT_STATUS,
    { timeoutMs: 5_000 }
  );
}
