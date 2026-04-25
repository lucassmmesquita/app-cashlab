/**
 * CashLab — Theme hook (iOS systemColors Light/Dark)
 *
 * Retorna cores, tipografia e espaçamento baseado no tema ativo.
 * Suporta: 'system' (segue celular), 'light', 'dark'.
 */
import { useColorScheme } from 'react-native';
import { useSettingsStore } from '@/store/useSettingsStore';
import {
  LightColors,
  DarkColors,
  Typography,
  Spacing,
  Radius,
  type ThemeColors,
} from '@/constants/theme';

export interface AppTheme {
  colors: ThemeColors;
  typography: typeof Typography;
  spacing: typeof Spacing;
  radius: typeof Radius;
  isDark: boolean;
}

export function useAppTheme(): AppTheme {
  const systemScheme = useColorScheme();
  const themeMode = useSettingsStore((s) => s.themeMode);

  let isDark: boolean;
  if (themeMode === 'system') {
    isDark = systemScheme === 'dark';
  } else {
    isDark = themeMode === 'dark';
  }

  return {
    colors: isDark ? DarkColors : LightColors,
    typography: Typography,
    spacing: Spacing,
    radius: Radius,
    isDark,
  };
}
