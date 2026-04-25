/**
 * CashLab — Auth store (Zustand + SecureStore)
 */
import { create } from 'zustand';
import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';
import type { AuthUser } from '../services/authService';

interface AuthState {
  isAuthenticated: boolean;
  isLoading: boolean;
  user: AuthUser | null;
  accessToken: string | null;
  refreshToken: string | null;

  // Actions
  setAuth: (user: AuthUser, accessToken: string, refreshToken: string) => void;
  clearAuth: () => void;
  setLoading: (loading: boolean) => void;
  hydrate: () => Promise<void>;
}

// SecureStore helpers (fallback para web)
async function setSecure(key: string, value: string) {
  if (Platform.OS === 'web') {
    localStorage.setItem(key, value);
  } else {
    await SecureStore.setItemAsync(key, value);
  }
}

async function getSecure(key: string): Promise<string | null> {
  if (Platform.OS === 'web') {
    return localStorage.getItem(key);
  }
  return SecureStore.getItemAsync(key);
}

async function deleteSecure(key: string) {
  if (Platform.OS === 'web') {
    localStorage.removeItem(key);
  } else {
    await SecureStore.deleteItemAsync(key);
  }
}

export const useAuthStore = create<AuthState>((set) => ({
  isAuthenticated: false,
  isLoading: true,
  user: null,
  accessToken: null,
  refreshToken: null,

  setAuth: async (user, accessToken, refreshToken) => {
    await setSecure('access_token', accessToken);
    await setSecure('refresh_token', refreshToken);
    await setSecure('user', JSON.stringify(user));
    set({ isAuthenticated: true, user, accessToken, refreshToken, isLoading: false });
  },

  clearAuth: async () => {
    await deleteSecure('access_token');
    await deleteSecure('refresh_token');
    await deleteSecure('user');
    set({ isAuthenticated: false, user: null, accessToken: null, refreshToken: null, isLoading: false });
  },

  setLoading: (loading) => set({ isLoading: loading }),

  hydrate: async () => {
    try {
      const accessToken = await getSecure('access_token');
      const refreshToken = await getSecure('refresh_token');
      const userStr = await getSecure('user');

      if (accessToken && refreshToken && userStr) {
        const user = JSON.parse(userStr);
        set({ isAuthenticated: true, user, accessToken, refreshToken, isLoading: false });
      } else {
        set({ isLoading: false });
      }
    } catch {
      set({ isLoading: false });
    }
  },
}));
