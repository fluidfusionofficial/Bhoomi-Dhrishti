'use client';

import * as React from 'react';

// ── Types ──────────────────────────────────────────────────────────────────────

export interface ParcelData {
  parcel_id: string;
  ulpin: string;
  survey_number: string;
  area: number;
  land_use: string;
  owner: string;
  status: string;
  status_detail: string;
  risk_level: string;
  anomaly_score: number;
  district: string;
  taluk: string;
  village: string;
}

export interface LayerState {
  // Tier 1: Base Spatial
  parcels: boolean;
  ulpin: boolean;
  villageBoundary: boolean;
  // Tier 2: Essential Governance
  ownership: boolean;
  landUse: boolean;
  zoning: boolean;
  registration: boolean;
  encumbrance: boolean;
  litigation: boolean;
  topologyConflicts: boolean;
  // Tier 3: Use-Case & Utility
  propertyTax: boolean;
  utilityLines: boolean;
  infrastructureRoW: boolean;
  envBuffers: boolean;
  extruded?: boolean;
}

export interface CadastralMapProps {
  layers: LayerState;
  statusFilter: string;
  riskFilter: string;
  selectedParcelId: string | null;
  onParcelSelect: (parcel: ParcelData) => void;
  /** Render as a 3-D globe (MapLibre GL globe projection). Default: false (flat 2-D). */
  globe?: boolean;
  /** Called when the map reference is ready — lets parent trigger flyTo etc. */
  onMapReady?: (map: any) => void;
}

// ── Parcel GeoJSON (15 real Chengalpattu parcels from HTML prototype) ──────────

