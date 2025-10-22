/**
 * API Client
 * Base HTTP client for making API requests with error handling and retries
 */

import { getApiConfig } from '../config/api';


export interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
  headers?: Record<string, string>;
  body?: unknown;
  timeout?: number;
  retries?: number;
}

class ApiClient {
  private baseUrl: string | null = null;
  private defaultTimeout: number = 30000;
  private defaultRetries: number = 3;
  private configPromise: Promise<void> | null = null;
  
  // Circuit breaker state
  private failureCount: number = 0;
  private lastFailureTime: number = 0;
  private circuitBreakerThreshold: number = 5;
  private circuitBreakerTimeout: number = 60000; // 1 minute

  constructor() {
    // Initialize configuration asynchronously
    this.initializeConfig();
  }

  private async initializeConfig(): Promise<void> {
    if (this.configPromise) {
      return this.configPromise;
    }

    this.configPromise = (async () => {
      try {
        const config = getApiConfig();
        this.baseUrl = config.baseUrl;
        this.defaultTimeout = config.timeout;
        this.defaultRetries = config.retries;
      } catch (error) {
        console.error('Failed to initialize API config:', error);
        // Use fallback values
        this.baseUrl = 'http://localhost:3000/v1';
      }
    })();

    return this.configPromise;
  }

  private async ensureConfigLoaded(): Promise<void> {
    if (!this.baseUrl) {
      await this.initializeConfig();
    }
  }

  /**
   * Check if circuit breaker is open
   */
  private isCircuitBreakerOpen(): boolean {
    if (this.failureCount >= this.circuitBreakerThreshold) {
      const timeSinceLastFailure = Date.now() - this.lastFailureTime;
      if (timeSinceLastFailure < this.circuitBreakerTimeout) {
        return true;
      } else {
        // Reset circuit breaker after timeout
        this.failureCount = 0;
        return false;
      }
    }
    return false;
  }

  /**
   * Record a successful request
   */
  private recordSuccess(): void {
    this.failureCount = 0;
  }

  /**
   * Record a failed request
   */
  private recordFailure(): void {
    this.failureCount++;
    this.lastFailureTime = Date.now();
  }

  /**
   * Make an HTTP request with automatic retries and error handling
   */
  async request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
    // Check circuit breaker
    if (this.isCircuitBreakerOpen()) {
      throw new ApiError('Circuit breaker is open - too many recent failures', 'CIRCUIT_BREAKER_OPEN', 503);
    }

    // Ensure configuration is loaded before making requests
    await this.ensureConfigLoaded();

    const {
      method = 'GET',
      headers = {},
      body,
      timeout = this.defaultTimeout,
      retries = this.defaultRetries
    } = options;

    const url = `${this.baseUrl}${endpoint}`;
    const requestHeaders: Record<string, string> = {
      'Content-Type': 'application/json',
      ...headers
    };

    const requestOptions: RequestInit = {
      method,
      headers: requestHeaders,
      signal: AbortSignal.timeout(timeout)
    };

    if (body && method !== 'GET') {
      if (body instanceof FormData) {
        // Remove Content-Type header for FormData (browser will set it with boundary)
        delete requestHeaders['Content-Type'];
        requestOptions.body = body;
      } else {
        requestOptions.body = JSON.stringify(body);
      }
    }

    let lastError: Error | null = null;

    for (let attempt = 0; attempt <= retries; attempt++) {
      try {
        const response = await fetch(url, requestOptions);
        
        if (!response.ok) {
          const errorData = await this.parseErrorResponse(response);
          throw new ApiError(
            errorData.message || `HTTP ${response.status}: ${response.statusText}`,
            errorData.errorCode,
            response.status
          );
        }

        // Handle empty responses
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
          return {} as T;
        }

        const data = await response.json();
        this.recordSuccess();
        return data;

      } catch (error) {
        lastError = error as Error;
        this.recordFailure();
        
        // Don't retry on client errors (4xx) or AbortError
        if (error instanceof ApiError && error.statusCode >= 400 && error.statusCode < 500) {
          throw error;
        }
        
        if (error instanceof Error && error.name === 'AbortError') {
          throw new ApiError('Request timeout', 'TIMEOUT', 408);
        }

        // Wait before retrying (exponential backoff)
        if (attempt < retries) {
          const delay = Math.min(1000 * 2 ** attempt, 10000);
          await new Promise(resolve => setTimeout(resolve, delay));
        }
      }
    }

    throw lastError || new Error('Request failed after retries');
  }

  /**
   * Parse error response from API
   */
  private async parseErrorResponse(response: Response): Promise<{ message: string; errorCode?: string }> {
    try {
      const errorData = await response.json();
      return {
        message: errorData.message || errorData.error || 'Unknown error',
        errorCode: errorData.errorCode
      };
    } catch {
      return {
        message: `HTTP ${response.status}: ${response.statusText}`
      };
    }
  }

  /**
   * GET request
   */
  async get<T>(endpoint: string, params?: Record<string, string | number> | { limit?: number; offset?: number }): Promise<T> {
    const searchParams = params ? new URLSearchParams() : null;
    if (params && searchParams) {
      Object.entries(params).forEach(([key, value]) => {
        searchParams.append(key, String(value));
      });
    }
    const url = searchParams ? `${endpoint}?${searchParams.toString()}` : endpoint;
    return this.request<T>(url, { method: 'GET' });
  }

  /**
   * POST request
   */
  async post<T>(endpoint: string, body?: unknown): Promise<T> {
    return this.request<T>(endpoint, { method: 'POST', body });
  }

  /**
   * PUT request
   */
  async put<T>(endpoint: string, body?: unknown): Promise<T> {
    return this.request<T>(endpoint, { method: 'PUT', body });
  }

  /**
   * DELETE request
   */
  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }

  /**
   * Upload file
   */
  async upload<T>(endpoint: string, file: File, additionalData?: Record<string, unknown>): Promise<T> {
    const formData = new FormData();
    formData.append('file', file);
    
    if (additionalData) {
      Object.entries(additionalData).forEach(([key, value]) => {
        formData.append(key, typeof value === 'string' ? value : JSON.stringify(value));
      });
    }

    return this.request<T>(endpoint, { 
      method: 'POST', 
      body: formData,
      headers: {} // Let browser set Content-Type with boundary
    });
  }
}

// Create and export singleton instance
export const apiClient = new ApiClient();

// Custom error class for API errors
export class ApiError extends Error {
  constructor(
    message: string,
    public errorCode?: string,
    public statusCode: number = 500
  ) {
    super(message);
    this.name = 'ApiError';
  }
}
