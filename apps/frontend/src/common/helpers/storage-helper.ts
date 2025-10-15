import { Mode, applyMode } from "@cloudscape-design/global-styles";
import { NavigationPanelState } from "../types";

const PREFIX = "example-app";
const THEME_STORAGE_NAME = `${PREFIX}-theme`;
const NAVIGATION_PANEL_STATE_STORAGE_NAME = `${PREFIX}-navigation-panel-state`;

export abstract class StorageHelper {
  static getTheme() {
    const value = localStorage.getItem(THEME_STORAGE_NAME);

    // If no theme is stored, default to light mode
    if (!value) {
      return Mode.Light;
    }

    const theme = value === Mode.Dark ? Mode.Dark : Mode.Light;
    return theme;
  }

  static applyTheme(theme: Mode) {
    console.log('Applying theme:', theme);
    localStorage.setItem(THEME_STORAGE_NAME, theme);
    applyMode(theme);

    // Set CSS custom properties
    document.documentElement.style.setProperty(
      "--app-color-scheme",
      theme === Mode.Dark ? "dark" : "light"
    );

    // Force update the data-awsui-theme attribute
    document.documentElement.setAttribute('data-awsui-theme', theme);

    return theme;
  }

  static getNavigationPanelState(): NavigationPanelState {
    const value =
      localStorage.getItem(NAVIGATION_PANEL_STATE_STORAGE_NAME) ??
      JSON.stringify({
        collapsed: true,
      });

    let state: NavigationPanelState | null = null;
    try {
      state = JSON.parse(value);
    } catch {
      state = {};
    }

    return state ?? {};
  }

  static setNavigationPanelState(state: Partial<NavigationPanelState>) {
    const currentState = this.getNavigationPanelState();
    const newState = { ...currentState, ...state };
    const stateStr = JSON.stringify(newState);
    localStorage.setItem(NAVIGATION_PANEL_STATE_STORAGE_NAME, stateStr);

    return newState;
  }
}
