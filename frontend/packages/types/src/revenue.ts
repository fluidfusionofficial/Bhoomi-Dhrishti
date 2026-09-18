// RoR, Rights, Party, Mutation types

import type { ProvenanceInfo } from './parcel';

export type PartyType = 'INDIVIDUAL' | 'COMPANY' | 'GOVERNMENT' | 'TRUST' | 'HUF';
export type RightType =
  | 'OWNERSHIP'
  | 'CO_OWNERSHIP'
  | 'MORTGAGE_HOLDER'
  | 'LESSEE'
  | 'EASEMENT'
  | 'USUFRUCT';

export interface Party {
  id: string;
  name: string;
  maskedName?: string;   // For citizen-facing display
  partyType: PartyType;
  aadhaarHash?: string;  // Hashed, never plain
  panHash?: string;
  address?: string;
  provenance: ProvenanceInfo;
}

export interface Right {
  id: string;
  rightType: RightType;
  shareNumerator: number;
  shareDenominator: number;
  sharePercent: number;
  party: Party;
  fromDate: string;
  toDate?: string;         // null if current
  isCurrent: boolean;
  provenance: ProvenanceInfo;
}

export interface RecordOfRights {
  id: string;
  ulpin: string;
  khataNumber: string;
  rights: Right[];
  encumbrances: string[];  // IDs
  remarks?: string;
  provenance: ProvenanceInfo;
  version: number;
  effectiveDate: string;
}

export type MutationStatus =
  | 'PENDING'
  | 'UNDER_REVIEW'
  | 'APPROVED'
  | 'REJECTED'
  | 'APPEAL_PENDING'
  | 'COMPLETED';

export type MutationType =
  | 'SALE'
  | 'INHERITANCE'
  | 'GIFT'
  | 'PARTITION'
  | 'COURT_ORDER'
  | 'GOVERNMENT_ACQUISITION'
  | 'EXCHANGE'
  | 'MORTGAGE_TRANSFER';

export interface Mutation {
  id: string;
  mutationNumber: string;
  ulpin: string;
  mutationType: MutationType;
  status: MutationStatus;
  applicationDate: string;
  decisionDate?: string;
  fromParties: Party[];
  toParties: Party[];
  deedReference?: string;
  remarks?: string;
  officerName?: string;
  officerDesignation?: string;
  provenance: ProvenanceInfo;
}
