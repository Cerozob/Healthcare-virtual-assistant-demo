export interface ApiError {
  message: string;
  code?: string;
  statusCode?: number;
  details?: unknown;
}

export const parseApiError = (error: unknown): ApiError => {
  if (error instanceof Error) {
    return {
      message: error.message,
      code: 'UNKNOWN_ERROR'
    };
  }

  if (typeof error === 'object' && error !== null) {
    const err = error as Record<string, unknown>;
    return {
      message: (err.message as string) || 'Ha ocurrido un error desconocido',
      code: err.code as string,
      statusCode: err.statusCode as number,
      details: err.details
    };
  }

  return {
    message: 'Ha ocurrido un error desconocido',
    code: 'UNKNOWN_ERROR'
  };
};

export const getErrorMessage = (error: unknown): string => {
  const apiError = parseApiError(error);
  
  // Network errors
  if (apiError.code === 'NETWORK_ERROR' || apiError.statusCode === 0) {
    return 'Error de conexión. Por favor, verifica tu conexión a internet.';
  }

  // Timeout errors
  if (apiError.code === 'TIMEOUT_ERROR') {
    return 'La solicitud ha tardado demasiado. Por favor, intenta nuevamente.';
  }

  // Authentication errors
  if (apiError.statusCode === 401) {
    return 'Tu sesión ha expirado. Por favor, inicia sesión nuevamente.';
  }

  // Authorization errors
  if (apiError.statusCode === 403) {
    return 'No tienes permisos para realizar esta acción.';
  }

  // Not found errors
  if (apiError.statusCode === 404) {
    return 'El recurso solicitado no fue encontrado.';
  }

  // Server errors
  if (apiError.statusCode && apiError.statusCode >= 500) {
    return 'Error del servidor. Por favor, intenta nuevamente más tarde.';
  }

  // Validation errors
  if (apiError.statusCode === 400) {
    return apiError.message || 'Los datos proporcionados no son válidos.';
  }

  return apiError.message;
};

export const isRetryableError = (error: unknown): boolean => {
  const apiError = parseApiError(error);
  
  // Retry on network errors, timeouts, and server errors
  if (
    apiError.code === 'NETWORK_ERROR' ||
    apiError.code === 'TIMEOUT_ERROR' ||
    (apiError.statusCode && apiError.statusCode >= 500)
  ) {
    return true;
  }

  return false;
};

export class RetryableError extends Error {
  constructor(message: string, public readonly originalError: unknown) {
    super(message);
    this.name = 'RetryableError';
  }
}

export const withRetry = async <T>(
  fn: () => Promise<T>,
  options: {
    maxRetries?: number;
    delayMs?: number;
    backoff?: boolean;
  } = {}
): Promise<T> => {
  const { maxRetries = 3, delayMs = 1000, backoff = true } = options;
  
  let lastError: unknown;
  
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;
      
      if (attempt < maxRetries && isRetryableError(error)) {
        const delay = backoff ? delayMs * Math.pow(2, attempt) : delayMs;
        await new Promise(resolve => setTimeout(resolve, delay));
      } else {
        break;
      }
    }
  }
  
  throw lastError;
};
