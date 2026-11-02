/**
 * TalentFlow AI — Jobs API Client
 */
import client from './client';
import { Job, Application } from '../types';

export interface CreateJobPayload {
  title: string;
  description: string;
  company_name?: string;
  department?: string;
  required_skills?: string;
  experience_required?: number;
  location?: string;
  job_type?: string;
  salary?: string;
  status?: string;
  occupational_class?: string;
  specific_role?: string;
}

export const jobsApi = {
  getJobs: async (params?: { hr_only?: boolean; status?: string; search?: string }): Promise<Job[]> => {
    const res = await client.get<{ status: string; data?: Job[]; jobs?: Job[] }>('/jobs', { params });
    return res.data || res.jobs || [];
  },

  getJob: async (id: string): Promise<Job> => {
    const res = await client.get<{ status: string; data?: Job; job?: Job }>(`/jobs/${id}`);
    return res.data || res.job || (res as any);
  },

  createJob: async (payload: CreateJobPayload): Promise<Job> => {
    const res = await client.post<{ status: string; data?: Job; job?: Job }>('/jobs', payload);
    return res.data || res.job || (res as any);
  },

  publishJob: async (id: string): Promise<Job> => {
    const res = await client.post<{ status: string; data?: Job; job?: Job }>(`/jobs/${id}/publish`);
    return res.data || res.job || (res as any);
  },

  updateJob: async (id: string, payload: Partial<CreateJobPayload>): Promise<Job> => {
    const res = await client.put<{ status: string; data?: Job; job?: Job }>(`/jobs/${id}`, payload);
    return res.data || res.job || (res as any);
  },

  deleteJob: async (id: string): Promise<void> => {
    await client.delete(`/jobs/${id}`);
  },

  getJobApplications: async (jobId: string): Promise<Application[]> => {
    const res = await client.get<{ status: string; data?: Application[]; applications?: Application[] }>(
      `/jobs/${jobId}/applications`
    );
    return res.data || res.applications || [];
  },
};

