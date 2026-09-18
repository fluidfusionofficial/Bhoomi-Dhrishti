import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
    '../../packages/ui/src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          hover: 'hsl(var(--primary-hover))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))',
        },
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))',
        },
        border: {
          DEFAULT: 'hsl(var(--border))',
          strong: '#B9C5D1',
        },
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        blue: {
          900: '#0B2E4E',
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
        surface: {
          DEFAULT: '#FFFFFF',
          muted: '#F6F7F9',
        },
        status: {
          approved: '#1E7B4D',
          pending: '#B8720B',
          rejected: '#A32E2E',
          info: '#5B6472',
        },
        success: 'hsl(var(--success))',
        warning: 'hsl(var(--warning))',
        destructive: 'hsl(var(--destructive))',
        info: 'hsl(var(--info))',
      },
      fontFamily: {
        sans: ['var(--font-public-sans)', 'Public Sans', 'IBM Plex Sans', 'system-ui', 'sans-serif'],
        serif: ['var(--font-ibm-plex-serif)', 'IBM Plex Serif', 'Roboto Slab', 'Georgia', 'serif'],
        tamil: ['Noto Sans Tamil', 'sans-serif'],
      },
      borderRadius: {
        sm: '4px',
        md: '8px',
        lg: '12px',
      },
      boxShadow: {
        float: '0 4px 16px rgba(11, 46, 78, 0.12)',
      },
    },
  },
  plugins: [],
};

export default config;

