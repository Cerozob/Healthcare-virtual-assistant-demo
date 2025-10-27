/**
 * Theme Toggle Component
 * Provides a button to switch between light and dark modes
 */

// React import removed - not needed for this component
import { Button, ButtonDropdown } from '@cloudscape-design/components';
import { useTheme } from '../../contexts/ThemeContext';
import { useLanguage } from '../../contexts/LanguageContext';

interface ThemeToggleProps {
  variant?: 'icon' | 'dropdown';
}

export function ThemeToggle({ variant = 'icon' }: ThemeToggleProps) {
  const { mode, toggleMode, setMode } = useTheme();
  const { t } = useLanguage();

  if (variant === 'dropdown') {
    return (
      <ButtonDropdown
        items={[
          {
            id: 'light',
            text: t.theme.light,
            iconName: 'status-positive',
            disabled: mode === 'light'
          },
          {
            id: 'dark', 
            text: t.theme.dark,
            iconName: 'status-negative',
            disabled: mode === 'dark'
          },

          {
            id: 'system',
            text: t.theme.system,
            iconName: 'settings'
          }
        ]}
        onItemClick={({ detail }) => {
          if (detail.id === 'light') {
            setMode('light');
          } else if (detail.id === 'dark') {
            setMode('dark');
          } else if (detail.id === 'system') {
            // Remove saved preference to follow system
            localStorage.removeItem('healthcare-theme-mode');
            const systemPrefersDark = window.matchMedia?.('(prefers-color-scheme: dark)').matches;
            setMode(systemPrefersDark ? 'dark' : 'light');
          }
        }}
        variant="icon"
        ariaLabel={t.theme.toggle}
      >
        {mode === 'light' ? (
          <span role="img" aria-label="Modo claro">☀️</span>
        ) : (
          <span role="img" aria-label="Modo oscuro">🌙</span>
        )}
      </ButtonDropdown>
    );
  }

  return (
    <Button
      variant="icon"
      iconName={mode === 'light' ? 'status-negative' : 'status-positive'}
      onClick={toggleMode}
      ariaLabel={mode === 'light' ? `${t.common.change} ${t.theme.dark}` : `${t.common.change} ${t.theme.light}`}
    />
  );
}

export default ThemeToggle;
