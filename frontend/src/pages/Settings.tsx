import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Settings as SettingsIcon, Shield, Server, LogOut, CheckCircle2, RefreshCw } from 'lucide-react';
import { useAuthStore } from '../store/authStore';
import { API_BASE_URL } from '../api/client';
import client from '../api/client';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Alert } from '../components/ui/Alert';

export const Settings: React.FC = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();
  const [healthStatus, setHealthStatus] = useState<string | null>(null);
  const [isCheckingHealth, setIsCheckingHealth] = useState(false);

  const handleCheckHealth = async () => {
    setIsCheckingHealth(true);
    try {
      const res = await client.get('/system/health');
      setHealthStatus(`Online: ${res.status || 'healthy'} (Version: ${res.version || 'v3.2.0'})`);
    } catch {
      setHealthStatus('Failed to connect to backend server.');
    } finally {
      setIsCheckingHealth(false);
    }
  };

  const handleSignOut = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-2xl font-black tracking-tight text-gray-900">System & Account Settings</h1>
        <p className="text-sm text-gray-500 mt-1">Manage session settings and review deployment configurations.</p>
      </div>

      <Card padding="lg">
        <h3 className="text-base font-bold text-gray-900 mb-4 flex items-center gap-2">
          <Shield className="w-5 h-5 text-indigo-600" />
          Active Account Session
        </h3>
        <div className="space-y-3 text-sm">
          <div className="flex justify-between py-2 border-b border-gray-100">
            <span className="text-gray-500">Name</span>
            <span className="font-semibold text-gray-900">{user?.name || user?.user || 'N/A'}</span>
          </div>
          <div className="flex justify-between py-2 border-b border-gray-100">
            <span className="text-gray-500">Email</span>
            <span className="font-semibold text-gray-900">{user?.email || 'N/A'}</span>
          </div>
          <div className="flex justify-between py-2 border-b border-gray-100">
            <span className="text-gray-500">Assigned Role</span>
            <Badge variant="primary">{user?.role?.toUpperCase() || 'CANDIDATE'}</Badge>
          </div>
          <div className="flex justify-between py-2">
            <span className="text-gray-500">Session Status</span>
            <Badge variant="success">Authenticated</Badge>
          </div>
        </div>
      </Card>

      <Card padding="lg">
        <h3 className="text-base font-bold text-gray-900 mb-4 flex items-center gap-2">
          <Server className="w-5 h-5 text-indigo-600" />
          API & Deployment Configuration
        </h3>
        <div className="space-y-3 text-sm">
          <div className="flex flex-col sm:flex-row sm:justify-between py-2 border-b border-gray-100 gap-1">
            <span className="text-gray-500">Configured API Base URL</span>
            <code className="bg-gray-100 px-2 py-1 rounded-md text-xs font-mono text-gray-800 break-all">
              {API_BASE_URL}
            </code>
          </div>
          <div className="flex justify-between py-2 border-b border-gray-100">
            <span className="text-gray-500">Environment Mode</span>
            <span className="font-semibold text-gray-900 capitalize">
              {import.meta.env.MODE || 'development'}
            </span>
          </div>
          <div className="pt-2 flex items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              isLoading={isCheckingHealth}
              onClick={handleCheckHealth}
              leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
            >
              Test Backend Health
            </Button>
            {healthStatus && <span className="text-xs font-semibold text-gray-700">{healthStatus}</span>}
          </div>
        </div>
      </Card>

      <Card padding="lg" className="border-red-100 bg-red-50/10">
        <h3 className="text-base font-bold text-red-900 mb-2">Sign Out</h3>
        <p className="text-xs text-gray-500 mb-4">
          Safely terminates your current authenticated session and clears tokens from localStorage.
        </p>
        <Button
          variant="danger"
          size="md"
          onClick={handleSignOut}
          leftIcon={<LogOut className="w-4 h-4" />}
        >
          Sign Out of TalentFlow
        </Button>
      </Card>
    </div>
  );
};

