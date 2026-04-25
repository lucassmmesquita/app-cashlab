/**
 * CashLab — Design Tokens (iOS systemColors)
 *
 * Ref: docs/CASHLAB_DESIGN_SYSTEM_v2.html
 * Exclusivamente iOS systemColors. Adaptação automática Light/Dark.
 * Grid 8pt. SF Pro (sistema). Sem gradientes.
 */

import { Platform } from 'react-native';

// ── Cores ─────────────────────────────────────────────────────────

export const SystemColors = {
  blue:   { light: '#007AFF', dark: '#0A84FF' },
  green:  { light: '#34C759', dark: '#30D158' },
  red:    { light: '#FF3B30', dark: '#FF453A' },
  orange: { light: '#FF9500', dark: '#FF9F0A' },
  yellow: { light: '#FFCC00', dark: '#FFD60A' },
  purple: { light: '#AF52DE', dark: '#BF5AF2' },
  pink:   { light: '#FF2D55', dark: '#FF375F' },
  teal:   { light: '#5AC8FA', dark: '#64D2FF' },
  indigo: { light: '#5856D6', dark: '#5E5CE6' },
  gray:   { light: '#8E8E93', dark: '#8E8E93' },
} as const;

export type ThemeMode = 'light' | 'dark';

export interface ThemeColors {
  // Surfaces
  bg: string;
  surface: string;
  surfaceSecondary: string;

  // Text
  label: string;
  secondaryLabel: string;
  tertiaryLabel: string;

  // Separators
  separator: string;

  // Semantic
  blue: string;
  green: string;
  red: string;
  orange: string;
  yellow: string;
  purple: string;
  pink: string;
  teal: string;
  indigo: string;
  gray: string;

  // Segments
  segmentBg: string;
  segmentActive: string;
}

export const LightColors: ThemeColors = {
  bg: '#F2F2F7',
  surface: '#FFFFFF',
  surfaceSecondary: '#F2F2F7',
  label: '#000000',
  secondaryLabel: 'rgba(60,60,67,0.6)',
  tertiaryLabel: 'rgba(60,60,67,0.3)',
  separator: 'rgba(60,60,67,0.29)',
  blue: '#007AFF',
  green: '#34C759',
  red: '#FF3B30',
  orange: '#FF9500',
  yellow: '#FFCC00',
  purple: '#AF52DE',
  pink: '#FF2D55',
  teal: '#5AC8FA',
  indigo: '#5856D6',
  gray: '#8E8E93',
  segmentBg: 'rgba(118,118,128,0.12)',
  segmentActive: '#FFFFFF',
};

export const DarkColors: ThemeColors = {
  bg: '#000000',
  surface: '#1C1C1E',
  surfaceSecondary: '#2C2C2E',
  label: '#FFFFFF',
  secondaryLabel: 'rgba(235,235,245,0.6)',
  tertiaryLabel: 'rgba(235,235,245,0.3)',
  separator: 'rgba(84,84,88,0.65)',
  blue: '#0A84FF',
  green: '#30D158',
  red: '#FF453A',
  orange: '#FF9F0A',
  yellow: '#FFD60A',
  purple: '#BF5AF2',
  pink: '#FF375F',
  teal: '#64D2FF',
  indigo: '#5E5CE6',
  gray: '#8E8E93',
  segmentBg: 'rgba(118,118,128,0.24)',
  segmentActive: '#636366',
};

// ── Tipografia ────────────────────────────────────────────────────

export const Typography = {
  largeTitle: { fontSize: 34, fontWeight: '700' as const, letterSpacing: -1.5 },
  heroValue:  { fontSize: 34, fontWeight: '700' as const, letterSpacing: -1 },
  title2:     { fontSize: 22, fontWeight: '700' as const, letterSpacing: -0.5 },
  headline:   { fontSize: 17, fontWeight: '600' as const },
  body:       { fontSize: 17, fontWeight: '400' as const },
  subheadline:{ fontSize: 15, fontWeight: '400' as const },
  footnote:   { fontSize: 13, fontWeight: '400' as const },
  caption2:   { fontSize: 11, fontWeight: '400' as const },
} as const;

// ── Espaçamento (8pt grid) ────────────────────────────────────────

export const Spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  base: 16,
  lg: 20,
  xl: 24,
  xxl: 32,
} as const;

// ── Border Radius ─────────────────────────────────────────────────

export const Radius = {
  sm: 6,
  md: 8,
  lg: 10,   // iOS grouped card
  xl: 12,   // botão
  pill: 999,
} as const;

// ── Legacy exports (backward compat) ──────────────────────────────

export const Fonts = Platform.select({
  ios: {
    sans: 'system-ui',
    serif: 'ui-serif',
    rounded: 'ui-rounded',
    mono: 'ui-monospace',
  },
  default: {
    sans: 'normal',
    serif: 'serif',
    rounded: 'normal',
    mono: 'monospace',
  },
});

export const BottomTabInset = Platform.select({ ios: 50, android: 80 }) ?? 0;
export const MaxContentWidth = 800;
