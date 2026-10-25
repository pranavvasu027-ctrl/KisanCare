/**
 * KisanCare Mobile API Error Classification
 */

export type ErrorType =
  | 'NETWORK_ERROR'
  | 'TIMEOUT_ERROR'
  | 'HTTP_ERROR'
  | 'PARSE_ERROR'
  | 'UNKNOWN_ERROR';

export class ApiError extends Error {
  public readonly status?: number;
  public readonly type: ErrorType;
  public readonly details?: unknown;

  constructor(message: string, type: ErrorType = 'UNKNOWN_ERROR', status?: number, details?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.type = type;
    this.status = status;
    this.details = details;
    Object.setPrototypeOf(this, ApiError.prototype);
  }

  get isTimeout(): boolean {
    return this.type === 'TIMEOUT_ERROR';
  }

  get isNetworkError(): boolean {
    return this.type === 'NETWORK_ERROR';
  }

  get isNotFound(): boolean {
    return this.status === 404;
  }

  get isUnauthorized(): boolean {
    return this.status === 401;
  }

  get isServerError(): boolean {
    return typeof this.status === 'number' && this.status >= 500;
  }

  get userFriendlyMessage(): string {
    if (this.isTimeout) {
      return 'The server took too long to respond. Please check your connection and try again.';
    }
    if (this.isNetworkError) {
      return 'Unable to reach the KisanCare server. Ensure the backend is running and reachable.';
    }
    if (this.status === 401) {
      return 'Session expired. Please log in again.';
    }
    if (this.status === 422) {
      return 'Invalid request parameters. Please verify input values.';
    }
    if (this.isServerError) {
      return 'The server encountered an error. Our technical team has been notified.';
    }
    return this.message || 'An unexpected error occurred.';
  }
}
