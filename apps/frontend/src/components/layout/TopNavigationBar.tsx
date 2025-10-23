import { TopNavigation } from '@cloudscape-design/components';
import type { TopNavigationProps } from '@cloudscape-design/components';
import { useNavigate } from 'react-router-dom';
import { useLanguage } from '../../contexts/LanguageContext';

interface TopNavigationBarProps {
  signOut?: () => void;
  user?: {
    signInDetails?: {
      loginId?: string;
    };
  };
}

export function TopNavigationBar({ signOut, user }: TopNavigationBarProps) {
  const { t } = useLanguage();
  const navigate = useNavigate();

  const utilities: TopNavigationProps.Utility[] = [
    {
      type: 'menu-dropdown',
      text: user?.signInDetails?.loginId || 'Usuario',
      description: user?.signInDetails?.loginId,
      iconName: 'user-profile',
      items: [
        {
          id: 'profile',
          text: t.nav.profile,
        },
        {
          id: 'settings',
          text: t.nav.settings,
        },
        {
          id: 'signout',
          text: t.auth.signOut,
        },
      ],
      onItemClick: ({ detail }) => {
        if (detail.id === 'signout') {
          signOut?.();
        } else if (detail.id === 'profile') {
          navigate('/profile');
        } else if (detail.id === 'settings') {
          navigate('/settings');
        }
      },
    },
  ];

  return (
    <TopNavigation
      identity={{
        href: '/',
        title: 'AnyHealthcare Demo',
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
