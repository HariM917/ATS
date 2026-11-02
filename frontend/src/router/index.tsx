import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { MainLayout } from '../layouts/MainLayout';
import { Login } from '../pages/Login';
import { Register } from '../pages/Register';
import { Dashboard } from '../pages/Dashboard';
import { CareerAnalysis } from '../pages/CareerAnalysis';
import { Profile } from '../pages/Profile';
import { MyResumes } from '../pages/MyResumes';
import { Jobs } from '../pages/Jobs';
import { Applications } from '../pages/Applications';
import { Chat } from '../pages/Chat';
import { Settings } from '../pages/Settings';
import { Quiz } from '../pages/Quiz';
import { Puzzle } from '../pages/Puzzle';
import { HRCandidates } from '../pages/HRCandidates';
import { Spinner } from '../components/ui/Spinner';
import { isRecruiter } from '../types';

interface ProtectedRouteProps {
  children: React.ReactElement;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuthStore();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <Spinner size="lg" label="Authenticating session..." />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
};

interface RoleRouteProps {
  allowedRoles: Array<'candidate' | 'hr'>;
  children: React.ReactElement;
}

const RoleRoute: React.FC<RoleRouteProps> = ({ allowedRoles, children }) => {
  const { user } = useAuthStore();
  const isHR = isRecruiter(user);
  const effectiveRole: 'candidate' | 'hr' = isHR ? 'hr' : 'candidate';

  if (!allowedRoles.includes(effectiveRole)) {
    return <Navigate to={isHR ? '/hr/dashboard' : '/dashboard'} replace />;
  }

  return children;
};

export const AppRouter: React.FC = () => {
  const { user, isAuthenticated, isLoading } = useAuthStore();
  const isHR = isRecruiter(user);
  const defaultHome = isHR ? '/hr/dashboard' : '/dashboard';

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <Spinner size="lg" label="Initializing TalentFlow..." />
      </div>
    );
  }

  return (
    <Routes>
      {/* Public Auth Routes */}
      <Route
        path="/login"
        element={isAuthenticated ? <Navigate to={defaultHome} replace /> : <Login />}
      />
      <Route
        path="/register"
        element={isAuthenticated ? <Navigate to={defaultHome} replace /> : <Register />}
      />

      {/* Protected Root with Layout */}
      <Route
        element={
          <ProtectedRoute>
            <MainLayout />
          </ProtectedRoute>
        }
      >
        {/* Candidate-only Routes */}
        <Route
          path="/dashboard"
          element={
            <RoleRoute allowedRoles={['candidate']}>
              <Dashboard />
            </RoleRoute>
          }
        />
        <Route
          path="/career-analysis"
          element={
            <RoleRoute allowedRoles={['candidate']}>
              <CareerAnalysis />
            </RoleRoute>
          }
        />
        <Route
          path="/my-resumes"
          element={
            <RoleRoute allowedRoles={['candidate']}>
              <MyResumes />
            </RoleRoute>
          }
        />
        <Route
          path="/resumes"
          element={
            <RoleRoute allowedRoles={['candidate']}>
              <MyResumes />
            </RoleRoute>
          }
        />
        <Route
          path="/jobs"
          element={
            <RoleRoute allowedRoles={['candidate']}>
              <Jobs />
            </RoleRoute>
          }
        />
        <Route
          path="/applications"
          element={
            <RoleRoute allowedRoles={['candidate']}>
              <Applications />
            </RoleRoute>
          }
        />
        <Route
          path="/ai-coach"
          element={
            <RoleRoute allowedRoles={['candidate']}>
              <Chat />
            </RoleRoute>
          }
        />
        <Route
          path="/chat"
          element={
            <RoleRoute allowedRoles={['candidate']}>
              <Chat />
            </RoleRoute>
          }
        />
        <Route
          path="/profile"
          element={
            <RoleRoute allowedRoles={['candidate']}>
              <Profile />
            </RoleRoute>
          }
        />
        <Route
          path="/settings"
          element={
            <RoleRoute allowedRoles={['candidate']}>
              <Settings />
            </RoleRoute>
          }
        />
        <Route
          path="/quiz"
          element={
            <RoleRoute allowedRoles={['candidate']}>
              <Quiz />
            </RoleRoute>
          }
        />
        <Route
          path="/puzzle"
          element={
            <RoleRoute allowedRoles={['candidate']}>
              <Puzzle />
            </RoleRoute>
          }
        />

        {/* HR-only Routes */}
        <Route
          path="/hr/dashboard"
          element={
            <RoleRoute allowedRoles={['hr']}>
              <Dashboard />
            </RoleRoute>
          }
        />
        <Route
          path="/hr/jobs"
          element={
            <RoleRoute allowedRoles={['hr']}>
              <Jobs />
            </RoleRoute>
          }
        />
        <Route
          path="/hr/candidates"
          element={
            <RoleRoute allowedRoles={['hr']}>
              <HRCandidates />
            </RoleRoute>
          }
        />
        <Route
          path="/hr/applications"
          element={
            <RoleRoute allowedRoles={['hr']}>
              <Applications />
            </RoleRoute>
          }
        />
        <Route
          path="/hr/profile"
          element={
            <RoleRoute allowedRoles={['hr']}>
              <Profile />
            </RoleRoute>
          }
        />
        <Route
          path="/hr/settings"
          element={
            <RoleRoute allowedRoles={['hr']}>
              <Settings />
            </RoleRoute>
          }
        />
      </Route>

      {/* Fallback */}
      <Route
        path="*"
        element={<Navigate to={isAuthenticated ? defaultHome : '/login'} replace />}
      />
    </Routes>
  );
};
