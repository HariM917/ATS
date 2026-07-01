const API_URL = import.meta.env.VITE_API_URL || (import.meta.env.PROD
  ? "https://ats-ibwo.onrender.com/api"
  : "http://127.0.0.1:5000/api");

const getAuthToken = (): string | null => {
  try {
    const stored = localStorage.getItem('user');
    if (stored) {
      const parsed = JSON.parse(stored);
      return parsed.token || null;
    }
  } catch (e) {
    console.error("[API] Failed to parse auth token", e);
  }
  return null;
};

const getHeaders = (isMultipart = false): Record<string, string> => {
  const headers: Record<string, string> = {};
  if (!isMultipart) {
    headers['Content-Type'] = 'application/json';
  }
  const token = getAuthToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
};

export const apiClient = {
  async get(endpoint: string) {
    const res = await fetch(`${API_URL}${endpoint}`, {
      method: 'GET',
      headers: getHeaders(),
    });
    if (res.status === 401) {
      localStorage.removeItem('user');
    }
    return res;
  },

  async post(endpoint: string, data?: any, isMultipart = false) {
    const res = await fetch(`${API_URL}${endpoint}`, {
      method: 'POST',
      headers: getHeaders(isMultipart),
      body: isMultipart ? data : JSON.stringify(data),
    });
    if (res.status === 401) {
      localStorage.removeItem('user');
    }
    return res;
  },

  async put(endpoint: string, data?: any) {
    const res = await fetch(`${API_URL}${endpoint}`, {
      method: 'PUT',
      headers: getHeaders(),
      body: JSON.stringify(data),
    });
    if (res.status === 401) {
      localStorage.removeItem('user');
    }
    return res;
  },

  async delete(endpoint: string) {
    const res = await fetch(`${API_URL}${endpoint}`, {
      method: 'DELETE',
      headers: getHeaders(),
    });
    if (res.status === 401) {
      localStorage.removeItem('user');
    }
    return res;
  }
};
