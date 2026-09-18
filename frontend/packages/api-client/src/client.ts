const DEFAULT_GATEWAY = 'http://localhost:8000';
const BASE_URL = (
  (typeof process !== 'undefined' && process.env?.NEXT_PUBLIC_API_URL) ||
  DEFAULT_GATEWAY
).replace(/\/$/, '');

export function buildUrl(endpoint: string): string {
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;

  // If endpoint is already a fully qualified URL
  if (cleanEndpoint.startsWith('http://') || cleanEndpoint.startsWith('https://')) {
    return cleanEndpoint;
  }

  // If BASE_URL already ends with /api/v1 and endpoint starts with /api/v1
  if (BASE_URL.endsWith('/api/v1') && cleanEndpoint.startsWith('/api/v1')) {
    return `${BASE_URL}${cleanEndpoint.replace('/api/v1', '')}`;
  }

  // If endpoint is a root route like /health, /workflows, /satellite, /ingest, /ogc
  const isRootRoute =
    cleanEndpoint.startsWith('/health') ||
    cleanEndpoint.startsWith('/workflows') ||
    cleanEndpoint.startsWith('/satellite') ||
    cleanEndpoint.startsWith('/ingest') ||
    cleanEndpoint.startsWith('/ogc');

  if (BASE_URL.endsWith('/api/v1') && isRootRoute) {
    const rootBase = BASE_URL.replace('/api/v1', '');
    return `${rootBase}${cleanEndpoint}`;
  }

  if (!BASE_URL.endsWith('/api/v1') && !cleanEndpoint.startsWith('/api/v1') && !isRootRoute) {
    return `${BASE_URL}/api/v1${cleanEndpoint}`;
  }

  return `${BASE_URL}${cleanEndpoint}`;
}

export interface ApiError {
  message: string;
  code?: string;
  status: number;
}

export class ApiClientError extends Error {
  status: number;
  code?: string;

  constructor(message: string, status: number, code?: string) {
    super(message);
    this.name = 'ApiClientError';
    this.status = status;
    this.code = code;
  }
}

export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = buildUrl(endpoint);

  const defaultHeaders: HeadersInit = {
    'Content-Type': 'application/json',
  };

  const token = getToken();
  if (token) {
    defaultHeaders['Authorization'] = `Bearer ${token}`;
  }

  const config: RequestInit = {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  };

  try {
    const response = await fetch(url, config);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({
        message: response.statusText,
      }));

      throw new ApiClientError(
        errorData.message || errorData.detail || 'An error occurred',
        response.status,
        errorData.code
      );
    }

    // Handle 204 No Content
    if (response.status === 204) {
      return undefined as T;
    }

    return await response.json();
  } catch (error) {
    if (error instanceof ApiClientError) {
      throw error;
    }

    throw new ApiClientError(
      error instanceof Error ? error.message : 'Network error',
      0
    );
  }
}

export const api = {
  get: <T>(endpoint: string, options?: RequestInit) =>
    apiRequest<T>(endpoint, { method: 'GET', ...options }),
  post: <T>(endpoint: string, data?: any, options?: RequestInit) =>
    apiRequest<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
      ...options,
    }),
  put: <T>(endpoint: string, data?: any, options?: RequestInit) =>
    apiRequest<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
      ...options,
    }),
  delete: <T>(endpoint: string, options?: RequestInit) =>
    apiRequest<T>(endpoint, { method: 'DELETE', ...options }),
};

let tokenStore: string | null = null;

export function setToken(token: string | null) {
  tokenStore = token;
  if (typeof window !== 'undefined') {
    if (token) {
      localStorage.setItem('bhoomi_auth_token', token);
    } else {
      localStorage.removeItem('bhoomi_auth_token');
    }
  }
}

export function getToken(): string | null {
  if (tokenStore) return tokenStore;

  if (typeof window !== 'undefined') {
    return localStorage.getItem('bhoomi_auth_token');
  }

  return null;
}
