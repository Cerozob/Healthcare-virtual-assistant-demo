# Dark Mode Implementation

This implementation leverages Cloudscape Design System's built-in visual modes feature to provide seamless dark/light mode switching.

## Features

- **Automatic System Detection**: Follows system preference by default
- **Manual Toggle**: Users can override system preference
- **Persistent Settings**: Theme preference is saved to localStorage
- **Smooth Transitions**: CSS transitions for theme changes
- **Accessibility**: Proper ARIA labels and focus states
- **Cloudscape Integration**: Uses official Cloudscape Mode API

## Components

### ThemeProvider (`contexts/ThemeContext.tsx`)
- Manages theme state globally
- Handles system preference detection
- Applies Cloudscape modes using `applyMode(Mode.Dark/Light)` from `@cloudscape-design/global-styles`
- Persists user preference in localStorage

### ThemeToggle (`components/common/ThemeToggle.tsx`)
- Provides UI controls for theme switching
- Two variants: `icon` (simple toggle) and `dropdown` (with system option)
- Internationalized labels

## Usage

```tsx
import { useTheme } from '../contexts/ThemeContext';
import { ThemeToggle } from '../components/common/ThemeToggle';

function MyComponent() {
  const { mode, toggleMode } = useTheme();
  
  return (
    <div>
      <p>Current theme: {mode}</p>
      <ThemeToggle variant="dropdown" />
    </div>
  );
}
```

## Required CSS Imports

Make sure to import the required Cloudscape CSS files in your main app:

```tsx
import '@cloudscape-design/global-styles/index.css';
import '@cloudscape-design/global-styles/dark-mode-utils.css';
```

## CSS Custom Properties

The implementation provides custom CSS properties for additional styling:

```css
/* Available in both themes */
--custom-bg-primary
--custom-bg-secondary  
--custom-text-primary
--custom-text-secondary
--custom-border-color
--custom-shadow
```

## Integration Points

1. **App.tsx**: Wraps app with `ThemeProvider`
2. **TopNavigationBar**: Includes theme toggle in utilities
3. **ChatPage**: Applies theme classes to chat container
4. **Global Styles**: Theme-specific CSS in `styles/theme.css`

## Browser Support

- Modern browsers with CSS custom properties support
- Graceful fallback to light mode for older browsers
- Respects `prefers-color-scheme` media query
