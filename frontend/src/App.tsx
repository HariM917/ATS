import React, { useState, useEffect } from 'react';
import { Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, Briefcase, MessageSquare, Settings, LogOut, Bell, Menu, X, 
  Sparkles, User, Brain, Puzzle, Zap, Loader2, Shield
} from 'lucide-react';
import { Helmet } from 'react-helmet-async';

import { AuthProvider, useAuth } from './contexts/AuthContext';
import { LoginPage } from './pages/LoginPage';
import { CandidateDashboard } from './pages/candidate/CandidateDashboard';
import { HRDashboard } from './pages/hr/HRDashboard';
import { JobBrowse } from './pages/candidate/JobBrowse';
import { JobManagement } from './pages/hr/JobManagement';
import { ChatPage } from './pages/ChatPage';
import { SettingsPage } from './pages/SettingsPage';
import TechQuiz from './TechQuiz';
import PuzzleGame from './PuzzleGame';
import { ErrorBoundary } from './components/ui';
import { ChatMessage } from './types';
import { apiClient } from './services/api';


// ============================================
// Layout wrapper for authenticated pages
// ============================================
const MainLayout = ({ 
  chatMessages, 
  setChatMessages 
}: { 
  chatMessages: ChatMessage[]; 
  setChatMessages: React.Dispatch<React.SetStateAction<ChatMessage[]>> 
}) => {
  const { user, logout, isHR } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Set default welcome message if empty
  useEffect(() => {
    if (user && chatMessages.length === 0) {
      setChatMessages([
        { role: "ai", text: "Hi! I'm your FlowATS AI career coach. Ask me anything about your career, jobs, or candidates.", timestamp: Date.now() }
      ]);
    }
  }, [user, chatMessages.length, setChatMessages]);

  // Fetch persistent chat history on mount/chat navigation
  useEffect(() => {
    if (user && location.pathname === '/chat' && chatMessages.length <= 1) {
      apiClient.get('/chat_history')
        .then(res => res.json())
        .then(data => {
          if (data.history && data.history.length > 0) {
            const formatted = data.history.map((h: any) => ([
              { role: "user" as const, text: h.user, timestamp: Date.now() },
              { role: "ai" as const, text: h.ai, timestamp: Date.now() }
            ])).flat();
            setChatMessages(formatted);
          }
        })
        .catch(() => {});
    }
  }, [user, location.pathname, chatMessages.length, setChatMessages]);

  // Keep-alive setup for Render production cold starts
  useEffect(() => {
    if (!import.meta.env.PROD) return;
    const ping = () => {
      apiClient.get('/system/health').catch(() => {});
    };
    ping();
    const id = window.setInterval(ping, 12 * 60 * 1000);
    return () => window.clearInterval(id);
  }, []);

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  const menuItems = isHR ? [
    { path: '/dashboard', label: 'Screening', icon: LayoutDashboard },
    { path: '/jobs', label: 'Job Posts', icon: Briefcase },
    { path: '/chat', label: 'AI Coach', icon: MessageSquare },
    { path: '/settings', label: 'Settings', icon: Settings },
  ] : [
    { path: '/dashboard', label: 'Career Analysis', icon: Sparkles },
    { path: '/jobs', label: 'Job Feed', icon: Briefcase },
    { path: '/chat', label: 'AI Coach', icon: MessageSquare },
    { path: '/puzzle', label: 'Brain Teasers', icon: Puzzle },
    { path: '/quiz', label: 'Tech Quizzes', icon: Brain },
    { path: '/settings', label: 'My Profile', icon: User },
  ];

  const handleSignOut = async () => {
    try {
      await apiClient.post('/logout');
    } catch {}
    logout();
    setChatMessages([]);
    navigate('/login');
  };

  const currentActiveItem = menuItems.find(item => item.path === location.pathname) || menuItems[0];

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden font-sans text-gray-900">
      
      {/* Mobile Sidebar overlay */}
      {mobileMenuOpen && (
        <div 
          className="fixed inset-0 z-20 bg-gray-900/50 lg:hidden backdrop-blur-sm" 
          onClick={() => setMobileMenuOpen(false)} 
        />
      )}

      {/* Sidebar Component */}
      <div className={`fixed inset-y-0 left-0 z-30 w-64 bg-white border-r border-gray-200 transform lg:static lg:translate-x-0 transition-transform duration-300 flex flex-col ${mobileMenuOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        
        {/* Logo */}
        <div className="flex h-20 items-center px-6 border-b border-gray-100">
          <div className="flex items-center gap-3">
            <div className={`w-9 h-9 rounded-xl flex items-center justify-center text-white shadow-md bg-gradient-to-br ${isHR ? 'from-indigo-600 to-violet-600' : 'from-emerald-500 to-teal-600'}`}>
              <Zap className="w-5 h-5" />
            </div>
            <span className={`text-xl font-black ${isHR ? 'gradient-text-primary' : 'gradient-text-emerald'}`}>
              FlowATS
            </span>
          </div>
        </div>

        {/* Navigation Items */}
        <div className="p-4 space-y-1 flex-1">
          {menuItems.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <button
                key={item.path}
                type="button"
                onClick={() => { navigate(item.path); setMobileMenuOpen(false); }}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold transition-all duration-200 cursor-pointer ${isActive
                  ? (isHR ? 'bg-indigo-55 bg-indigo-50 text-indigo-700 shadow-sm sidebar-active-indicator' : 'bg-emerald-50 text-emerald-700 shadow-sm')
                  : 'text-gray-500 hover:bg-gray-50 hover:text-gray-900'}`}
              >
                <item.icon className={`w-5 h-5 ${isActive ? (isHR ? 'text-indigo-600' : 'text-emerald-600') : 'text-gray-400'}`} /> {item.label}
              </button>
            );
          })}
        </div>

        {/* User Sidebar Panel */}
        <div className="p-4 border-t border-gray-100 bg-gray-50/50">
          <div className="flex items-center gap-3 mb-3 px-2">
            <div className={`w-9 h-9 rounded-full flex items-center justify-center text-white text-xs font-bold shadow-md bg-gradient-to-r ${isHR ? 'from-indigo-500 to-violet-500' : 'from-emerald-500 to-teal-500'}`}>
              {user.user?.[0]?.toUpperCase() || "?"}
            </div>
            <div className="overflow-hidden flex-1">
              <p className="text-sm font-bold text-gray-900 truncate">{user.user}</p>
              <p className="text-xs text-gray-500 capitalize">{user.role}</p>
            </div>
          </div>
          <button 
            type="button"
            onClick={handleSignOut} 
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 border border-gray-200 rounded-xl text-xs font-bold text-gray-600 hover:bg-white hover:text-red-500 hover:border-red-200 transition-all cursor-pointer"
          >
            <LogOut className="w-3.5 h-3.5" /> Sign Out
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        
        {/* Header */}
        <header className="h-16 bg-white/80 glass border-b border-gray-200 px-6 flex items-center justify-between sticky top-0 z-10">
          <div className="flex items-center gap-4">
            <button 
              type="button"
              onClick={() => setMobileMenuOpen(true)} 
              className="lg:hidden text-gray-500 hover:text-gray-900 p-1 cursor-pointer"
            >
              <Menu className="w-6 h-6" />
            </button>
            <h2 className="text-lg font-bold text-gray-800 capitalize hidden sm:block">
              {currentActiveItem?.label}
            </h2>
          </div>
          <div className="flex items-center gap-3">
            <button 
              type="button"
              className="p-2 text-gray-400 hover:text-indigo-600 transition-colors relative rounded-xl hover:bg-gray-50 cursor-pointer"
            >
              <Bell className="w-5 h-5" />
              <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full ring-2 ring-white" />
            </button>
          </div>
        </header>

        {/* Content Body */}
        <main className="flex-1 overflow-auto p-4 sm:p-6 lg:p-8 relative">
          <div className="max-w-7xl mx-auto h-full">
            <ErrorBoundary>
              <Routes>
                <Route path="/dashboard" element={isHR ? <HRDashboard /> : <CandidateDashboard />} />
                <Route path="/jobs" element={isHR ? <JobManagement /> : <JobBrowse />} />
                <Route path="/chat" element={<ChatPage messages={chatMessages} setMessages={setChatMessages} />} />
                <Route path="/settings" element={<SettingsPage />} />
                
                {/* Candidate Only routes */}
                {!isHR && <Route path="/quiz" element={<TechQuiz />} />}
                {!isHR && <Route path="/puzzle" element={<PuzzleGame />} />}

                {/* Redirect any other sub-route to dashboard */}
                <Route path="*" element={<Navigate to="/dashboard" replace />} />
              </Routes>
            </ErrorBoundary>
          </div>
        </main>
      </div>
    </div>
  );
};

// ============================================
// Main Application Component
// ============================================
export default function App() {
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);

  return (
    <ErrorBoundary>
      <AuthProvider>
        <AppRoutes chatMessages={chatMessages} setChatMessages={setChatMessages} />
      </AuthProvider>
    </ErrorBoundary>
  );
}

// Inner routes wrapper to consume useAuth context
const AppRoutes = ({ 
  chatMessages, 
  setChatMessages 
}: { 
  chatMessages: ChatMessage[]; 
  setChatMessages: React.Dispatch<React.SetStateAction<ChatMessage[]>> 
}) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <Loader2 className="w-10 h-10 animate-spin text-indigo-600" />
      </div>
    );
  }

  return (
    <Routes>
      <Route 
        path="/login" 
        element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <LoginPage />} 
      />
      
      {/* Protected routes layout */}
      <Route 
        path="/*" 
        element={
          isAuthenticated ? (
            <MainLayout chatMessages={chatMessages} setChatMessages={setChatMessages} />
          ) : (
            <Navigate to="/login" replace />
          )
        } 
      />
    </Routes>
  );
};