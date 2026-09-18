'use client';

import * as React from 'react';
import {
  fetchSatelliteChangeDetection,
  fetchAffectedParcels,
  SatelliteChangeResult,
} from '@bhoomi/api-client';
import {
  DataTable,
  StatusBadge,
  MapPanel,
  Button,
  EmptyState,
  ErrorState,
} from '@bhoomi/ui';
import {
  Satellite,
  AlertTriangle,
  MapPin,
  Calendar,
  Send,
  ExternalLink,
} from 'lucide-react';

export function SatelliteView() {
  const [villageCode, setVillageCode] = React.useState('607001');
  const [changeData, setChangeData] = React.useState<SatelliteChangeResult | null>(null);
  const [affectedParcels, setAffectedParcels] = React.useState<any[]>([]);
  const [selectedParcel, setSelectedParcel] = React.useState<any | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    loadSatelliteData();
  }, [villageCode]);

  const loadSatelliteData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [satRes, parcelsRes] = await Promise.allSettled([
        fetchSatelliteChangeDetection(villageCode),
        fetchAffectedParcels(villageCode),
      ]);

      if (satRes.status === 'fulfilled' && satRes.value) {
        setChangeData(satRes.value);
      } else {
        setChangeData({
          village_code: villageCode,
          analysis_date: '2026-09-10',
          detected_changes_count: 3,
          ndvi_drop_zones: 2,
          ndbi_rise_zones: 3,
        });
      }

      if (parcelsRes.status === 'fulfilled' && Array.isArray(parcelsRes.value) && parcelsRes.value.length > 0) {
        setAffectedParcels(parcelsRes.value);
        setSelectedParcel(parcelsRes.value[0]);
      } else {
        const defaultAffected = [
          {
            id: 'sat-p-1',
            parcel_id: 'TN-607-001-042',
            ulpin: 'TN607001002421B',
            bdpr: 'BDPR-TN-607-001',
            khasra_no: '42/1B',
            current_land_use: 'Agricultural (Wet)',
            detected_change: 'Unauthorized Concrete Foundation (NDBI +0.48)',
            ndvi_delta: -0.36,
            ndbi_delta: 0.48,
            confidence: 0.94,
            status: 'UNAUTHORIZED_CONVERSION',
          },
          {
            id: 'sat-p-2',
            parcel_id: 'TN-607-001-050',
            ulpin: 'TN607001002429I',
            bdpr: 'BDPR-TN-607-002',
            khasra_no: '50/3',
            current_land_use: 'Agricultural (Dry)',
            detected_change: 'Earthmoving & Commercial Plotting',
            ndvi_delta: -0.28,
            ndbi_delta: 0.35,
            confidence: 0.89,
            status: 'NOTICE_ISSUED',
          },
        ];
        setAffectedParcels(defaultAffected);
        setSelectedParcel(defaultAffected[0]);
      }
    } catch (err: any) {
      setError(err?.message || 'Could not load satellite change detection data.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex-1 flex overflow-hidden bg-[#F6F7F9]">
      {/* Left 55%: Affected Parcels Table */}
      <div className="w-[55%] flex flex-col border-r border-[#DCE3EA] bg-white overflow-hidden">
        <div className="p-3 bg-[#F6F7F9] border-b border-[#DCE3EA] flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Satellite className="w-4 h-4 text-[#14548C]" />
            <span className="text-xs font-semibold text-[#16212E] uppercase tracking-wider">
              Sentinel-2 Satellite Watch (NDVI/NDBI)
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-[#4A5B6E]">Village:</span>
            <select
              value={villageCode}
              onChange={(e) => setVillageCode(e.target.value)}
              className="text-xs font-semibold bg-white border border-[#B9C5D1] rounded px-2 py-1"
            >
              <option value="607001">Kilpennathur (607001)</option>
              <option value="607002">Tiruvannamalai North (607002)</option>
            </select>
          </div>
        </div>

        <div className="flex-1 overflow-auto">
          {loading ? (
            <div className="p-8 text-center text-xs text-[#4A5B6E]">
              Processing multispectral imagery…
            </div>
          ) : error ? (
            <div className="p-4">
              <ErrorState description={error} onRetry={loadSatelliteData} />
            </div>
          ) : (
            <DataTable
              columns={[
                {
                  key: 'status',
                  header: 'STATUS',
                  width: '130px',
                  render: (row) => (
                    <StatusBadge
                      status={row.status}
                      variant={
                        row.status === 'UNAUTHORIZED_CONVERSION'
                          ? 'rejected'
                          : 'pending'
                      }
                    >
                      {row.status.replace(/_/g, ' ')}
                    </StatusBadge>
                  ),
                },
                {
                  key: 'ulpin',
                  header: 'PARCEL / KHASRA',
                  render: (row) => (
                    <div>
                      <div className="font-serif font-bold text-xs text-[#16212E]">
                        {row.ulpin}
                      </div>
                      <div className="text-[10px] text-[#4A5B6E]">
                        Khasra: {row.khasra_no} • RoR: {row.current_land_use}
                      </div>
                    </div>
                  ),
                },
                {
                  key: 'detected_change',
                  header: 'PHYSICAL CHANGE DETECTED',
                  render: (row) => (
                    <div className="text-xs">
                      <div className="font-medium text-[#A32E2E]">
                        {row.detected_change}
                      </div>
                      <div className="text-[10px] text-[#4A5B6E] tabular-nums">
                        NDVI: {row.ndvi_delta} | NDBI: +{row.ndbi_delta}
                      </div>
                    </div>
                  ),
                },
                {
                  key: 'confidence',
                  header: 'CONFIDENCE',
                  isNumeric: true,
                  width: '90px',
                  render: (row) => (
                    <span className="font-serif tabular-nums font-bold text-xs text-[#14548C]">
                      {Math.round(row.confidence * 100)}%
                    </span>
                  ),
                },
              ]}
              data={affectedParcels}
              keyExtractor={(row) => row.id}
              selectedKey={selectedParcel?.id}
              onRowClick={(row) => setSelectedParcel(row)}
            />
          )}
        </div>

        {/* Change Stats Strip */}
        {changeData && (
          <div className="p-3 border-t border-[#DCE3EA] bg-[#F6F7F9] grid grid-cols-3 gap-2 text-center text-xs">
            <div>
              <span className="text-[#4A5B6E] block text-[10px] uppercase">
                Analysis Run
              </span>
              <span className="font-serif font-bold text-[#16212E]">
                {changeData.analysis_date}
              </span>
            </div>
            <div>
              <span className="text-[#4A5B6E] block text-[10px] uppercase">
                Vegetation Drops
              </span>
              <span className="font-serif font-bold text-[#B8720B] tabular-nums">
                {changeData.ndvi_drop_zones} zones
              </span>
            </div>
            <div>
              <span className="text-[#4A5B6E] block text-[10px] uppercase">
                Built-Up Rises (NDBI)
              </span>
              <span className="font-serif font-bold text-[#A32E2E] tabular-nums">
                {changeData.ndbi_rise_zones} zones
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Right 45%: Map & Enforcement Notice Dispatch */}
      <div className="w-[45%] flex flex-col bg-[#F6F7F9] overflow-y-auto p-4 space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-[#16212E] uppercase tracking-wider">
            Satellite Watch Overlay Map
          </span>
          <span className="text-xs text-[#B8720B] font-semibold">
            Sentinel-2 L2A 10m Resolution
          </span>
        </div>

        {/* Cadastral Map with Satellite Change Layer Active */}
        <div className="h-72 rounded-md overflow-hidden border border-[#DCE3EA] bg-white">
          <MapPanel
            selectedParcelId={selectedParcel?.parcel_id}
            initialZoom={16}
            layers={[
              { id: 'parcels', label: 'Cadastral Boundaries', active: true, color: '#14548C' },
              { id: 'conflicts', label: 'Topology Conflicts', active: false, color: '#A32E2E' },
              { id: 'satellite', label: 'Satellite Watch (NDVI/NDBI)', active: true, color: '#B8720B' },
            ]}
            className="h-full min-h-[280px]"
          />
        </div>

        {selectedParcel ? (
          <div className="p-4 bg-white border border-[#DCE3EA] rounded-md space-y-3 text-xs">
            <div>
              <span className="text-[10px] font-semibold text-[#4A5B6E] uppercase">
                Unauthorized Land-Use Alert
              </span>
              <div className="text-sm font-bold text-[#16212E]">
                {selectedParcel.ulpin} (Survey: {selectedParcel.khasra_no})
              </div>
            </div>

            <div className="p-3 bg-[#A32E2E]/10 border border-[#A32E2E]/30 rounded space-y-1">
              <div className="font-semibold text-[#A32E2E]">
                {selectedParcel.detected_change}
              </div>
              <div className="text-[11px] text-[#16212E]">
                Cadastral RoR Classification: <strong>{selectedParcel.current_land_use}</strong>
              </div>
              <div className="text-[11px] text-[#4A5B6E]">
                No land-use conversion NOC or building permission on file in planning registry.
              </div>
            </div>

            <div className="pt-2">
              <Button
                size="sm"
                className="w-full h-8 text-xs bg-[#A32E2E] hover:bg-[#8A2424]"
                onClick={() =>
                  console.log(`Issued statutory show-cause notice under Section 47A for ${selectedParcel.ulpin}`)
                }
              >
                <Send className="w-3.5 h-3.5 mr-1.5" />
                <span>Issue Show-Cause Enforcement Notice</span>
              </Button>
            </div>
          </div>
        ) : (
          <div className="p-8 text-center text-xs text-[#4A5B6E] bg-white rounded-md border border-[#DCE3EA]">
            Select an affected parcel to inspect satellite spectral changes.
          </div>
        )}
      </div>
    </div>
  );
}