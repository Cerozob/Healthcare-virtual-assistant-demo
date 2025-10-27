import { TopNavigation } from '@cloudscape-design/components';
import type { TopNavigationProps } from '@cloudscape-design/components';
import { useNavigate } from 'react-router-dom';
import { useLanguage } from '../../contexts/LanguageContext';

interface TopNavigationBarProps {
  signOut?: () => void;
}

export function TopNavigationBar({ signOut }: TopNavigationBarProps) {
  const { t } = useLanguage();
  const navigate = useNavigate();

  const utilities: TopNavigationProps.Utility[] = [
    {
      type: 'button',
      iconName: 'settings',
      ariaLabel: 'Configuración',
      onClick: () => navigate('/configuration'),
    },
    {
      type: 'button',
      iconName: 'unlocked',
      ariaLabel: t.auth.signOut,
      onClick: () => signOut?.(),
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
