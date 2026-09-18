import { api } from './client';

export interface MyParcelSummary {
  parcel_id: string;
  ulpin: string;
  land_use?: string;
  area_sq_m?: number;
  survey_number?: string;
  village_name?: string;
  district_name?: string;
  state_code?: string;
  has_active_mutation?: boolean;
  encumbered?: boolean;
  has_dispute?: boolean;
}

export interface MyParcelsResponse {
  citizen_id: string;
  parcels: MyParcelSummary[];
}

export interface ParcelProfile {
  parcel_id: string;
  ulpin: string;
  area_sq_m?: number;
  land_use?: string;
  geometry?: any;
  is_urban?: boolean;
  encumbered?: boolean;
  has_dispute?: boolean;
  state_code?: string;
  district_code?: string;
  village_code?: string;
  rights?: Array<{
    right_type: string;
    holder_name: string;
    share?: string;
  }>;
  encumbrances?: Array<{
    encumbrance_type: string;
    holder_name: string;
    amount?: number;
    is_active: boolean;
  }>;
  disputes?: Array<{
    case_number: string;
    status: string;
  }>;
  own_deeds?: Array<{
    deed_type: string;
    registration_date: string;
    consideration_amount?: number;
  }>;
}

export interface CatalogServiceItem {
  id: string;
  code: string;
  title: string;
  name?: string;
  description: string;
  department: string;
  estimated_days: number;
  fee_inr: number;
  required_documents: string[];
}

export interface ApplicationSubmission {
  service_code: string;
  parcel_id: string;
  applicant_name: string;
  applicant_phone: string;
  applicant_email?: string;
  applicant_id?: string;
  details?: Record<string, any>;
  documents?: Array<{
    doc_type: string;
    file_name: string;
    file_size_bytes?: number;
  }>;
}

export interface ApplicationRecord {
  application_id: string;
  id?: string;
  service_code: string;
  service_name?: string;
  parcel_id: string;
  ulpin?: string;
  status: 'SUBMITTED' | 'IN_REVIEW' | 'APPROVED' | 'REJECTED' | 'DISPUTED';
  submission_date: string;
  applicant_name: string;
  current_officer?: string;
  tracking_id?: string;
  remarks?: string;
  timeline?: Array<{
    status: string;
    timestamp: string;
    actor: string;
    notes?: string;
  }>;
}

export interface ParcelAccessLogEntry {
  id: string;
  timestamp: string;
  parcel_id: string;
  ulpin?: string;
  accessor_role: string;
  accessor_department: string;
  accessor_id: string;
  purpose: string;
  access_type: 'VIEW' | 'MUTATION_REVIEW' | 'ENCUMBRANCE_CHECK' | 'DISPUTE_TRIAGE';
}

export interface NotificationItem {
  id: string;
  user_id: string;
  title: string;
  message: string;
  type: 'INFO' | 'ALERT' | 'SUCCESS' | 'WARNING';
  created_at: string;
  is_read: boolean;
  link_url?: string;
}

// ── Citizen Services API Calls ────────────────────────────────────────────────

export async function fetchMyParcels(): Promise<MyParcelsResponse> {
  return api.get<MyParcelsResponse>('/services/parcels/my');
}

export async function fetchParcelProfile(parcelId: string): Promise<ParcelProfile> {
  return api.get<ParcelProfile>(`/services/parcels/${parcelId}/profile`);
}

export async function fetchServiceCatalog(): Promise<CatalogServiceItem[]> {
  return api.get<CatalogServiceItem[]>('/services/catalog');
}

export async function submitApplication(data: ApplicationSubmission): Promise<{ application_id: string; status: string; tracking_number: string }> {
  return api.post<{ application_id: string; status: string; tracking_number: string }>('/services/applications', data);
}

export async function fetchMyApplications(): Promise<ApplicationRecord[]> {
  return api.get<ApplicationRecord[]>('/services/applications/my');
}

export async function fetchApplicationById(appId: string): Promise<ApplicationRecord> {
  return api.get<ApplicationRecord>(`/services/applications/${appId}`);
}

export async function fetchMyParcelAccessLogs(parcelId?: string | null): Promise<ParcelAccessLogEntry[]> {
  const params = parcelId ? `?parcel_id=${encodeURIComponent(parcelId)}` : '';
  return api.get<ParcelAccessLogEntry[]>(`/audit/citizen/my-parcel-access${params}`);
}

export async function fetchUserNotifications(userId: string): Promise<NotificationItem[]> {
  return api.get<NotificationItem[]>(`/notifications/user/${userId}`);
}

export async function markNotificationAsRead(notificationId: string): Promise<void> {
  return api.put<void>(`/notifications/${notificationId}/read`);
}

export async function searchParcelsCitizen(query: Record<string, any>): Promise<any> {
  return api.post<any>('/search/parcels', query);
}

export async function getSearchSuggestions(query: string): Promise<string[]> {
  return api.get<string[]>(`/search/suggestions?q=${encodeURIComponent(query)}`);
}

export async function searchNaturalLanguage(query: string): Promise<any> {
  return api.post<any>('/search/natural-language', { query });
}