// Realistic irregular cadastral polygons — diagonal boundaries, varying vertex counts,
// sizes proportional to land use (agricultural >> residential >> commercial).
// Positioned in the Tirupporur village area, Chengalpattu district, Tamil Nadu.
const PARCEL_GEOJSON = {
  type: 'FeatureCollection',
  features: [
    // ── Northern belt (lat ~12.731–12.734) ──────────────────────────────────
    { type: 'Feature', properties: { parcel_id: 'P001', ulpin: 'TN-CHN-000001', survey_number: '41/1A', area: 3.1, land_use: 'Agricultural', owner: 'Lakshmi Narayanan', status: 'Verified', status_detail: 'Verified', risk_level: 'Low', anomaly_score: 0.12, district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Demo Village' },
      geometry: { type: 'Polygon', coordinates: [[[80.1806,12.7322],[80.1838,12.7331],[80.1851,12.7318],[80.1843,12.7302],[80.1818,12.7294],[80.1798,12.7306],[80.1806,12.7322]]] } },

    { type: 'Feature', properties: { parcel_id: 'P002', ulpin: 'TN-CHN-000002', survey_number: '41/2B', area: 1.85, land_use: 'Residential', owner: 'Meena Rajendran', status: 'Verified', status_detail: 'Verified', risk_level: 'Low', anomaly_score: 0.08, district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Demo Village' },
      geometry: { type: 'Polygon', coordinates: [[[80.1853,12.7320],[80.1866,12.7325],[80.1876,12.7315],[80.1870,12.7300],[80.1853,12.7296],[80.1843,12.7302],[80.1853,12.7320]]] } },

    { type: 'Feature', properties: { parcel_id: 'P003', ulpin: 'TN-CHN-000003', survey_number: '42/3B', area: 2.4, land_use: 'Residential', owner: 'Arun Kumar', status: 'Conflict', status_detail: 'Ownership Conflict', risk_level: 'High', anomaly_score: 0.91, district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Demo Village' },
      geometry: { type: 'Polygon', coordinates: [[[80.1876,12.7323],[80.1896,12.7330],[80.1910,12.7317],[80.1904,12.7298],[80.1882,12.7290],[80.1870,12.7300],[80.1876,12.7323]]] } },

    { type: 'Feature', properties: { parcel_id: 'P004', ulpin: 'TN-CHN-000004', survey_number: '42/4A', area: 4.2, land_use: 'Agricultural', owner: 'Suresh Babu', status: 'Warning', status_detail: 'Encumbrance Warning', risk_level: 'Medium', anomaly_score: 0.52, district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Demo Village' },
      geometry: { type: 'Polygon', coordinates: [[[80.1910,12.7317],[80.1928,12.7328],[80.1944,12.7322],[80.1946,12.7304],[80.1928,12.7291],[80.1908,12.7290],[80.1904,12.7298],[80.1910,12.7317]]] } },

    { type: 'Feature', properties: { parcel_id: 'P005', ulpin: 'TN-CHN-000005', survey_number: '43/1C', area: 0.95, land_use: 'Commercial', owner: 'Priya Venkatesh', status: 'Warning', status_detail: 'Tax Warning', risk_level: 'Medium', anomaly_score: 0.48, district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Demo Village' },
      geometry: { type: 'Polygon', coordinates: [[[80.1946,12.7318],[80.1960,12.7324],[80.1970,12.7312],[80.1966,12.7297],[80.1948,12.7291],[80.1946,12.7304],[80.1946,12.7318]]] } },

    // ── Middle belt (lat ~12.728–12.731) ─────────────────────────────────────
    { type: 'Feature', properties: { parcel_id: 'P006', ulpin: 'TN-CHN-000006', survey_number: '43/2A', area: 2.75, land_use: 'Mixed', owner: 'Karthik Selvam', status: 'Conflict', status_detail: 'Planning Conflict', risk_level: 'High', anomaly_score: 0.87, district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Demo Village' },
      geometry: { type: 'Polygon', coordinates: [[[80.1798,12.7306],[80.1818,12.7294],[80.1826,12.7279],[80.1814,12.7264],[80.1793,12.7260],[80.1782,12.7273],[80.1790,12.7292],[80.1798,12.7306]]] } },

    { type: 'Feature', properties: { parcel_id: 'P007', ulpin: 'TN-CHN-000007', survey_number: '44/1B', area: 1.4, land_use: 'Residential', owner: 'Divya Anand', status: 'Warning', status_detail: 'Building Permission Warning', risk_level: 'Medium', anomaly_score: 0.55, district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Demo Village' },
      geometry: { type: 'Polygon', coordinates: [[[80.1843,12.7302],[80.1853,12.7296],[80.1859,12.7280],[80.1846,12.7266],[80.1830,12.7268],[80.1826,12.7279],[80.1843,12.7302]]] } },

    { type: 'Feature', properties: { parcel_id: 'P008', ulpin: 'TN-CHN-000008', survey_number: '45/2A', area: 3.6, land_use: 'Agricultural', owner: 'Arun Raj', status: 'Verified', status_detail: 'Verified', risk_level: 'Low', anomaly_score: 0.15, district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Demo Village' },
      geometry: { type: 'Polygon', coordinates: [[[80.1870,12.7300],[80.1882,12.7290],[80.1892,12.7275],[80.1882,12.7258],[80.1860,12.7253],[80.1846,12.7260],[80.1846,12.7266],[80.1859,12.7280],[80.1870,12.7300]]] } },

    { type: 'Feature', properties: { parcel_id: 'P009', ulpin: 'TN-CHN-000009', survey_number: '45/3B', area: 2.1, land_use: 'Residential', owner: 'Ganesh Moorthy', status: 'Warning', status_detail: 'Area Discrepancy', risk_level: 'Medium', anomaly_score: 0.61, district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Demo Village' },
      geometry: { type: 'Polygon', coordinates: [[[80.1904,12.7298],[80.1920,12.7290],[80.1930,12.7276],[80.1918,12.7260],[80.1898,12.7254],[80.1882,12.7258],[80.1892,12.7275],[80.1904,12.7298]]] } },

    { type: 'Feature', properties: { parcel_id: 'P010', ulpin: 'TN-CHN-000010', survey_number: '46/1A', area: 1.2, land_use: 'Commercial', owner: 'Ravi Chandran', status: 'Pending', status_detail: 'Pending Transaction', risk_level: 'Medium', anomaly_score: 0.44, district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Demo Village' },
      geometry: { type: 'Polygon', coordinates: [[[80.1946,12.7304],[80.1948,12.7291],[80.1964,12.7282],[80.1966,12.7265],[80.1946,12.7258],[80.1930,12.7264],[80.1930,12.7276],[80.1946,12.7304]]] } },

    // ── Southern belt (lat ~12.724–12.728) ───────────────────────────────────
    { type: 'Feature', properties: { parcel_id: 'P011', ulpin: 'TN-CHN-000011', survey_number: '46/2C', area: 5.3, land_use: 'Agricultural', owner: 'Saravanan Pillai', status: 'Verified', status_detail: 'Verified', risk_level: 'Low', anomaly_score: 0.10, district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Demo Village' },
      geometry: { type: 'Polygon', coordinates: [[[80.1782,12.7273],[80.1793,12.7260],[80.1814,12.7264],[80.1830,12.7268],[80.1828,12.7248],[80.1808,12.7236],[80.1784,12.7232],[80.1768,12.7248],[80.1782,12.7273]]] } },

    { type: 'Feature', properties: { parcel_id: 'P012', ulpin: 'TN-CHN-000012', survey_number: '47/1B', area: 0.8, land_use: 'Industrial', owner: 'Nithya Sundaram', status: 'Conflict', status_detail: 'High Risk Transaction', risk_level: 'High', anomaly_score: 0.93, district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Demo Village' },
      geometry: { type: 'Polygon', coordinates: [[[80.1830,12.7268],[80.1846,12.7266],[80.1860,12.7253],[80.1854,12.7238],[80.1836,12.7232],[80.1820,12.7238],[80.1820,12.7252],[80.1830,12.7268]]] } },

    { type: 'Feature', properties: { parcel_id: 'P013', ulpin: 'TN-CHN-000013', survey_number: '47/3A', area: 2.95, land_use: 'Residential', owner: 'Bala Subramani', status: 'Verified', status_detail: 'Verified', risk_level: 'Low', anomaly_score: 0.18, district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Demo Village' },
      geometry: { type: 'Polygon', coordinates: [[[80.1860,12.7253],[80.1882,12.7258],[80.1894,12.7244],[80.1888,12.7230],[80.1866,12.7224],[80.1846,12.7230],[80.1854,12.7238],[80.1860,12.7253]]] } },

    { type: 'Feature', properties: { parcel_id: 'P014', ulpin: 'TN-CHN-000014', survey_number: '48/1A', area: 3.85, land_use: 'Mixed', owner: 'Kavya Raman', status: 'Warning', status_detail: 'Planning Warning', risk_level: 'Medium', anomaly_score: 0.58, district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Demo Village' },
      geometry: { type: 'Polygon', coordinates: [[[80.1898,12.7254],[80.1918,12.7260],[80.1936,12.7252],[80.1940,12.7234],[80.1920,12.7224],[80.1898,12.7226],[80.1888,12.7238],[80.1898,12.7254]]] } },

    { type: 'Feature', properties: { parcel_id: 'P015', ulpin: 'TN-CHN-000015', survey_number: '48/2B', area: 1.65, land_use: 'Water Body', owner: 'Village Commons', status: 'Verified', status_detail: 'Verified', risk_level: 'Low', anomaly_score: 0.05, district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Demo Village' },
      geometry: { type: 'Polygon', coordinates: [[[80.1946,12.7258],[80.1966,12.7265],[80.1978,12.7254],[80.1976,12.7238],[80.1958,12.7228],[80.1940,12.7230],[80.1940,12.7234],[80.1946,12.7258]]] } },
  ],
} as const;

export const PARCEL_DATA: ParcelData[] = PARCEL_GEOJSON.features.map(
  (f) => f.properties as unknown as ParcelData
);

// ── Conflict overlay geometry (overlap zone between P003 & P008) ───────────────

// Small overlap zone between P003 (Conflict) and P008 (Verified) — shows topology conflict
const CONFLICT_GEOJSON = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: {},
      geometry: {
        type: 'Polygon',
        coordinates: [[[80.1876, 12.7302],[80.1886, 12.7300],[80.1884, 12.7292],[80.1874, 12.7294],[80.1876, 12.7302]]],
      },
    },
  ],
};

// ── Tier 2: Governance overlay GeoJSON ────────────────────────────────────────

// Registration deed markers — centroids of parcels with registered deeds
const REGISTRATION_GEOJSON = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { parcel_id: 'P001', deed_no: '1042/2019', deed_type: 'SALE_DEED', sro: 'SRO Chengalpattu', status: 'VERIFIED' }, geometry: { type: 'Point', coordinates: [80.1825, 12.7312] } },
    { type: 'Feature', properties: { parcel_id: 'P002', deed_no: '0221/2021', deed_type: 'SALE_DEED', sro: 'SRO Chengalpattu', status: 'VERIFIED' }, geometry: { type: 'Point', coordinates: [80.1858, 12.7311] } },
    { type: 'Feature', properties: { parcel_id: 'P004', deed_no: '0891/2021', deed_type: 'MORTGAGE_DEED', sro: 'SRO Tirupporur', status: 'ENCUMBERED' }, geometry: { type: 'Point', coordinates: [80.1928, 12.7308] } },
    { type: 'Feature', properties: { parcel_id: 'P008', deed_no: '1204/2018', deed_type: 'SALE_DEED', sro: 'SRO Chengalpattu', status: 'VERIFIED' }, geometry: { type: 'Point', coordinates: [80.1868, 12.7277] } },
    { type: 'Feature', properties: { parcel_id: 'P013', deed_no: '0562/2022', deed_type: 'GIFT_DEED', sro: 'SRO Chengalpattu', status: 'VERIFIED' }, geometry: { type: 'Point', coordinates: [80.1869, 12.7238] } },
  ],
};

// Encumbrance certificate zone outlines — parcels with active mortgages/liens
const ENCUMBRANCE_GEOJSON = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { parcel_id: 'P004', ec_type: 'MORTGAGE', lender: 'SBI Chengalpattu', amount: 1500000, period: '2021–2031' },
      geometry: { type: 'Polygon', coordinates: [[[80.1908,12.7320],[80.1946,12.7325],[80.1948,12.7303],[80.1908,12.7298],[80.1908,12.7320]]] } },
    { type: 'Feature', properties: { parcel_id: 'P007', ec_type: 'LIEN', lender: 'Canara Bank', amount: 800000, period: '2020–2030' },
      geometry: { type: 'Polygon', coordinates: [[[80.1836,12.7296],[80.1860,12.7282],[80.1855,12.7268],[80.1832,12.7272],[80.1836,12.7296]]] } },
  ],
};

// Court litigation / stay order zones
const LITIGATION_GEOJSON = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { parcel_id: 'P003', case_no: 'OS-421/2024', court: 'Chengalpattu District Court', type: 'OWNERSHIP_DISPUTE', status: 'STAY_GRANTED' },
      geometry: { type: 'Polygon', coordinates: [[[80.1876,12.7328],[80.1910,12.7332],[80.1912,12.7295],[80.1876,12.7292],[80.1876,12.7328]]] } },
    { type: 'Feature', properties: { parcel_id: 'P012', case_no: 'OS-188/2023', court: 'Chengalpattu District Court', type: 'TITLE_DISPUTE', status: 'PENDING' },
      geometry: { type: 'Polygon', coordinates: [[[80.1828,12.7270],[80.1862,12.7255],[80.1857,12.7232],[80.1823,12.7238],[80.1828,12.7270]]] } },
  ],
};

// Zoning master plan polygons (residential / agricultural / commercial bands)
const ZONING_GEOJSON = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { zone: 'Residential', plan: 'Tirupporur Master Plan 2041' },
      geometry: { type: 'Polygon', coordinates: [[[80.1840,12.7335],[80.1980,12.7335],[80.1980,12.7305],[80.1840,12.7305],[80.1840,12.7335]]] } },
    { type: 'Feature', properties: { zone: 'Agricultural', plan: 'Tirupporur Master Plan 2041' },
      geometry: { type: 'Polygon', coordinates: [[[80.1770,12.7310],[80.1840,12.7310],[80.1840,12.7225],[80.1770,12.7225],[80.1770,12.7310]]] } },
    { type: 'Feature', properties: { zone: 'Commercial', plan: 'Tirupporur Master Plan 2041' },
      geometry: { type: 'Polygon', coordinates: [[[80.1940,12.7305],[80.1990,12.7305],[80.1990,12.7255],[80.1940,12.7255],[80.1940,12.7305]]] } },
  ],
};

