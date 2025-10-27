import type React from 'react';
import { Container, Header, SpaceBetween, Box } from '@cloudscape-design/components';
// ApiExample removed - was only for testing
import { MainLayout } from '../components/layout/MainLayout';
import { useTheme } from '../contexts/ThemeContext';

interface HomePageProps {
  signOut?: () => void;
  user?: {
    signInDetails?: {
      loginId?: string;
    };
  };
}

const HomePage: React.FC<HomePageProps> = ({ signOut, user }) => {
  const { mode } = useTheme();
  
  return (
    <MainLayout signOut={signOut} user={user}>
      <SpaceBetween size="l">
        <Header variant="h1">
          Bienvenido a AWSome Builder
        </Header>
        <Container>
          <Box padding="l">
            <p>¡Su aplicación de salud está lista para usar!</p>
            <p>Utilice el chat para interactuar con el asistente de IA o configure pacientes, médicos y exámenes.</p>
            <Box margin={{ top: 'm' }} color="text-body-secondary">
              <small>Tema actual: {mode === 'light' ? '☀️ Claro' : '🌙 Oscuro'} - Use el botón en la barra superior para cambiar</small>
            </Box>
          </Box>
        </Container>
      </SpaceBetween>
    </MainLayout>
  );
};

export default HomePage;
