/**
 * Cloudscape Design System theme configuration
 * This file configures the visual theme for the application
 */

import { applyMode, Mode } from '@cloudscape-design/global-styles';

export type ThemeMode = 'light' | 'dark';

/**
 * Apply the Cloudscape theme mode
 * @param mode - The theme mode to apply ('light' or 'dark')
 */
export const applyTheme = (mode: ThemeMode = 'light'): void => {
  const cloudscapeMode: Mode = mode === 'dark' ? Mode.Dark : Mode.Light;
  applyMode(cloudscapeMode);
};

/**
 * Initialize the default theme
 */
export const initializeTheme = (): void => {
  // Default to light mode
  applyTheme('light');
};

/**
 * Theme configuration constants
 */
export const THEME_CONFIG = {
  defaultMode: 'light' as ThemeMode,
  storageKey: 'cloudscape-theme-mode',
};
