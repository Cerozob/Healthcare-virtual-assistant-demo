import { Authenticator } from '@aws-amplify/ui-react';
import '@aws-amplify/ui-react/styles.css';
import { Alert, AppLayout, Box, ContentLayout, Spinner, TopNavigation } from '@cloudscape-design/components';
import { Amplify, type ResourcesConfig } from 'aws-amplify';
import { useEffect, useState } from 'react';
import { Route, BrowserRouter as Router, Routes } from 'react-router-dom';
import outputs from '../amplify_outputs.json';
import HomePage from './pages/HomePage';
import { configService } from './services/configService';

// Configure Amplify with existing CDK resources
const configureAmplify = async () => {
  // Get CDK resource values from Amplify outputs (populated from secrets)
  // Handle both resolved strings and secret objects
  const apiEndpoint = typeof outputs.custom?.apiGatewayEndpoint === 'string' 
    ? outputs.custom.apiGatewayEndpoint 
    : 'http://localhost:3000/v1';
  const bucketName = typeof outputs.custom?.s3BucketName === 'string'
    ? outputs.custom.s3BucketName
    : 'healthcare-documents-bucket';
  const region = typeof outputs.custom?.awsRegion === 'string'
    ? outputs.custom.awsRegion
    : 'us-east-1';
  
  console.log('🔧 Configuring Amplify with CDK resources:');
  console.log('   API Endpoint:', apiEndpoint);
  console.log('   S3 Bucket:', bucketName);
  console.log('   Region:', region);
  
  // Merge Amplify auth config with existing CDK resources
  const amplifyConfig: ResourcesConfig = {
    ...outputs,
    API: {
      REST: {
        HealthcareAPI: {
          endpoint: apiEndpoint,
          region,
        },
      },
    },
    Storage: {
      S3: {
        bucket: bucketName,
        region,
      },
    },
  };

  Amplify.configure(amplifyConfig);
  
  // Store config globally for other services to access
  (window as { amplifyConfig?: ResourcesConfig }).amplifyConfig = amplifyConfig;
  
  // Also load config service for any additional configuration
  await configService.loadConfig();
};

const App: React.FC = () => {
  const [configError, setConfigError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Initialize configuration and Amplify on app start
    const loadConfiguration = async () => {
      try {
        setIsLoading(true);
        await configureAmplify();
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
    <Authenticator>
      {({ signOut, user }: { signOut?: () => void; user?: { signInDetails?: { loginId?: string } } }) => (
        <Router>
          <TopNavigation
            identity={{
              href: '/',
              title: 'Healthcare System'
            }}
            utilities={[
              {
                type: 'menu-dropdown',
                text: user?.signInDetails?.loginId || 'User',
                items: [
                  {
                    id: 'profile',
                    text: 'Profile'
                  },
                  {
                    id: 'signout',
                    text: 'Sign out'
                  }
                ],
                onItemClick: ({ detail }) => {
                  if (detail.id === 'signout') {
                    signOut?.();
                  }
                }
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
      )}
    </Authenticator>
  );
};

export default App;
