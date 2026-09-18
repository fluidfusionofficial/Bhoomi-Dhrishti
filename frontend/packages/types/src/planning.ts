// Zone, BuildingPermission, Dispute types

import type { ProvenanceInfo } from './parcel';

export type ZoneType =
  | 'RESIDENTIAL_LOW_DENSITY'
  | 'RESIDENTIAL_HIGH_DENSITY'
  | 'COMMERCIAL_LOCAL'
  | 'COMMERCIAL_GENERAL'
  | 'INDUSTRIAL_LIGHT'
  | 'INDUSTRIAL_HEAVY'
  | 'MIXED_USE'
  | 'AGRICULTURAL_PROTECTED'
  | 'GREEN_BELT'
  | 'SPECIAL_ECONOMIC_ZONE'
  | 'HERITAGE_ZONE'
  | 'COASTAL_REGULATION'
  | 'FOREST_AREA';

export interface Zone {
  id: string;
  ulpin: string;
  zoneType: ZoneType;
  zoneCode: string;
  masterPlanYear: number;
  permittedFSI: number;     // Floor Space Index
  maxHeight: number;        // meters
  setbacks: {
    front: number;
    rear: number;
    side: number;
  };
  restrictionNotes?: string;
  provenance: ProvenanceInfo;
}

export type PermitStatus =
  | 'APPLIED'
  | 'UNDER_SCRUTINY'
  | 'APPROVED'
  | 'REJECTED'
  | 'REVOKED'
  | 'EXPIRED'
  | 'COMPLETED';

export interface BuildingPermission {
  id: string;
  permitNumber: string;
  ulpin: string;
  applicant: string;
  status: PermitStatus;
  applicationDate: string;
  approvalDate?: string;
  expiryDate?: string;
  builtUpArea: number;
  floors: number;
  permittedUse: string;
  remarks?: string;
  provenance: ProvenanceInfo;
}

export type DisputeStatus =
  | 'OPEN'
  | 'IN_COURT'
  | 'APPEAL'
  | 'RESOLVED'
  | 'DISMISSED';

export type DisputeType =
  | 'BOUNDARY_DISPUTE'
  | 'OWNERSHIP_DISPUTE'
  | 'ENCROACHMENT'
  | 'ADVERSE_POSSESSION'
  | 'PARTITION_DISPUTE'
  | 'REVENUE_DISPUTE';

export interface Dispute {
  id: string;
  ulpin: string;
  disputeType: DisputeType;
  status: DisputeStatus;
  courtName?: string;
  caseNumber?: string;
  filingDate: string;
  lastHearingDate?: string;
  nextHearingDate?: string;
  parties: string[];
  summary: string;
  provenance: ProvenanceInfo;
}
