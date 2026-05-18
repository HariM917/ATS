import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { HelmetProvider } from 'react-helmet-async';
import { BrowserRouter } from 'react-router-dom';

// --- CSS IMPORT ---
// Recommendation: Move 'index.css' into the 'src' folder.
// If you moved it to 'src', use: './index.css'
// If you kept it in the root 'frontend' folder, use: '../index.css'
import './index.css'; 

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <HelmetProvider>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </HelmetProvider>
  </React.StrictMode>,
);