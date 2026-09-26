// Parcel, Geometry, LGD Admin types

export type DataFreshness = 'LIVE' | 'CACHED' | 'SYNTHETIC' | 'DEMO';

export interface ProvenanceInfo {
  department: string;
  state: string;
  asOfDate: string; // ISO date string
  freshness: DataFreshness;
  lastSynced: string; // ISO datetime string
}

export interface LGDAdminBoundary {
  stateCode: string;
  stateName: string;
  districtCode: string;
  districtName: string;
  subDistrictCode?: string;
  subDistrictName?: string;
  villageCode?: string;
  villageName?: string;
}

export type GeometryType =
  | 'Point'
  | 'MultiPoint'
  | 'LineString'
  | 'MultiLineString'
  | 'Polygon'
  | 'MultiPolygon';

export interface Geometry {
  type: GeometryType;
  coordinates: number[] | number[][] | number[][][] | number[][][][];
  crs?: string; // e.g. "EPSG:4326"
}

export interface GeoJSONFeature {
  type: 'Feature';
  geometry: Geometry;
  properties: Record<string, unknown>;
}

export type LandUseCategory =
  | 'AGRICULTURAL'
  | 'RESIDENTIAL'
  | 'COMMERCIAL'
  | 'INDUSTRIAL'
  | 'GREEN_OPEN'
  | 'GOVERNMENT'
  | 'MIXED_USE'
  | 'WATER_BODY'
  | 'FOREST'
  | 'PORAMBOKE'
  | 'ROAD'
  | 'RAILWAY'
  | 'UNOCCUPIED'
  | 'UNKNOWN';

export type TenureType =
  | 'FREEHOLD'
  | 'LEASEHOLD'
  | 'GOVERNMENT'
  | 'COMMUNAL'
  | 'DISPUTED';

export interface Parcel {
  ulpin: string;          // Unique Land Parcel Identification Number
  bdpr: string;           // Bhoomi Dhrishti Parcel Reference
  surveyNumber: string;
  subDivisionNumber?: string;
  address: string;
  lgd: LGDAdminBoundary;
  area: number;           // in square meters
  areaHectares: number;
  landUse: LandUseCategory;
  tenure: TenureType;
  geometry?: Geometry;
  lastSynced: string;     // ISO datetime
  provenance: ProvenanceInfo;
  hasConflicts: boolean;
  conflictCount: number;
  trustScore: number;     // 0-100
  riskBand: 'HIGH' | 'MEDIUM' | 'LOW';
}

export interface ParcelSearchResult {
  ulpin: string;
  bdpr: string;
  address: string;
  surveyNumber: string;
  area: number;
  landUse: LandUseCategory;
  riskBand: 'HIGH' | 'MEDIUM' | 'LOW';
  hasConflicts: boolean;
}

export interface ParcelSearchRequest {
  query: string;
  state?: string;
  district?: string;
  landUse?: LandUseCategory;
  page?: number;
  pageSize?: number;
}

export interface ParcelSearchResponse {
  results: ParcelSearchResult[];
  total: number;
  page: number;
  pageSize: number;
}
