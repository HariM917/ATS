import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { apiClient } from '../services/api';
import { Briefcase, User, Loader2, Zap } from 'lucide-react';
import { Helmet } from 'react-helmet-async';

export const LoginPage = () => {
  const { login } = useAuth();
  const [role, setRole] = useState<'hr' | 'candidate'>('candidate');
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [formData, setFormData] = useState({
    username: '', // Candidate Full Name or Recruiter Name
    email: '',
    password: '',
    company_name: '',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      if (mode === 'login') {
        const payload = {
          role,
          email: formData.email,
          password: formData.password,
          username: role === 'hr' ? formData.username : undefined
        };
        const res = await apiClient.post('/login', payload);
        const data = await res.json();
        if (res.ok && data.status === "success") {
          login(data);
        } else {
          setError(data.message || "Invalid credentials.");
        }
      } else {
        const payload = {
          role,
          username: formData.username,
          email: formData.email,
          password: formData.password,
          company_name: role === 'hr' ? formData.company_name : undefined
        };
        const res = await apiClient.post('/register', payload);
        const data = await res.json();
        if (res.ok && data.status === "success") {
          login(data);
        } else {
          setError(data.message || "Registration failed.");
        }
      }
    } catch (err) {
      setError("Server connection failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4 bg-white font-sans">
      <Helmet>
        <title>{mode === 'login' ? 'Sign In' : 'Register'} | FlowATS</title>
      </Helmet>

      <div className="w-full max-w-sm space-y-8">
        
        {/* Header */}
        <div className="text-center space-y-2">
          <div className="w-12 h-12 mx-auto rounded-xl flex items-center justify-center text-white bg-black">
            <Zap className="w-6 h-6" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mt-4">FlowATS</h1>
          <p className="text-sm font-medium text-gray-500">AI-Powered Hiring Platform</p>
        </div>

        <div className="w-full border-t border-gray-200"></div>

        {/* Auth Mode Toggle */}
        <div className="flex justify-center gap-8 text-sm font-medium">
          <button
            type="button"
            onClick={() => { setMode('login'); setError(''); }}
            className={`pb-1 ${mode === 'login' ? 'text-black border-b-2 border-black font-semibold' : 'text-gray-400 hover:text-gray-600'}`}
          >
            Login
          </button>
          <button
            type="button"
            onClick={() => { setMode('register'); setError(''); }}
            className={`pb-1 ${mode === 'register' ? 'text-black border-b-2 border-black font-semibold' : 'text-gray-400 hover:text-gray-600'}`}
          >
            Register
          </button>
        </div>

        {/* Role Toggle */}
        <div className="flex bg-gray-100 p-1 rounded-md">
          <button
            type="button"
            onClick={() => { setRole('hr'); setError(''); }}
            className={`flex-1 flex items-center justify-center gap-2 py-1.5 text-sm transition-colors ${role === 'hr' ? 'bg-white shadow-sm rounded text-black font-semibold' : 'text-gray-500'}`}
          >
            <Briefcase className="w-4 h-4" /> Recruiter
          </button>
          <button
            type="button"
            onClick={() => { setRole('candidate'); setError(''); }}
            className={`flex-1 flex items-center justify-center gap-2 py-1.5 text-sm transition-colors ${role === 'candidate' ? 'bg-white shadow-sm rounded text-black font-semibold' : 'text-gray-500'}`}
          >
            <User className="w-4 h-4" /> Candidate
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && <div className="text-red-500 text-sm text-center font-medium">{error}</div>}

          {mode === 'register' && role === 'hr' && (
            <div>
              <input
                required
                className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-black focus:ring-1 focus:ring-black text-sm"
                placeholder="Company Name"
                value={formData.company_name}
                onChange={e => setFormData({ ...formData, company_name: e.target.value })}
              />
            </div>
          )}

          {(mode === 'register' || (mode === 'login' && role === 'hr')) && (
            <div>
              <input
                required
                className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-black focus:ring-1 focus:ring-black text-sm"
                placeholder={role === 'hr' ? "Recruiter Name" : "Full Name"}
                value={formData.username}
                onChange={e => setFormData({ ...formData, username: e.target.value })}
              />
            </div>
          )}

          <div>
            <input
              type="email"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-black focus:ring-1 focus:ring-black text-sm"
              placeholder={role === 'hr' ? "Work Email" : "Email"}
              value={formData.email}
              onChange={e => setFormData({ ...formData, email: e.target.value })}
            />
          </div>

          <div>
            <input
              type="password"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-black focus:ring-1 focus:ring-black text-sm"
              placeholder="Password"
              value={formData.password}
              onChange={e => setFormData({ ...formData, password: e.target.value })}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2 bg-black text-white rounded text-sm font-semibold hover:bg-gray-800 disabled:opacity-50"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin mx-auto" /> : (mode === 'login' ? 'Sign In' : 'Create Account')}
          </button>
        </form>

        {mode === 'login' && (
          <div className="text-center">
            <a href="#" className="text-xs text-gray-500 hover:text-black">Forgot Password?</a>
          </div>
        )}

        <div className="w-full border-t border-gray-200 mt-6"></div>

        <div className="text-center pt-2">
          {mode === 'login' ? (
            <div className="text-sm text-gray-600">
              Don't have an account? <button type="button" onClick={() => setMode('register')} className="text-black font-semibold hover:underline">Create Account</button>
            </div>
          ) : (
            <div className="text-sm text-gray-600">
              Already have an account? <button type="button" onClick={() => setMode('login')} className="text-black font-semibold hover:underline">Sign In</button>
            </div>
          )}
        </div>

      </div>
    </div>
  );
};