// ── Tier 3: Use-Case & Utility overlay GeoJSON ─────────────────────────────────

// Utility lines — water main, electricity, gas (simplified line segments through village)
const UTILITY_GEOJSON = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { type: 'WATER_MAIN', operator: 'TWAD Board', diameter_mm: 200 },
      geometry: { type: 'LineString', coordinates: [[80.1780,12.7290],[80.1830,12.7285],[80.1880,12.7280],[80.1940,12.7275],[80.1980,12.7268]] } },
    { type: 'Feature', properties: { type: 'ELECTRICITY', operator: 'TANGEDCO', voltage_kv: 11 },
      geometry: { type: 'LineString', coordinates: [[80.1795,12.7330],[80.1840,12.7310],[80.1880,12.7295],[80.1930,12.7285],[80.1970,12.7280]] } },
    { type: 'Feature', properties: { type: 'GAS_PIPELINE', operator: 'GAIL', pressure: 'medium' },
      geometry: { type: 'LineString', coordinates: [[80.1780,12.7245],[80.1840,12.7248],[80.1900,12.7250],[80.1960,12.7248]] } },
  ],
};

// Infrastructure Right-of-Way (RoW) corridors
const ROW_GEOJSON = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { type: 'STATE_HIGHWAY', road_no: 'SH-114', row_width_m: 30 },
      geometry: { type: 'Polygon', coordinates: [[[80.1780,12.7302],[80.1980,12.7302],[80.1980,12.7290],[80.1780,12.7290],[80.1780,12.7302]]] } },
    { type: 'Feature', properties: { type: 'PANCHAYAT_ROAD', row_width_m: 7 },
      geometry: { type: 'Polygon', coordinates: [[[80.1870,12.7335],[80.1874,12.7335],[80.1874,12.7225],[80.1870,12.7225],[80.1870,12.7335]]] } },
  ],
};

