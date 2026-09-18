'use client';

import { Map, ParcelLayer, ParcelPopup } from '@bhoomi/map';
import { useRouter } from 'next/navigation';

export default function MapView() {
  const router = useRouter();

  const handleViewDetails = (ulpin: string) => {
    router.push(`/parcels/${ulpin}`);
  };

  const tileUrl = `${process.env.NEXT_PUBLIC_TILE_URL}/parcels/{z}/{x}/{y}.pbf`;

  return (
    <Map
      initialCenter={[80.2707, 13.0827]} // Chennai
      initialZoom={12}
      style={`https://api.maptiler.com/maps/streets/style.json?key=${process.env.NEXT_PUBLIC_MAPTILER_KEY || 'demo'}`}
    >
      <ParcelLayer tileUrl={tileUrl} />
      <ParcelPopup layerId="parcels-fill" onViewDetails={handleViewDetails} />
    </Map>
  );
}
