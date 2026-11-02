/**
 * TalentFlow AI — Applications Pipeline API Client
 */
import client from './client';
import { Application } from '../types';

export interface SubmitApplicationPayload {
  job_id: string;
  resume_id?: string;
  resume_path?: string;
}

export interface UpdateStagePayload {
  stage: string;
  notes?: string;
}

export const applicationsApi = {
  getApplications: async (): Promise<Application[]> => {
    const res = await client.get<{ status: string; data?: Application[]; applications?: Application[] }>(
      '/applications'
    );
    return res.data || res.applications || [];
  },

  submitApplication: async (payload: SubmitApplicationPayload): Promise<Application> => {
    const res = await client.post<{ status: string; data?: Application; application?: Application }>(
      '/applications',
      payload
    );
    return res.data || res.application || (res as any);
  },

  getApplication: async (id: string): Promise<Application> => {
    const res = await client.get<{ status: string; data?: Application; application?: Application }>(
      `/applications/${id}`
    );
    return res.data || res.application || (res as any);
  },

  updateStage: async (id: string, payload: UpdateStagePayload): Promise<Application> => {
    const res = await client.put<{ status: string; data?: Application; application?: Application }>(
      `/applications/${id}`,
      payload
    );
    return res.data || res.application || (res as any);
  },

  apply: async (jobId: string, resumeId?: string): Promise<Application> => {
    return applicationsApi.submitApplication({ job_id: jobId, resume_id: resumeId });
  },
};

