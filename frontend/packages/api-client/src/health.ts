import { apiRequest } from './client';

export interface ServiceEndpointConfig {
  id: string;
  name: string;
  port: number;
  healthPath: string;
}

export const PLATFORM_SERVICES: ServiceEndpointConfig[] = [
  { id: 'gateway', name: 'API Gateway (NGINX)', port: 8000, healthPath: '/health' },
  { id: 'parcel-identity', name: 'Parcel Identity Service', port: 8001, healthPath: '/health' },
  { id: 'geospatial', name: 'Geospatial & Vector Tiles', port: 8002, healthPath: '/health' },
  { id: 'revenue-records', name: 'Revenue Records & RoR', port: 8003, healthPath: '/health' },
  { id: 'registration', name: 'Registration & Deeds', port: 8004, healthPath: '/health' },
  { id: 'planning-zoning', name: 'Planning & Master Plan', port: 8005, healthPath: '/health' },
  { id: 'fiscal', name: 'Fiscal & Property Tax', port: 8006, healthPath: '/health' },
  { id: 'utilities', name: 'Utilities Interconnect', port: 8007, healthPath: '/health' },
  { id: 'trust-engine', name: 'Trust Engine & Graph', port: 8008, healthPath: '/health' },
  { id: 'ml-inference', name: 'ML Inference Service', port: 8009, healthPath: '/health' },
  { id: 'citizen-services', name: 'Citizen Services & Passport', port: 8010, healthPath: '/health' },
  { id: 'audit', name: 'Audit & Hash-Chain Ledger', port: 8011, healthPath: '/health' },
  { id: 'notifications', name: 'Notifications & Alerts', port: 8012, healthPath: '/health' },
  { id: 'search', name: 'Full-text & NL Search', port: 8013, healthPath: '/health' },
  { id: 'analytics', name: 'Analytics & Reporting', port: 8014, healthPath: '/health' },
  { id: 'interoperability', name: 'State Interoperability', port: 8015, healthPath: '/health' },
  { id: 'satellite', name: 'Satellite Watch (Sentinel)', port: 8016, healthPath: '/health' },
  { id: 'workflows', name: 'Workflows Orchestrator', port: 8000, healthPath: '/workflows/health' },
];

export interface CheckedHealthResult {
  id: string;
  name: string;
  status: 'healthy' | 'unhealthy' | 'degraded' | 'checking';
  port: number;
  latencyMs?: number;
  message?: string;
}

export async function checkSingleServiceHealth(svc: ServiceEndpointConfig): Promise<CheckedHealthResult> {
  const start = Date.now();
  try {
    const url = `http://localhost:${svc.port}${svc.healthPath}`;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 2000);

    const res = await fetch(url, { signal: controller.signal, cache: 'no-store' });
    clearTimeout(timeoutId);
    const latency = Date.now() - start;

    if (res.ok) {
      return {
        id: svc.id,
        name: svc.name,
        status: 'healthy',
        port: svc.port,
        latencyMs: latency,
      };
    }
    return {
      id: svc.id,
      name: svc.name,
      status: 'unhealthy',
      port: svc.port,
      latencyMs: latency,
      message: `HTTP ${res.status}`,
    };
  } catch (err: any) {
    return {
      id: svc.id,
      name: svc.name,
      status: 'unhealthy',
      port: svc.port,
      latencyMs: Date.now() - start,
      message: err?.message || 'Connection refused',
    };
  }
}

export async function checkAllServicesHealth(): Promise<CheckedHealthResult[]> {
  const promises = PLATFORM_SERVICES.map(checkSingleServiceHealth);
  return Promise.all(promises);
}