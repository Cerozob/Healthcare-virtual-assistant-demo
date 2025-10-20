import { useState, useCallback } from 'react';
import { getErrorMessage, withRetry } from '../utils/errorHandling';

interface UseApiCallOptions<T> {
  onSuccess?: (data: T) => void;
  onError?: (error: unknown) => void;
  enableRetry?: boolean;
  maxRetries?: number;
}

interface UseApiCallResult<T, Args extends unknown[]> {
  data: T | null;
  loading: boolean;
  error: string | null;
  execute: (...args: Args) => Promise<T | null>;
  reset: () => void;
  retry: () => Promise<T | null>;
}

export const useApiCall = <T, Args extends unknown[]>(
  apiFunction: (...args: Args) => Promise<T>,
  options: UseApiCallOptions<T> = {}
): UseApiCallResult<T, Args> => {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastArgs, setLastArgs] = useState<Args | null>(null);

  const { onSuccess, onError, enableRetry = true, maxRetries = 3 } = options;

  const execute = useCallback(
    async (...args: Args): Promise<T | null> => {
      setLoading(true);
      setError(null);
      setLastArgs(args);

      try {
        const result = enableRetry
          ? await withRetry(() => apiFunction(...args), { maxRetries })
          : await apiFunction(...args);

        setData(result);
        onSuccess?.(result);
        return result;
      } catch (err) {
        const errorMessage = getErrorMessage(err);
        setError(errorMessage);
        onError?.(err);
        return null;
      } finally {
        setLoading(false);
      }
    },
    [apiFunction, onSuccess, onError, enableRetry, maxRetries]
  );

  const retry = useCallback(async (): Promise<T | null> => {
    if (lastArgs === null) {
      return null;
    }
    return execute(...lastArgs);
  }, [execute, lastArgs]);

  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setLoading(false);
    setLastArgs(null);
  }, []);

  return {
    data,
    loading,
    error,
    execute,
    reset,
    retry
  };
};
