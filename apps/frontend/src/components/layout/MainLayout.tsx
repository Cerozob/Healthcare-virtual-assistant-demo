import { AppLayout, BreadcrumbGroup, ContentLayout } from '@cloudscape-design/components';
import type { BreadcrumbGroupProps } from '@cloudscape-design/components';
import { type ReactNode } from 'react';
import { TopNavigationBar } from './TopNavigationBar';

interface MainLayoutProps {
  children: ReactNode;
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
  return (
    <>
      <TopNavigationBar signOut={signOut} user={user} />
      <AppLayout
        navigationHide
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
      />
    </>
  );
}