// Environmental buffers — waterbody, coastal regulation zone, forest reserve
const ENV_BUFFER_GEOJSON = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { type: 'WATERBODY_BUFFER', body: 'Palar River Tributary', buffer_m: 100, regulation: 'CRZ-III' },
      geometry: { type: 'Polygon', coordinates: [[[80.1946,12.7260],[80.1978,12.7268],[80.1985,12.7230],[80.1955,12.7225],[80.1938,12.7228],[80.1946,12.7260]]] } },
    { type: 'Feature', properties: { type: 'FOREST_BUFFER', body: 'Reserve Forest Block 42', buffer_m: 50, regulation: 'Forest Act 1980' },
      geometry: { type: 'Polygon', coordinates: [[[80.1768,12.7260],[80.1795,12.7265],[80.1798,12.7230],[80.1770,12.7225],[80.1768,12.7260]]] } },
  ],
};

// ── MapLibre expression helpers ────────────────────────────────────────────────

function statusColorExpr() {
  return [
    'match', ['get', 'status'],
    'Verified', '#16a34a',
    'Conflict', '#dc2626',
    'Warning',  '#d97706',
    'Pending',  '#2456a6',
    '#9aa4b3',
  ];
}

// Bright border colors for satellite imagery contrast (more saturated than fill)
function satBorderColorExpr() {
  return [
    'match', ['get', 'status'],
    'Verified', '#00ff88',   // bright lime-green
    'Conflict', '#ff4400',   // vivid orange-red
    'Warning',  '#ffa500',   // bright orange
    'Pending',  '#44aaff',   // bright blue
    '#ffffff',
  ];
}

function landUseColorExpr() {
  return [
    'match', ['get', 'land_use'],
    'Agricultural', '#65a30d',
    'Residential',  '#2563eb',
    'Commercial',   '#c026d3',
    'Industrial',   '#e11d48',
    'Mixed',        '#ea580c',
    'Water Body',   '#0891b2',
    '#9aa4b3',
  ];
}

function fillOpacityExpr(pid: string | null) {
  return ['case', ['==', ['get', 'parcel_id'], pid ?? '##NONE##'], 0.55, 0.2] as any;
}

function lineWidthExpr(pid: string | null) {
  return ['case', ['==', ['get', 'parcel_id'], pid ?? '##NONE##'], 3.5, 1.8] as any;
}

function buildFilterExpr(statusFilter: string, riskFilter: string): any[] | null {
  const conditions: any[] = ['all'];
  if (statusFilter !== 'all') {
    const m: Record<string, string> = { verified: 'Verified', conflict: 'Conflict', warning: 'Warning', pending: 'Pending' };
    conditions.push(['==', ['get', 'status'], m[statusFilter] ?? statusFilter]);
  }
  if (riskFilter !== 'all') {
    const m: Record<string, string> = { low: 'Low', medium: 'Medium', high: 'High' };
    conditions.push(['==', ['get', 'risk_level'], m[riskFilter] ?? riskFilter]);
  }
  return conditions.length > 1 ? conditions : null;
}

