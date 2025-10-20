import { Authenticator } from '@aws-amplify/ui-react';
import '@aws-amplify/ui-react/styles.css';
import { AppLayout, ContentLayout, TopNavigation } from '@cloudscape-design/components';
import { Amplify } from 'aws-amplify';
import { Route, BrowserRouter as Router, Routes } from 'react-router-dom';
import outputs from '../amplify_outputs.json';
import DocumentTestPage from './pages/DocumentTestPage';
import HomePage from './pages/HomePage';

// Configure Amplify - it will automatically use the generated outputs
Amplify.configure(outputs);

const App: React.FC = () => {
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
                type: 'button',
                text: 'Test Documents',
                href: '/test-documents'
              },
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
                <Routes>
                  <Route path="/" element={<HomePage />} />
                  <Route path="/test-documents" element={<DocumentTestPage />} />
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
