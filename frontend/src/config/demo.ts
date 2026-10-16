/**
 * Demo Mode Configuration
 *
 * Controls whether the application runs in unauthenticated demonstration/development mode.
 * Configured via Vite environment variable: VITE_DEMO_MODE ('true' | 'false').
 *
 * When active:
 * - Route authentication is bypassed for local demonstrations only.
 * - Frontend data requests use clearly marked demo data.
 * - Missing Supabase credentials will not cause startup errors.
 *
 * Demo mode is not authentication and must never be used to grant access to
 * protected data or operations.
 */

export const IS_DEMO_MODE: boolean = import.meta.env.VITE_DEMO_MODE === 'true';
