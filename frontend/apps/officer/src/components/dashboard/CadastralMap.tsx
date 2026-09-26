'use client';

import * as React from 'react';
import {
  PARCEL_GEOJSON, PARCEL_DATA as _PARCEL_DATA, CONFLICT_GEOJSON,
  REGISTRATION_GEOJSON, ENCUMBRANCE_GEOJSON, LITIGATION_GEOJSON,
  ZONING_GEOJSON, UTILITY_GEOJSON, ROW_GEOJSON, ENV_BUFFER_GEOJSON,
  ROADS_GEOJSON, RAILWAY_GEOJSON, VILLAGE_BOUNDARY_GEOJSON,
  GOVERNMENT_LAND_GEOJSON,
  type ParcelData,
} from '../../data/cadastral-data';

export type { ParcelData } from '../../data/cadastral-data';
export const PARCEL_DATA = _PARCEL_DATA;

export interface LayerState {
  // Tier 1: Base Spatial
  parcels: boolean;
  ulpin: boolean;
  villageBoundary: boolean;
  roads: boolean;
  railway: boolean;
  governmentLand: boolean;
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

// All GeoJSON data is imported from ../../data/cadastral-data

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
    'Forest',       '#15803d',
    'Government',   '#4527a0',
    'Poramboke',    '#795548',
    'Unoccupied',   '#9e9e9e',
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
  safeSet(map, () => map.setLayoutProperty('roads-line', 'visibility', visStr(layers.roads)));
  safeSet(map, () => map.setLayoutProperty('roads-labels', 'visibility', visStr(layers.roads)));
  safeSet(map, () => map.setLayoutProperty('railway-line', 'visibility', visStr(layers.railway)));
  safeSet(map, () => map.setLayoutProperty('railway-labels', 'visibility', visStr(layers.railway)));
  safeSet(map, () => map.setLayoutProperty('govt-land-fill', 'visibility', visStr(layers.governmentLand)));
  safeSet(map, () => map.setLayoutProperty('govt-land-outline', 'visibility', visStr(layers.governmentLand)));

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
          data: VILLAGE_BOUNDARY_GEOJSON as any,
        });
        map.addLayer({
          id: 'village-boundary',
          type: 'line',
          source: 'village-boundary-src',
          layout: { visibility: 'none' },
          paint: { 'line-color': '#c9b48a', 'line-width': 2, 'line-dasharray': [6, 3] },
        });

        // ── Tier 1: Road network ──────────────────────────────────────
        map.addSource('roads', { type: 'geojson', data: ROADS_GEOJSON as any });
        map.addLayer({
          id: 'roads-line',
          type: 'line',
          source: 'roads',
          layout: { visibility: 'none' },
          paint: {
            'line-color': ['match', ['get', 'road_class'],
              'STATE_HIGHWAY', '#f59e0b',
              'MAJOR_DISTRICT_ROAD', '#fb923c',
              'VILLAGE_ROAD', '#d4d4d8',
              '#a8a29e'] as any,
            'line-width': ['match', ['get', 'road_class'],
              'STATE_HIGHWAY', 4,
              'MAJOR_DISTRICT_ROAD', 3,
              'VILLAGE_ROAD', 2,
              1.5] as any,
          },
        });
        map.addLayer({
          id: 'roads-labels',
          type: 'symbol',
          source: 'roads',
          layout: {
            visibility: 'none',
            'symbol-placement': 'line',
            'text-field': ['get', 'name'],
            'text-size': 10,
            'text-font': ['Noto Sans Bold'],
          } as any,
          paint: { 'text-color': '#fbbf24', 'text-halo-color': '#000', 'text-halo-width': 1.2 },
        });

        // ── Tier 1: Railway line ──────────────────────────────────────
        map.addSource('railway', { type: 'geojson', data: RAILWAY_GEOJSON as any });
        map.addLayer({
          id: 'railway-line',
          type: 'line',
          source: 'railway',
          layout: { visibility: 'none' },
          paint: {
            'line-color': '#ef4444',
            'line-width': 3,
            'line-dasharray': [8, 4, 2, 4],
          },
        });
        map.addLayer({
          id: 'railway-labels',
          type: 'symbol',
          source: 'railway',
          layout: {
            visibility: 'none',
            'symbol-placement': 'line',
            'text-field': ['get', 'name'],
            'text-size': 10,
            'text-font': ['Noto Sans Bold'],
          } as any,
          paint: { 'text-color': '#fca5a5', 'text-halo-color': '#000', 'text-halo-width': 1.2 },
        });

        // ── Tier 1: Government & institutional land zones ─────────────
        map.addSource('government-land', { type: 'geojson', data: GOVERNMENT_LAND_GEOJSON as any });
        map.addLayer({
          id: 'govt-land-fill',
          type: 'fill',
          source: 'government-land',
          layout: { visibility: 'none' },
          paint: {
            'fill-color': ['match', ['get', 'type'],
              'RAILWAY_LAND', '#37474F',
              'GOVERNMENT_BUILDING', '#4527A0',
              'PORAMBOKE', '#795548',
              'WATER_BODY', '#0277BD',
              '#616161'] as any,
            'fill-opacity': 0.25,
          },
        });
        map.addLayer({
          id: 'govt-land-outline',
          type: 'line',
          source: 'government-land',
          layout: { visibility: 'none' },
          paint: {
            'line-color': ['match', ['get', 'type'],
              'RAILWAY_LAND', '#37474F',
              'GOVERNMENT_BUILDING', '#4527A0',
              'PORAMBOKE', '#795548',
              'WATER_BODY', '#0277BD',
              '#616161'] as any,
            'line-width': 2,
            'line-dasharray': [5, 3],
          },
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
