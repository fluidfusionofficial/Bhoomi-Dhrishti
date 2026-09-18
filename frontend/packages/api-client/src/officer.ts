import { api } from './client';

// ── Review Queue & Entity Resolution ──────────────────────────────────────────

export interface ReviewQueueItem {
  id: string;
  link_id?: string;
  type: 'IDENTITY_MATCH' | 'MUTATION_REVIEW' | 'TOPOLOGY_CONFLICT' | 'ANOMALY_TRIAGE';
  title: string;
  parcel_id?: string;
  ulpin?: string;
  confidence: number;
  priority: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  source_a: {
    system: string;
    identifier: string;
    value: string;
    owner_name?: string;
  };
  source_b: {
    system: string;
    identifier: string;
    value: string;
    owner_name?: string;
  };
  discrepancy_details?: string;
  created_at: string;
  status: 'PENDING' | 'APPROVED' | 'REJECTED';
}

export interface ReviewQueueResponse {
  total: number;
  items: ReviewQueueItem[];
}

export interface ResolutionMetrics {
  total_candidates: number;
  auto_linked: number;
  manual_reviewed: number;
  pending_review: number;
  accuracy_score: number;
  precision_rate: number;
}

export async function fetchReviewQueue(): Promise<ReviewQueueResponse> {
  return api.get<ReviewQueueResponse>('/reviews/queue');
}

export async function approveReviewLink(linkId: string, remarks?: string): Promise<{ success: boolean; link_id: string }> {
  return api.post<{ success: boolean; link_id: string }>(`/reviews/${linkId}/approve`, { remarks });
}

export async function rejectReviewLink(linkId: string, remarks?: string): Promise<{ success: boolean; link_id: string }> {
  return api.post<{ success: boolean; link_id: string }>(`/reviews/${linkId}/reject`, { remarks });
}

export async function fetchResolutionMetrics(): Promise<ResolutionMetrics> {
  return api.get<ResolutionMetrics>('/resolution/metrics');
}

export async function runResolution(options?: { state_code?: string; threshold?: number }): Promise<{ job_id: string; status: string }> {
  return api.post<{ job_id: string; status: string }>('/resolution/run', options);
}

// ── Revenue & Mutations ───────────────────────────────────────────────────────

export interface RoRRecord {
  parcel_id: string;
  ulpin: string;
  khasra_number: string;
  village_name: string;
  district_name: string;
  state_code: string;
  land_use: string;
  soil_class?: string;
  irrigation_type?: string;
  total_area_sq_m: number;
  owners: Array<{
    id: string;
    name: string;
    relation?: string;
    share_percent: number;
  }>;
  tax_status: 'PAID' | 'DUE' | 'EXEMPT';
}

export interface MutationRecord {
  id: string;
  mutation_id?: string;
  parcel_id: string;
  ulpin?: string;
  mutation_type: 'SALE' | 'INHERITANCE' | 'GIFT' | 'PARTITION' | 'COURT_ORDER';
  from_party_name: string;
  to_party_name: string;
  share_transferred?: string;
  applicant_name?: string;
  status: 'SUBMITTED' | 'UNDER_REVIEW' | 'APPROVED' | 'REJECTED' | 'DISPUTED';
  created_at: string;
  hearing_date?: string;
  officer_remarks?: string;
}

export async function fetchParcelRoR(parcelId: string): Promise<RoRRecord> {
  return api.get<RoRRecord>(`/revenue/parcels/${parcelId}/ror`);
}

export async function fetchParcelRights(parcelId: string): Promise<any> {
  return api.get<any>(`/revenue/parcels/${parcelId}/rights`);
}

export async function fetchParcelMutations(parcelId: string): Promise<MutationRecord[]> {
  return api.get<MutationRecord[]>(`/revenue/parcels/${parcelId}/mutations`);
}

export async function fetchRoRHistory(parcelId: string): Promise<any[]> {
  return api.get<any[]>(`/revenue/ror/${parcelId}/history`);
}

export async function createMutation(data: Partial<MutationRecord>): Promise<MutationRecord> {
  return api.post<MutationRecord>('/revenue/mutations', data);
}

export async function fetchMutationById(mutationId: string): Promise<MutationRecord> {
  return api.get<MutationRecord>(`/revenue/mutations/${mutationId}`);
}

export async function approveMutation(mutationId: string, remarks?: string): Promise<{ success: boolean; mutation_id: string }> {
  return api.put<{ success: boolean; mutation_id: string }>(`/revenue/mutations/${mutationId}/approve`, { remarks });
}

