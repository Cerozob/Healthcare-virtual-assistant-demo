import { Container, Header, SpaceBetween } from '@cloudscape-design/components';
import { MainLayout } from '../components/layout';
import { useLanguage } from '../contexts/LanguageContext';

interface DashboardPageProps {
  signOut?: () => void;
  user?: {
    signInDetails?: {
      loginId?: string;
    };
  };
}

export default function DashboardPage({ signOut, user }: DashboardPageProps) {
  const { t } = useLanguage();

  return (
    <MainLayout signOut={signOut} user={user}>
      <SpaceBetween size="l">
        <Header variant="h1">{t.nav.dashboard}</Header>
        <Container>
          <p>Panel de pacientes - Próximamente</p>
        </Container>
      </SpaceBetween>
    </MainLayout>
  );
}
