'use client';

import * as React from 'react';
import { useMap } from './Map';

export interface ThreeDBuildingsProps {
  sourceId?: string;
  layerId?: string;
  sourceLayer?: string;
  tileUrl: string;
}

export function ThreeDBuildings({
  sourceId = 'buildings',
  layerId = 'buildings-3d',
  sourceLayer = 'building',
  tileUrl,
}: ThreeDBuildingsProps) {
  const map = useMap();

  React.useEffect(() => {
    if (!map) return;

    // Wait for style to load
    if (!map.isStyleLoaded()) {
      map.once('styledata', addLayer);
    } else {
      addLayer();
    }

    function addLayer() {
      if (!map) return;

      // Add source
      if (!map.getSource(sourceId)) {
        map.addSource(sourceId, {
          type: 'vector',
          tiles: [tileUrl],
          minzoom: 14,
          maxzoom: 18,
        });
      }

      // Add 3D extrusion layer
      if (!map.getLayer(layerId)) {
        map.addLayer({
          id: layerId,
          type: 'fill-extrusion',
          source: sourceId,
          'source-layer': sourceLayer,
          paint: {
            'fill-extrusion-color': '#aaa',
            'fill-extrusion-height': [
              'interpolate',
              ['linear'],
              ['zoom'],
              15,
              0,
              15.05,
              ['get', 'height'],
            ],
            'fill-extrusion-base': [
              'interpolate',
              ['linear'],
              ['zoom'],
              15,
              0,
              15.05,
              ['get', 'min_height'],
            ],
            'fill-extrusion-opacity': 0.6,
          },
        });
      }
    }

    return () => {
      if (map.getLayer(layerId)) {
        map.removeLayer(layerId);
      }
      if (map.getSource(sourceId)) {
        map.removeSource(sourceId);
      }
    };
  }, [map, sourceId, layerId, sourceLayer, tileUrl]);

  return null;
}
