// Design tokens for Bhoomi Dhrishti (DoLR / Ministry of Rural Development)
// Strictly follows the institutional design system: light theme only, solid fills, institutional blue

export const colors = {
  // Institutional Blue brand family
  blue: {
    900: '#0B2E4E', // Text on blue, deep accents, sidebar bg (Officer/Admin)
    700: '#14548C', // Primary — buttons, links, active nav, brand mark
    600: '#103F68', // Primary hover/pressed
    500: '#2E6DA6', // Secondary interactive, icons
    100: '#E2ECF5', // Selected row, hover background, tinted chip
    50: '#F4F7FB',  // Page background tint (Citizen portal), subtle section bg
  },

  // Charcoal & Slate body ink
  ink: {
    900: '#16212E', // Body text — navy-tinted charcoal, never pure black
    600: '#4A5B6E', // Secondary text, labels, captions
  },

  // Surfaces
  surface: {
    DEFAULT: '#FFFFFF', // Card/panel background
    muted: '#F6F7F9',   // Page background (Officer/Admin), table stripe
  },

  // Borders
  border: {
    DEFAULT: '#DCE3EA', // Default hairline border
    strong: '#B9C5D1',  // Input borders, table header rule
  },

  // Solid categorical status colors (always paired with text labels)
  status: {
    approved: '#1E7B4D', // Approved / Verified / Healthy
    pending: '#B8720B',  // Pending / In review / Awaiting
    rejected: '#A32E2E', // Rejected / Disputed / Conflict
    info: '#5B6472',     // Informational / Neutral / Syncing
  },

  // Status direct shortcuts
  success: '#1E7B4D',
  warning: '#B8720B',
  error: '#A32E2E',

  // Neutral ramp
  neutral: {
    100: '#F6F7F9',
    200: '#E2ECF5',
    300: '#DCE3EA',
    400: '#B9C5D1',
    500: '#8A99A8',
    600: '#5B6472',
    700: '#4A5B6E',
    800: '#2E3A47',
    900: '#16212E',
  },

  // Land use classification tints
  landUse: {
    agricultural: '#2E7D32',
    residential: '#1565C0',
    commercial: '#E65100',
    industrial: '#546E7A',
    greenOpen: '#43A047',
    government: '#4527A0',
    mixedUse: '#8D6E63',
    waterBody: '#0277BD',
    forest: '#1B5E20',
    poramboke: '#795548',
    road: '#616161',
    railway: '#37474F',
    unoccupied: '#9E9E9E',
  },
} as const;


export const typography = {
  fontFamily: {
    sans: ['"Public Sans"', '"IBM Plex Sans"', 'system-ui', 'sans-serif'],
    serif: ['"IBM Plex Serif"', '"Roboto Slab"', 'Georgia', 'serif'],
    tamil: ['"Noto Sans Tamil"', 'sans-serif'],
  },
} as const;

export const borderRadius = {
  none: '0',
  sm: '4px',  // badges, inputs, chips
  md: '8px',  // buttons, cards
  lg: '12px', // modals, dropdown panels
  full: '9999px',
} as const;

export const shadows = {
  none: 'none',
  float: '0 4px 16px rgba(11, 46, 78, 0.12)', // Blue-tinted float shadow for dropdowns/modals
} as const;
