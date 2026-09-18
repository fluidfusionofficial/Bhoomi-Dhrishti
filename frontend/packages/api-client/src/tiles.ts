import { apiRequest } from './client';

export interface TileJSON {
  tilejson: string;
  name: string;
  description?: string;
  version: string;
  attribution?: string;
  scheme: string;
  tiles: string[];
  minzoom: number;
  maxzoom: number;
  bounds: [number, number, number, number];
  center: [number, number, number];
  vector_layers?: VectorLayer[];
}

export interface VectorLayer {
  id: string;
  description?: string;
  minzoom?: number;
  maxzoom?: number;
  fields: Record<string, string>;
}

export async function getTileJSON(layerName: string): Promise<TileJSON> {
  return apiRequest<TileJSON>(`/tiles/${layerName}.json`);
}

export function buildTileUrl(layerName: string, z: number, x: number, y: number): string {
  const baseUrl = process.env.NEXT_PUBLIC_TILE_URL || 'http://localhost:8000/api/v1/tiles';
  return `${baseUrl}/${layerName}/{z}/{x}/{y}.pbf`.replace('{z}', String(z)).replace('{x}', String(x)).replace('{y}', String(y));
}

export function buildPMTilesUrl(filename: string): string {
  const baseUrl = process.env.NEXT_PUBLIC_PMTILES_URL || 'http://localhost:8000/tiles';
  return `${baseUrl}/${filename}`;
}
