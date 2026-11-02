/**
 * TalentFlow AI — Candidates API Client
 */
import client from './client';
import { CandidateProfile, Application } from '../types';

export const candidatesApi = {
  getProfile: async (): Promise<CandidateProfile> => {
    const res = await client.get('/candidates/profile');
    return res.data || res.profile || res;
  },

  updateProfile: async (data: Partial<CandidateProfile>): Promise<CandidateProfile> => {
    const res = await client.put('/candidates/profile', data);
    return res.data || res.profile || res;
  },

  getDashboard: async (): Promise<any> => {
    const res = await client.get('/candidates/dashboard');
    return res.data || res;
  },

  getApplications: async (): Promise<Application[]> => {
    const res = await client.get('/candidates/applications');
    return res.data || res.applications || [];
  },

  listCandidates: async (params?: { search?: string; skill?: string }): Promise<any[]> => {
    const res = await client.get('/candidates', { params });
    return res.data || res.candidates || [];
  },
};