export async function rejectMutation(mutationId: string, reason: string): Promise<{ success: boolean; mutation_id: string }> {
  return api.put<{ success: boolean; mutation_id: string }>(`/revenue/mutations/${mutationId}/reject`, { reason });
}

export async function searchParties(query: string): Promise<any[]> {
  return api.get<any[]>(`/revenue/parties/search?q=${encodeURIComponent(query)}`);
}

export async function fetchPartyById(partyId: string): Promise<any> {
  return api.get<any>(`/revenue/parties/${partyId}`);
}

// ── Registration & Deeds ──────────────────────────────────────────────────────

export interface DeedRecord {
  id: string;
  deed_number: string;
  deed_type: 'SALE_DEED' | 'MORTGAGE_DEED' | 'GIFT_DEED' | 'LEASE_AGREEMENT';
  registration_date: string;
  sub_registrar_office: string;
  parcel_id: string;
  ulpin?: string;
  consideration_amount: number;
  stamp_duty_paid: number;
  parties: Array<{ name: string; role: 'SELLER' | 'BUYER' | 'LENDER' }>;
  verified: boolean;
}

export interface EncumbranceCertificate {
  parcel_id: string;
  ulpin: string;
  period_from: string;
  period_to: string;
  issued_on: string;
  encumbrances: Array<{
    entry_number: string;
    deed_number: string;
    registered_on: string;
    type: string;
    amount?: number;
    parties: string;
    status: 'ACTIVE' | 'DISCHARGED';
  }>;
}

export async function fetchParcelDeeds(parcelId: string): Promise<DeedRecord[]> {
  return api.get<DeedRecord[]>(`/registration/parcels/${parcelId}/deeds`);
}

export async function fetchDeedById(deedId: string): Promise<DeedRecord> {
  return api.get<DeedRecord>(`/registration/deeds/${deedId}`);
}

export async function fetchEncumbranceCertificate(parcelId: string): Promise<EncumbranceCertificate> {
  return api.get<EncumbranceCertificate>(`/registration/parcels/${parcelId}/ec`);
}

export async function checkDuplicateDeed(params: { deed_number: string; sro_code?: string; year?: number }): Promise<{ is_duplicate: boolean; existing_record?: any }> {
  const q = new URLSearchParams(params as any).toString();
  return api.get<{ is_duplicate: boolean; existing_record?: any }>(`/registration/deeds/check-duplicate?${q}`);
}

export async function preCheckDeed(data: any): Promise<{ pass: boolean; warnings: string[]; blockers: string[] }> {
  return api.post<{ pass: boolean; warnings: string[]; blockers: string[] }>('/registration/deeds/pre-check', data);
}

export async function fetchParcelEncumbrances(parcelId: string): Promise<any[]> {
  return api.get<any[]>(`/registration/parcels/${parcelId}/encumbrances`);
}

// ── Spatial & Topology Conflicts ──────────────────────────────────────────────

export interface TopologyConflict {
  id: string;
  conflict_id?: string;
  type: 'OVERLAP' | 'GAP' | 'DISPUTE' | 'SLIVER';
  severity: 'HIGH' | 'MEDIUM' | 'LOW';
  parcel_a_id: string;
  parcel_b_id?: string;
  ulpin_a?: string;
  ulpin_b?: string;
  overlap_area_sq_m?: number;
  detected_at: string;
  status: 'DETECTED' | 'INVESTIGATING' | 'RESOLVED' | 'DISPUTED';
  geometry?: any;
}

export async function fetchTopologyConflicts(): Promise<TopologyConflict[]> {
  return api.get<TopologyConflict[]>('/topology/conflicts');
}

export async function fetchTopologyConflictById(conflictId: string): Promise<TopologyConflict> {
  return api.get<TopologyConflict>(`/topology/conflicts/${conflictId}`);
}

export async function detectTopologyConflicts(options?: { village_code?: string }): Promise<{ detected_count: number; conflicts: TopologyConflict[] }> {
  return api.post<{ detected_count: number; conflicts: TopologyConflict[] }>('/topology/detect', options);
}

export async function fixTopologyConflict(conflictId: string, fixData: { strategy: 'SNAP_TO_SURVEY' | 'TRIM_OVERLAP' | 'SURVEY_REVISIT'; notes?: string }): Promise<{ success: boolean; updated_conflict: TopologyConflict }> {
  return api.post<{ success: boolean; updated_conflict: TopologyConflict }>(`/topology/conflicts/${conflictId}/fix`, fixData);
}

export async function fetchParcelGeometry(parcelId: string): Promise<any> {
  return api.get<any>(`/geo/parcels/${parcelId}/geometry`);
}

// ── Trust Engine & Anomalies ──────────────────────────────────────────────────

