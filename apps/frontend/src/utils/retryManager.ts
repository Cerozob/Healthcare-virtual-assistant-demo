/**
 * Enhanced Retry Manager
 * Provides sophisticated retry mechanisms for file operations with user feedback
 */

import { ErrorHandler, type RetryConfig } from './errorHandler';
import { FileError } from '../types/unifiedFile';

export interface RetryState {
  attempt: number;
  maxAttempts: number;
  isRetrying: boolean;
  lastError: string | null;
  nextRetryDelay: number;
  canRetry: boolean;
}

export interface RetryOptions {
  maxRetries?: number;
  baseDelay?: number;
  maxDelay?: number;
  backoffMultiplier?: number;
  onRetryAttempt?: (attempt: number, delay: number, error: string) => void;
  onRetrySuccess?: (attempt: number) => void;
  onRetryFailed?: (finalError: string, totalAttempts: number) => void;
  shouldRetry?: (error: unknown, attempt: number) => boolean;
}

export class RetryManager {
  private state: RetryState;
  private config: RetryConfig;
  private options: RetryOptions;
  private retryTimer: NodeJS.Timeout | null = null;

  constructor(options: RetryOptions = {}) {
    this.options = options;
    this.config = {
      maxRetries: options.maxRetries || 3,
      baseDelay: options.baseDelay || 1000,
      maxDelay: options.maxDelay || 10000,
      backoffMultiplier: options.backoffMultiplier || 2,
    };

    this.state = {
      attempt: 0,
      maxAttempts: this.config.maxRetries,
      isRetrying: false,
      lastError: null,
      nextRetryDelay: 0,
      canRetry: true,
    };
  }

  /**
   * Execute operation with retry logic
   */
  async execute<T>(operation: () => Promise<T>): Promise<T> {
    this.reset();

    while (this.state.attempt <= this.config.maxRetries) {
      try {
        this.state.attempt++;
        
        if (this.state.attempt > 1) {
          this.state.isRetrying = true;
          
          // Calculate delay for this attempt
          const delay = ErrorHandler.calculateRetryDelay(this.state.attempt - 2, this.config);
          this.state.nextRetryDelay = delay;

          // Notify about retry attempt
          if (this.options.onRetryAttempt) {
            this.options.onRetryAttempt(this.state.attempt, delay, this.state.lastError || 'Unknown error');
          }

          // Wait before retrying
          await this.delay(delay);
        }

        // Execute the operation
        const result = await operation();

        // Success - notify if this was a retry
        if (this.state.attempt > 1 && this.options.onRetrySuccess) {
          this.options.onRetrySuccess(this.state.attempt);
        }

        this.state.isRetrying = false;
        return result;

      } catch (error) {
        const errorDetails = ErrorHandler.getErrorDetails(error);
        this.state.lastError = errorDetails.userMessage;

        // Check if we should retry this error
        const shouldRetry = this.options.shouldRetry 
          ? this.options.shouldRetry(error, this.state.attempt)
          : errorDetails.isRetryable;

        // Check if we have attempts left
        const hasAttemptsLeft = this.state.attempt < this.config.maxRetries;

        if (!shouldRetry || !hasAttemptsLeft) {
          // Final failure
          this.state.canRetry = false;
          this.state.isRetrying = false;

          if (this.options.onRetryFailed) {
            this.options.onRetryFailed(errorDetails.userMessage, this.state.attempt);
          }

          throw errorDetails;
        }
      }
    }

    // This should never be reached, but TypeScript requires it
    throw new Error('Retry logic error');
  }

  /**
   * Manual retry trigger
   */
  async retry<T>(operation: () => Promise<T>): Promise<T> {
    if (!this.state.canRetry) {
      throw new Error('No more retry attempts available');
    }

    return this.execute(operation);
  }

