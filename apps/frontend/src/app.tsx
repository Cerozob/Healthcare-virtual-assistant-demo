import { Amplify } from 'aws-amplify';
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom';
import outputs from '../amplify_outputs.json';
import { SpanishAuthenticator } from './components/auth/SpanishAuthenticator';
import { ProtectedRoute } from './components/routing/ProtectedRoute';
import { LanguageProvider } from './contexts/LanguageContext';
import { PatientProvider } from './contexts/PatientContext';
import { NotificationProvider } from './contexts/NotificationContext';
import { NotificationCenter } from './components/notifications';
import ChatPage from './pages/ChatPage';
import ConfigurationPage from './pages/ConfigurationPage';
import { PatientDashboardPage } from './pages/PatientDashboardPage';
import DocumentTestPage from './pages/DocumentTestPage';
import FileProcessingDemoPage from './pages/FileProcessingDemoPage';
import HomePage from './pages/HomePage';
import { initializeTheme } from './theme/cloudscape-theme';

// Configure Amplify
Amplify.configure(outputs);

// Initialize Cloudscape theme
initializeTheme();

function App() {
  return (
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
                  <Route
                    path="/dashboard"
                    element={
                      <ProtectedRoute>
                        <PatientDashboardPage signOut={signOut} user={user} />
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
                  <Route
                    path="/test-documents"
                    element={
                      <ProtectedRoute>
                        <DocumentTestPage signOut={signOut} user={user} />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/demo-notifications"
                    element={
                      <ProtectedRoute>
                        <FileProcessingDemoPage signOut={signOut} user={user} />
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
  );
}

export default App;
