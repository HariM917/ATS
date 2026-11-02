/**
 * TalentFlow AI — Matching & Occupational Classification API Client
 */
import client from './client';
import { MatchResult } from '../types';

export interface EvaluatePayload {
  resume_text?: string;
  resume_id?: string;
  job_description?: string;
  role_id?: string;
  specific_role?: string;
  required_skills?: string;
  experience_required?: number;
}

export const matchingApi = {
  evaluate: async (payload: EvaluatePayload): Promise<MatchResult> => {
    const res = await client.post<{ status: string; data?: MatchResult; result?: MatchResult }>(
      '/matching/evaluate',
      payload,
      { timeoutMs: 60000 }
    );
    return res.data || res.result || (res as any);
  },

  getRankings: async (jobId: string): Promise<any[]> => {
    const res = await client.get(`/matching/rankings/${jobId}`);
    return res.data || res.rankings || [];
  },

  batchScreen: async (jobId: string): Promise<any> => {
    return client.post(`/matching/batch-screen/${jobId}`);
  },
};

