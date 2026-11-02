/**
 * TalentFlow AI — Centralized Enterprise API Client
 * Features:
 * - Environment-driven Base URL (VITE_API_BASE_URL)
 * - Automatic Authorization Header injection
 * - Transparent 401 Interception & Refresh Token Rotation
 * - Concurrent Request Queue during Token Refresh
 * - Timeout handling via AbortController
 * - Error Normalization with descriptive human-readable messages
 * - Multipart File Upload support without boundary corruption
 */

import { ApiError } from '../types';

// Resolve base URL from environment or fallback cleanly
const rawBase = (import.meta.env.VITE_API_BASE_URL || (import.meta.env.PROD
  ? 'https://ats-ibwo.onrender.com/api/v1'
  : 'http://127.0.0.1:5000/api/v1')).trim().replace(/\/+$/, '');

export const API_BASE_URL = rawBase.includes('/api')
  ? rawBase
  : `${rawBase}/api/v1`;

export const getAccessToken = (): string | null => {
  try {
    return localStorage.getItem('tf_access_token');
  } catch {
    return null;
  }
};

export const getRefreshToken = (): string | null => {
  try {
    return localStorage.getItem('tf_refresh_token');
  } catch {
    return null;
  }
};

export const setTokens = (token: string, refreshToken?: string) => {
  try {
    localStorage.setItem('tf_access_token', token);
    if (refreshToken) {
      localStorage.setItem('tf_refresh_token', refreshToken);
    }
  } catch {}
};

export const clearTokens = () => {
  try {
    localStorage.removeItem('tf_access_token');
    localStorage.removeItem('tf_refresh_token');
    localStorage.removeItem('tf_user');
  } catch {}
  window.dispatchEvent(new CustomEvent('auth:logout'));
};

let isRefreshing = false;
let refreshSubscribers: Array<(token: string | null) => void> = [];

const subscribeTokenRefresh = (cb: (token: string | null) => void) => {
  refreshSubscribers.push(cb);
};

const onRefreshed = (token: string | null) => {
  refreshSubscribers.forEach((cb) => cb(token));
  refreshSubscribers = [];
};

/**
 * Perform transparent refresh token rotation
 */
export const refreshAccessToken = async (): Promise<string | null> => {
  const refreshToken = getRefreshToken();
  if (!refreshToken) {
    clearTokens();
    return null;
  }

  if (isRefreshing) {
    return new Promise((resolve) => {
      subscribeTokenRefresh((token) => resolve(token));
    });
  }

  isRefreshing = true;
  try {
    const res = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (res.ok) {
      const data = await res.json();
      if (data.token) {
        setTokens(data.token, data.refresh_token);
        onRefreshed(data.token);
        return data.token;
      }
    }
    clearTokens();
    onRefreshed(null);
    return null;
  } catch {
    clearTokens();
    onRefreshed(null);
    return null;
  } finally {
    isRefreshing = false;
  }
};

export interface RequestOptions extends RequestInit {
  timeoutMs?: number;
  isMultipart?: boolean;
  params?: Record<string, any>;
}

/**
 * Core HTTP Request Execution
 */
export async function apiRequest<T = any>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<T> {
  const { timeoutMs = 30000, isMultipart = false, params, headers: customHeaders, ...rest } = options;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  const headers: Record<string, string> = {};
  if (!isMultipart) {
    headers['Content-Type'] = 'application/json';
  }

  const token = getAccessToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  // Request tracing
  headers['X-Request-ID'] = `tf-${Date.now()}-${Math.random().toString(36).substring(2, 8)}`;

  if (customHeaders) {
    Object.assign(headers, customHeaders);
  }

  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  let url = endpoint.startsWith('http') ? endpoint : `${API_BASE_URL}${cleanEndpoint}`;

  if (params && Object.keys(params).length > 0) {
    const searchParams = new URLSearchParams();
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== null && value !== '') {
        searchParams.append(key, String(value));
      }
    }
    const qs = searchParams.toString();
    if (qs) {
      url += (url.includes('?') ? '&' : '?') + qs;
    }
  }

  try {
    let response = await fetch(url, {
      ...rest,
      headers,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    // Handle 401 Unauthorized with token refresh & replay
    if (response.status === 401 && getRefreshToken() && !endpoint.includes('/auth/login') && !endpoint.includes('/auth/refresh')) {
      const newToken = await refreshAccessToken();
      if (newToken) {
        headers['Authorization'] = `Bearer ${newToken}`;
        response = await fetch(url, {
          ...rest,
          headers,
        });
      }
    }

    // Parse response
    let responseData: any;
    const contentType = response.headers.get('content-type') || '';
    if (contentType.includes('application/json')) {
      responseData = await response.json();
    } else {
      responseData = await response.text();
    }

    if (!response.ok) {
      const errorMessage =
        (typeof responseData === 'object' && responseData !== null && responseData.message) ||
        (typeof responseData === 'string' && responseData.length > 0 ? responseData : 'An unexpected error occurred.');
      
      const errorCode =
        (typeof responseData === 'object' && responseData !== null && responseData.error_code) ||
        `HTTP_${response.status}`;

      const error: ApiError = {
        status: 'error',
        error_code: errorCode,
        message: errorMessage,
        details: responseData,
      };

      throw error;
    }

    return responseData as T;
  } catch (err: any) {
    clearTimeout(timeoutId);
    if (err.name === 'AbortError') {
      const timeoutError: ApiError = {
        status: 'error',
        error_code: 'TIMEOUT',
        message: 'Request timed out. The server may be waking up, please try again.',
      };
      throw timeoutError;
    }
    if (err.status === 'error' && err.message) {
      throw err;
    }
    const networkError: ApiError = {
      status: 'error',
      error_code: 'NETWORK_ERROR',
      message: err.message || 'Network connection failed. Please check your internet connection.',
    };
    throw networkError;
  }
}

/**
 * Convenient HTTP helpers
 */
export const client = {
  get: <T = any>(endpoint: string, options?: RequestOptions) =>
    apiRequest<T>(endpoint, { ...options, method: 'GET' }),

  post: <T = any>(endpoint: string, data?: any, options?: RequestOptions) =>
    apiRequest<T>(endpoint, {
      ...options,
      method: 'POST',
      body: options?.isMultipart ? data : data !== undefined ? JSON.stringify(data) : undefined,
    }),

  put: <T = any>(endpoint: string, data?: any, options?: RequestOptions) =>
    apiRequest<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: options?.isMultipart ? data : data !== undefined ? JSON.stringify(data) : undefined,
    }),

  delete: <T = any>(endpoint: string, options?: RequestOptions) =>
    apiRequest<T>(endpoint, { ...options, method: 'DELETE' }),
};

export default client;

