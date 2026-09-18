// ConflictScore, EntityLink, NetworkFlag types

import type { ProvenanceInfo } from './parcel';

export type RiskBand = 'HIGH' | 'MEDIUM' | 'LOW';
export type ConflictType =
  | 'OWNER_MISMATCH'
  | 'AREA_DISCREPANCY'
  | 'BOUNDARY_OVERLAP'
  | 'ENCUMBRANCE_INCONSISTENCY'
  | 'CHAIN_OF_TITLE_BREAK'
  | 'PHANTOM_OWNER'
  | 'SUSPICIOUS_TRANSFER_VELOCITY'
  | 'SUSPICIOUS_PRICE_DEVIATION'
  | 'DUPLICATE_REGISTRATION'
  | 'MISSING_MUTATION';

export type ConflictStatus =
  | 'DETECTED'
  | 'UNDER_REVIEW'
  | 'RESOLVED'
  | 'DEFERRED'
  | 'FALSE_POSITIVE';

export interface ConflictRecord {
  id: string;
  ulpin: string;
  conflictType: ConflictType;
  status: ConflictStatus;
  anomalyScore: number;   // 0.0 - 1.0
  riskBand: RiskBand;
  detectedAt: string;
  resolvedAt?: string;
  departmentsInvolved: string[];
  registryA: {
    department: string;
    value: string;
    asOf: string;
  };
  registryB: {
    department: string;
    value: string;
    asOf: string;
  };
  aiReason: string;
  detectorVersion: string;
  reviewedBy?: string;
  resolution?: string;
  provenance: ProvenanceInfo;
}

export interface TrustScoreReason {
  code: string;
  description: string;
  impact: 'POSITIVE' | 'NEGATIVE' | 'NEUTRAL';
  weight: number;         // contribution to score
}

export interface TrustScore {
  ulpin: string;
  score: number;          // 0-100
  riskBand: RiskBand;
  computedAt: string;
  engineVersion: string;
  reasons: TrustScoreReason[];
  dataCompleteness: number; // 0-100
  crossDeptConsistency: number; // 0-100
}

export interface MLScore {
  ulpin: string;
  score: number;          // 0-100 (higher = riskier)
  riskBand: RiskBand;
  modelVersion: string;
  computedAt: string;
  featureImportance: {
    feature: string;
    importance: number;
    direction: 'UP' | 'DOWN';
  }[];
  topReason: string;
  disagreesWithTrust: boolean;
  trustScoreBand: RiskBand;
}

export interface EntityLink {
  id: string;
  entityAId: string;
  entityAName: string;
  entityBId: string;
  entityBName: string;
  linkType: 'SAME_PERSON' | 'RELATED_PARTY' | 'ALIAS' | 'CORPORATE_LINK';
  confidence: number;     // 0-1
  evidenceSources: string[];
}

export interface NetworkFlag {
  id: string;
  ulpin: string;
  flagType:
    | 'CIRCULAR_TRANSFER'
    | 'RAPID_RESALE'
    | 'CONNECTED_PARTIES'
    | 'PRICE_ANOMALY'
    | 'SHELL_ENTITY';
  severity: RiskBand;
  description: string;
  linkedParcels: string[];
  linkedParties: string[];
  detectedAt: string;
}
