import { TopNavigation } from '@cloudscape-design/components';
import type { TopNavigationProps } from '@cloudscape-design/components';
import { useNavigate } from 'react-router-dom';
import { useLanguage } from '../../contexts/LanguageContext';
import { useTheme } from '../../contexts/ThemeContext';

interface TopNavigationBarProps {
  signOut?: () => void;
  user?: {
    signInDetails?: {
      loginId?: string;
    };
    username?: string;
    attributes?: {
      name?: string;
      given_name?: string;
      family_name?: string;
      email?: string;
    };
  };
}

export function TopNavigationBar({ signOut, user }: TopNavigationBarProps) {
  const { t } = useLanguage();
  const navigate = useNavigate();
  const { mode, toggleMode } = useTheme();

  // Get user's display name - prioritize full name over username/email
  const getUserDisplayName = () => {
    
    return user?.signInDetails?.loginId;
  };

  const utilities: TopNavigationProps.Utility[] = [
    {
      type: 'menu-dropdown',
      text: getUserDisplayName(),
      iconName: 'user-profile',
      items: [
        {
          id: 'theme-toggle',
          text: mode === 'light' ? 'Modo oscuro' : 'Modo claro',
          iconName: mode === 'light' ? 'view-vertical' : 'view-horizontal'
        },
        {
          id: 'configuration',
          text: 'Configuración',
          iconName: 'settings'
        },
        {
          id: 'signout',
          text: t.auth.signOut,
          iconName: 'close'
        }
      ],

      onItemClick: ({ detail }) => {
        if (detail.id === 'theme-toggle') {
          toggleMode();
        } else if (detail.id === 'configuration') {
          navigate('/configuration');
        } else if (detail.id === 'signout') {
          signOut?.();
        }
      }
    }
  ];

  return (
    <TopNavigation
      identity={{
        href: '/',
        title: 'AnyHealthcare Demo',
        logo: {
          src: '/logo.png',
          alt: 'AnyHealthcare Logo'
          
        },

        onFollow: (e) => {
          e.preventDefault();
          navigate('/');
        },
      }}
      utilities={utilities}

      i18nStrings={{
        searchIconAriaLabel: t.common.search,
        searchDismissIconAriaLabel: t.common.close,
        overflowMenuTriggerText: 'Más',
        overflowMenuTitleText: 'Todas',
        overflowMenuBackIconAriaLabel: t.common.back,
        overflowMenuDismissIconAriaLabel: t.common.close,
      }}
    />
  );
}
