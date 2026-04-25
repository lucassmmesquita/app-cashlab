/**
 * CashLab — Auth service (login, register, social, refresh)
 */
import api from './api';

export interface AuthUser {
  id: number;
  name: string;
  email: string;
  is_active: boolean;
  auth_provider: string;
  avatar_url: string | null;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: AuthUser;
}

export const authService = {
  async login(email: string, password: string): Promise<AuthResponse> {
    const response = await api.post('/auth/login', { email, password });
    return response.data;
  },

  async register(name: string, email: string, password: string): Promise<AuthResponse> {
    const response = await api.post('/auth/register', { name, email, password });
    return response.data;
  },

  async socialLogin(provider: 'google' | 'apple', idToken: string): Promise<AuthResponse> {
    const response = await api.post('/auth/social', { provider, id_token: idToken });
    return response.data;
  },

  async refreshToken(refreshToken: string): Promise<{ access_token: string }> {
    const response = await api.post('/auth/refresh', { refresh_token: refreshToken });
    return response.data;
  },

  async getMe(): Promise<AuthUser> {
    const response = await api.get('/auth/me');
    return response.data;
  },
};
