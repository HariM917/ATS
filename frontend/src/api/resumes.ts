/**
 * TalentFlow AI — Resumes API Client
 */
import client from './client';
import { Resume, ResumeUploadResponse, ResumeQualityAnalysis } from '../types';

export const resumesApi = {
  upload: async (file: File): Promise<Resume> => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await client.post<ResumeUploadResponse>('/resumes/upload', formData, {
      isMultipart: true,
      timeoutMs: 60000,
    });
    return res.data || res.resume || (res as any);
  },

  getMyResumes: async (): Promise<Resume[]> => {
    const res = await client.get<{ status: string; data?: Resume[]; resumes?: Resume[] }>('/resumes/my-resumes');
    return res.data || res.resumes || [];
  },

  getResume: async (id: string): Promise<Resume> => {
    const res = await client.get<{ status: string; data?: Resume; resume?: Resume }>(`/resumes/${id}`);
    return res.data || res.resume || (res as any);
  },

  deleteResume: async (id: string): Promise<void> => {
    await client.delete(`/resumes/${id}`);
  },

  getAnalysis: async (id: string): Promise<any> => {
    const res = await client.get(`/resumes/${id}/analysis`);
    return res.data || res.analysis || res;
  },

  analyzeQuality: async (resumeId?: string, rawText?: string): Promise<ResumeQualityAnalysis> => {
    const res = await client.post<{ status: string; data?: ResumeQualityAnalysis; quality?: ResumeQualityAnalysis }>(
      '/resumes/analyze-quality',
      { resume_id: resumeId, raw_text: rawText }
    );
    return res.data || res.quality || (res as any);
  },
};

