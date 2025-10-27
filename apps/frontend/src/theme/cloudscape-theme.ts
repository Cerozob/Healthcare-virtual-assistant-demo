/**
 * Cloudscape Design System theme configuration
 * This file provides theme utilities and constants
 * 
 * Note: Theme application is now handled by ThemeContext
 */

export type ThemeMode = 'light' | 'dark';

/**
 * Theme configuration constants
 */
export const THEME_CONFIG = {
  defaultMode: 'light' as ThemeMode,
  storageKey: 'healthcare-theme-mode',
};

/**
 * Initialize basic theme setup (called once on app start)
 */
export const initializeTheme = (): void => {
  // Theme initialization is now handled by ThemeProvider
  // This function is kept for compatibility
  console.log('Theme initialization handled by ThemeProvider');
};
