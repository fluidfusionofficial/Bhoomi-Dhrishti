'use client';

import * as React from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';

export interface MapProps {
  initialCenter?: [number, number];
  initialZoom?: number;
  style?: string;
  className?: string;
  onLoad?: (map: maplibregl.Map) => void;
  children?: React.ReactNode;
}

export const MapContext = React.createContext<maplibregl.Map | null>(null);

export function Map({
  initialCenter = [78.9629, 20.5937], // India center
  initialZoom = 5,
  style = 'https://api.maptiler.com/maps/streets/style.json?key=get_your_own_key',
  className = 'w-full h-full',
  onLoad,
  children,
}: MapProps) {
  const mapContainer = React.useRef<HTMLDivElement>(null);
  const map = React.useRef<maplibregl.Map | null>(null);
  const [mapLoaded, setMapLoaded] = React.useState(false);

  React.useEffect(() => {
    if (!mapContainer.current || map.current) return;

    map.current = new maplibregl.Map({
      container: mapContainer.current,
      style: style,
      center: initialCenter,
      zoom: initialZoom,
    });

    map.current.on('load', () => {
      setMapLoaded(true);
      if (onLoad && map.current) {
        onLoad(map.current);
      }
    });

    return () => {
      if (map.current) {
        map.current.remove();
        map.current = null;
      }
    };
  }, []);

  return (
    <div className={className}>
      <div ref={mapContainer} className="w-full h-full" />
      {mapLoaded && map.current && (
        <MapContext.Provider value={map.current}>
          {children}
        </MapContext.Provider>
      )}
    </div>
  );
}

export function useMap(): maplibregl.Map | null {
  return React.useContext(MapContext);
}
