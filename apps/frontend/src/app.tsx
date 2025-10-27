import { Amplify } from 'aws-amplify';
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom';
import outputs from '../amplify_outputs.json';
import { configService } from './services/configService';
import { SpanishAuthenticator } from './components/auth/SpanishAuthenticator';
import { ProtectedRoute } from './components/routing/ProtectedRoute';
import { LanguageProvider } from './contexts/LanguageContext';
import { PatientProvider } from './contexts/PatientContext';
import { NotificationProvider } from './contexts/NotificationContext';
import { ThemeProvider } from './contexts/ThemeContext';
import { NotificationCenter } from './components/notifications';
import ChatPage from './pages/ChatPage';
import ConfigurationPage from './pages/ConfigurationPage';
// PatientDashboardPage import removed - using integrated patient dashboard
import HomePage from './pages/HomePage';
import { initializeTheme } from './theme/cloudscape-theme';
import '@cloudscape-design/global-styles/index.css';
import '@cloudscape-design/global-styles/dark-mode-utils.css';
import './styles/theme.css';

// Get runtime configuration for dynamic bucket name
const runtimeConfig = configService.getConfig();

console.log('🔧 Configuring Amplify with dynamic settings:');
console.log('📍 S3 Bucket:', runtimeConfig.s3BucketName);
console.log('🌍 Region:', runtimeConfig.region);
console.log('🔗 API Base URL:', runtimeConfig.apiBaseUrl);

// Configure Amplify with the default configuration
// Custom bucket access is handled via the bucket parameter in storage APIs
const amplifyConfig = {
  ...outputs,
};

console.log('🔧 Final Amplify configuration:', JSON.stringify(amplifyConfig.storage, null, 2));

Amplify.configure(amplifyConfig);

console.log('✅ Amplify configured successfully with dynamic storage settings');

// Initialize Cloudscape theme
initializeTheme();

function App() {
  return (
    <ThemeProvider>
      <LanguageProvider>
        <NotificationProvider>
          <PatientProvider>
            <SpanishAuthenticator>
            {({ signOut, user }) => (
              <>
                <NotificationCenter />
                <Router>
                  <Routes>
              {/* If not authenticated, show login message */}
              {!user && (
                <Route path="*" element={<div>Cargando...</div>} />
              )}

              {/* Protected routes */}
              {user && (
                <>
                  <Route
                    path="/"
                    element={
                      <ProtectedRoute>
                        <HomePage signOut={signOut} user={user} />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/chat"
                    element={
                      <ProtectedRoute>
                        <ChatPage signOut={signOut} user={user} />
                      </ProtectedRoute>
                    }
                  />
                  {/* Dashboard route removed - functionality moved to PatientDashboardPage */}
                  <Route
                    path="/configuration"
                    element={
                      <ProtectedRoute>
                        <ConfigurationPage signOut={signOut} user={user} />
                      </ProtectedRoute>
                    }
                  />
                  {/* Catch all - redirect to home */}
                  <Route path="*" element={<Navigate to="/" replace />} />
                </>
              )}
                  </Routes>
                </Router>
              </>
            )}
            </SpanishAuthenticator>
          </PatientProvider>
        </NotificationProvider>
      </LanguageProvider>
    </ThemeProvider>
  );
}

export default App;
