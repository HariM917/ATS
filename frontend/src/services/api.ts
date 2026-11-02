/**
 * TalentFlow AI — Single Centralized API Contract
 * Canonical interface re-exporting client and all domain API modules.
 */
import client, { API_BASE_URL, getAccessToken, clearTokens } from '../api/client';
import { authApi } from '../api/auth';
import { candidatesApi } from '../api/candidates';
import { resumesApi } from '../api/resumes';
import { matchingApi } from '../api/matching';
import { jobsApi } from '../api/jobs';
import { applicationsApi } from '../api/applications';
import { chatApi } from '../api/chat';
import { analyticsApi } from '../api/analytics';
import { rolesApi } from '../api/roles';

export {
  client,
  API_BASE_URL,
  getAccessToken,
  clearTokens,
  authApi,
  candidatesApi,
  resumesApi,
  matchingApi,
  jobsApi,
  applicationsApi,
  chatApi,
  analyticsApi,
  rolesApi,
};

export default client;

