/**
 * useApi Hook
 * Generic hook for API calls with loading, error, and data state management
 */

import { useCallback, useState, useRef, useEffect } from 'react';
import { ApiError } from '../services/apiClient';

export interface UseApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

export interface UseApiReturn<T> extends UseApiState<T> {
  execute: (...args: any[]) => Promise<T | null>;
  reset: () => void;
}

export function useApi<T>(
  apiFunction: (...args: any[]) => Promise<T>
): UseApiReturn<T> {
  const [state, setState] = useState<UseApiState<T>>({
    data: null,
    loading: false,
    error: null
  });

  // Use ref to store the latest apiFunction to avoid stale closures
  const apiFunctionRef = useRef(apiFunction);
  
  useEffect(() => {
    apiFunctionRef.current = apiFunction;
  }, [apiFunction]);

  const execute = useCallback(async (...args: any[]): Promise<T | null> => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const result = await apiFunctionRef.current(...args);
      setState({ data: result, loading: false, error: null });
      return result;
    } catch (error) {
      const errorMessage = error instanceof ApiError 
        ? error.message 
        : error instanceof Error 
        ? error.message 
        : 'An unexpected error occurred';
      
      setState({ data: null, loading: false, error: errorMessage });
      return null;
    }
  }, []); // Remove apiFunction from dependencies to prevent infinite loops

  const reset = useCallback(() => {
    setState({ data: null, loading: false, error: null });
  }, []);

  return {
    ...state,
    execute,
    reset
  };
}
