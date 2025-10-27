/**
 * Theme Context for Dark/Light Mode Toggle
 * Leverages Cloudscape's visual modes feature
 */

import { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import { applyMode, Mode } from '@cloudscape-design/global-styles';

export type ThemeMode = 'light' | 'dark';

interface ThemeContextType {
  mode: ThemeMode;
  toggleMode: () => void;
  setMode: (mode: ThemeMode) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

interface ThemeProviderProps {
  children: ReactNode;
}

export function ThemeProvider({ children }: ThemeProviderProps) {
  // Initialize theme from localStorage or default to light
  const [mode, setModeState] = useState<ThemeMode>(() => {
    if (typeof window !== 'undefined') {
      const savedMode = localStorage.getItem('healthcare-theme-mode') as ThemeMode;
      if (savedMode === 'light' || savedMode === 'dark') {
        return savedMode;
      }
      // Check system preference
      if (window.matchMedia?.('(prefers-color-scheme: dark)').matches) {
        return 'dark';
      }
    }
    return 'light';
  });

  // Apply theme to Cloudscape
  useEffect(() => {
    // Apply the mode using the correct Cloudscape API
    const cloudscapeMode = mode === 'dark' ? Mode.Dark : Mode.Light;
    applyMode(cloudscapeMode);

    // Save to localStorage
    localStorage.setItem('healthcare-theme-mode', mode);

    // Optional: Update document class for custom CSS
    document.documentElement.setAttribute('data-theme', mode);
  }, [mode]);

  // Listen for system theme changes
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const mediaQuery = window.matchMedia?.('(prefers-color-scheme: dark)');
      if (!mediaQuery) return;
      
      const handleChange = (e: MediaQueryListEvent) => {
        // Only auto-switch if user hasn't manually set a preference
        const savedMode = localStorage.getItem('healthcare-theme-mode');
        if (!savedMode) {
          setModeState(e.matches ? 'dark' : 'light');
        }
      };

      mediaQuery.addEventListener('change', handleChange);
      return () => mediaQuery.removeEventListener('change', handleChange);
    }
  }, []);

  const setMode = (newMode: ThemeMode) => {
    setModeState(newMode);
  };

  const toggleMode = () => {
    setModeState(prevMode => prevMode === 'light' ? 'dark' : 'light');
  };

  const value: ThemeContextType = {
    mode,
    toggleMode,
    setMode,
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme(): ThemeContextType {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}
