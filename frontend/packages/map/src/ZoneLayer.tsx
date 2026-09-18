'use client';

import * as React from 'react';
import { useMap } from './Map';
import { colors } from '@bhoomi/ui';

export interface ZoneLayerProps {
  sourceId?: string;
  layerId?: string;
  sourceLayer?: string;
  tileUrl: string;
}

export function ZoneLayer({
  sourceId = 'zones',
  layerId = 'zones-fill',
  sourceLayer = 'zones',
  tileUrl,
}: ZoneLayerProps) {
  const map = useMap();

  React.useEffect(() => {
    if (!map) return;

    // Add source
    if (!map.getSource(sourceId)) {
      map.addSource(sourceId, {
        type: 'vector',
        tiles: [tileUrl],
        minzoom: 8,
        maxzoom: 16,
      });
    }

    // Add fill layer with colourblind-safe palette
    if (!map.getLayer(layerId)) {
      map.addLayer({
        id: layerId,
        type: 'fill',
        source: sourceId,
        'source-layer': sourceLayer,
        paint: {
          'fill-color': [
            'match',
            ['get', 'zone_type'],
            'AGRICULTURAL', colors.landUse.agricultural,
            'RESIDENTIAL', colors.landUse.residential,
            'COMMERCIAL', colors.landUse.commercial,
            'INDUSTRIAL', colors.landUse.industrial,
            'GREEN_OPEN', colors.landUse.greenOpen,
            colors.neutral[300], // default
          ],
          'fill-opacity': 0.3,
        },
      });

      // Add outline layer
      map.addLayer({
        id: `${layerId}-outline`,
        type: 'line',
        source: sourceId,
        'source-layer': sourceLayer,
        paint: {
          'line-color': colors.neutral[600],
          'line-width': 2,
          'line-dasharray': [2, 2],
        },
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
