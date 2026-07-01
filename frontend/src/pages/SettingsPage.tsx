import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { apiClient } from '../services/api';
import { Card, Button } from '../components/ui';
import { UserCircle, Shield, Loader2, Save } from 'lucide-react';

export const SettingsPage = () => {
  const { user } = useAuth();
  const [profile, setProfile] = useState<any>({});
  const [loading, setLoading] = useState(false);
  
  // We can write a simple custom toast handler if useToast fails to import
  const [toast, setToast] = useState<{ type: 'success' | 'error', msg: string } | null>(null);

  const showToast = (type: 'success' | 'error', msg: string) => {
    setToast({ type, msg });
    setTimeout(() => setToast(null), 4000);
  };

  useEffect(() => {
    if (user) {
      setProfile((prev: any) => ({ ...prev, ...user }));
      apiClient.get('/profile')
        .then(res => res.json())
        .then(data => setProfile((prev: any) => ({ ...prev, ...data })))
        .catch(() => {});
    }
  }, [user]);

  const handleSave = async () => {
    setLoading(true);
    try {
      const response = await apiClient.put('/profile', profile);
      const data = await response.json();
      if (data.success) {
        showToast('success', 'Profile updated successfully');
        // Update user state if needed (username might have changed)
        const stored = localStorage.getItem('user');
        if (stored) {
          const parsed = JSON.parse(stored);
          parsed.user = profile.username || parsed.user;
          localStorage.setItem('user', JSON.stringify(parsed));
        }
      } else {
        showToast('error', data.message || 'Failed to save profile');
      }
    } catch (error: any) {
      showToast('error', error.message || 'Connection failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto py-6 page-enter">
      {toast && (
        <div className={`fixed top-4 right-4 z-50 flex items-center gap-2 px-4 py-3 rounded-xl shadow-lg text-white font-medium ${toast.type === 'success' ? 'bg-emerald-500' : 'bg-red-500'}`}>
          <span>{toast.msg}</span>
        </div>
      )}
      <div className="flex items-start gap-8">
        <div className="w-64 hidden lg:block space-y-1">
          <button className="w-full flex items-center gap-3 px-4 py-3 bg-white text-indigo-600 rounded-xl font-medium shadow-sm border border-gray-100">
            <UserCircle className="w-5 h-5" /> My Profile
          </button>
          <button className="w-full flex items-center gap-3 px-4 py-3 text-gray-500 hover:bg-white hover:text-gray-900 rounded-xl font-medium transition-colors">
            <Shield className="w-5 h-5" /> Security
          </button>
        </div>

        <div className="flex-1 space-y-6">
          <Card className="overflow-hidden">
            <div className="h-32 bg-gradient-to-r from-indigo-500 to-purple-600 relative">
              <div className="absolute -bottom-10 left-8 flex items-end gap-4">
                <div className="w-24 h-24 rounded-full bg-white p-1 shadow-xl">
                  <div className="w-full h-full rounded-full bg-gradient-to-br from-indigo-100 to-purple-100 flex items-center justify-center text-3xl font-bold text-indigo-600 border-4 border-white">
                    {(profile.firstName?.charAt(0) || profile.username?.charAt(0) || "A").toUpperCase()}
                  </div>
                </div>
                <div className="mb-2">
                  <h2 className="text-xl font-bold text-white drop-shadow-md">
                    {profile.firstName || profile.username || "Admin"} {profile.lastName || ""}
                  </h2>
                  <span className="px-2 py-0.5 bg-white/20 backdrop-blur-md text-white rounded text-xs font-medium border border-white/30 capitalize">{profile.role || 'User'}</span>
                </div>
              </div>
            </div>

            <div className="pt-16 p-8">
              <h3 className="text-lg font-bold text-gray-900 mb-6 border-b pb-2">Personal Information</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 mb-6">
                <div>
                  <label className="block text-xs font-bold text-gray-500 uppercase mb-2">First Name</label>
                  <input className="w-full p-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none" value={profile.firstName || profile.first_name || ""} placeholder="Enter first name" onChange={e => setProfile({ ...profile, firstName: e.target.value })} />
                </div>
                <div>
                  <label className="block text-xs font-bold text-gray-500 uppercase mb-2">Last Name</label>
                  <input className="w-full p-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none" value={profile.lastName || profile.last_name || ""} placeholder="Enter last name" onChange={e => setProfile({ ...profile, lastName: e.target.value })} />
                </div>
                <div className="sm:col-span-2">
                  <label className="block text-xs font-bold text-gray-500 uppercase mb-2">Bio</label>
                  <textarea className="w-full p-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none h-24 resize-none" value={profile.bio || ""} placeholder="Tell us about yourself" onChange={e => setProfile({ ...profile, bio: e.target.value })} />
                </div>
              </div>

              <h3 className="text-lg font-bold text-gray-900 mb-6 border-b pb-2 pt-4">Contact Info</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 mb-8">
                <div>
                  <label className="block text-xs font-bold text-gray-500 uppercase mb-2">Email Address</label>
                  <input type="email" disabled className="w-full p-3 bg-gray-100 border border-gray-200 rounded-xl outline-none cursor-not-allowed opacity-75" value={profile.email || ""} />
                </div>
                <div>
                  <label className="block text-xs font-bold text-gray-500 uppercase mb-2">Phone</label>
                  <input className="w-full p-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none" value={profile.phone || ""} placeholder="Enter phone number" onChange={e => setProfile({ ...profile, phone: e.target.value })} />
                </div>
                <div>
                  <label className="block text-xs font-bold text-gray-500 uppercase mb-2">City</label>
                  <input className="w-full p-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none" value={profile.city || ""} onChange={e => setProfile({ ...profile, city: e.target.value })} />
                </div>
                <div>
                  <label className="block text-xs font-bold text-gray-500 uppercase mb-2">State</label>
                  <input className="w-full p-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none" value={profile.state || ""} onChange={e => setProfile({ ...profile, state: e.target.value })} />
                </div>
              </div>

              <div className="flex justify-end pt-4">
                <Button onClick={handleSave} disabled={loading} className="px-8 py-3">
                  {loading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Save className="w-4 h-4 mr-2" />}
                  {loading ? "Saving..." : "Save Changes"}
                </Button>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};
