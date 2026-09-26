'use client';

import * as React from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { cn } from '../lib/utils';

// ── Types ─────────────────────────────────────────────────────────────────────

export interface MapLayerConfig {
  id: string;
  label: string;
  active: boolean;
  color: string;
  description?: string;
}

export interface MapPanelProps {
  initialCenter?: [number, number];
  initialZoom?: number;
  layers?: MapLayerConfig[];
  onLayerToggle?: (layerId: string, active: boolean) => void;
  selectedParcelId?: string;
  geojsonFeature?: any;
  topologyConflicts?: any[];
  satelliteChanges?: any[];
  className?: string;
  children?: React.ReactNode;
}

// ── 15 Chengalpattu parcel polygons (same dataset as CadastralMap) ────────────

export const PANEL_PARCEL_GEOJSON = {
  type: 'FeatureCollection' as const,
  features: [
    // Northern belt (lat ~12.731-12.734)
    {
      type: 'Feature' as const,
      properties: { parcel_id: 'P001', ulpin: '33230101000001', survey_number: '41/1A', patta_no: 'PT/2019/1042', area: 3.1, land_use: 'Agricultural', owner: 'Lakshmi Narayanan', status: 'Verified', status_detail: 'Verified', risk_level: 'Low', district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Tirupporur', place: 'Kovilpathagai' },
      geometry: { type: 'Polygon' as const, coordinates: [[[80.1806,12.7322],[80.1838,12.7331],[80.1851,12.7318],[80.1843,12.7302],[80.1818,12.7294],[80.1798,12.7306],[80.1806,12.7322]]] },
    },
    {
      type: 'Feature' as const,
      properties: { parcel_id: 'P002', ulpin: '33230101000002', survey_number: '41/2B', patta_no: 'PT/2021/0221', area: 1.85, land_use: 'Residential', owner: 'Meena Rajendran', status: 'Verified', status_detail: 'Verified', risk_level: 'Low', district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Tirupporur', place: 'Kovilpathagai' },
      geometry: { type: 'Polygon' as const, coordinates: [[[80.1853,12.7320],[80.1866,12.7325],[80.1876,12.7315],[80.1870,12.7300],[80.1853,12.7296],[80.1843,12.7302],[80.1853,12.7320]]] },
    },
    {
      type: 'Feature' as const,
      properties: { parcel_id: 'P003', ulpin: '33230101000003', survey_number: '42/3B', patta_no: 'PT/2020/0789', area: 2.4, land_use: 'Residential', owner: 'Arun Kumar', status: 'Conflict', status_detail: 'Ownership Conflict', risk_level: 'High', district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Tirupporur', place: 'Kovilpathagai' },
      geometry: { type: 'Polygon' as const, coordinates: [[[80.1876,12.7323],[80.1896,12.7330],[80.1910,12.7317],[80.1904,12.7298],[80.1882,12.7290],[80.1870,12.7300],[80.1876,12.7323]]] },
    },
    {
      type: 'Feature' as const,
      properties: { parcel_id: 'P004', ulpin: '33230101000004', survey_number: '42/4A', patta_no: 'PT/2018/0634', area: 4.2, land_use: 'Agricultural', owner: 'Suresh Babu', status: 'Warning', status_detail: 'Encumbrance Warning', risk_level: 'Medium', district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Tirupporur', place: 'Kovilpathagai' },
      geometry: { type: 'Polygon' as const, coordinates: [[[80.1910,12.7317],[80.1928,12.7328],[80.1944,12.7322],[80.1946,12.7304],[80.1928,12.7291],[80.1908,12.7290],[80.1904,12.7298],[80.1910,12.7317]]] },
    },
    {
      type: 'Feature' as const,
      properties: { parcel_id: 'P005', ulpin: '33230101000005', survey_number: '43/1C', patta_no: 'PT/2022/1128', area: 0.95, land_use: 'Commercial', owner: 'Priya Venkatesh', status: 'Warning', status_detail: 'Tax Warning', risk_level: 'Medium', district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Tirupporur', place: 'Kovilpathagai' },
      geometry: { type: 'Polygon' as const, coordinates: [[[80.1946,12.7318],[80.1960,12.7324],[80.1970,12.7312],[80.1966,12.7297],[80.1948,12.7291],[80.1946,12.7304],[80.1946,12.7318]]] },
    },
    // Middle belt (lat ~12.728-12.731)
    {
      type: 'Feature' as const,
      properties: { parcel_id: 'P006', ulpin: '33230101000006', survey_number: '43/2A', patta_no: 'PT/2017/0512', area: 2.75, land_use: 'Mixed', owner: 'Karthik Selvam', status: 'Conflict', status_detail: 'Planning Conflict', risk_level: 'High', district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Tirupporur', place: 'Thottakkal' },
      geometry: { type: 'Polygon' as const, coordinates: [[[80.1798,12.7306],[80.1818,12.7294],[80.1826,12.7279],[80.1814,12.7264],[80.1793,12.7260],[80.1782,12.7273],[80.1790,12.7292],[80.1798,12.7306]]] },
    },
    {
      type: 'Feature' as const,
      properties: { parcel_id: 'P007', ulpin: '33230101000007', survey_number: '44/1B', patta_no: 'PT/2020/0856', area: 1.4, land_use: 'Residential', owner: 'Divya Anand', status: 'Warning', status_detail: 'Building Permission Warning', risk_level: 'Medium', district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Tirupporur', place: 'Thottakkal' },
      geometry: { type: 'Polygon' as const, coordinates: [[[80.1843,12.7302],[80.1853,12.7296],[80.1859,12.7280],[80.1846,12.7266],[80.1830,12.7268],[80.1826,12.7279],[80.1843,12.7302]]] },
    },
    {
      type: 'Feature' as const,
      properties: { parcel_id: 'P008', ulpin: '33230101000008', survey_number: '45/2A', patta_no: 'PT/2018/1204', area: 3.6, land_use: 'Agricultural', owner: 'Arun Raj', status: 'Verified', status_detail: 'Verified', risk_level: 'Low', district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Tirupporur', place: 'Thottakkal' },
      geometry: { type: 'Polygon' as const, coordinates: [[[80.1870,12.7300],[80.1882,12.7290],[80.1892,12.7275],[80.1882,12.7258],[80.1860,12.7253],[80.1846,12.7260],[80.1846,12.7266],[80.1859,12.7280],[80.1870,12.7300]]] },
    },
    {
      type: 'Feature' as const,
      properties: { parcel_id: 'P009', ulpin: '33230101000009', survey_number: '45/3B', patta_no: 'PT/2019/0945', area: 2.1, land_use: 'Residential', owner: 'Ganesh Moorthy', status: 'Warning', status_detail: 'Area Discrepancy', risk_level: 'Medium', district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Tirupporur', place: 'Thottakkal' },
      geometry: { type: 'Polygon' as const, coordinates: [[[80.1904,12.7298],[80.1920,12.7290],[80.1930,12.7276],[80.1918,12.7260],[80.1898,12.7254],[80.1882,12.7258],[80.1892,12.7275],[80.1904,12.7298]]] },
    },
    {
      type: 'Feature' as const,
      properties: { parcel_id: 'P010', ulpin: '33230101000010', survey_number: '46/1A', patta_no: 'PT/2021/1067', area: 1.2, land_use: 'Commercial', owner: 'Ravi Chandran', status: 'Pending', status_detail: 'Pending Transaction', risk_level: 'Medium', district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Tirupporur', place: 'Thottakkal' },
      geometry: { type: 'Polygon' as const, coordinates: [[[80.1946,12.7304],[80.1948,12.7291],[80.1964,12.7282],[80.1966,12.7265],[80.1946,12.7258],[80.1930,12.7264],[80.1930,12.7276],[80.1946,12.7304]]] },
    },
    // Southern belt (lat ~12.724-12.728)
    {
      type: 'Feature' as const,
      properties: { parcel_id: 'P011', ulpin: '33230101000011', survey_number: '46/2C', patta_no: 'PT/2016/0445', area: 5.3, land_use: 'Agricultural', owner: 'Saravanan Pillai', status: 'Verified', status_detail: 'Verified', risk_level: 'Low', district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Tirupporur', place: 'Manimangalam' },
      geometry: { type: 'Polygon' as const, coordinates: [[[80.1782,12.7273],[80.1793,12.7260],[80.1814,12.7264],[80.1830,12.7268],[80.1828,12.7248],[80.1808,12.7236],[80.1784,12.7232],[80.1768,12.7248],[80.1782,12.7273]]] },
    },
    {
      type: 'Feature' as const,
      properties: { parcel_id: 'P012', ulpin: 'TN-CHN-000012', survey_number: '47/1B', area: 0.8, land_use: 'Industrial', owner: 'Nithya Sundaram', status: 'Conflict', status_detail: 'High Risk Transaction', risk_level: 'High', district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Demo Village' },
      geometry: { type: 'Polygon' as const, coordinates: [[[80.1830,12.7268],[80.1846,12.7266],[80.1860,12.7253],[80.1854,12.7238],[80.1836,12.7232],[80.1820,12.7238],[80.1820,12.7252],[80.1830,12.7268]]] },
    },
    {
      type: 'Feature' as const,
      properties: { parcel_id: 'P013', ulpin: 'TN-CHN-000013', survey_number: '47/3A', area: 2.95, land_use: 'Residential', owner: 'Bala Subramani', status: 'Verified', status_detail: 'Verified', risk_level: 'Low', district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Demo Village' },
      geometry: { type: 'Polygon' as const, coordinates: [[[80.1860,12.7253],[80.1882,12.7258],[80.1894,12.7244],[80.1888,12.7230],[80.1866,12.7224],[80.1846,12.7230],[80.1854,12.7238],[80.1860,12.7253]]] },
    },
    {
      type: 'Feature' as const,
      properties: { parcel_id: 'P014', ulpin: 'TN-CHN-000014', survey_number: '48/1A', area: 3.85, land_use: 'Mixed', owner: 'Kavya Raman', status: 'Warning', status_detail: 'Planning Warning', risk_level: 'Medium', district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Demo Village' },
      geometry: { type: 'Polygon' as const, coordinates: [[[80.1898,12.7254],[80.1918,12.7260],[80.1936,12.7252],[80.1940,12.7234],[80.1920,12.7224],[80.1898,12.7226],[80.1888,12.7238],[80.1898,12.7254]]] },
    },
    {
      type: 'Feature' as const,
      properties: { parcel_id: 'P015', ulpin: 'TN-CHN-000015', survey_number: '48/2B', area: 1.65, land_use: 'Water Body', owner: 'Village Commons', status: 'Verified', status_detail: 'Verified', risk_level: 'Low', district: 'Chengalpattu', taluk: 'Tirupporur', village: 'Demo Village' },
      geometry: { type: 'Polygon' as const, coordinates: [[[80.1946,12.7258],[80.1966,12.7265],[80.1978,12.7254],[80.1976,12.7238],[80.1958,12.7228],[80.1940,12.7230],[80.1940,12.7234],[80.1946,12.7258]]] },
    },
  ],
};

// Default conflict overlay (overlap zone between P003 and P008)
const DEFAULT_CONFLICT_GEOJSON = {
  type: 'FeatureCollection' as const,
  features: [
    {
      type: 'Feature' as const,
      properties: { label: 'OVERLAP 42m²' },
      geometry: {
        type: 'Polygon' as const,
        coordinates: [[[80.1876, 12.7302],[80.1886, 12.7300],[80.1884, 12.7292],[80.1874, 12.7294],[80.1876, 12.7302]]],
      },
    },
  ],
};

// ── MapLibre expression helpers ───────────────────────────────────────────────

function statusFillColor(): any {
  return [
    'match', ['get', 'status'],
    'Verified', '#16a34a',
    'Conflict', '#dc2626',
    'Warning',  '#d97706',
    'Pending',  '#2456a6',
    '#9aa4b3',
  ];
}

function statusBorderColor(): any {
  return [
    'match', ['get', 'status'],
    'Verified', '#00ff88',
    'Conflict', '#ff4400',
    'Warning',  '#ffa500',
    'Pending',  '#44aaff',
    '#ffffff',
  ];
}

function selectedFillOpacity(parcelId: string | undefined): any {
  if (!parcelId) return 0.3;
  return ['case', ['any', ['==', ['get', 'parcel_id'], parcelId], ['==', ['get', 'ulpin'], parcelId]], 0.55, 0.3];
}

function selectedLineWidth(parcelId: string | undefined): any {
  if (!parcelId) return 2;
  return ['case', ['any', ['==', ['get', 'parcel_id'], parcelId], ['==', ['get', 'ulpin'], parcelId]], 4, 2];
}

// Compute bounding box from a polygon coordinate ring
function bboxFromCoords(coords: number[][]): [[number, number], [number, number]] {
  return coords.reduce<[[number, number], [number, number]]>(
    (acc, c) => [
      [Math.min(acc[0][0], c[0]), Math.min(acc[0][1], c[1])],
      [Math.max(acc[1][0], c[0]), Math.max(acc[1][1], c[1])],
    ],
    [[Infinity, Infinity], [-Infinity, -Infinity]]
  );
}

// ── Component ─────────────────────────────────────────────────────────────────

export function MapPanel({
  initialCenter = [80.187, 12.729],
  initialZoom = 14,
  layers: _layers,
  onLayerToggle: _onLayerToggle,
  selectedParcelId,
  geojsonFeature,
  topologyConflicts,
  satelliteChanges: _satelliteChanges,
  className,
  children,
}: MapPanelProps) {
  const containerRef = React.useRef<HTMLDivElement>(null);
  const mapRef = React.useRef<maplibregl.Map | null>(null);
  const loadedRef = React.useRef(false);

  // Stable refs for values used inside map callbacks
  const selectedRef = React.useRef(selectedParcelId);
  React.useEffect(() => { selectedRef.current = selectedParcelId; }, [selectedParcelId]);

  // ── Mount: create the MapLibre map once ─────────────────────────────────
  React.useEffect(() => {
    if (!containerRef.current) return;
    let destroyed = false;

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: {
        version: 8,
        glyphs: 'https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf',
        sources: {
          satellite: {
            type: 'raster',
            tiles: [
              'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            ],
            tileSize: 256,
            attribution: '© Esri, Maxar, Earthstar Geographics',
          },
        },
        layers: [{ id: 'satellite-bg', type: 'raster', source: 'satellite' }],
      },
      center: initialCenter,
      zoom: initialZoom,
      attributionControl: false,
    });

    mapRef.current = map;

    // Controls
    map.addControl(new maplibregl.NavigationControl({ showCompass: true }), 'top-right');
    map.addControl(new maplibregl.ScaleControl({ maxWidth: 120 }), 'bottom-left');

    map.on('load', () => {
      if (destroyed) return;
      loadedRef.current = true;

      // Determine parcel data source: prefer geojsonFeature prop, fall back to built-in parcels
      const parcelData: any = geojsonFeature ?? PANEL_PARCEL_GEOJSON;

      map.addSource('panel-parcels', { type: 'geojson', data: parcelData });

      // Fill layer: status-based coloring
      map.addLayer({
        id: 'panel-parcels-fill',
        type: 'fill',
        source: 'panel-parcels',
        paint: {
          'fill-color': statusFillColor(),
          'fill-opacity': selectedFillOpacity(selectedRef.current),
        },
      });

      // Outline layer: bright borders for satellite contrast
      map.addLayer({
        id: 'panel-parcels-outline',
        type: 'line',
        source: 'panel-parcels',
        paint: {
          'line-color': statusBorderColor(),
          'line-width': selectedLineWidth(selectedRef.current),
        },
      });

      // Labels layer: parcel IDs with halo for readability on satellite
      map.addLayer({
        id: 'panel-parcels-labels',
        type: 'symbol',
        source: 'panel-parcels',
        layout: {
          'text-field': ['get', 'parcel_id'],
          'text-size': 10,
          'text-font': ['Noto Sans Bold'],
          'text-anchor': 'center',
        },
        paint: {
          'text-color': '#ffffff',
          'text-halo-color': '#000000',
          'text-halo-width': 1.2,
        },
      });

      // Conflict overlay source: prefer topologyConflicts prop, fall back to default
      const conflictData: any = (topologyConflicts && topologyConflicts.length > 0)
        ? { type: 'FeatureCollection', features: topologyConflicts }
        : DEFAULT_CONFLICT_GEOJSON;

      map.addSource('panel-conflicts', { type: 'geojson', data: conflictData });

      map.addLayer({
        id: 'panel-conflict-fill',
        type: 'fill',
        source: 'panel-conflicts',
        paint: { 'fill-color': '#dc2626', 'fill-opacity': 0.55 },
      });

      map.addLayer({
        id: 'panel-conflict-outline',
        type: 'line',
        source: 'panel-conflicts',
        paint: {
          'line-color': '#ff4400',
          'line-width': 2,
          'line-dasharray': [4, 2],
        },
      });

      // If a parcel is pre-selected, fly to it
      if (selectedRef.current) {
        fitToParcel(map, selectedRef.current);
      }
    });

    return () => {
      destroyed = true;
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
        loadedRef.current = false;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── React to selectedParcelId changes ───────────────────────────────────
  React.useEffect(() => {
    const map = mapRef.current;
    if (!map || !loadedRef.current) return;

    try {
      map.setPaintProperty('panel-parcels-fill', 'fill-opacity', selectedFillOpacity(selectedParcelId));
      map.setPaintProperty('panel-parcels-outline', 'line-width', selectedLineWidth(selectedParcelId));
    } catch (_) {
      // Layers may not be ready yet
    }

    if (selectedParcelId) {
      fitToParcel(map, selectedParcelId);
    }
  }, [selectedParcelId]);

  // ── React to topologyConflicts changes ──────────────────────────────────
  React.useEffect(() => {
    const map = mapRef.current;
    if (!map || !loadedRef.current) return;

    const src = map.getSource('panel-conflicts') as maplibregl.GeoJSONSource | undefined;
    if (!src) return;

    if (topologyConflicts && topologyConflicts.length > 0) {
      src.setData({ type: 'FeatureCollection', features: topologyConflicts } as any);
    } else {
      src.setData(DEFAULT_CONFLICT_GEOJSON as any);
    }
  }, [topologyConflicts]);

  // ── React to geojsonFeature changes ─────────────────────────────────────
  React.useEffect(() => {
    const map = mapRef.current;
    if (!map || !loadedRef.current || !geojsonFeature) return;

    const src = map.getSource('panel-parcels') as maplibregl.GeoJSONSource | undefined;
    if (src) {
      src.setData(geojsonFeature);
    }
  }, [geojsonFeature]);

  return (
    <div
      className={cn(
        'relative w-full h-full min-h-[380px] rounded-md overflow-hidden',
        className
      )}
    >
      <div ref={containerRef} className="absolute inset-0 w-full h-full" />
      {children}
    </div>
  );
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function fitToParcel(map: maplibregl.Map, parcelId: string) {
  const feature = PANEL_PARCEL_GEOJSON.features.find(
    (f) => f.properties.parcel_id === parcelId || f.properties.ulpin === parcelId
  );
  if (!feature) return;

  try {
    const coords = feature.geometry.coordinates[0];
    const bounds = bboxFromCoords(coords);
    map.fitBounds(bounds, { padding: 60, maxZoom: 17, animate: true });
  } catch (_) {
    // Geometry may be malformed; silently ignore
  }
}
