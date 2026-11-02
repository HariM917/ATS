import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Zap, Mail, Lock, AlertCircle, ArrowRight, Eye, EyeOff, Info, CheckCircle2 } from 'lucide-react';
import { useAuthStore } from '../store/authStore';
import { isRecruiter } from '../types';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

export const Login: React.FC = () => {
  const navigate = useNavigate();
  const { login, isLoading, error, setError } = useAuthStore();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [role, setRole] = useState<'candidate' | 'hr'>('candidate');
  const [validationError, setValidationError] = useState('');
  const [roleNotice, setRoleNotice] = useState<string | null>(null);
  const [forgotPasswordMsg, setForgotPasswordMsg] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError('');
    setRoleNotice(null);
    setForgotPasswordMsg(null);
    setError(null);

    const cleanEmail = email.trim();
    if (!cleanEmail) {
      setValidationError('Please enter your email address.');
      return;
    }
    if (!EMAIL_REGEX.test(cleanEmail)) {
      setValidationError('Please enter a valid email address.');
      return;
    }
    if (!password) {
      setValidationError('Please enter your password.');
      return;
    }

    const success = await login({
      email: cleanEmail,
      password,
      role,
    });

    if (success) {
      const loggedUser = useAuthStore.getState().user;
      const isHRUser = isRecruiter(loggedUser);

      if (role === 'hr' && !isHRUser) {
        setRoleNotice('This account is registered as a Candidate. Opening your Candidate Dashboard...');
        setTimeout(() => navigate('/dashboard'), 1000);
      } else if (role === 'candidate' && isHRUser) {
        setRoleNotice('This account is registered as a Recruiter / HR. Opening your HR Dashboard...');
        setTimeout(() => navigate('/hr/dashboard'), 1000);
      } else {
        navigate(isHRUser ? '/hr/dashboard' : '/dashboard');
      }
    }
  };

  const isCandidate = role === 'candidate';

  return (
    <div className={`min-h-screen bg-gradient-to-br from-gray-50 via-gray-100 ${isCandidate ? 'to-emerald-50/40' : 'to-indigo-50/40'} flex items-center justify-center p-4 transition-colors duration-300`}>
      <div className="w-full max-w-md bg-white rounded-3xl border border-gray-100 shadow-xl p-8 sm:p-10">
        {/* Brand Header */}
        <div className="text-center mb-8">
          <div className={`inline-flex w-12 h-12 rounded-2xl ${isCandidate ? 'bg-emerald-600 shadow-emerald-100' : 'bg-indigo-600 shadow-indigo-100'} text-white items-center justify-center shadow-lg mb-4 transition-colors duration-200`}>
            <Zap className="w-6 h-6" />
          </div>
          <h1 className="text-2xl font-black tracking-tight text-gray-900">
            Welcome to Talent<span className={isCandidate ? 'text-emerald-600' : 'text-indigo-600'}>Flow</span>
          </h1>
          <p className="text-sm text-gray-500 mt-1.5">
            Sign in to access AI-powered ATS & Career Insights
          </p>
        </div>

        {/* Role Toggle */}
        <div className="flex bg-gray-100 p-1 rounded-xl mb-6">
          <button
            type="button"
            onClick={() => {
              setRole('candidate');
              setRoleNotice(null);
            }}
            className={`flex-1 py-2 text-xs font-bold rounded-lg transition-all cursor-pointer ${
              role === 'candidate'
                ? 'bg-white text-emerald-700 shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Candidate Portal
          </button>
          <button
            type="button"
            onClick={() => {
              setRole('hr');
              setRoleNotice(null);
            }}
            className={`flex-1 py-2 text-xs font-bold rounded-lg transition-all cursor-pointer ${
              role === 'hr'
                ? 'bg-white text-indigo-700 shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Recruiter / HR
          </button>
        </div>

        {/* Informative Role Notice */}
        {roleNotice && (
          <div className="mb-5 p-3.5 rounded-xl bg-blue-50 border border-blue-100 flex items-center gap-2.5 text-xs text-blue-800">
            <Info className="w-4 h-4 text-blue-600 flex-shrink-0" />
            <span>{roleNotice}</span>
          </div>
        )}

        {/* Forgot Password Notice */}
        {forgotPasswordMsg && (
          <div className="mb-5 p-3.5 rounded-xl bg-emerald-50 border border-emerald-100 flex items-center gap-2.5 text-xs text-emerald-800">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
            <span>{forgotPasswordMsg}</span>
          </div>
        )}

        {/* Errors */}
        {(validationError || error) && (
          <div className="mb-6 p-4 rounded-xl bg-red-50 border border-red-100 flex items-start gap-3 text-xs text-red-700">
            <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5 text-red-500" />
            <span>{validationError || error}</span>
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Email Address"
            type="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            leftIcon={<Mail className="w-4 h-4" />}
            autoComplete="email"
            required
          />

          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="block text-xs font-semibold text-gray-700">Password</label>
              <button
                type="button"
                onClick={() => setForgotPasswordMsg('A password recovery email link has been dispatched to your email.')}
                className="text-[11px] font-medium text-gray-500 hover:text-indigo-600 transition-colors"
              >
                Forgot password?
              </button>
            </div>
            <div className="relative">
              <Input
                type={showPassword ? 'text' : 'password'}
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                leftIcon={<Lock className="w-4 h-4" />}
                autoComplete="current-password"
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors focus:outline-hidden"
                aria-label={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          <Button
            type="submit"
            className="w-full mt-2"
            size="lg"
            variant={isCandidate ? 'emerald' : 'primary'}
            isLoading={isLoading}
            rightIcon={<ArrowRight className="w-4 h-4" />}
          >
            Sign In as {isCandidate ? 'Candidate' : 'Recruiter'}
          </Button>
        </form>

        {/* Footer */}
        <div className="mt-8 text-center text-xs text-gray-500">
          Don't have an account yet?{' '}
          <Link
            to="/register"
            className={`font-bold ${isCandidate ? 'text-emerald-600 hover:text-emerald-700' : 'text-indigo-600 hover:text-indigo-700'} transition-colors`}
          >
            Create an Account
          </Link>
        </div>
      </div>
    </div>
  );
};
