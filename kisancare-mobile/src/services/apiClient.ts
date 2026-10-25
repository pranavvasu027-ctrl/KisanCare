/**
 * KisanCare Central API Client
 * Enterprise-grade fetch wrapper with timeouts, safe parsing, and error normalization.
 */

import { getApiBaseUrl, API_TIMEOUT_MS, UPLOAD_TIMEOUT_MS } from './config';
import { ApiError } from './apiError';

export interface RequestOptions {
  headers?: Record<string, string>;
  timeoutMs?: number;
  signal?: AbortSignal;
  params?: Record<string, string | number | boolean | undefined>;
}

export class ApiClient {
  private baseUrl: string;
  private authToken: string | null = null;

  constructor(baseUrl?: string) {
    this.baseUrl = baseUrl || getApiBaseUrl();
  }

  public setAuthToken(token: string | null): void {
    this.authToken = token;
  }

  public getAuthToken(): string | null {
    return this.authToken;
  }

  public getBaseUrl(): string {
    return this.baseUrl;
  }

  public setBaseUrl(newUrl: string): void {
    this.baseUrl = newUrl.replace(/\/+$/, '');
  }

  private buildUrl(path: string, params?: Record<string, string | number | boolean | undefined>): string {
    const cleanPath = path.startsWith('/') ? path : `/${path}`;
    const fullUrl = `${this.baseUrl}${cleanPath}`;

    if (!params) return fullUrl;

    const queryParts: string[] = [];
    for (const [key, val] of Object.entries(params)) {
      if (val !== undefined && val !== null) {
        queryParts.push(`${encodeURIComponent(key)}=${encodeURIComponent(String(val))}`);
      }
    }

    if (queryParts.length === 0) return fullUrl;
    const delimiter = fullUrl.includes('?') ? '&' : '?';
    return `${fullUrl}${delimiter}${queryParts.join('&')}`;
  }

  private async execute<T>(
    path: string,
    method: 'GET' | 'POST' | 'PUT' | 'DELETE',
    body?: unknown,
    options: RequestOptions = {}
  ): Promise<T> {
    const url = this.buildUrl(path, options.params);
    const timeoutMs = options.timeoutMs ?? API_TIMEOUT_MS;

    const controller = new AbortController();
    let timeoutId: ReturnType<typeof setTimeout> | null = null;

    if (options.signal) {
      options.signal.addEventListener('abort', () => controller.abort());
    }

    timeoutId = setTimeout(() => {
      controller.abort();
    }, timeoutMs);

    const headers: Record<string, string> = {
      Accept: 'application/json',
      ...options.headers,
    };

    if (this.authToken && !headers['Authorization']) {
      headers['Authorization'] = `Bearer ${this.authToken}`;
    }

    let serializedBody: string | undefined;
    if (body !== undefined) {
      headers['Content-Type'] = 'application/json';
      serializedBody = JSON.stringify(body);
    }

    try {
      const response = await fetch(url, {
        method,
        headers,
        body: serializedBody,
        signal: controller.signal,
      });

      if (timeoutId) clearTimeout(timeoutId);

      // Extract response payload safely
      let data: unknown;
      const contentType = response.headers.get('content-type') || '';

      if (contentType.includes('application/json')) {
        try {
          data = await response.json();
        } catch (jsonErr) {
          throw new ApiError(
            'Failed to parse JSON response from server',
            'PARSE_ERROR',
            response.status
          );
        }
      } else {
        data = await response.text();
      }

      if (!response.ok) {
        const errorDetail =
          typeof data === 'object' && data !== null && 'detail' in data
            ? (data as { detail: unknown }).detail
            : data;

        const message =
          typeof errorDetail === 'string'
            ? errorDetail
            : `HTTP request failed with status ${response.status}`;

        throw new ApiError(message, 'HTTP_ERROR', response.status, data);
      }

      return data as T;
    } catch (err) {
      if (timeoutId) clearTimeout(timeoutId);

      if (err instanceof ApiError) {
        throw err;
      }

      if (err instanceof Error) {
        if (err.name === 'AbortError') {
          throw new ApiError(
            `Request timed out after ${timeoutMs}ms`,
            'TIMEOUT_ERROR'
          );
        }
        return Promise.reject(
          new ApiError(err.message, 'NETWORK_ERROR', undefined, err)
        );
      }

      throw new ApiError('An unknown error occurred during network request', 'UNKNOWN_ERROR');
    }
  }

  public async get<T>(path: string, options?: RequestOptions): Promise<T> {
    return this.execute<T>(path, 'GET', undefined, options);
  }

  public async post<T>(path: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return this.execute<T>(path, 'POST', body, options);
  }

  public async put<T>(path: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return this.execute<T>(path, 'PUT', body, options);
  }

  public async delete<T>(path: string, options?: RequestOptions): Promise<T> {
    return this.execute<T>(path, 'DELETE', undefined, options);
  }

  /**
   * Multipart Form-Data upload for leaf photos and documents.
   * Does NOT manually set Content-Type header to allow fetch to inject proper multipart boundaries.
   */
  public async upload<T>(
    path: string,
    formData: FormData,
    options: RequestOptions = {}
  ): Promise<T> {
    const url = this.buildUrl(path, options.params);
    const timeoutMs = options.timeoutMs ?? UPLOAD_TIMEOUT_MS;

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    try {
      const headers: Record<string, string> = {
        Accept: 'application/json',
        ...options.headers,
      };

      if (this.authToken && !headers['Authorization']) {
        headers['Authorization'] = `Bearer ${this.authToken}`;
      }
      // Explicitly DO NOT set Content-Type: multipart/form-data
      // Let React Native / browser generate the boundary automatically!

      const response = await fetch(url, {
        method: 'POST',
        headers,
        body: formData,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      let data: unknown;
      const contentType = response.headers.get('content-type') || '';
      if (contentType.includes('application/json')) {
        data = await response.json();
      } else {
        data = await response.text();
      }

      if (!response.ok) {
        throw new ApiError(
          `Upload failed with status ${response.status}`,
          'HTTP_ERROR',
          response.status,
          data
        );
      }

      return data as T;
    } catch (err) {
      clearTimeout(timeoutId);
      if (err instanceof ApiError) throw err;
      if (err instanceof Error && err.name === 'AbortError') {
        throw new ApiError(`Upload timed out after ${timeoutMs}ms`, 'TIMEOUT_ERROR');
      }
      throw new ApiError('Image upload network failure', 'NETWORK_ERROR');
    }
  }
}

// Global singleton instance
export const apiClient = new ApiClient();
