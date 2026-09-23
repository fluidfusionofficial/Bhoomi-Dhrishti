'use client';

import * as React from 'react';

type Freshness = 'LIVE' | 'CACHED' | 'CHECKING';

const FreshnessContext = React.createContext<Freshness>('CACHED');

export function FreshnessProvider({ children }: { children: React.ReactNode }) {
  const [freshness, setFreshness] = React.useState<Freshness>('CHECKING');

  React.useEffect(() => {
    const check = async () => {
      try {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 3000);
        const res = await fetch('/api/parcel-identity/health', { signal: controller.signal });
        clearTimeout(timeout);
        setFreshness(res.ok ? 'LIVE' : 'CACHED');
      } catch {
        setFreshness('CACHED');
      }
    };
    check();
  }, []);

  return (
    <FreshnessContext.Provider value={freshness}>
      {children}
    </FreshnessContext.Provider>
  );
}

export function useFreshness(): 'LIVE' | 'CACHED' {
  const ctx = React.useContext(FreshnessContext);
  return ctx === 'CHECKING' ? 'CACHED' : ctx;
}