  /**
   * Reset retry state
   */
  reset(): void {
    this.state = {
      attempt: 0,
      maxAttempts: this.config.maxRetries,
      isRetrying: false,
      lastError: null,
      nextRetryDelay: 0,
      canRetry: true,
    };

    if (this.retryTimer) {
      clearTimeout(this.retryTimer);
      this.retryTimer = null;
    }
  }

  /**
   * Cancel ongoing retry
   */
  cancel(): void {
    this.state.canRetry = false;
    this.state.isRetrying = false;

    if (this.retryTimer) {
      clearTimeout(this.retryTimer);
      this.retryTimer = null;
    }
  }

  /**
   * Get current retry state
   */
  getState(): Readonly<RetryState> {
    return { ...this.state };
  }

  /**
   * Check if operation can be retried
   */
  canRetry(): boolean {
    return this.state.canRetry && this.state.attempt < this.config.maxRetries;
  }

  /**
   * Get remaining retry attempts
   */
  getRemainingAttempts(): number {
    return Math.max(0, this.config.maxRetries - this.state.attempt);
  }

  /**
   * Update retry configuration
   */
  updateConfig(newConfig: Partial<RetryConfig>): void {
    this.config = { ...this.config, ...newConfig };
    this.state.maxAttempts = this.config.maxRetries;
  }

  /**
   * Delay utility
   */
  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => {
      this.retryTimer = setTimeout(resolve, ms);
    });
  }
}

/**
 * Create retry manager for file operations
 */
export function createFileOperationRetryManager(options: RetryOptions = {}): RetryManager {
  const defaultOptions: RetryOptions = {
    maxRetries: 3,
    baseDelay: 2000, // 2 seconds
    maxDelay: 30000, // 30 seconds
    backoffMultiplier: 1.5,
    shouldRetry: (error: unknown, _attempt: number) => {
      const errorDetails = ErrorHandler.getErrorDetails(error);
      
      // Don't retry certain error types
      if ([
        FileError.NOT_FOUND,
        FileError.ACCESS_DENIED,
        FileError.SIZE_LIMIT_EXCEEDED,
        FileError.UNSUPPORTED_TYPE,
        FileError.INVALID_CONTENT,
      ].includes(errorDetails.type)) {
        return false;
      }

      // Retry network and timeout errors
      return [FileError.NETWORK_ERROR, FileError.TIMEOUT].includes(errorDetails.type);
    },
    ...options,
  };

  return new RetryManager(defaultOptions);
}

/**
 * Create retry manager for network operations
 */
export function createNetworkRetryManager(options: RetryOptions = {}): RetryManager {
  const defaultOptions: RetryOptions = {
    maxRetries: 5,
    baseDelay: 1000, // 1 second
    maxDelay: 15000, // 15 seconds
    backoffMultiplier: 2,
    shouldRetry: (error: unknown, _attempt: number) => {
      const errorDetails = ErrorHandler.getErrorDetails(error);
      
      // Retry most network-related errors
      return [
        FileError.NETWORK_ERROR,
        FileError.TIMEOUT,
      ].includes(errorDetails.type);
    },
    ...options,
  };

  return new RetryManager(defaultOptions);
}

/**
 * Hook for using retry manager in React components
 */
export function useRetryManager(options: RetryOptions = {}) {
  const retryManager = new RetryManager(options);

  return {
    execute: retryManager.execute.bind(retryManager),
    retry: retryManager.retry.bind(retryManager),
    reset: retryManager.reset.bind(retryManager),
    cancel: retryManager.cancel.bind(retryManager),
    getState: retryManager.getState.bind(retryManager),
    canRetry: retryManager.canRetry.bind(retryManager),
    getRemainingAttempts: retryManager.getRemainingAttempts.bind(retryManager),
  };
}

/**
 * Utility function for simple retry operations
 */
export async function withRetry<T>(
  operation: () => Promise<T>,
  options: RetryOptions = {}
): Promise<T> {
  const retryManager = new RetryManager(options);
  return retryManager.execute(operation);
}
