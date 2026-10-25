/**
 * KisanCare Mobile Design System & Theme Tokens
 * Green-and-white agricultural theme designed for readability and large touch targets.
 */

import '@/global.css';
import { Platform } from 'react-native';

export const Colors = {
  light: {
    // Primary Greens
    primary: '#2E7D32',
    primaryLight: '#4CAF50',
    primaryDark: '#1B5E20',
    primaryContainer: '#E8F5E9',
    primarySelected: '#C8E6C9',
    tint: '#2E7D32',

    // Harvest Gold / Secondary Accents
    accent: '#F57F17',
    accentLight: '#FFF8E1',
    accentDark: '#E65100',

    // Background & Surfaces
    background: '#F8FAF8',
    surface: '#FFFFFF',
    backgroundElement: '#E8F5E9',
    backgroundSelected: '#C8E6C9',

    // Borders & Dividers
    border: '#E0EAE1',
    borderLight: '#EEF4EF',

    // Text & Contrast
    text: '#1B2E1D',
    textSecondary: '#556E58',
    textMuted: '#7E9681',
    textInverse: '#FFFFFF',

    // Status Colors
    success: '#2E7D32',
    successLight: '#E8F5E9',
    warning: '#ED6C02',
    warningLight: '#FFF3E0',
    error: '#D32F2F',
    errorLight: '#FFEBEE',
    info: '#0288D1',
    infoLight: '#E1F5FE',
  },
  dark: {
    primary: '#81C784',
    primaryLight: '#A5D6A7',
    primaryDark: '#2E7D32',
    primaryContainer: '#1B2A1E',
    primarySelected: '#2D4532',
    tint: '#81C784',

    accent: '#FFB74D',
    accentLight: '#3E2A10',
    accentDark: '#F57F17',

    background: '#101811',
    surface: '#1A241C',
    backgroundElement: '#1B2A1E',
    backgroundSelected: '#2D4532',

    border: '#2C3A2E',
    borderLight: '#233025',

    text: '#FFFFFF',
    textSecondary: '#A3B8A6',
    textMuted: '#6B826F',
    textInverse: '#101811',

    success: '#81C784',
    successLight: '#1B2A1E',
    warning: '#FFB74D',
    warningLight: '#332310',
    error: '#EF5350',
    errorLight: '#331515',
    info: '#4FC3F7',
    infoLight: '#0E2838',
  },
} as const;

export type ThemeColor = keyof typeof Colors.light & keyof typeof Colors.dark;

export const Typography = {
  sizes: {
    xs: 12,
    sm: 14,
    md: 16,
    lg: 18,
    xl: 20,
    xxl: 24,
    title: 28,
  },
  weights: {
    normal: '400' as const,
    regular: '400' as const,
    medium: '500' as const,
    semibold: '600' as const,
    bold: '700' as const,
  },
  lineHeights: {
    tight: 1.2,
    normal: 1.4,
    relaxed: 1.6,
  },
};

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
  web: {
    sans: 'var(--font-display)',
    serif: 'var(--font-serif)',
    rounded: 'var(--font-rounded)',
    mono: 'var(--font-mono)',
  },
});

export const Spacing = {
  half: 2,
  one: 4,
  two: 8,
  three: 12,
  four: 16,
  five: 20,
  six: 24,
  seven: 32,
  eight: 40,
} as const;

export const BorderRadius = {
  sm: 8,
  md: 12,
  card: 16,
  lg: 20,
  pill: 999,
} as const;

export const Shadows = {
  card: Platform.select({
    ios: {
      shadowColor: '#1B2E1D',
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.06,
      shadowRadius: 8,
    },
    android: {
      elevation: 2,
    },
    default: {
      boxShadow: '0 2px 8px rgba(27, 46, 29, 0.06)',
    },
  }),
  cardRaised: Platform.select({
    ios: {
      shadowColor: '#1B2E1D',
      shadowOffset: { width: 0, height: 4 },
      shadowOpacity: 0.1,
      shadowRadius: 12,
    },
    android: {
      elevation: 4,
    },
    default: {
      boxShadow: '0 4px 12px rgba(27, 46, 29, 0.1)',
    },
  }),
};

export const Layout = {
  minTouchTarget: 48,
  bottomTabHeight: Platform.select({ ios: 60, android: 68 }) ?? 64,
  maxWidth: 720,
};

export const BottomTabInset = Platform.select({ ios: 50, android: 72 }) ?? 0;
export const MaxContentWidth = 720;
