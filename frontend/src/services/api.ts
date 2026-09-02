/**
 * TalentFlow AI — Centralized Frontend API Service
 * Supports Automatic Refresh Token Rotation, JWT Interception, Request Tracing, and Error Normalization.
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL || (import.meta.env.PROD
  ? "https://ats-ibwo.onrender.com/api/v1"
  : "http://127.0.0.1:5000/api/v1");

const getStoredUser = () => {
  try {
    const raw = localStorage.getItem('user');
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
};

const getAuthToken = (): string | null => {
  const user = getStoredUser();
  return user ? user.token : null;
};

const getRefreshToken = (): string | null => {
  const user = getStoredUser();
  return user ? user.refresh_token : null;
};

const updateTokens = (token: string, refreshToken?: string) => {
  const user = getStoredUser() || {};
  user.token = token;
  if (refreshToken) user.refresh_token = refreshToken;
  localStorage.setItem('user', JSON.stringify(user));
};

const clearAuth = () => {
  localStorage.removeItem('user');
  window.dispatchEvent(new Event('auth:logout'));
};

let isRefreshing = false;
let refreshQueue: Array<(token: string) => void> = [];

const refreshAccessToken = async (): Promise<string | null> => {
  const refreshToken = getRefreshToken();
  if (!refreshToken) {
    clearAuth();
    return null;
  }

  if (isRefreshing) {
    return new Promise((resolve) => {
      refreshQueue.push((token) => resolve(token));
    });
  }

  isRefreshing = true;
  try {
    const res = await fetch(`${API_BASE}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken })
    });

    if (res.ok) {
      const data = await res.json();
      if (data.token) {
        updateTokens(data.token, data.refresh_token);
        refreshQueue.forEach((callback) => callback(data.token));
        refreshQueue = [];
        return data.token;
      }
    }
    clearAuth();
    return null;
  } catch (err) {
    clearAuth();
    return null;
  } finally {
    isRefreshing = false;
  }
};

const makeRequest = async (
  endpoint: string,
  method: string = 'GET',
  body?: any,
  isMultipart: boolean = false
): Promise<Response> => {
  const headers: Record<string, string> = {};
  if (!isMultipart) {
    headers['Content-Type'] = 'application/json';
  }
  const token = getAuthToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  // Generate unique client request ID
  headers['X-Request-ID'] = `tf-${Date.now()}-${Math.random().toString(36).substring(2, 8)}`;

  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint}`;
  let response = await fetch(url, {
    method,
    headers,
    body: isMultipart ? body : body ? JSON.stringify(body) : undefined
  });

  // If unauthorized, attempt transparent refresh once
  if (response.status === 401 && getRefreshToken()) {
    const newToken = await refreshAccessToken();
    if (newToken) {
      headers['Authorization'] = `Bearer ${newToken}`;
      response = await fetch(url, {
        method,
        headers,
        body: isMultipart ? body : body ? JSON.stringify(body) : undefined
      });
    }
  }

  return response;
};

export const apiClient = {
  get: (endpoint: string) => makeRequest(endpoint, 'GET'),
  post: (endpoint: string, data?: any, isMultipart = false) => makeRequest(endpoint, 'POST', data, isMultipart),
  put: (endpoint: string, data?: any) => makeRequest(endpoint, 'PUT', data),
  delete: (endpoint: string) => makeRequest(endpoint, 'DELETE'),
};

export default apiClient;
