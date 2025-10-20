import React from 'react';
import { Container, Header, SpaceBetween, Box } from '@cloudscape-design/components';
import ApiExample from '../components/ApiExample';
import { MainLayout } from '../components/layout/MainLayout';

interface HomePageProps {
  signOut?: () => void;
  user?: {
    signInDetails?: {
      loginId?: string;
    };
  };
}

const HomePage: React.FC<HomePageProps> = ({ signOut, user }) => {
  return (
    <MainLayout signOut={signOut} user={user}>
      <SpaceBetween size="l">
        <Header variant="h1">
          Bienvenido a AWSome Builder
        </Header>
        <Container>
          <Box padding="l">
            <p>¡Su aplicación Cloudscape está lista para ser construida!</p>
            <p>Los servicios de API están configurados y listos para usar. Vea el ejemplo a continuación:</p>
          </Box>
        </Container>
        <ApiExample />
      </SpaceBetween>
    </MainLayout>
  );
};

export default HomePage;
