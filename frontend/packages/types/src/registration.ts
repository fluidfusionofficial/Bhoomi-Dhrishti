// Deed, Encumbrance types

import type { ProvenanceInfo } from './parcel';
import type { Party } from './revenue';

export type DeedType =
  | 'SALE_DEED'
  | 'GIFT_DEED'
  | 'PARTITION_DEED'
  | 'WILL'
  | 'POWER_OF_ATTORNEY'
  | 'MORTGAGE_DEED'
  | 'RELEASE_DEED'
  | 'SETTLEMENT_DEED'
  | 'EXCHANGE_DEED';

export interface Deed {
  id: string;
  documentNumber: string;
  deedType: DeedType;
  executionDate: string;
  registrationDate: string;
  sroCode: string;         // Sub-Registrar Office code
  sroName: string;
  bookNumber: string;
  volume: string;
  pageFrom: number;
  pageTo: number;
  sellers: Party[];
  buyers: Party[];
  consideration: number;   // in INR
  stampDuty: number;
  ulpins: string[];        // parcels this deed covers
  remarks?: string;
  documentUrl?: string;    // redacted/blurred for citizen
  provenance: ProvenanceInfo;
}

export type EncumbranceType =
  | 'MORTGAGE'
  | 'CHARGE'
  | 'LIEN'
  | 'ATTACHMENT'
  | 'RESTRICTION'
  | 'EASEMENT'
  | 'LEASE';

export interface Encumbrance {
  id: string;
  encumbranceType: EncumbranceType;
  ulpin: string;
  claimant: Party;
  amount?: number;
  fromDate: string;
  toDate?: string;
  isActive: boolean;
  documentReference?: string;
  remarks?: string;
  provenance: ProvenanceInfo;
}
