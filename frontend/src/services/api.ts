/**
 * Re-exporting API service and client for KisanCare
 * Provides seamless compatibility for both `services/api.ts` and `services/apiService.ts`
 */

export * from './apiService';
export { apiService as default } from './apiService';
