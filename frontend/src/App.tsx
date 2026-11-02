import React, { useEffect } from 'react';
import { useAuthStore } from './store/authStore';
import { AppRouter } from './router';
import { ErrorBoundary } from './components/ui/ErrorBoundary';

export default function App() {
  const { loadUser } = useAuthStore();

  useEffect(() => {
    loadUser();
  }, [loadUser]);

  return (
    <ErrorBoundary>
      <AppRouter />
    </ErrorBoundary>
  );
}
