import { api } from './client';

// ── Executive Overview & KPIs ─────────────────────────────────────────────────

export interface StateDashboardKPIs {
  state_code: string;
  state_name: string;
  total_parcels: number;
  total_area_sq_km: number;
  active_mutations: number;
  pending_mutations: number;
  open_conflicts: number;
  resolved_conflicts: number;
  conformance_percent: number;
  avg_mutation_sla_days: number;
  anomaly_rate_percent: number;
  districts_count: number;
  last_sync_timestamp: string;
}

export interface DistrictDashboardKPIs {
  lgd_code: string;
  district_name: string;
  state_code: string;
  total_parcels: number;
  active_disputes: number;
  open_conflicts: number;
  mutation_sla_days: number;
  unapproved_conversion_alerts: number;
}

export async function fetchStateDashboardAnalytics(stateCode: string): Promise<StateDashboardKPIs> {
  return api.get<StateDashboardKPIs>(`/analytics/dashboard/state/${stateCode}`);
}

export async function fetchDistrictDashboardAnalytics(lgdCode: string): Promise<DistrictDashboardKPIs> {
  return api.get<DistrictDashboardKPIs>(`/analytics/dashboard/district/${lgdCode}`);
}

export async function fetchConflictsSummary(): Promise<{
  total_conflicts: number;
  by_type: Record<string, number>;
  by_severity: Record<string, number>;
  by_district: Record<string, number>;
}> {
  return api.get<{
    total_conflicts: number;
    by_type: Record<string, number>;
    by_severity: Record<string, number>;
    by_district: Record<string, number>;
  }>('/analytics/conflicts/summary');
}

export async function fetchAdminResolutionMetrics(): Promise<any> {
  return api.get<any>('/analytics/resolution/metrics');
}

// ── State Onboarding & Interop ────────────────────────────────────────────────

export interface OnboardedStateItem {
  code: string;
  name: string;
  status: 'ACTIVE' | 'ONBOARDING' | 'PENDING' | 'SUSPENDED';
  onboarded_date: string;
  parcels_ingested: number;
  conformance_score: number;
  revenue_endpoint?: string;
  registration_endpoint?: string;
  last_sync?: string;
}

export async function fetchInteropStates(): Promise<OnboardedStateItem[]> {
  return api.get<OnboardedStateItem[]>('/interop/states');
}

export async function onboardState(code: string, data: Partial<OnboardedStateItem>): Promise<{ success: boolean; state: OnboardedStateItem }> {
  return api.post<{ success: boolean; state: OnboardedStateItem }>(`/interop/states/${code}/onboard`, data);
}

export async function fetchStateSyncStatus(code: string): Promise<{
  state_code: string;
  status: 'HEALTHY' | 'SYNCING' | 'ERROR';
  departments: Record<string, { status: string; last_sync: string; records_synced: number }>;
}> {
  return api.get<any>(`/interop/states/${code}/sync-status`);
}

export async function triggerStateDepartmentSync(stateCode: string, department: string): Promise<{ success: boolean; job_id: string }> {
  return api.post<{ success: boolean; job_id: string }>(`/interop/sync/${stateCode}/${department}`);
}

export async function fetchOnboardingStatesAnalytics(): Promise<any> {
  return api.get<any>('/analytics/onboarding/states');
}

// ── Mapping & Conformance ─────────────────────────────────────────────────────

export interface SchemaMapping {
  id: string;
  state_code: string;
  department: string;
  field_mappings: Record<string, string>;
  is_valid: boolean;
  validation_errors?: string[];
}

export async function fetchInteropMappings(): Promise<SchemaMapping[]> {
  return api.get<SchemaMapping[]>('/interop/mappings');
}

export async function validateInteropMapping(data: any): Promise<{ valid: boolean; errors: string[] }> {
  return api.post<{ valid: boolean; errors: string[] }>('/interop/mappings/validate', data);
}

