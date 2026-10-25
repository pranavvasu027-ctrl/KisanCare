/**
 * KisanCare Authentication Readiness Service
 * Defines authentication contracts, session management, and Supabase Auth boundaries.
 */

import { AuthSession, AuthUser } from '@/types';
import { apiClient } from './apiClient';

export interface AuthStatus {
  isConfigured: boolean;
  isAuthenticated: boolean;
  provider: 'supabase' | 'mock' | 'none';
  user: AuthUser | null;
  missingConfig?: string[];
}

let currentSession: AuthSession | null = null;

export function getAuthStatus(): AuthStatus {
  const hasToken = apiClient.getAuthToken() !== null || currentSession !== null;

  return {
    isConfigured: false, // Flagged false: Remote Supabase DNS resolution currently offline in host environment
    isAuthenticated: hasToken,
    provider: hasToken ? 'supabase' : 'none',
    user: currentSession?.user || null,
    missingConfig: [
      'SUPABASE_URL (Cloud DNS resolution failed in audit)',
      'SUPABASE_ANON_KEY (Public anon key for mobile GoTrue client)',
      'expo-secure-store (For encrypted mobile token persistence in Step 7)',
    ],
  };
}

export async function setSessionToken(token: string, user: AuthUser): Promise<void> {
  currentSession = {
    accessToken: token,
    user,
    expiresAt: Date.now() + 3600 * 1000,
  };
  apiClient.setAuthToken(token);
}

export async function clearSession(): Promise<void> {
  currentSession = null;
  apiClient.setAuthToken(null);
}
