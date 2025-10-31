/**
 * Enhanced Error Handling Utilities
 * Provides comprehensive error handling and user feedback for file operations
 */

import { FileError } from '../types/unifiedFile';

export interface ErrorDetails {
  type: FileError;
  message: string;
  userMessage: string;
  isRetryable: boolean;
  suggestedAction?: string;
  technicalDetails?: Record<string, unknown>;
}

export interface RetryConfig {
  maxRetries: number;
  baseDelay: number;
  maxDelay: number;
  backoffMultiplier: number;
}

export interface NotificationMessage {
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message: string;
  dismissible: boolean;
  autoHide?: boolean;
  duration?: number;
  action?: {
    label: string;
    handler: () => void;
  };
}

/**
 * Default retry configuration for different error types
 */
const DEFAULT_RETRY_CONFIG: RetryConfig = {
  maxRetries: 3,
  baseDelay: 1000, // 1 second
  maxDelay: 10000, // 10 seconds
  backoffMultiplier: 2,
};

const NETWORK_ERROR_RETRY_CONFIG: RetryConfig = {
  maxRetries: 5,
  baseDelay: 2000, // 2 seconds
  maxDelay: 30000, // 30 seconds
  backoffMultiplier: 1.5,
};

/**
 * Enhanced error handler class
 */
export class ErrorHandler {
  /**
   * Convert technical errors to user-friendly error details
   */
  static getErrorDetails(error: unknown, context?: string): ErrorDetails {
    // Handle FileError enum types
    if (typeof error === 'string' && Object.values(FileError).includes(error as FileError)) {
      return this.getFileErrorDetails(error as FileError, context);
    }

    // Handle Error objects
    if (error instanceof Error) {
      return this.getJavaScriptErrorDetails(error, context);
    }

    // Handle custom error objects
    if (typeof error === 'object' && error !== null && 'type' in error) {
      const customError = error as { type: FileError; message: string; details?: Record<string, unknown> };
      return this.getFileErrorDetails(customError.type, context, customError.message, customError.details);
    }

    // Fallback for unknown errors
    return {
      type: FileError.NETWORK_ERROR,
      message: String(error),
      userMessage: 'Ha ocurrido un error inesperado. Por favor, intente nuevamente.',
      isRetryable: true,
      suggestedAction: 'Intente la operación nuevamente o contacte al soporte técnico si el problema persiste.',
      technicalDetails: { originalError: error },
    };
  }

