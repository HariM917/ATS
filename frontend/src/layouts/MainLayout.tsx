import React, { useState, useEffect } from 'react';
import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Sparkles,
  FileText,
  Briefcase,
  Layers,
  MessageSquare,
  User,
  Settings,
  LogOut,
  Menu,
  X,
  Zap,
  Brain,
  Puzzle,
  TrendingUp,
  Users,
} from 'lucide-react';
import { useAuthStore } from '../store/authStore';
import { isRecruiter } from '../types';
import client from '../api/client';

export const MainLayout: React.FC = () => {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const isHR = isRecruiter(user);

  // Keep-alive setup for Render production cold starts
  useEffect(() => {
    if (!import.meta.env.PROD) return;
    const ping = () => {
      client.get('/system/health').catch(() => {});
    };
    ping();
    const id = window.setInterval(ping, 10 * 60 * 1000);
    return () => window.clearInterval(id);
  }, []);

  const handleSignOut = async () => {
    await logout();
    navigate('/login');
  };

  const candidateNav = [
    { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/career-analysis', label: 'Career Analysis', icon: Sparkles },
    { to: '/my-resumes', label: 'My Resumes', icon: FileText },
    { to: '/jobs', label: 'Job Feed', icon: Briefcase },
    { to: '/applications', label: 'Applications', icon: Layers },
    { to: '/ai-coach', label: 'AI Coach', icon: MessageSquare },
    { to: '/quiz', label: 'Tech Quizzes', icon: Brain },
    { to: '/puzzle', label: 'Brain Teasers', icon: Puzzle },
    { to: '/profile', label: 'My Profile', icon: User },
    { to: '/settings', label: 'Settings', icon: Settings },
  ];

  const hrNav = [
    { to: '/hr/dashboard', label: 'HR Dashboard', icon: LayoutDashboard },
    { to: '/hr/jobs', label: 'Job Management', icon: Briefcase },
    { to: '/hr/candidates', label: 'Candidate Pool', icon: Users },
    { to: '/hr/applications', label: 'Application Pipeline', icon: Layers },
    { to: '/hr/profile', label: 'Recruiter Profile', icon: User },
    { to: '/hr/settings', label: 'Settings', icon: Settings },
  ];

  const navItems = isHR ? hrNav : candidateNav;

  return (
    <div className="flex h-screen bg-gray-50/60 overflow-hidden font-sans text-gray-900">
      {/* Mobile Drawer Overlay */}
      {mobileMenuOpen && (
        <div
          className="fixed inset-0 z-40 bg-gray-900/50 backdrop-blur-sm lg:hidden transition-opacity"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 w-64 bg-white border-r border-gray-100 flex flex-col justify-between transform transition-transform duration-300 lg:static lg:translate-x-0 ${
          mobileMenuOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div>
          {/* Brand Logo */}
          <div className="h-18 flex items-center justify-between px-6 border-b border-gray-100">
            <div className="flex items-center gap-3">
              <div
                className={`w-9 h-9 rounded-xl flex items-center justify-center text-white shadow-md ${
                  isHR
                    ? 'bg-gradient-to-tr from-indigo-600 to-violet-600'
                    : 'bg-gradient-to-tr from-emerald-500 to-teal-600'
                }`}
              >
                <Zap className="w-5 h-5" />
              </div>
              <span className="text-xl font-black tracking-tight text-gray-900">
                Talent<span className={isHR ? 'text-indigo-600' : 'text-emerald-600'}>Flow</span>
              </span>
            </div>
            <button
              onClick={() => setMobileMenuOpen(false)}
              className="lg:hidden p-1 text-gray-400 hover:text-gray-600"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Navigation Links */}
          <nav className="p-4 space-y-1 overflow-y-auto max-h-[calc(100vh-160px)]">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                onClick={() => setMobileMenuOpen(false)}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-semibold transition-all duration-150 ${
                    isActive
                      ? isHR
                        ? 'bg-indigo-50 text-indigo-700 shadow-sm'
                        : 'bg-emerald-50 text-emerald-700 shadow-sm'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                  }`
                }
              >
                <item.icon className="w-4 h-4 flex-shrink-0" />
                <span className="truncate">{item.label}</span>
              </NavLink>
            ))}
          </nav>
        </div>

        {/* User Card & Sign Out */}
        <div className="p-4 border-t border-gray-100 bg-gray-50/50">
          <div className="flex items-center gap-3 mb-3 px-2">
            <div
              className={`w-9 h-9 rounded-full flex items-center justify-center text-white text-xs font-bold shadow-sm ${
                isHR
                  ? 'bg-gradient-to-tr from-indigo-500 to-violet-500'
                  : 'bg-gradient-to-tr from-emerald-500 to-teal-500'
              }`}
            >
              {(user?.name || user?.user || user?.email || 'U')[0].toUpperCase()}
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-xs font-bold text-gray-900 truncate">
                {user?.name || user?.user || user?.email}
              </p>
              <p className="text-[11px] text-gray-400 capitalize">{user?.role || 'Candidate'}</p>
            </div>
          </div>
          <button
            onClick={handleSignOut}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 text-xs font-semibold text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-xl border border-gray-200 transition-colors cursor-pointer"
          >
            <LogOut className="w-3.5 h-3.5" />
            Sign Out
          </button>
        </div>
      </aside>

      {/* Main Container */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Header */}
        <header className="h-16 bg-white border-b border-gray-100 px-6 flex items-center justify-between sticky top-0 z-30">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setMobileMenuOpen(true)}
              className="lg:hidden p-1.5 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg cursor-pointer"
            >
              <Menu className="w-5 h-5" />
            </button>
            <span className="text-xs font-medium text-gray-400 capitalize hidden sm:inline">
              TalentFlow ATS / {location.pathname.replace('/', '') || 'Dashboard'}
            </span>
          </div>

          <div className="flex items-center gap-2">
            <span
              className={`px-2.5 py-1 text-xs font-bold rounded-full ${
                isHR
                  ? 'bg-indigo-50 text-indigo-700 border border-indigo-100'
                  : 'bg-emerald-50 text-emerald-700 border border-emerald-100'
              }`}
            >
              {isHR ? 'HR Portal' : 'Candidate Portal'}
            </span>
          </div>
        </header>

        {/* Content Body */}
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8">
          <div className="max-w-7xl mx-auto">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
};

