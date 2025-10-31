import '@cloudscape-design/global-styles/dark-mode-utils.css';
import '@cloudscape-design/global-styles/index.css';
import { Amplify } from 'aws-amplify';
import { Navigate, Route, BrowserRouter as Router, Routes } from 'react-router-dom';
import outputs from '../amplify_outputs.json';
import { SpanishAuthenticator } from './components/auth/SpanishAuthenticator';

import { ProtectedRoute } from './components/routing/ProtectedRoute';
import { LanguageProvider } from './contexts/LanguageContext';
import { NotificationProvider } from './components/common/NotificationSystem';
import { PatientProvider } from './contexts/PatientContext';
import { ThemeProvider } from './contexts/ThemeContext';
import ChatPage from './pages/ChatPage';
import ConfigurationPage from './pages/ConfigurationPage';
import './styles/theme.css';
import { initializeTheme } from './theme/cloudscape-theme';


// Configure Amplify with the default configuration
// Custom bucket access is handled via the bucket parameter in storage APIs
const amplifyConfig = {
  ...outputs,
};


Amplify.configure(amplifyConfig);


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
                        <ChatPage signOut={signOut} user={user} />
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
                  <Route
                    path="/configuration"
                    element={
                      <ProtectedRoute>
                        <ConfigurationPage signOut={signOut} user={user} />
                      </ProtectedRoute>
                    }
                  />
                  {/* Catch all - redirect to chat */}
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
