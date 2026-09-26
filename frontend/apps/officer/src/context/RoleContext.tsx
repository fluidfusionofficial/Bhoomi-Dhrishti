'use client';

import * as React from 'react';

export type OfficerRole =
  | 'tehsildar'
  | 'sub-registrar'
  | 'town-planner'
  | 'surveyor'
  | 'collector';

export type OfficerNavTab =
  | 'home'
  | 'cadastral'
  | 'parcels'
  | 'queue'
  | 'revenue'
  | 'registration'
  | 'resolution'
  | 'spatial'
  | 'trust'
  | 'satellite'
  | 'planning'
  | 'analytics'
  | 'workflows'
  | 'search';

export interface RoleConfig {
  id: OfficerRole;
  title: string;
  subtitle: string;
  keycloakRole: string;
  color: string;
  bgColor: string;
  allowedTabs: OfficerNavTab[];
  defaultTab: OfficerNavTab;
}

export const ROLE_CONFIGS: Record<OfficerRole, RoleConfig> = {
  tehsildar: {
    id: 'tehsildar',
    title: 'Tehsildar',
    subtitle: 'Revenue Officer',
    keycloakRole: 'revenue_officer',
    color: '#14548C',
    bgColor: '#E2ECF5',
    allowedTabs: [
      'home',
      'cadastral',
      'parcels',
      'queue',
      'revenue',
      'registration',
      'planning',
      'resolution',
      'spatial',
      'trust',
      'workflows',
      'search',
    ],
    defaultTab: 'home',
  },
  'sub-registrar': {
    id: 'sub-registrar',
    title: 'Sub-Registrar',
    subtitle: 'Registration & Deeds Officer',
    keycloakRole: 'registration_officer',
    color: '#7C3AED',
    bgColor: '#EDE9FE',
    allowedTabs: [
      'home',
      'cadastral',
      'parcels',
      'queue',
      'registration',
      'revenue',
      'planning',
      'resolution',
      'spatial',
      'trust',
      'workflows',
      'search',
    ],
    defaultTab: 'home',
  },
  'town-planner': {
    id: 'town-planner',
    title: 'Town Planner',
    subtitle: 'Planning & Zoning Officer',
    keycloakRole: 'planning_officer',
    color: '#B45309',
    bgColor: '#FEF3C7',
    allowedTabs: [
      'home',
      'cadastral',
      'parcels',
      'queue',
      'planning',
      'revenue',
      'registration',
      'spatial',
      'satellite',
      'trust',
      'workflows',
      'search',
    ],
    defaultTab: 'home',
  },
  surveyor: {
    id: 'surveyor',
    title: 'Surveyor',
    subtitle: 'Cadastral Survey Officer',
    keycloakRole: 'field_officer',
    color: '#0369A1',
    bgColor: '#E0F2FE',
    allowedTabs: [
      'home',
      'cadastral',
      'parcels',
      'queue',
      'spatial',
      'revenue',
      'registration',
      'satellite',
      'resolution',
      'trust',
      'workflows',
      'search',
    ],
    defaultTab: 'home',
  },
  collector: {
    id: 'collector',
    title: 'District Collector',
    subtitle: 'Executive & Policy Analytics',
    keycloakRole: 'district_collector',
    color: '#0B2E4E',
    bgColor: '#E2ECF5',
    allowedTabs: [
      'home',
      'analytics',
      'cadastral',
      'parcels',
      'queue',
      'revenue',
      'registration',
      'resolution',
      'spatial',
      'trust',
      'satellite',
      'planning',
      'workflows',
      'search',
    ],
    defaultTab: 'home',
  },
};

interface RoleContextValue {
  role: OfficerRole;
  config: RoleConfig;
  setRole: (role: OfficerRole) => void;
  isTabAllowed: (tab: OfficerNavTab) => boolean;
}

const RoleContext = React.createContext<RoleContextValue | null>(null);

export function RoleProvider({ children }: { children: React.ReactNode }) {
  const [role, setRole] = React.useState<OfficerRole>('tehsildar');
  const [initialized, setInitialized] = React.useState(false);

  React.useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const urlRole = params.get('role') as OfficerRole | null;
    if (urlRole && urlRole in ROLE_CONFIGS) {
      setRole(urlRole);
    }
    setInitialized(true);
  }, []);

  const config = ROLE_CONFIGS[role];

  const isTabAllowed = React.useCallback(
    (tab: OfficerNavTab) => config.allowedTabs.includes(tab),
    [config]
  );

  if (!initialized) return null;

  return (
    <RoleContext.Provider value={{ role, config, setRole, isTabAllowed }}>
      {children}
    </RoleContext.Provider>
  );
}

export function useRole() {
  const ctx = React.useContext(RoleContext);
  if (!ctx) throw new Error('useRole must be used within RoleProvider');
  return ctx;
}
