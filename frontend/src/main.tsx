import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
// This assumes index.css is in the frontend folder (one level up)
// If index.css is inside src, change this to: import './index.css'
import '../index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)