  /**
   * Get error details for FileError enum types
   */
  private static getFileErrorDetails(
    errorType: FileError,
    context?: string,
    customMessage?: string,
    technicalDetails?: Record<string, unknown>
  ): ErrorDetails {
    const contextPrefix = context ? `${context}: ` : '';

    switch (errorType) {
      case FileError.NOT_FOUND:
        return {
          type: errorType,
          message: customMessage || 'File not found',
          userMessage: `${contextPrefix}El archivo no se encontró. Es posible que haya sido movido o eliminado.`,
          isRetryable: false,
          suggestedAction: 'Verifique que el archivo existe o actualice la lista de archivos.',
          technicalDetails,
        };

      case FileError.ACCESS_DENIED:
        return {
          type: errorType,
          message: customMessage || 'Access denied',
          userMessage: `${contextPrefix}No tiene permisos para acceder a este archivo.`,
          isRetryable: false,
          suggestedAction: 'Contacte al administrador del sistema para obtener los permisos necesarios.',
          technicalDetails,
        };

      case FileError.SIZE_LIMIT_EXCEEDED:
        return {
          type: errorType,
          message: customMessage || 'File size limit exceeded',
          userMessage: `${contextPrefix}El archivo es demasiado grande para mostrar vista previa.`,
          isRetryable: false,
          suggestedAction: 'Use la opción de descarga para ver el archivo completo.',
          technicalDetails,
        };

      case FileError.UNSUPPORTED_TYPE:
        return {
          type: errorType,
          message: customMessage || 'Unsupported file type',
          userMessage: `${contextPrefix}Este tipo de archivo no es compatible con la vista previa.`,
          isRetryable: false,
          suggestedAction: 'Descargue el archivo para verlo en una aplicación externa.',
          technicalDetails,
        };

      case FileError.NETWORK_ERROR:
        return {
          type: errorType,
          message: customMessage || 'Network error',
          userMessage: `${contextPrefix}Error de conexión al cargar el archivo.`,
          isRetryable: true,
          suggestedAction: 'Verifique su conexión a internet e intente nuevamente.',
          technicalDetails,
        };

      case FileError.TIMEOUT:
        return {
          type: errorType,
          message: customMessage || 'Request timeout',
          userMessage: `${contextPrefix}La carga del archivo tardó demasiado tiempo.`,
          isRetryable: true,
          suggestedAction: 'Intente nuevamente o descargue el archivo si el problema persiste.',
          technicalDetails,
        };

      case FileError.INVALID_CONTENT:
        return {
          type: errorType,
          message: customMessage || 'Invalid file content',
          userMessage: `${contextPrefix}El contenido del archivo no es válido o está corrupto.`,
          isRetryable: false,
          suggestedAction: 'Verifique que el archivo no esté dañado o intente con otro archivo.',
          technicalDetails,
        };

      default:
        return {
          type: FileError.NETWORK_ERROR,
          message: customMessage || 'Unknown error',
          userMessage: `${contextPrefix}Ha ocurrido un error desconocido.`,
          isRetryable: true,
          suggestedAction: 'Intente la operación nuevamente.',
          technicalDetails,
        };
    }
  }

  /**
   * Get error details for JavaScript Error objects
   */
  private static getJavaScriptErrorDetails(error: Error, context?: string): ErrorDetails {
    const contextPrefix = context ? `${context}: ` : '';
    let errorType = FileError.NETWORK_ERROR;
    let userMessage = `${contextPrefix}Ha ocurrido un error inesperado.`;
    let isRetryable = true;
    let suggestedAction = 'Intente la operación nuevamente.';

    // Analyze error message to determine type
    const errorMessage = error.message.toLowerCase();

    if (errorMessage.includes('timeout') || errorMessage.includes('timed out')) {
      errorType = FileError.TIMEOUT;
      userMessage = `${contextPrefix}La operación tardó demasiado tiempo en completarse.`;
      suggestedAction = 'Intente nuevamente o verifique su conexión a internet.';
    } else if (errorMessage.includes('network') || errorMessage.includes('fetch')) {
      errorType = FileError.NETWORK_ERROR;
      userMessage = `${contextPrefix}Error de conexión de red.`;
      suggestedAction = 'Verifique su conexión a internet e intente nuevamente.';
    } else if (errorMessage.includes('not found') || errorMessage.includes('404')) {
      errorType = FileError.NOT_FOUND;
      userMessage = `${contextPrefix}El recurso solicitado no se encontró.`;
      isRetryable = false;
      suggestedAction = 'Verifique que el archivo existe o actualice la página.';
    } else if (errorMessage.includes('forbidden') || errorMessage.includes('403') || errorMessage.includes('unauthorized') || errorMessage.includes('401')) {
      errorType = FileError.ACCESS_DENIED;
      userMessage = `${contextPrefix}No tiene permisos para realizar esta operación.`;
      isRetryable = false;
      suggestedAction = 'Contacte al administrador del sistema.';
    } else if (errorMessage.includes('abort')) {
      // Request was cancelled, don't treat as error
      userMessage = `${contextPrefix}La operación fue cancelada.`;
      isRetryable = false;
      suggestedAction = 'Puede intentar la operación nuevamente si lo desea.';
    }

    return {
      type: errorType,
      message: error.message,
      userMessage,
      isRetryable,
      suggestedAction,
      technicalDetails: {
        name: error.name,
        stack: error.stack,
      },
    };
  }