function safeSet(map: any, fn: () => void) {
  try { fn(); } catch (_) {}
}

function visStr(on: boolean | undefined): 'visible' | 'none' {
  return on ? 'visible' : 'none';
}

function applyLayerState(map: any, layers: LayerState, pid: string | null) {
  // Tier 1: Base Spatial
  safeSet(map, () => map.setLayoutProperty('parcels-fill', 'visibility', visStr(layers.parcels)));
  safeSet(map, () => map.setLayoutProperty('parcels-outline', 'visibility', visStr(layers.parcels)));
  safeSet(map, () => map.setLayoutProperty('parcels-labels', 'visibility', visStr(layers.ulpin)));
  safeSet(map, () => map.setLayoutProperty('village-boundary', 'visibility', visStr(layers.villageBoundary)));

  // Tier 2: Governance
  safeSet(map, () => map.setLayoutProperty('zoning-fill', 'visibility', visStr(layers.zoning)));
  safeSet(map, () => map.setLayoutProperty('zoning-outline', 'visibility', visStr(layers.zoning)));
  safeSet(map, () => map.setLayoutProperty('registration-points', 'visibility', visStr(layers.registration)));
  safeSet(map, () => map.setLayoutProperty('encumbrance-fill', 'visibility', visStr(layers.encumbrance)));
  safeSet(map, () => map.setLayoutProperty('encumbrance-outline', 'visibility', visStr(layers.encumbrance)));
  safeSet(map, () => map.setLayoutProperty('litigation-fill', 'visibility', visStr(layers.litigation)));
  safeSet(map, () => map.setLayoutProperty('litigation-outline', 'visibility', visStr(layers.litigation)));
  safeSet(map, () => map.setLayoutProperty('conflict-fill', 'visibility', visStr(layers.topologyConflicts)));
  safeSet(map, () => map.setLayoutProperty('conflict-outline', 'visibility', visStr(layers.topologyConflicts)));

  // Tier 3: Use-Case & Utility
  safeSet(map, () => map.setLayoutProperty('utility-lines', 'visibility', visStr(layers.utilityLines)));
  safeSet(map, () => map.setLayoutProperty('utility-labels', 'visibility', visStr(layers.utilityLines)));
  safeSet(map, () => map.setLayoutProperty('row-fill', 'visibility', visStr(layers.infrastructureRoW)));
  safeSet(map, () => map.setLayoutProperty('row-outline', 'visibility', visStr(layers.infrastructureRoW)));
  safeSet(map, () => map.setLayoutProperty('env-buffer-fill', 'visibility', visStr(layers.envBuffers)));
  safeSet(map, () => map.setLayoutProperty('env-buffer-outline', 'visibility', visStr(layers.envBuffers)));

  // 3D extrusion toggle
  safeSet(map, () => map.setLayoutProperty('parcels-extrusion', 'visibility', visStr(layers.extruded)));

  // Parcel coloring priority: landUse > zoning override > ownership status
  const colorExpr = layers.landUse
    ? landUseColorExpr()
    : layers.ownership
    ? statusColorExpr()
    : '#3b6fbf';

  safeSet(map, () => map.setPaintProperty('parcels-fill', 'fill-color', colorExpr));
  safeSet(map, () => map.setPaintProperty('parcels-fill', 'fill-opacity', fillOpacityExpr(pid)));
  safeSet(map, () => map.setPaintProperty('parcels-outline', 'line-color', satBorderColorExpr()));
  safeSet(map, () => map.setPaintProperty('parcels-outline', 'line-width', lineWidthExpr(pid)));
  safeSet(map, () => map.setPaintProperty('parcels-extrusion', 'fill-extrusion-color', colorExpr));
}

function applyFilters(map: any, statusFilter: string, riskFilter: string) {
  const f = buildFilterExpr(statusFilter, riskFilter);
  ['parcels-fill', 'parcels-outline', 'parcels-labels', 'parcels-extrusion'].forEach((id) => {
    safeSet(map, () => map.setFilter(id, f));
  });
}

// ── Component ──────────────────────────────────────────────────────────────────

