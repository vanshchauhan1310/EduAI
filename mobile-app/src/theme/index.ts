// Brand palette — Government of Telangana examinations theme:
//   Sky Blue   #008DDF — navigation bars, headers, primary buttons, logo text
//   Deep Navy  #01337B — main brand text, darkest primary shade
//   Dark Amber #D36100 / Light Coral #EE6B00 — secondary accents, section headings
//   Leaf Green #5CB811 — action buttons / success states
//   Cyan Blue  #0055AA — links / informational accents
//   Cream      #FEFBF0 — page background canvas
export const Colors = {
  primary: {
    50:  '#ebf6fc',
    100: '#d1eaf9',
    200: '#9ed4f3',
    400: '#38a6e6',
    500: '#1496e2',
    600: '#008DDF',
    700: '#006eae',
    800: '#004e8c',
    900: '#01337B',
  },
  secondary: {
    500: '#EE6B00',
    600: '#D36100',
  },
  success: '#5CB811',
  warning: '#f59e0b',
  danger:  '#ef4444',
  info:    '#0055AA',

  neutral: {
    50:  '#f9fafb',
    100: '#f3f4f6',
    200: '#e5e7eb',
    300: '#d1d5db',
    400: '#9ca3af',
    500: '#6b7280',
    600: '#4b5563',
    700: '#374151',
    800: '#1f2937',
    900: '#111827',
  },

  white: '#ffffff',
  black: '#000000',

  background: '#FEFBF0',
  surface: '#ffffff',
  border: '#e5e7eb',
  text: {
    primary:   '#111827',
    secondary: '#6b7280',
    disabled:  '#9ca3af',
    inverse:   '#ffffff',
  },
};

export const Typography = {
  sizes: {
    xs:   10,
    sm:   12,
    base: 14,
    md:   16,
    lg:   18,
    xl:   20,
    '2xl': 24,
    '3xl': 30,
    '4xl': 36,
  },
  weights: {
    regular: '400' as const,
    medium:  '500' as const,
    semibold: '600' as const,
    bold:    '700' as const,
  },
};

export const Spacing = {
  xs:  4,
  sm:  8,
  md:  12,
  base: 16,
  lg:  20,
  xl:  24,
  '2xl': 32,
  '3xl': 48,
};

export const BorderRadius = {
  sm:   4,
  md:   8,
  lg:   12,
  xl:   16,
  '2xl': 24,
  full: 9999,
};

export const Shadows = {
  sm: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  md: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 4,
    elevation: 3,
  },
  lg: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.12,
    shadowRadius: 8,
    elevation: 5,
  },
};
