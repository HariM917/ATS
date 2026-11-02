/**
 * TalentFlow AI — Analytics API Client
 */
import client from './client';

export const analyticsApi = {
  getOverview: async (): Promise<any> => {
    const res = await client.get('/analytics/overview');
    return res.data || res;
  },

  getRecruiterOverview: async (): Promise<any> => {
    const res = await client.get('/analytics/recruiter');
    return res.data || res;
  },
};

