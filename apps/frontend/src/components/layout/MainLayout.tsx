import { AppLayout, BreadcrumbGroup, ContentLayout } from '@cloudscape-design/components';
import type { BreadcrumbGroupProps } from '@cloudscape-design/components';
import { useState, type ReactNode } from 'react';
import { useLanguage } from '../../contexts/LanguageContext';
import { SideNavigation } from './SideNavigation';
import { TopNavigationBar } from './TopNavigationBar';

interface MainLayoutProps {
  children: ReactNode;
  signOut?: () => void;
  user?: {
    signInDetails?: {
      loginId?: string;
    };
  };
  breadcrumbs?: BreadcrumbGroupProps.Item[];
  contentHeader?: ReactNode;
}

export function MainLayout({ 
  children, 
  signOut, 
  user,
  breadcrumbs,
  contentHeader,
}: MainLayoutProps) {
  const { t } = useLanguage();
  const [navigationOpen, setNavigationOpen] = useState(true);

  return (
    <>
      <TopNavigationBar signOut={signOut} user={user} />
      <AppLayout
        navigation={<SideNavigation />}
        navigationOpen={navigationOpen}
        onNavigationChange={({ detail }) => setNavigationOpen(detail.open)}
        toolsHide
        breadcrumbs={
          breadcrumbs ? (
            <BreadcrumbGroup
              items={breadcrumbs}
              ariaLabel="Navegación"
            />
          ) : undefined
        }
        content={
          <ContentLayout header={contentHeader}>
            {children}
          </ContentLayout>
        }
        contentType="default"
        navigationWidth={280}
        ariaLabels={{
          navigation: t.nav.home,
          navigationClose: t.common.close,
          navigationToggle: 'Abrir navegación',
          notifications: t.notifications.title,
          tools: 'Herramientas',
          toolsClose: t.common.close,
          toolsToggle: 'Abrir herramientas',
        }}
      />
    </>
  );
}
