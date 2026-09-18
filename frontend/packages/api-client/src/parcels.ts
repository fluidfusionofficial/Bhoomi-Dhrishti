import { apiRequest } from './client';
import type {
  Parcel,
  ParcelSearchRequest,
  ParcelSearchResponse,
} from '@bhoomi/types';

export async function fetchParcel(ulpin: string): Promise<Parcel> {
  return apiRequest<Parcel>(`/parcels/${ulpin}`);
}

export async function searchParcels(
  params: ParcelSearchRequest
): Promise<ParcelSearchResponse> {
  const queryParams = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      queryParams.append(key, String(value));
    }
  });

  return apiRequest<ParcelSearchResponse>(`/parcels/search?${queryParams}`);
}

export async function resolveByCoordinates(
  lat: number,
  lon: number
): Promise<Parcel | null> {
  return apiRequest<Parcel | null>(`/parcels/resolve?lat=${lat}&lon=${lon}`);
}

export interface LineageEntry {
  timestamp: string;
  operation: string;
  ulpin: string;
  area: number;
  surveyNumber: string;
  source: string;
  trustScore: number;
}

export async function getLineage(ulpin: string): Promise<LineageEntry[]> {
  return apiRequest<LineageEntry[]>(`/parcels/${ulpin}/lineage`);
}

export interface Conflict {
  id: string;
  ulpin: string;
  type: 'OWNERSHIP' | 'BOUNDARY' | 'AREA' | 'ATTRIBUTE';
  severity: 'HIGH' | 'MEDIUM' | 'LOW';
  sourceA: {
    system: string;
    value: string;
    confidence: number;
  };
  sourceB: {
    system: string;
    value: string;
    confidence: number;
  };
  detectedAt: string;
  status: 'PENDING' | 'UNDER_REVIEW' | 'RESOLVED';
  evidence?: {
    areaDiffPercent?: number;
    nameSimilarity?: number;
    iou?: number;
  };
}

export async function getConflicts(ulpin: string): Promise<Conflict[]> {
  return apiRequest<Conflict[]>(`/parcels/${ulpin}/conflicts`);
}

export interface ParcelRight {
  id: string;
  type: 'OWNERSHIP' | 'LEASE' | 'MORTGAGE' | 'EASEMENT';
  holderName: string;
  share?: string;
  validFrom: string;
  validUntil?: string;
  source: string;
  department: string;
  asOfDate: string;
}

export async function getParcelRights(ulpin: string): Promise<ParcelRight[]> {
  return apiRequest<ParcelRight[]>(`/parcels/${ulpin}/rights`);
}

export interface Transaction {
  id: string;
  date: string;
  type: 'SALE' | 'GIFT' | 'INHERITANCE' | 'PARTITION' | 'MORTGAGE';
  fromParty: string;
  toParty: string;
  consideration?: number;
  registrationNumber: string;
  source: string;
}

export async function getTransactions(ulpin: string): Promise<Transaction[]> {
  return apiRequest<Transaction[]>(`/parcels/${ulpin}/transactions`);
}

export interface Encumbrance {
  id: string;
  type: 'MORTGAGE' | 'LIEN' | 'CHARGE' | 'CAVEAT';
  description: string;
  amount?: number;
  holder: string;
  registeredDate: string;
  status: 'ACTIVE' | 'DISCHARGED';
}

export async function getEncumbrances(ulpin: string): Promise<Encumbrance[]> {
  return apiRequest<Encumbrance[]>(`/parcels/${ulpin}/encumbrances`);
}
