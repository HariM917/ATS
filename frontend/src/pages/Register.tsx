import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Zap, User, Mail, Lock, Building, GraduationCap, AlertCircle, ArrowRight, Eye, EyeOff } from 'lucide-react';
import { useAuthStore } from '../store/authStore';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';

const NAME_REGEX = /^[A-Za-z][A-Za-z .'-]{2,49}$/;
const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
const PASSWORD_REGEX = /^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,64}$/;

export const Register: React.FC = () => {
  const navigate = useNavigate();
  const { register, isLoading, error, setError } = useAuthStore();

  const [role, setRole] = useState<'candidate' | 'hr'>('candidate');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [branch, setBranch] = useState('');
  const [graduationYear, setGraduationYear] = useState('2025');
  const [companyName, setCompanyName] = useState('');
  const [validationError, setValidationError] = useState('');

  const isCandidate = role === 'candidate';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError('');
    setError(null);

    const cleanName = name.trim();
    const cleanEmail = email.trim().toLowerCase();

    if (!NAME_REGEX.test(cleanName)) {
      setValidationError('Full Name must be 3–50 characters (letters, spaces, periods, apostrophes, and hyphens).');
      return;
    }

    if (!EMAIL_REGEX.test(cleanEmail)) {
      setValidationError('Please enter a valid email address (e.g. user@example.com).');
      return;
    }

    if (!PASSWORD_REGEX.test(password)) {
      setValidationError(
        'Password must be 8–64 characters and contain at least one letter, one number, and one special character (@$!%*#?&).'
      );
      return;
    }

    const success = await register({
      name: cleanName,
      email: cleanEmail,
      password,
      role,
      branch: isCandidate ? branch : undefined,
      graduation_year: isCandidate && graduationYear ? parseInt(graduationYear, 10) : undefined,
      company_name: !isCandidate ? companyName : undefined,
    });

    if (success) {
      navigate(isCandidate ? '/dashboard' : '/hr/dashboard');
    }
  };

  return (
    <div className={`min-h-screen bg-gradient-to-br from-gray-50 via-gray-100 ${isCandidate ? 'to-emerald-50/40' : 'to-indigo-50/40'} flex items-center justify-center p-4 transition-colors duration-300`}>
      <div className="w-full max-w-lg bg-white rounded-3xl border border-gray-100 shadow-xl p-8 sm:p-10 my-8">
        {/* Brand Header */}
        <div className="text-center mb-8">
          <div className={`inline-flex w-12 h-12 rounded-2xl ${isCandidate ? 'bg-emerald-600 shadow-emerald-100' : 'bg-indigo-600 shadow-indigo-100'} text-white items-center justify-center shadow-lg mb-4 transition-colors duration-200`}>
            <Zap className="w-6 h-6" />
          </div>
          <h1 className="text-2xl font-black tracking-tight text-gray-900">
            Create your Talent<span className={isCandidate ? 'text-emerald-600' : 'text-indigo-600'}>Flow</span> Account
          </h1>
          <p className="text-sm text-gray-500 mt-1.5">
            Join the modern AI-assisted recruitment platform
          </p>
        </div>

        {/* Role Toggle */}
        <div className="flex bg-gray-100 p-1 rounded-xl mb-6">
          <button
            type="button"
            onClick={() => setRole('candidate')}
            className={`flex-1 py-2 text-xs font-bold rounded-lg transition-all cursor-pointer ${
              isCandidate
                ? 'bg-white text-emerald-700 shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            I am a Candidate
          </button>
          <button
            type="button"
            onClick={() => setRole('hr')}
            className={`flex-1 py-2 text-xs font-bold rounded-lg transition-all cursor-pointer ${
              !isCandidate
                ? 'bg-white text-indigo-700 shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            I am a Recruiter / HR
          </button>
        </div>

        {/* Validation Errors */}
        {(validationError || error) && (
          <div className="mb-6 p-4 rounded-xl bg-red-50 border border-red-100 flex items-start gap-3 text-xs text-red-700">
            <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5 text-red-500" />
            <span>{validationError || error}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Full Name"
            type="text"
            placeholder="John Doe"
            value={name}
            onChange={(e) => setName(e.target.value)}
            leftIcon={<User className="w-4 h-4" />}
            required
          />

          <Input
            label="Email Address"
            type="email"
            placeholder="john.doe@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            leftIcon={<Mail className="w-4 h-4" />}
            required
          />

          <div className="relative">
            <Input
              label="Password"
              type={showPassword ? 'text' : 'password'}
              placeholder="Min 8 chars with letter, number, & special symbol"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              leftIcon={<Lock className="w-4 h-4" />}
              required
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-8 text-gray-400 hover:text-gray-600 transition-colors focus:outline-hidden"
              aria-label={showPassword ? 'Hide password' : 'Show password'}
            >
              {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>

          {isCandidate ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Input
                label="Major / Branch"
                type="text"
                placeholder="Computer Science"
                value={branch}
                onChange={(e) => setBranch(e.target.value)}
                leftIcon={<GraduationCap className="w-4 h-4" />}
              />
              <Input
                label="Graduation Year"
                type="number"
                min="1990"
                max="2035"
                placeholder="2025"
                value={graduationYear}
                onChange={(e) => setGraduationYear(e.target.value)}
              />
            </div>
          ) : (
            <Input
              label="Company Name"
              type="text"
              placeholder="TalentFlow Inc"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              leftIcon={<Building className="w-4 h-4" />}
            />
          )}

          <Button
            type="submit"
            className="w-full mt-4"
            size="lg"
            variant={isCandidate ? 'emerald' : 'primary'}
            isLoading={isLoading}
            rightIcon={<ArrowRight className="w-4 h-4" />}
          >
            Create {isCandidate ? 'Candidate' : 'Recruiter'} Account
          </Button>
        </form>

        {/* Footer */}
        <div className="mt-8 text-center text-xs text-gray-500">
          Already have an account?{' '}
          <Link
            to="/login"
            className={`font-bold ${isCandidate ? 'text-emerald-600 hover:text-emerald-700' : 'text-indigo-600 hover:text-indigo-700'} transition-colors`}
          >
            Sign In
          </Link>
        </div>
      </div>
    </div>
  );
};
