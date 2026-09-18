'use client';

import * as React from 'react';
import maplibregl from 'maplibre-gl';
import { useMap } from './Map';

export interface ParcelPopupData {
  ulpin: string;
  landClass: string;
  area: number;
  conflictCount: number;
}

export interface ParcelPopupProps {
  layerId: string;
  onViewDetails?: (ulpin: string) => void;
}

export function ParcelPopup({ layerId, onViewDetails }: ParcelPopupProps) {
  const map = useMap();
  const popupRef = React.useRef<maplibregl.Popup | null>(null);

  React.useEffect(() => {
    if (!map) return;

    const onClick = (e: maplibregl.MapLayerMouseEvent) => {
      const features = e.features;
      if (!features || features.length === 0) return;

      const feature = features[0];
      const properties = feature.properties;

      if (!properties) return;

      // Remove existing popup
      if (popupRef.current) {
        popupRef.current.remove();
      }

      // Create popup content
      const popupContent = document.createElement('div');
      popupContent.className = 'p-2 min-w-[200px]';
      popupContent.innerHTML = `
        <div class="space-y-2">
          <div>
            <p class="text-xs text-neutral-500">ULPIN</p>
            <p class="font-mono text-sm font-semibold">${properties.ulpin || 'N/A'}</p>
          </div>
          <div>
            <p class="text-xs text-neutral-500">Land Class</p>
            <p class="text-sm">${properties.land_class || 'N/A'}</p>
          </div>
          <div>
            <p class="text-xs text-neutral-500">Area</p>
            <p class="text-sm">${properties.area_hectares || 'N/A'} ha</p>
          </div>
          ${
            properties.conflict_count > 0
              ? `<div class="text-xs text-red-600">⚠ ${properties.conflict_count} conflicts</div>`
              : ''
          }
          <button
            id="view-details-btn"
            class="w-full mt-2 px-3 py-1.5 bg-[#1B4F72] text-white text-sm rounded hover:bg-[#16415D]"
          >
            View Details
          </button>
        </div>
      `;

      // Create and show popup
      popupRef.current = new maplibregl.Popup({
        closeButton: true,
        closeOnClick: false,
      })
        .setLngLat(e.lngLat)
        .setDOMContent(popupContent)
        .addTo(map);

      // Add click handler for button
      const btn = popupContent.querySelector('#view-details-btn');
      if (btn && onViewDetails) {
        btn.addEventListener('click', () => {
          onViewDetails(properties.ulpin);
          popupRef.current?.remove();
        });
      }
    };

    map.on('click', layerId, onClick);

    return () => {
      map.off('click', layerId, onClick);
      if (popupRef.current) {
        popupRef.current.remove();
      }
    };
  }, [map, layerId, onViewDetails]);

  return null;
}
