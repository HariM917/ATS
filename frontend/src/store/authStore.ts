/**
 * TalentFlow AI — Global Auth Store (Zustand)
 */
import { create } from 'zustand';
import { User, UserRole } from '../types';
import { authApi, LoginPayload, RegisterPayload } from '../api/auth';
import { getAccessToken, clearTokens } from '../api/client';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  login: (payload: LoginPayload) => Promise<boolean>;
  register: (payload: RegisterPayload) => Promise<boolean>;
  logout: () => Promise<void>;
  loadUser: () => Promise<void>;
  setUser: (user: User | null) => void;
  setError: (error: string | null) => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: getAccessToken(),
  isAuthenticated: !!getAccessToken(),
  isLoading: true,
  error: null,

  login: async (payload: LoginPayload) => {
    set({ isLoading: true, error: null });
    try {
      const res = await authApi.login(payload);
      if (res.token) {
        const userObj: User = {
          id: '',
          email: res.email || payload.email,
          role: (res.role as UserRole) || 'candidate',
          name: res.user,
          username: res.user,
        };
        try {
          const me = await authApi.getCurrentUser();
          if (me.user) {
            Object.assign(userObj, me.user);
          }
        } catch {}
        set({
          user: userObj,
          token: res.token,
          isAuthenticated: true,
          isLoading: false,
          error: null,
        });
        return true;
      }
      set({ isLoading: false, error: res.message || 'Login failed.' });
      return false;
    } catch (err: any) {
      set({
        isLoading: false,
        error: err.message || 'Invalid email or password.',
      });
      return false;
    }
  },

  register: async (payload: RegisterPayload) => {
    set({ isLoading: true, error: null });
    try {
      const res = await authApi.register(payload);
      if (res.token) {
        const userObj: User = {
          id: '',
          email: res.email || payload.email,
          role: (res.role as UserRole) || (payload.role as UserRole) || 'candidate',
          name: res.user || payload.name,
          username: res.user || payload.name,
        };
        try {
          const me = await authApi.getCurrentUser();
          if (me.user) {
            Object.assign(userObj, me.user);
          }
        } catch {}
        set({
          user: userObj,
          token: res.token,
          isAuthenticated: true,
          isLoading: false,
          error: null,
        });
        return true;
      }
      set({ isLoading: false, error: res.message || 'Registration failed.' });
      return false;
    } catch (err: any) {
      set({
        isLoading: false,
        error: err.message || 'Registration failed. Please check your details.',
      });
      return false;
    }
  },

  logout: async () => {
    set({ isLoading: true });
    await authApi.logout();
    set({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    });
  },

  loadUser: async () => {
    const token = getAccessToken();
    if (!token) {
      set({ user: null, token: null, isAuthenticated: false, isLoading: false });
      return;
    }

    try {
      const res = await authApi.getCurrentUser();
      if (res.user) {
        set({
          user: res.user,
          token: getAccessToken(),
          isAuthenticated: true,
          isLoading: false,
        });
        return;
      }
    } catch {
      clearTokens();
      set({ user: null, token: null, isAuthenticated: false, isLoading: false });
    }
  },

  setUser: (user) => set({ user }),
  setError: (error) => set({ error }),
}));

// Listen for global logout events (triggered on token refresh failure)
if (typeof window !== 'undefined') {
  window.addEventListener('auth:logout', () => {
    useAuthStore.getState().logout();
  });
}

