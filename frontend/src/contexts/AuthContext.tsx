import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';

export interface UserData {
  user: string;
  email: string;
  role: 'hr' | 'candidate';
  token?: string;
  refresh_token?: string;
}

interface AuthContextType {
  user: UserData | null;
  token: string | null;
  isAuthenticated: boolean;
  isHR: boolean;
  isCandidate: boolean;
  login: (data: any) => void;
  logout: () => void;
  refreshSession: () => void;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  token: null,
  isAuthenticated: false,
  isHR: false,
  isCandidate: false,
  login: () => {},
  logout: () => {},
  refreshSession: () => {},
  loading: true,
});

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [user, setUser] = useState<UserData | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // Helper to decode JWT payload safely without external dependencies
  const isTokenExpired = useCallback((jwtToken: string): boolean => {
    try {
      const payloadBase64 = jwtToken.split('.')[1];
      if (!payloadBase64) return true;
      const decodedPayload = JSON.parse(atob(payloadBase64.replace(/-/g, '+').replace(/_/g, '/')));
      if (decodedPayload.exp) {
        const expirationDate = decodedPayload.exp * 1000;
        return Date.now() >= expirationDate;
      }
      return false;
    } catch {
      return true; // Treat invalid structure as expired
    }
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('user');
    setUser(null);
    setToken(null);
  }, []);

  const refreshSession = useCallback(() => {
    try {
      const stored = localStorage.getItem('user');
      if (stored) {
        const parsed: UserData = JSON.parse(stored);
        setUser(parsed);
        setToken(parsed.token || null);
      }
    } catch (e) {
      console.error("[AUTH] Failed to refresh session state:", e);
    }
  }, []);

  useEffect(() => {
    const initializeAuth = () => {
      try {
        const stored = localStorage.getItem('user');
        if (stored) {
          const parsed: UserData = JSON.parse(stored);
          if (parsed.token) {
            // Note: with refresh tokens, an expired access token is okay to load initially,
            // the api.ts interceptor will refresh it on the first request.
            setUser(parsed);
            setToken(parsed.token);
          }
        }
      } catch (e) {
        console.error("[AUTH] Failed to initialize session:", e);
      } finally {
        setLoading(false);
      }
    };
    initializeAuth();

    const handleLogoutEvent = () => logout();
    window.addEventListener('auth:logout', handleLogoutEvent);
    
    // Listen for storage events (e.g. from api.ts updating the token)
    const handleStorageEvent = (e: StorageEvent) => {
      if (e.key === 'user') {
        refreshSession();
      }
    };
    window.addEventListener('storage', handleStorageEvent);
    
    return () => {
      window.removeEventListener('auth:logout', handleLogoutEvent);
      window.removeEventListener('storage', handleStorageEvent);
    };
  }, [logout, refreshSession]);

  const login = (data: any) => {
    const userData: UserData = {
      user: data.user || data.username || "",
      email: data.email || "",
      role: data.role || "candidate",
      token: data.token,
      refresh_token: data.refresh_token,
    };
    localStorage.setItem('user', JSON.stringify(userData));
    setUser(userData);
    setToken(data.token || null);
  };

  const isAuthenticated = !!token;
  const isHR = user?.role === 'hr';
  const isCandidate = user?.role === 'candidate';

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated,
        isHR,
        isCandidate,
        login,
        logout,
        refreshSession,
        loading,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

