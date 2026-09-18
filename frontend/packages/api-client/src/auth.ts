import { useState, useEffect, useCallback } from 'react';
import { setToken, getToken } from './client';

declare global {
  interface Window {
    Keycloak: any;
  }
}

export interface User {
  id: string;
  username: string;
  email: string;
  name: string;
  roles: string[];
}

export interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  isLoading: boolean;
}

let keycloakInstance: any = null;

export async function initKeycloak(): Promise<any> {
  if (keycloakInstance) return keycloakInstance;

  const keycloakUrl = process.env.NEXT_PUBLIC_KEYCLOAK_URL || 'http://localhost:8080';
  const realm = process.env.NEXT_PUBLIC_KEYCLOAK_REALM || 'bhoomi';
  const clientId = process.env.NEXT_PUBLIC_KEYCLOAK_CLIENT_ID || 'bhoomi-officer';

  // Dynamic import for Keycloak JS adapter
  if (typeof window === 'undefined') return null;

  // @ts-ignore
  const Keycloak = (await import('keycloak-js' as any)).default || (window as any).Keycloak;

  keycloakInstance = new Keycloak({
    url: keycloakUrl,
    realm: realm,
    clientId: clientId,
  });

  try {
    const authenticated = await keycloakInstance.init({
      onLoad: 'check-sso',
      pkceMethod: 'S256',
      silentCheckSsoRedirectUri: window.location.origin + '/silent-check-sso.html',
    });

    if (authenticated && keycloakInstance.token) {
      setToken(keycloakInstance.token);

      // Refresh token before it expires
      setInterval(() => {
        keycloakInstance
          .updateToken(70)
          .then((refreshed: boolean) => {
            if (refreshed && keycloakInstance.token) {
              setToken(keycloakInstance.token);
            }
          })
          .catch(() => {
            console.error('Failed to refresh token');
          });
      }, 60000);
    }

    return keycloakInstance;
  } catch (error) {
    console.error('Keycloak initialization failed', error);
    return null;
  }
}

export function useAuth(): AuthState & {
  login: () => Promise<void>;
  logout: () => Promise<void>;
  register: () => Promise<void>;
} {
  const [authState, setAuthState] = useState<AuthState>({
    isAuthenticated: false,
    user: null,
    isLoading: true,
  });

  useEffect(() => {
    initKeycloak().then((kc) => {
      if (kc?.authenticated) {
        const user: User = {
          id: kc.subject,
          username: kc.tokenParsed?.preferred_username || '',
          email: kc.tokenParsed?.email || '',
          name: kc.tokenParsed?.name || '',
          roles: kc.tokenParsed?.realm_access?.roles || [],
        };

        setAuthState({
          isAuthenticated: true,
          user,
          isLoading: false,
        });
      } else {
        setAuthState({
          isAuthenticated: false,
          user: null,
          isLoading: false,
        });
      }
    });
  }, []);

  const login = useCallback(async () => {
    if (keycloakInstance) {
      await keycloakInstance.login();
    }
  }, []);

  const logout = useCallback(async () => {
    if (keycloakInstance) {
      setToken(null);
      await keycloakInstance.logout();
    }
  }, []);

  const register = useCallback(async () => {
    if (keycloakInstance) {
      await keycloakInstance.register();
    }
  }, []);

  return {
    ...authState,
    login,
    logout,
    register,
  };
}

export { getToken };
