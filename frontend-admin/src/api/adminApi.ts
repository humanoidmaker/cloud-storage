import axios from 'axios';
import type { DashboardStats, AdminUser, SystemHealth, AdminSettings, StorageBreakdownItem } from '../types/admin';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const client = axios.create({ baseURL: API_URL, headers: { 'Content-Type': 'application/json' } });

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('admin_access_token');
  if (token && config.headers) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export const adminApi = {
  login: (email: string, password: string) => client.post('/api/auth/login', { email, password }),
  getMe: () => client.get('/api/auth/me'),
  getDashboard: () => client.get<DashboardStats>('/api/admin/dashboard'),
  getUsers: (params?: Record<string, string | number>) => client.get('/api/admin/users', { params }),
  createUser: (data: { email: string; name: string; password: string; role?: string }) => client.post('/api/admin/users', data),
  updateUser: (id: string, data: Record<string, string>) => client.put(`/api/admin/users/${id}`, data),
  updateQuota: (id: string, quota: number) => client.put(`/api/admin/users/${id}/quota`, { storage_quota: quota }),
  deactivateUser: (id: string) => client.post(`/api/admin/users/${id}/deactivate`),
  activateUser: (id: string) => client.post(`/api/admin/users/${id}/activate`),
  resetPassword: (id: string) => client.post(`/api/admin/users/${id}/reset-password`),
  deleteUser: (id: string, transferTo?: string) => client.delete(`/api/admin/users/${id}`, { params: transferTo ? { transfer_to: transferTo } : {} }),
  getStorageBreakdown: () => client.get<StorageBreakdownItem[]>('/api/admin/storage/breakdown'),
  getTopConsumers: () => client.get('/api/admin/storage/top-consumers'),
  getStorageTrends: () => client.get('/api/admin/storage/trends'),
  bulkQuota: (userIds: string[], quota: number) => client.post('/api/admin/storage/bulk-quota', { user_ids: userIds, storage_quota: quota }),
  getFiles: (userId: string, folderId?: string) => client.get('/api/admin/files', { params: { user_id: userId, folder_id: folderId } }),
  deleteFile: (id: string) => client.delete(`/api/admin/files/${id}`),
  getActivity: (params?: Record<string, string | number>) => client.get('/api/admin/activity', { params }),
  exportActivity: (params?: Record<string, string>) => client.get('/api/admin/activity/export', { params, responseType: 'blob' }),
  getHealth: () => client.get<SystemHealth>('/api/admin/system/health'),
  getSettings: () => client.get<AdminSettings>('/api/admin/settings'),
  updateSettings: (data: Partial<AdminSettings>) => client.put('/api/admin/settings', data),
};