export function CadastralMap({
  layers,
  statusFilter,
  riskFilter,
  selectedParcelId,
  onParcelSelect,
  globe = false,
  onMapReady,
}: CadastralMapProps) {
  const containerRef = React.useRef<HTMLDivElement>(null);
  const mapRef = React.useRef<any>(null);
  const loadedRef = React.useRef(false);
  const animFrameRef = React.useRef<number>(0);
  const [coordText, setCoordText] = React.useState<string>('');

  const onParcelSelectRef = React.useRef(onParcelSelect);
  React.useEffect(() => { onParcelSelectRef.current = onParcelSelect; }, [onParcelSelect]);
  const onMapReadyRef = React.useRef(onMapReady);
  React.useEffect(() => { onMapReadyRef.current = onMapReady; }, [onMapReady]);

  // ── Mount: create the map once ────────────────────────────────────────
  React.useEffect(() => {
    if (!containerRef.current) return;
    let destroyed = false;
    const flyTimers: Array<ReturnType<typeof setTimeout>> = [];

    import('maplibre-gl').then((mod) => {
      if (destroyed || !containerRef.current || mapRef.current) return;
      const maplibregl = mod.default;

      // Globe mode: start from space above India.
      // Flat mode: jump straight to the parcel area with oblique pitch.
      const initCenter: [number, number] = globe ? [78.9629, 20.5937] : [80.187375, 12.729005];
      const initZoom = globe ? 2.5 : 15;

      const baseStyle: any = {
        version: 8,
        glyphs: 'https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf',
        sources: {
          satellite: {
            type: 'raster',
            tiles: ['https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'],
            tileSize: 256,
            attribution: '© Esri, Maxar, Earthstar Geographics',
          },
        },
        layers: [{ id: 'satellite-bg', type: 'raster', source: 'satellite' }],
      };

      const map = new maplibregl.Map({
        container: containerRef.current,
        style: baseStyle,
        center: initCenter,
        zoom: initZoom,
        pitch: globe ? 0 : 60,
        attributionControl: false,
      });

      mapRef.current = map;
      if (onMapReadyRef.current) onMapReadyRef.current(map);

      // ── Professional GIS chrome ──────────────────────────────────────
      try {
        map.addControl(
          new maplibregl.ScaleControl({ maxWidth: 120, unit: 'metric' }),
          'bottom-right'
        );
        map.addControl(
          new maplibregl.NavigationControl({ showCompass: true, showZoom: true }),
          'top-right'
        );
      } catch (_) { /* controls unsupported — degrade gracefully */ }

      // ── Coordinate readout ───────────────────────────────────────────
      map.on('mousemove', (e: any) => {
        const { lng, lat } = e.lngLat;
        const latDir = lat >= 0 ? 'N' : 'S';
        const lngDir = lng >= 0 ? 'E' : 'W';
        setCoordText(
          `${Math.abs(lat).toFixed(4)}°${latDir}, ${Math.abs(lng).toFixed(4)}°${lngDir}`
        );
      });

      map.on('load', () => {
        if (destroyed) return;
        loadedRef.current = true;

        // ── Globe mode: spherical projection + cinematic multi-stage fly-in ──
        if (globe) {
          // setProjection must be called after load in MapLibre GL 4.x
          safeSet(map, () => (map as any).setProjection({ type: 'globe' }));

          // Deep-space atmosphere (space black + blue horizon + stars)
          safeSet(map, () => (map as any).setFog({
            color: 'rgba(180, 210, 240, 0.7)',
            'high-color': 'rgba(28, 70, 200, 0.92)',
            'horizon-blend': 0.025,
            'space-color': 'rgb(6, 6, 18)',
            'star-intensity': 0.75,
          }));

          // Stage 1 (0ms): Already at space view — zoom 2.5, center India
          // Stage 2 (2200ms): Fly to India
          flyTimers.push(setTimeout(() => {
            if (destroyed || !mapRef.current) return;
            map.flyTo({
              center: [78.9629, 20.5937],
              zoom: 5,
              duration: 2000,
              curve: 1.4,
              essential: true,
            });
          }, 2200));

          // Stage 3 (4500ms): Fly to Tamil Nadu
          flyTimers.push(setTimeout(() => {
            if (destroyed || !mapRef.current) return;
            map.flyTo({
              center: [80.0, 11.5],
              zoom: 8,
              pitch: 20,
              duration: 2000,
              curve: 1.3,
              essential: true,
            });
          }, 4500));

          // Stage 4 (6500ms): Fly to Chengalpattu district
          flyTimers.push(setTimeout(() => {
            if (destroyed || !mapRef.current) return;
            map.flyTo({
              center: [80.187, 12.729],
              zoom: 12,
              pitch: 45,
              duration: 1800,
              curve: 1.2,
              essential: true,
            });
          }, 6500));

          // Stage 5 (8000ms): Final zoom to parcel area
          flyTimers.push(setTimeout(() => {
            if (destroyed || !mapRef.current) return;
            map.flyTo({
              center: [80.187375, 12.729005],
              zoom: 15,
              pitch: 60,
              duration: 2000,
              curve: 1.1,
              essential: true,
            });
          }, 8000));
        }

        // ── 3D Terrain: raster-dem + hillshade ──────────────────────────
        try {
          map.addSource('terrain', {
            type: 'raster-dem',
            tiles: ['https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png'],
            encoding: 'terrarium',
            tileSize: 256,
          });

          // Hillshade — added BEFORE parcel layers for correct z-order
          map.addLayer({
            id: 'hillshade',
            type: 'hillshade',
            source: 'terrain',
            paint: { 'hillshade-exaggeration': 0.5 },
          });

          map.setTerrain({ source: 'terrain', exaggeration: 1.5 });
        } catch (_) { /* terrain unsupported — degrade gracefully */ }

        // ── Parcel source ──────────────────────────────────────────────
        map.addSource('parcels', { type: 'geojson', data: PARCEL_GEOJSON as any });

        // Fill — higher opacity so parcels read clearly on satellite
        map.addLayer({
          id: 'parcels-fill',
          type: 'fill',
          source: 'parcels',
          paint: {
            'fill-color': statusColorExpr() as any,
            'fill-opacity': 0.42,
          },
        });

        // ── 3D Parcel extrusion by risk score ──────────────────────────
        try {
          map.addLayer({
            id: 'parcels-extrusion',
            type: 'fill-extrusion',
            source: 'parcels',
            paint: {
              'fill-extrusion-color': statusColorExpr() as any,
              'fill-extrusion-height': [
                'match', ['get', 'risk_level'],
                'High', 180,
                'Medium', 100,
                'Low', 30,
                20,
              ] as any,
              'fill-extrusion-base': 0,
              'fill-extrusion-opacity': 0.75,
            },
          });
        } catch (_) { /* fill-extrusion unsupported — degrade gracefully */ }

        // Outline — bright, thick border for aerial contrast (like the Google Earth overlay)
        map.addLayer({
          id: 'parcels-outline',
          type: 'line',
          source: 'parcels',
          paint: {
            'line-color': satBorderColorExpr() as any,
            'line-width': 2.5,
          },
        });

        // Labels — white text + dark halo for readability on satellite imagery
        map.addLayer({
          id: 'parcels-labels',
          type: 'symbol',
          source: 'parcels',
          layout: {
            'text-field': ['get', 'parcel_id'],
            'text-size': 11,
            'text-font': ['Noto Sans Bold'],
            'text-anchor': 'center',
          } as any,
          paint: {
            'text-color': '#ffffff',
            'text-halo-color': '#000000',
            'text-halo-width': 1.5,
          },
        });

        // ── Conflict zone overlay ──────────────────────────────────────
        map.addSource('conflicts', { type: 'geojson', data: CONFLICT_GEOJSON as any });
        map.addLayer({
          id: 'conflict-fill',
          type: 'fill',
          source: 'conflicts',
          paint: { 'fill-color': '#dc2626', 'fill-opacity': 0.6 },
        });
        map.addLayer({
          id: 'conflict-outline',
          type: 'line',
          source: 'conflicts',
          paint: { 'line-color': '#dc2626', 'line-width': 2, 'line-dasharray': [4, 2] },
        });

        // ── Tier 1: Village boundary outline ──────────────────────────
        map.addSource('village-boundary-src', {
          type: 'geojson',
          data: {
            type: 'Feature',
            properties: { name: 'Tirupporur Village' },
            geometry: { type: 'Polygon', coordinates: [[[80.1760,12.7345],[80.1995,12.7345],[80.1995,12.7215],[80.1760,12.7215],[80.1760,12.7345]]] },
          } as any,
        });
        map.addLayer({
          id: 'village-boundary',
          type: 'line',
          source: 'village-boundary-src',
          layout: { visibility: 'none' },
          paint: { 'line-color': '#c9b48a', 'line-width': 2, 'line-dasharray': [6, 3] },
        });

        // ── Tier 2: Zoning master plan ─────────────────────────────────
        map.addSource('zoning', { type: 'geojson', data: ZONING_GEOJSON as any });
        map.addLayer({
          id: 'zoning-fill',
          type: 'fill',
          source: 'zoning',
          layout: { visibility: 'none' },
          paint: {
            'fill-color': ['match', ['get', 'zone'], 'Residential', '#2563eb', 'Agricultural', '#65a30d', 'Commercial', '#c026d3', '#9aa4b3'],
            'fill-opacity': 0.18,
          },
        });
        map.addLayer({
          id: 'zoning-outline',
          type: 'line',
          source: 'zoning',
          layout: { visibility: 'none' },
          paint: {
            'line-color': ['match', ['get', 'zone'], 'Residential', '#2563eb', 'Agricultural', '#65a30d', 'Commercial', '#c026d3', '#9aa4b3'],
            'line-width': 1.5,
            'line-dasharray': [3, 2],
          },
        });

        // ── Tier 2: Registration deeds ─────────────────────────────────
        map.addSource('registration', { type: 'geojson', data: REGISTRATION_GEOJSON as any });
        map.addLayer({
          id: 'registration-points',
          type: 'circle',
          source: 'registration',
          layout: { visibility: 'none' },
          paint: {
            'circle-radius': 7,
            'circle-color': ['match', ['get', 'status'], 'ENCUMBERED', '#d97706', '#7c3aed'],
            'circle-stroke-color': '#ffffff',
            'circle-stroke-width': 2,
            'circle-opacity': 0.9,
          },
        });

        // ── Tier 2: Encumbrance certificate zones ──────────────────────
        map.addSource('encumbrance', { type: 'geojson', data: ENCUMBRANCE_GEOJSON as any });
        map.addLayer({
          id: 'encumbrance-fill',
          type: 'fill',
          source: 'encumbrance',
          layout: { visibility: 'none' },
          paint: { 'fill-color': '#d97706', 'fill-opacity': 0.22 },
        });
        map.addLayer({
          id: 'encumbrance-outline',
          type: 'line',
          source: 'encumbrance',
          layout: { visibility: 'none' },
          paint: { 'line-color': '#d97706', 'line-width': 2, 'line-dasharray': [4, 2] },
        });

        // ── Tier 2: Court litigation / stay zones ──────────────────────
        map.addSource('litigation', { type: 'geojson', data: LITIGATION_GEOJSON as any });
        map.addLayer({
          id: 'litigation-fill',
          type: 'fill',
          source: 'litigation',
          layout: { visibility: 'none' },
          paint: { 'fill-color': '#7c3aed', 'fill-opacity': 0.25 },
        });
        map.addLayer({
          id: 'litigation-outline',
          type: 'line',
          source: 'litigation',
          layout: { visibility: 'none' },
          paint: { 'line-color': '#7c3aed', 'line-width': 2, 'line-dasharray': [3, 3] },
        });

        // ── Tier 3: Utility lines ──────────────────────────────────────
        map.addSource('utilities', { type: 'geojson', data: UTILITY_GEOJSON as any });
        map.addLayer({
          id: 'utility-lines',
          type: 'line',
          source: 'utilities',
          layout: { visibility: 'none' },
          paint: {
            'line-color': ['match', ['get', 'type'], 'WATER_MAIN', '#0891b2', 'ELECTRICITY', '#f59e0b', 'GAS_PIPELINE', '#f97316', '#6b7688'],
            'line-width': 2.5,
            'line-dasharray': ['match', ['get', 'type'], 'GAS_PIPELINE', ['literal', [6, 3]], ['literal', [1, 0]]] as any,
          },
        });
        map.addLayer({
          id: 'utility-labels',
          type: 'symbol',
          source: 'utilities',
          layout: {
            visibility: 'none',
            'symbol-placement': 'line',
            'text-field': ['get', 'type'],
            'text-size': 9,
            'text-font': ['Noto Sans Bold'],
          } as any,
          paint: { 'text-color': '#f59e0b', 'text-halo-color': '#000', 'text-halo-width': 1 },
        });

        // ── Tier 3: Infrastructure Right-of-Way ────────────────────────
        map.addSource('row', { type: 'geojson', data: ROW_GEOJSON as any });
        map.addLayer({
          id: 'row-fill',
          type: 'fill',
          source: 'row',
          layout: { visibility: 'none' },
          paint: { 'fill-color': '#78716c', 'fill-opacity': 0.20 },
        });
        map.addLayer({
          id: 'row-outline',
          type: 'line',
          source: 'row',
          layout: { visibility: 'none' },
          paint: { 'line-color': '#78716c', 'line-width': 1.5 },
        });

        // ── Tier 3: Environmental buffers ──────────────────────────────
        map.addSource('env-buffers', { type: 'geojson', data: ENV_BUFFER_GEOJSON as any });
        map.addLayer({
          id: 'env-buffer-fill',
          type: 'fill',
          source: 'env-buffers',
          layout: { visibility: 'none' },
          paint: {
            'fill-color': ['match', ['get', 'type'], 'WATERBODY_BUFFER', '#0891b2', '#15803d'],
            'fill-opacity': 0.28,
          },
        });
        map.addLayer({
          id: 'env-buffer-outline',
          type: 'line',
          source: 'env-buffers',
          layout: { visibility: 'none' },
          paint: {
            'line-color': ['match', ['get', 'type'], 'WATERBODY_BUFFER', '#0891b2', '#15803d'],
            'line-width': 1.5,
            'line-dasharray': [4, 2],
          },
        });

        // ── Animated conflict zones — pulsing opacity ──────────────────
        try {
          let conflictOpacity = 0.3;
          let rising = true;
          function animateConflict() {
            if (!mapRef.current) return;
            conflictOpacity += rising ? 0.008 : -0.008;
            if (conflictOpacity >= 0.65) rising = false;
            if (conflictOpacity <= 0.25) rising = true;
            safeSet(mapRef.current, () =>
              mapRef.current.setPaintProperty('conflict-fill', 'fill-opacity', conflictOpacity)
            );
            animFrameRef.current = requestAnimationFrame(animateConflict);
          }
          animateConflict();
        } catch (_) { /* animation unsupported — degrade gracefully */ }

        // ── Click handler ──────────────────────────────────────────────
        map.on('click', 'parcels-fill', (e: any) => {
          if (!e.features?.[0]) return;
          const props = e.features[0].properties as ParcelData;
          onParcelSelectRef.current(props);
          try {
            const coords: number[][] = e.features[0].geometry.coordinates[0];
            const b = coords.reduce<[[number, number], [number, number]]>(
              (acc, c) => [[Math.min(acc[0][0], c[0]), Math.min(acc[0][1], c[1])], [Math.max(acc[1][0], c[0]), Math.max(acc[1][1], c[1])]],
              [[Infinity, Infinity], [-Infinity, -Infinity]]
            );
            map.fitBounds(b, { padding: 140, maxZoom: 18, animate: true });
          } catch (_) {}
        });

        map.on('mousemove', 'parcels-fill', () => { map.getCanvas().style.cursor = 'pointer'; });
        map.on('mouseleave', 'parcels-fill', () => { map.getCanvas().style.cursor = ''; });

        // Apply initial state
        applyLayerState(map, layers, selectedParcelId);
        applyFilters(map, statusFilter, riskFilter);
      });
    });

    return () => {
      destroyed = true;
      flyTimers.forEach(clearTimeout);
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
        loadedRef.current = false;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── Layer state / selection changes ───────────────────────────────────
  React.useEffect(() => {
    const map = mapRef.current;
    if (!map || !loadedRef.current) return;
    applyLayerState(map, layers, selectedParcelId);
  }, [layers, selectedParcelId]);

  // ── Filter changes ─────────────────────────────────────────────────────
  React.useEffect(() => {
    const map = mapRef.current;
    if (!map || !loadedRef.current) return;
    applyFilters(map, statusFilter, riskFilter);
  }, [statusFilter, riskFilter]);

  return (
    <div className="absolute inset-0 w-full h-full">
      <div ref={containerRef} className="absolute inset-0 w-full h-full" />
      {coordText && (
        <div className="absolute bottom-2 left-2 bg-black/70 text-white text-xs px-2 py-1 rounded font-mono pointer-events-none z-10">
          {coordText}
        </div>
      )}
    </div>
  );
}
