import { SideNavigation as CloudscapeSideNav } from '@cloudscape-design/components';
import type { SideNavigationProps } from '@cloudscape-design/components';
import { useLocation, useNavigate } from 'react-router-dom';
import { useLanguage } from '../../contexts/LanguageContext';

export function SideNavigation() {
  const { t } = useLanguage();
  const navigate = useNavigate();
  const location = useLocation();

  const navItems: SideNavigationProps.Item[] = [
    {
      type: 'link',
      text: t.nav.chat,
      href: '/chat',
    },
    {
      type: 'link',
      text: t.nav.dashboard,
      href: '/dashboard',
    },
    {
      type: 'link',
      text: t.nav.configuration,
      href: '/configuration',
    },
  ];

  return (
    <CloudscapeSideNav
      activeHref={location.pathname}
      header={{
        href: '/',
        text: 'AnyHealthcare Demo',
      }}
      items={navItems}
      onFollow={(event) => {
        event.preventDefault();
        if (event.detail.href) {
          navigate(event.detail.href);
        }
      }}
    />
  );
}
