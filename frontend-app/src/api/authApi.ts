import client from './client';
import type { AuthTokens, LoginCredentials, RegisterData, User } from '../types/user';

export const authApi = {
  register: (data: RegisterData) => client.post<User>('/api/auth/register', data),
  login: (data: LoginCredentials) => client.post<AuthTokens>('/api/auth/login', data),
  refresh: (refreshToken: string) => client.post<AuthTokens>('/api/auth/refresh', { refresh_token: refreshToken }),
  logout: () => client.post('/api/auth/logout'),
  getMe: () => client.get<User>('/api/auth/me'),
  changePassword: (currentPassword: string, newPassword: string) =>
    client.post('/api/auth/change-password', { current_password: currentPassword, new_password: newPassword }),
};
