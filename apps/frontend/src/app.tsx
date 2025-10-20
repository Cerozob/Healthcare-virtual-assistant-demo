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
  console.log('🔧 Loading configuration from Amplify outputs...');
  console.log('Raw outputs:', outputs.custom);

  // Get CDK resource values from Amplify outputs (populated from secrets)
  const apiEndpoint = outputs.custom?.apiGatewayEndpoint;
  const bucketName = outputs.custom?.s3BucketName;
  const region = outputs.custom?.awsRegion;

  // Validate that all required secrets are available
  const missingSecrets = [];
  if (!apiEndpoint || typeof apiEndpoint !== 'string' || apiEndpoint.includes('PLACEHOLDER') || apiEndpoint.includes('localhost')) {
    missingSecrets.push('CDK_API_GATEWAY_ENDPOINT');
  }
  if (!bucketName || typeof bucketName !== 'string' || bucketName.includes('PLACEHOLDER')) {
    missingSecrets.push('CDK_S3_BUCKET_NAME');
  }
  if (!region || typeof region !== 'string' || region.includes('PLACEHOLDER')) {
    missingSecrets.push('AWS_REGION');
  }

  if (missingSecrets.length > 0) {
    const errorMessage = `Missing or invalid Amplify secrets: ${missingSecrets.join(', ')}. Please configure these secrets in the Amplify Console under Hosting → Secrets.`;
    console.error('❌ Configuration Error:', errorMessage);
    throw new Error(errorMessage);
  }

  console.log('✅ Configuration loaded successfully:');
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
          Loading configuration from Amplify secrets...
        </Box>
        <Box variant="small" padding={{ top: 's' }} color="text-body-secondary">
          <details>
            <summary>Debug Info</summary>
            <pre style={{ fontSize: '12px', marginTop: '8px' }}>
              {JSON.stringify(outputs.custom, null, 2)}
            </pre>
          </details>
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
                    type="error"
                    header="Configuration Error"
                    dismissible
                    onDismiss={() => setConfigError(null)}
                  >
                    <div>
                      <p>{configError}</p>
                      <p><strong>To fix this:</strong></p>
                      <ol>
                        <li>Go to the <a href="https://console.aws.amazon.com/amplify/" target="_blank" rel="noopener noreferrer">Amplify Console</a></li>
                        <li>Select your app → Hosting → Secrets</li>
                        <li>Add the required secrets with values from your CDK deployment</li>
                        <li>Redeploy the application</li>
                      </ol>
                    </div>
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
