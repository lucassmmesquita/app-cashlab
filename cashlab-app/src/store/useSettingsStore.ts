/**
 * CashLab — Settings store (Zustand + AsyncStorage)
 *
 * Persiste: tema (system/light/dark), biometria habilitada.
 */
import { create } from 'zustand';
import AsyncStorage from '@react-native-async-storage/async-storage';

type ThemeMode = 'system' | 'light' | 'dark';

interface SettingsState {
  themeMode: ThemeMode;
  biometricEnabled: boolean;
  isHydrated: boolean;

  setThemeMode: (mode: ThemeMode) => void;
  setBiometricEnabled: (enabled: boolean) => void;
  hydrate: () => Promise<void>;
}

const STORAGE_KEY = '@cashlab_settings';

export const useSettingsStore = create<SettingsState>((set, get) => ({
  themeMode: 'system',
  biometricEnabled: false,
  isHydrated: false,

  setThemeMode: async (mode) => {
    set({ themeMode: mode });
    await persistSettings(get());
  },

  setBiometricEnabled: async (enabled) => {
    set({ biometricEnabled: enabled });
    await persistSettings(get());
  },

  hydrate: async () => {
    try {
      const raw = await AsyncStorage.getItem(STORAGE_KEY);
      if (raw) {
        const data = JSON.parse(raw);
        set({
          themeMode: data.themeMode || 'system',
          biometricEnabled: data.biometricEnabled || false,
          isHydrated: true,
        });
      } else {
        set({ isHydrated: true });
      }
    } catch {
      set({ isHydrated: true });
    }
  },
}));

async function persistSettings(state: SettingsState) {
  try {
    await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify({
      themeMode: state.themeMode,
      biometricEnabled: state.biometricEnabled,
    }));
  } catch {
    // Silently fail
  }
}
