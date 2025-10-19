import React from 'react';
import { Container, Header, SpaceBetween, Box } from '@cloudscape-design/components';
import ApiExample from '../components/ApiExample';

const HomePage: React.FC = () => {
  return (
    <SpaceBetween size="l">
      <Header variant="h1">
        Welcome to AWSome Builder
      </Header>
      <Container>
        <Box padding="l">
          <p>Your fresh Cloudscape application is ready to be built!</p>
          <p>The API services are configured and ready to use. Check out the example below:</p>
        </Box>
      </Container>
      <ApiExample />
    </SpaceBetween>
  );
};

export default HomePage;
