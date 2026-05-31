import api from './api';
import { AuthTokens } from '../types';

export const authService = {
  login: async (email: string, password: string): Promise<AuthTokens> => {
    const normalizedEmail = email.trim().toLowerCase();
    const { data } = await api.post<AuthTokens>('/auth/login', { email: normalizedEmail, password });
    return data;
  },

  logout: async (): Promise<void> => {
    await api.post('/auth/logout');
  },

  refreshToken: async (refreshToken: string): Promise<AuthTokens> => {
    const { data } = await api.post<AuthTokens>('/auth/refresh', { refresh_token: refreshToken });
    return data;
  },

  forgotPassword: async (email: string): Promise<{ message: string }> => {
    const { data } = await api.post('/auth/forgot-password', { email });
    return data;
  },

  resetPassword: async (token: string, newPassword: string): Promise<{ message: string }> => {
    const { data } = await api.post('/auth/reset-password', { token, new_password: newPassword });
    return data;
  },

  getMe: async () => {
    const { data } = await api.get('/auth/me');
    return data;
  },

  updateFcmToken: async (token: string): Promise<void> => {
    await api.put(`/notifications/fcm-token?token=${encodeURIComponent(token)}`);
  },
};