  /**
   * Get retry configuration for error type
   */
  static getRetryConfig(errorType: FileError): RetryConfig {
    switch (errorType) {
      case FileError.NETWORK_ERROR:
      case FileError.TIMEOUT:
        return NETWORK_ERROR_RETRY_CONFIG;
      default:
        return DEFAULT_RETRY_CONFIG;
    }
  }

  /**
   * Calculate delay for retry attempt
   */
  static calculateRetryDelay(attempt: number, config: RetryConfig): number {
    const delay = Math.min(
      config.baseDelay * Math.pow(config.backoffMultiplier, attempt),
      config.maxDelay
    );
    
    // Add jitter to prevent thundering herd
    const jitter = Math.random() * 0.1 * delay;
    return Math.floor(delay + jitter);
  }

  /**
   * Check if error should be retried
   */
  static shouldRetry(errorDetails: ErrorDetails, currentAttempt: number): boolean {
    if (!errorDetails.isRetryable) {
      return false;
    }

    const config = this.getRetryConfig(errorDetails.type);
    return currentAttempt < config.maxRetries;
  }

  /**
   * Create notification message for error
   */
  static createErrorNotification(errorDetails: ErrorDetails, includeAction = true): NotificationMessage {
    const notification: NotificationMessage = {
      type: 'error',
      title: 'Error en la operación',
      message: errorDetails.userMessage,
      dismissible: true,
      autoHide: false,
    };

    if (includeAction && errorDetails.suggestedAction) {
      notification.message += ` ${errorDetails.suggestedAction}`;
    }

    return notification;
  }

  /**
   * Create notification message for success
   */
  static createSuccessNotification(
    title: string,
    message: string,
    autoHide = true,
    duration = 5000
  ): NotificationMessage {
    return {
      type: 'success',
      title,
      message,
      dismissible: true,
      autoHide,
      duration,
    };
  }

  /**
   * Create notification message for warning
   */
  static createWarningNotification(
    title: string,
    message: string,
    action?: { label: string; handler: () => void }
  ): NotificationMessage {
    return {
      type: 'warning',
      title,
      message,
      dismissible: true,
      autoHide: false,
      action,
    };
  }

  /**
   * Create notification message for info
   */
  static createInfoNotification(
    title: string,
    message: string,
    autoHide = true,
    duration = 3000
  ): NotificationMessage {
    return {
      type: 'info',
      title,
      message,
      dismissible: true,
      autoHide,
      duration,
    };
  }
}

/**
 * Retry utility function with exponential backoff
 */
export async function retryOperation<T>(
  operation: () => Promise<T>,
  errorHandler: (error: unknown) => ErrorDetails,
  onRetry?: (attempt: number, delay: number, errorDetails: ErrorDetails) => void
): Promise<T> {
  let attempt = 0;

  while (true) {
    try {
      return await operation();
    } catch (error) {
      const errorDetails = errorHandler(error);
      attempt++;

      if (!ErrorHandler.shouldRetry(errorDetails, attempt)) {
        throw errorDetails;
      }

      const config = ErrorHandler.getRetryConfig(errorDetails.type);
      const delay = ErrorHandler.calculateRetryDelay(attempt - 1, config);

      if (onRetry) {
        onRetry(attempt, delay, errorDetails);
      }

      // Wait before retrying
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
}

/**
 * Safe async operation wrapper that handles errors gracefully
 */
export async function safeAsyncOperation<T>(
  operation: () => Promise<T>,
  fallbackValue: T,
  onError?: (errorDetails: ErrorDetails) => void
): Promise<T> {
  try {
    return await operation();
  } catch (error) {
    const errorDetails = ErrorHandler.getErrorDetails(error);
    
    if (onError) {
      onError(errorDetails);
    }
    
    console.error('Safe async operation failed:', errorDetails);
    return fallbackValue;
  }
}
