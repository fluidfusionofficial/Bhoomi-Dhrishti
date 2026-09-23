import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './src/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        blue: {
          900: '#0B2E4E',
          800: '#12315e',
          700: '#14548C',
          600: '#103F68',
          500: '#2E6DA6',
          100: '#E2ECF5',
          50: '#F4F7FB',
        },
        ink: {
          900: '#16212E',
          600: '#4A5B6E',
        },
      },
      fontFamily: {
        sans: ['var(--font-public-sans)', 'Public Sans', 'system-ui', 'sans-serif'],
        serif: ['var(--font-ibm-plex-serif)', 'IBM Plex Serif', 'Georgia', 'serif'],
      },
    },
  },
  plugins: [],
};

export default config;
