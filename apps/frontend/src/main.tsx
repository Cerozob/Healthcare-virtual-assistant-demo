import React from "react";
import ReactDOM from "react-dom/client";
import { StorageHelper } from "./common/helpers/storage-helper";
import { configureAmplify } from "./amplify-config";
import App from "./app";
import "@cloudscape-design/global-styles/index.css";

// Configure Amplify before rendering the app
configureAmplify();

const root = ReactDOM.createRoot(
  document.getElementById("root") as HTMLElement
);

// Initialize theme - force light mode if no preference is set
const theme = StorageHelper.getTheme();
console.log('Initializing theme:', theme);
StorageHelper.applyTheme(theme);

// Set document language to Spanish
document.documentElement.lang = 'es';

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