export async function fetchStateConformance(stateCode: string): Promise<{
  state_code: string;
  overall_score: number;
  ogc_wfs_conformance: boolean;
  ogc_wms_conformance: boolean;
  schema_conformance: number;
  last_run: string;
  test_results: Array<{ test: string; passed: boolean; message: string }>;
}> {
  return api.get<any>(`/interop/conformance/${stateCode}`);
}

export async function runStateConformance(stateCode: string): Promise<any> {
  return api.post<any>(`/interop/conformance/${stateCode}/run`);
}

// ── Ingestion Monitor ─────────────────────────────────────────────────────────

export async function triggerIngest(sourceType: string, data: any): Promise<{ job_id: string; status: string }> {
  return api.post<{ job_id: string; status: string }>(`/ingest/${sourceType}`, data);
}

export async function fetchIngestStatus(jobId: string): Promise<{
  job_id: string;
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  records_processed: number;
  errors_count: number;
  progress_percent: number;
}> {
  return api.get<any>(`/ingest/status/${jobId}`);
}

export async function fetchIngestSources(): Promise<Array<{ id: string; name: string; type: string; status: string }>> {
  return api.get<any[]>('/ingest/sources');
}

export async function fetchIngestMappings(stateCode: string): Promise<any> {
  return api.get<any>(`/ingest/mappings/${stateCode}`);
}

export async function saveIngestMappings(stateCode: string, data: any): Promise<any> {
  return api.post<any>(`/ingest/mappings/${stateCode}`, data);
}

// ── Trends & Service Delivery SLA ─────────────────────────────────────────────

export interface LandUseTrendPoint {
  month: string;
  agricultural: number;
  residential: number;
  commercial: number;
  industrial: number;
  government: number;
}

export async function fetchLandUseTrends(months: number = 12): Promise<LandUseTrendPoint[]> {
  return api.get<LandUseTrendPoint[]>(`/analytics/land-use/trends?months=${months}`);
}

export interface ServiceDeliverySLA {
  average_days: number;
  p90_days: number;
  sla_met_percent: number;
  by_service: Array<{
    service_name: string;
    avg_days: number;
    p90_days: number;
    sla_target_days: number;
    compliance_rate: number;
  }>;
}

export async function fetchServiceDeliverySLA(): Promise<ServiceDeliverySLA> {
  return api.get<ServiceDeliverySLA>('/analytics/service-delivery/time');
}

// ── Natural Language Query Console ────────────────────────────────────────────

export async function queryNaturalLanguage(query: string): Promise<any> {
  return api.post<any>('/analytics/query/natural-language', { query });
}

export async function fetchNLQueryExamples(): Promise<string[]> {
  return api.get<string[]>('/analytics/query/examples');
}

export async function fetchNLQueryCapabilities(): Promise<any> {
  return api.get<any>('/analytics/query/capabilities');
}

export async function fetchNLQueryHelp(): Promise<any> {
  return api.get<any>('/analytics/query/help');
}

// ── Audit & Integrity ─────────────────────────────────────────────────────────

export interface AuditEvent {
  id: string;
  event_type: string;
  timestamp: string;
  actor_id: string;
  actor_role: string;
  resource_type: string;
  resource_id: string;
  parcel_id?: string;
  purpose?: string;
  hash: string;
  prev_hash: string;
}

export interface IntegrityVerification {
  verified: boolean;
  total_events: number;
  chain_valid: boolean;
  tampered_blocks_count: number;
  last_verified_at: string;
  root_hash: string;
}

export async function searchAuditEvents(params?: Record<string, any>): Promise<AuditEvent[]> {
  const query = params ? `?${new URLSearchParams(params as any).toString()}` : '';
  return api.get<AuditEvent[]>(`/audit/events/search${query}`);
}

export async function verifyAuditIntegrity(): Promise<IntegrityVerification> {
  return api.get<IntegrityVerification>('/audit/integrity/verify');
}