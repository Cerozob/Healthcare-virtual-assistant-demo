import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './app';
import { configService } from './services/configService';
import '@cloudscape-design/global-styles/index.css';
import './styles/global.css';

const rootElement = document.getElementById('root');
if (!rootElement) throw new Error('Root element not found');

// Load runtime configuration before rendering the app
configService.loadConfig().then(() => {
  ReactDOM.createRoot(rootElement).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
}).catch(error => {
  console.error('Failed to initialize app:', error);
  // Render anyway with fallback config
  ReactDOM.createRoot(rootElement).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
});
