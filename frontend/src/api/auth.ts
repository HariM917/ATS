/**
 * TalentFlow AI — Authentication API Client
 */
import client, { setTokens, clearTokens } from './client';
import { AuthResponse, User } from '../types';

export interface RegisterPayload {
  name: string;
  email: string;
  password: string;
  role?: string;
  branch?: string;
  graduation_year?: number;
  company_name?: string;
}

export interface LoginPayload {
  email: string;
  password: string;
  role?: string;
}

export const authApi = {
  register: async (payload: RegisterPayload): Promise<AuthResponse> => {
    const res = await client.post<AuthResponse>('/auth/register', payload);
    if (res.token) {
      setTokens(res.token, res.refresh_token);
    }
    return res;
  },

  login: async (payload: LoginPayload): Promise<AuthResponse> => {
    const res = await client.post<AuthResponse>('/auth/login', payload);
    if (res.token) {
      setTokens(res.token, res.refresh_token);
    }
    return res;
  },

  logout: async (): Promise<void> => {
    try {
      await client.post('/auth/logout');
    } catch {}
    clearTokens();
  },

  getCurrentUser: async (): Promise<{ status: string; user: User }> => {
    return client.get<{ status: string; user: User }>('/auth/me');
  },
};

