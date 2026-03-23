import { useState, useEffect, useCallback } from 'react';
import { adminApi } from '../api/adminApi';

export function useAdminAuth() {
  const [user, setUser] = useState<Record<string, unknown> | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const token = localStorage.getItem('admin_access_token');
      if (!token) { setUser(null); return; }
      const { data } = await adminApi.getMe();
      if (data.role !== 'admin' && data.role !== 'superadmin') { setUser(null); return; }
      setUser(data);
    } catch { setUser(null); }
  }, []);

  useEffect(() => { refresh().finally(() => setIsLoading(false)); }, [refresh]);

  const login = async (email: string, password: string) => {
    const { data } = await adminApi.login(email, password);
    localStorage.setItem('admin_access_token', data.access_token);
    localStorage.setItem('admin_refresh_token', data.refresh_token);
    await refresh();
  };

  const logout = () => {
    localStorage.removeItem('admin_access_token');
    localStorage.removeItem('admin_refresh_token');
    setUser(null);
  };

  return { user, isLoading, isAuthenticated: !!user, login, logout, refresh };
}
