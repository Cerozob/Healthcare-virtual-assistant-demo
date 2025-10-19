import { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AppLayout, TopNavigation, ContentLayout, Spinner, Box, Alert } from '@cloudscape-design/components';
import HomePage from './pages/HomePage';
import { configService } from './services/configService';

const App: React.FC = () => {
  const [configError, setConfigError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Initialize configuration on app start
    const loadConfiguration = async () => {
      try {
        setIsLoading(true);
        await configService.loadConfig();
        setConfigError(null);
      } catch (error) {
        console.error('Failed to load configuration:', error);
        const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
        setConfigError(`Failed to load configuration from AWS: ${errorMessage}`);
      } finally {
        setIsLoading(false);
      }
    };

    loadConfiguration();
  }, []);

  if (isLoading) {
    return (
      <Box textAlign="center" padding="xxl">
        <Spinner size="large" />
        <Box variant="h3" padding={{ top: 'm' }}>
          Loading Configuration
        </Box>
        <Box variant="p" padding={{ top: 's' }} color="text-body-secondary">
          Fetching API endpoint from AWS Systems Manager...
        </Box>
      </Box>
    );
  }

  return (
    <Router>
      <TopNavigation
        identity={{
          href: '/',
          title: 'AWSome Builder'
        }}
        utilities={[
          {
            type: 'button',
            text: 'Documentation',
            href: '#',
            external: true,
            externalIconAriaLabel: ' (opens in a new tab)'
          }
        ]}
      />
      <AppLayout
        navigationHide
        toolsHide
        content={
          <ContentLayout>
            {configError && (
              <Alert
                type="warning"
                header="Configuration Warning"
                dismissible
                onDismiss={() => setConfigError(null)}
              >
                {configError}. The application is using localhost fallback configuration.
              </Alert>
            )}
            <Routes>
              <Route path="/" element={<HomePage />} />
            </Routes>
          </ContentLayout>
        }
      />
    </Router>
  );
};

export default App;
