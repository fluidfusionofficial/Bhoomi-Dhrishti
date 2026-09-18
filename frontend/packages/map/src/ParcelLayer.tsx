'use client';

import * as React from 'react';
import { useMap } from './Map';
import { colors } from '@bhoomi/ui';

export interface ParcelLayerProps {
  sourceId?: string;
  layerId?: string;
  sourceLayer?: string;
  tileUrl: string;
}

export function ParcelLayer({
  sourceId = 'parcels',
  layerId = 'parcels-fill',
  sourceLayer = 'parcels',
  tileUrl,
}: ParcelLayerProps) {
  const map = useMap();

  React.useEffect(() => {
    if (!map) return;

    // Add source
    if (!map.getSource(sourceId)) {
      map.addSource(sourceId, {
        type: 'vector',
        tiles: [tileUrl],
        minzoom: 10,
        maxzoom: 18,
      });
    }

    // Add fill layer with land use colors
    if (!map.getLayer(layerId)) {
      map.addLayer({
        id: layerId,
        type: 'fill',
        source: sourceId,
        'source-layer': sourceLayer,
        paint: {
          'fill-color': [
            'match',
            ['get', 'land_class'],
            'AGRICULTURAL', colors.landUse.agricultural,
            'RESIDENTIAL', colors.landUse.residential,
            'COMMERCIAL', colors.landUse.commercial,
            'INDUSTRIAL', colors.landUse.industrial,
            'GREEN_OPEN', colors.landUse.greenOpen,
            'GOVERNMENT', colors.landUse.government,
            'MIXED_USE', colors.landUse.mixedUse,
            colors.neutral[300], // default
          ],
          'fill-opacity': 0.6,
        },
      });

      // Add outline layer
      map.addLayer({
        id: `${layerId}-outline`,
        type: 'line',
        source: sourceId,
        'source-layer': sourceLayer,
        paint: {
          'line-color': colors.neutral[700],
          'line-width': 1,
        },
      });

      // Add hover effect
      map.on('mousemove', layerId, () => {
        map.getCanvas().style.cursor = 'pointer';
      });

      map.on('mouseleave', layerId, () => {
        map.getCanvas().style.cursor = '';
      });
    }

    return () => {
      if (map.getLayer(`${layerId}-outline`)) {
        map.removeLayer(`${layerId}-outline`);
      }
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
