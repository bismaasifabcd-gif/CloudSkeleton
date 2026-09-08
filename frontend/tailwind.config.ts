import type { Config } from 'tailwindcss';

export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: {
          50: '#f8fafc',
          100: '#eef2f7',
          200: '#dbe3ee',
          300: '#b7c4d6',
          400: '#8393aa',
          500: '#5f7089',
          600: '#44546a',
          700: '#334155',
          800: '#1f2937',
          900: '#111827',
          950: '#070b12',
        },
        signal: {
          50: '#ecfeff',
          100: '#cffafe',
          500: '#06b6d4',
          600: '#0891b2',
          700: '#0e7490',
        },
        aws: {
          orange: '#ff9900',
          deep: '#232f3e',
        },
      },
      boxShadow: {
        panel: '0 18px 60px rgba(15, 23, 42, 0.08)',
      },
    },
  },
  plugins: [],
} satisfies Config;