export interface TrustAnomaly {
  parcel_id: string;
  ulpin: string;
  anomaly_score: number; // 0.0 to 1.0
  risk_level: 'HIGH' | 'MEDIUM' | 'LOW';
  flags: string[];
  rapid_flip_count: number;
  circular_transfers_detected: boolean;
  value_mismatch_percent?: number;
  last_evaluated: string;
}

export interface TrustSummary {
  high_risk_count: number;
  medium_risk_count: number;
  low_risk_count: number;
  average_trust_score: number;
  circular_chains_count: number;
  rapid_flips_count: number;
}

export async function fetchTrustAnomalies(): Promise<TrustAnomaly[]> {
  return api.get<TrustAnomaly[]>('/trust/anomalies');
}

export async function fetchParcelAnomaly(parcelId: string): Promise<TrustAnomaly> {
  return api.get<TrustAnomaly>(`/trust/anomalies/${parcelId}`);
}

export async function rescoreTrustAnomalies(options?: { parcel_id?: string }): Promise<{ scored_count: number; status: string }> {
  return api.post<{ scored_count: number; status: string }>('/trust/anomalies/rescore', options);
}

export async function fetchTrustAnomaliesSummary(): Promise<TrustSummary> {
  return api.get<TrustSummary>('/trust/anomalies/summary');
}

export async function fetchCircularChains(): Promise<any[]> {
  return api.get<any[]>('/trust/graph/circular-chains');
}

export async function fetchRapidFlips(): Promise<any[]> {
  return api.get<any[]>('/trust/graph/rapid-flips');
}

export async function fetchPartyRisk(partyId: string): Promise<{ party_id: string; risk_score: number; flagged_transactions: any[] }> {
  return api.get<{ party_id: string; risk_score: number; flagged_transactions: any[] }>(`/trust/graph/party/${partyId}/risk`);
}

export async function fetchTrustNetworkGraph(): Promise<{ nodes: any[]; edges: any[] }> {
  return api.get<{ nodes: any[]; edges: any[] }>('/trust/graph/network');
}

export async function fetchFullGraphAnalysis(): Promise<any> {
  return api.get<any>('/trust/graph/analysis/full');
}

// ── Satellite Change Detection ────────────────────────────────────────────────

export interface SatelliteChangeResult {
  village_code: string;
  analysis_date: string;
  detected_changes_count: number;
  features?: any[];
  ndvi_drop_zones: number;
  ndbi_rise_zones: number;
}

export async function fetchSatelliteChangeDetection(villageCode: string): Promise<SatelliteChangeResult> {
  return api.get<SatelliteChangeResult>(`/satellite/change-detection/${villageCode}`);
}

export async function fetchSatelliteChangeLayers(villageCode: string): Promise<any> {
  return api.get<any>(`/satellite/change-layers/${villageCode}`);
}

export async function fetchAffectedParcels(villageCode: string): Promise<any[]> {
  return api.get<any[]>(`/satellite/affected-parcels/${villageCode}`);
}

// ── Guided Workflows ──────────────────────────────────────────────────────────

export async function executePropertySaleWorkflow(data: any): Promise<any> {
  return api.post<any>('/workflows/property-sale', data);
}

export async function executeBuildingPermitWorkflow(data: any): Promise<any> {
  return api.post<any>('/workflows/building-permit', data);
}

export async function executeLandUseEnforcementWorkflow(data: any): Promise<any> {
  return api.post<any>('/workflows/land-use-enforcement', data);
}

export async function scheduleLandUseEnforcement(data: any): Promise<any> {
  return api.post<any>('/workflows/land-use-enforcement/schedule', data);
}

// ── Lineage & Aliases ─────────────────────────────────────────────────────────

export interface ParcelAlias {
  id: string;
  parcel_id: string;
  alias_type: string; // e.g. SURVEY_NO, PATTA_NO, KHASRA_NO, STATE_ID
  alias_value: string;
  state_code: string;
  is_primary?: boolean;
}

export interface ParcelLineageNode {
  id: string;
  parcel_id: string;
  ulpin?: string;
  event_type: string; // SPLIT, MERGE, RE-SURVEY, REALLOCATION
  parent_parcel_ids?: string[];
  child_parcel_ids?: string[];
  effective_date: string;
  mutation_id?: string;
  remarks?: string;
}

export async function fetchParcelAliases(parcelId: string): Promise<ParcelAlias[]> {
  return api.get<ParcelAlias[]>(`/aliases/parcel/${parcelId}`);
}

export async function fetchParcelLineage(parcelId: string): Promise<ParcelLineageNode[]> {
  return api.get<ParcelLineageNode[]>(`/lineage/${parcelId}`);
}