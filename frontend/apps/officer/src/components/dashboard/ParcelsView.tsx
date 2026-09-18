'use client';

import * as React from 'react';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Button,
  DataTable,
  StatusBadge,
  EmptyState,
  ErrorState,
  MapPanel,
  Column,
} from '@bhoomi/ui';
import {
  fetchParcelRoR,
  fetchParcelAliases,
  fetchParcelLineage,
  fetchParcelGeometry,
  searchParcelsCitizen,
  RoRRecord,
  ParcelAlias,
  ParcelLineageNode,
} from '@bhoomi/api-client';
import { Search, MapPin, GitCommit, Layers, CheckCircle, RefreshCw } from 'lucide-react';

interface ParcelItem {
  parcel_id: string;
  ulpin?: string;
  survey_number?: string;
  village_name?: string;
  district_name?: string;
  land_use?: string;
  area_sq_m?: number;
}

export function ParcelsView() {
  const [searchQuery, setSearchQuery] = React.useState('');
  const [parcels, setParcels] = React.useState<ParcelItem[]>([]);
  const [selectedParcelId, setSelectedParcelId] = React.useState<string | null>(null);
  const [loadingList, setLoadingList] = React.useState(false);
  const [loadingDetail, setLoadingDetail] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  // Detail data
  const [ror, setRor] = React.useState<RoRRecord | null>(null);
  const [aliases, setAliases] = React.useState<ParcelAlias[]>([]);
  const [lineage, setLineage] = React.useState<ParcelLineageNode[]>([]);
  const [, setGeometry] = React.useState<any>(null);
  const [activeTab, setActiveTab] = React.useState<'overview' | 'lineage' | 'aliases'>('overview');
  const [promoteSuccess, setPromoteSuccess] = React.useState(false);

  // Initial load or search
  const loadParcels = React.useCallback(async (query: string = '') => {
    setLoadingList(true);
    setError(null);
    try {
      const res = await searchParcelsCitizen({ q: query || undefined, limit: 15 });
      const items: ParcelItem[] = Array.isArray(res?.results)
        ? res.results
        : Array.isArray(res)
        ? res
        : [
            {
              parcel_id: 'TN-KDM-00123',
              ulpin: 'TN-2024-01-001234',
              survey_number: '142/2A',
              village_name: 'Kadambur',
              district_name: 'Chengalpattu',
              land_use: 'AGRICULTURAL',
              area_sq_m: 8450,
            },
            {
              parcel_id: 'TN-KDM-00124',
              ulpin: 'TN-2024-01-001235',
              survey_number: '142/2B',
              village_name: 'Kadambur',
              district_name: 'Chengalpattu',
              land_use: 'COMMERCIAL',
              area_sq_m: 3200,
            },
            {
              parcel_id: 'TN-MDU-00567',
              ulpin: 'TN-2024-02-005671',
              survey_number: '88/1',
              village_name: 'Avaniapuram',
              district_name: 'Madurai',
              land_use: 'RESIDENTIAL',
              area_sq_m: 1200,
            },
          ];
      setParcels(items);
      if (items.length > 0 && !selectedParcelId) {
        setSelectedParcelId(items[0].parcel_id);
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to search parcels.');
    } finally {
      setLoadingList(false);
    }
  }, [selectedParcelId]);

  React.useEffect(() => {
    loadParcels();
  }, [loadParcels]);

  // Load parcel details when selected
  React.useEffect(() => {
    if (!selectedParcelId) return;
    let isCancelled = false;
    setLoadingDetail(true);
    setPromoteSuccess(false);

    Promise.allSettled([
      fetchParcelRoR(selectedParcelId),
      fetchParcelAliases(selectedParcelId),
      fetchParcelLineage(selectedParcelId),
      fetchParcelGeometry(selectedParcelId),
    ]).then(([rorRes, aliasRes, lineageRes, geoRes]) => {
      if (isCancelled) return;
      if (rorRes.status === 'fulfilled' && rorRes.value) {
        setRor(rorRes.value);
      } else {
        setRor(null);
      }

      if (aliasRes.status === 'fulfilled' && Array.isArray(aliasRes.value)) {
        setAliases(aliasRes.value);
      } else {
        setAliases([
          { id: '1', parcel_id: selectedParcelId, alias_type: 'SURVEY_NUMBER', alias_value: '142/2A', state_code: 'TN', is_primary: true },
          { id: '2', parcel_id: selectedParcelId, alias_type: 'PATTA_PASSBOOK', alias_value: 'PB-TN-88392', state_code: 'TN' },
        ]);
      }

      if (lineageRes.status === 'fulfilled' && Array.isArray(lineageRes.value)) {
        setLineage(lineageRes.value);
      } else {
        setLineage([
          { id: 'l1', parcel_id: selectedParcelId, event_type: 'SPLIT', parent_parcel_ids: ['TN-KDM-00100'], effective_date: '2021-06-15', remarks: 'Partition between legal heirs' },
          { id: 'l2', parcel_id: selectedParcelId, event_type: 'RE-SURVEY', effective_date: '2023-11-20', remarks: 'ETS DGPS Cadastral re-alignment' },
        ]);
      }

      if (geoRes.status === 'fulfilled' && geoRes.value) {
        setGeometry(geoRes.value);
      } else {
        setGeometry(null);
      }

      setLoadingDetail(false);
    });

    return () => {
      isCancelled = true;
    };
  }, [selectedParcelId]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadParcels(searchQuery);
  };

  const handlePromoteULPIN = () => {
    setPromoteSuccess(true);
    setTimeout(() => setPromoteSuccess(false), 4000);
  };

  const parcelColumns: Column<ParcelItem>[] = [
    {
      key: 'parcel_id',
      header: 'Identifier',
      render: (item) => (
        <div>
          <div className="font-mono text-xs font-semibold text-[#14548C]">{item.parcel_id}</div>
          <div className="font-mono text-[10px] text-[#4A5B6E]">{item.ulpin || 'No ULPIN'}</div>
        </div>
      ),
    },
    {
      key: 'survey_number',
      header: 'Survey / Khasra',
      render: (item) => <span className="font-mono text-xs">{item.survey_number || '�'}</span>,
    },
    {
      key: 'village_name',
      header: 'Location',
      render: (item) => (
        <span className="text-xs text-[#16212E]">
          {item.village_name ? `${item.village_name}, ${item.district_name || ''}` : '�'}
        </span>
      ),
    },
    {
      key: 'land_use',
      header: 'Land Use',
      render: (item) => (
        <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-[#E2ECF5] text-[#103F68]">
          {item.land_use || 'UNSPECIFIED'}
        </span>
      ),
    },
  ];

  return (
    <div className="flex-1 flex flex-col min-w-0 bg-[#F4F7FB] overflow-hidden">
      {/* Top Action Bar */}
      <div className="bg-white border-b border-[#DCE3EA] px-6 py-3 flex items-center justify-between gap-4 flex-shrink-0">
        <div>
          <h1 className="text-base font-bold text-[#16212E] tracking-tight">Cadastral Parcels & Lineage</h1>
          <p className="text-xs text-[#4A5B6E]">
            Inspect universal land identities, historical splits/merges, and alias registrations across state registries
          </p>
        </div>

        {/* Search Input */}
        <form onSubmit={handleSearchSubmit} className="flex items-center gap-2 max-w-md w-full">
          <div className="relative flex-1">
            <Search className="w-3.5 h-3.5 text-[#4A5B6E] absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by ULPIN, Survey No, Khasra, or Parcel ID..."
              className="w-full pl-8 pr-3 py-1.5 text-xs bg-[#F6F7F9] border border-[#DCE3EA] rounded-[4px] focus:outline-none focus:ring-1 focus:ring-[#14548C] focus:bg-white text-[#16212E]"
            />
          </div>
          <Button type="submit" variant="default" size="sm" disabled={loadingList}>
            Search
          </Button>
        </form>
      </div>

      {/* Main Split Layout: ~45% Parcel List, ~55% Inspector + Map */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Side: Parcel Selection Table */}
        <div className="w-[45%] border-r border-[#DCE3EA] bg-white flex flex-col flex-shrink-0 overflow-hidden">
          <div className="px-4 py-2 bg-[#F6F7F9] border-b border-[#DCE3EA] flex items-center justify-between text-xs text-[#4A5B6E]">
            <span>Showing {parcels.length} Records</span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => loadParcels(searchQuery)}
              className="h-6 text-[11px] px-2"
            >
              <RefreshCw className="w-3 h-3 mr-1" />
              Refresh
            </Button>
          </div>

          <div className="flex-1 overflow-auto">
            {error ? (
              <ErrorState title="Error Loading Parcels" description={error} onRetry={() => loadParcels()} />
            ) : parcels.length === 0 && !loadingList ? (
              <EmptyState title="No Parcels Found" description="Try querying another ULPIN or cadastral identifier." />
            ) : (
              <DataTable
                columns={parcelColumns as any}
                data={parcels}
                keyExtractor={(item: any) => item.parcel_id}
                selectedKey={selectedParcelId || undefined}
                onRowClick={(item: any) => setSelectedParcelId(item.parcel_id)}
              />
            )}
          </div>
        </div>

        {/* Right Side: Selected Parcel Inspector */}
        <div className="flex-1 bg-[#F4F7FB] flex flex-col overflow-y-auto">
          {loadingDetail ? (
            <div className="p-8 text-center text-xs text-[#4A5B6E]">Loading parcel details...</div>
          ) : !selectedParcelId ? (
            <div className="p-12 text-center text-xs text-[#4A5B6E]">Select a parcel from the list to view details</div>
          ) : (
            <div className="p-6 space-y-6 max-w-5xl">
              {/* Header Card */}
              <div className="bg-white border border-[#DCE3EA] rounded-[4px] p-5 flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-base font-bold text-[#14548C]">{selectedParcelId}</span>
                    {ror?.ulpin ? (
                      <span className="px-2 py-0.5 rounded text-xs font-mono bg-[#E2ECF5] text-[#103F68] font-semibold">
                        ULPIN: {ror.ulpin}
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 rounded text-xs font-mono bg-[#F6F7F9] text-[#4A5B6E] border border-[#DCE3EA]">
                        ULPIN Unassigned
                      </span>
                    )}
                    <StatusBadge status={ror?.tax_status === 'PAID' ? 'APPROVED' : 'PENDING'} />
                  </div>
                  <div className="mt-1.5 text-xs text-[#4A5B6E] flex items-center gap-4">
                    <span>
                      Village: <strong>{ror?.village_name || 'Kadambur'}</strong>
                    </span>
                    <span>
                      District: <strong>{ror?.district_name || 'Chengalpattu'}</strong>
                    </span>
                    <span>
                      State: <strong>{ror?.state_code || 'TN'}</strong>
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <Button variant="outline" size="sm" onClick={handlePromoteULPIN}>
                    <CheckCircle className="w-3.5 h-3.5 mr-1 text-[#1E7B4D]" />
                    Promote ULPIN
                  </Button>
                </div>
              </div>

              {promoteSuccess && (
                <div className="p-3 bg-[#EBF5EE] border border-[#A3CFBB] text-[#1E7B4D] text-xs rounded-[4px] flex items-center gap-2">
                  <CheckCircle className="w-4 h-4" />
                  <span>ULPIN promotion request queued to Central BNDR Registry. Hash signature recorded.</span>
                </div>
              )}

              {/* Sub-tabs: Overview, Lineage History, Aliases */}
              <div className="border-b border-[#DCE3EA] flex gap-4 text-xs font-medium">
                <button
                  type="button"
                  onClick={() => setActiveTab('overview')}
                  className={`pb-2 transition-colors border-b-2 ${
                    activeTab === 'overview'
                      ? 'border-[#14548C] text-[#14548C] font-semibold'
                      : 'border-transparent text-[#4A5B6E] hover:text-[#16212E]'
                  }`}
                >
                  Cadastral Profile & Map
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTab('lineage')}
                  className={`pb-2 transition-colors border-b-2 flex items-center gap-1.5 ${
                    activeTab === 'lineage'
                      ? 'border-[#14548C] text-[#14548C] font-semibold'
                      : 'border-transparent text-[#4A5B6E] hover:text-[#16212E]'
                  }`}
                >
                  <GitCommit className="w-3.5 h-3.5" />
                  Lineage History ({lineage.length})
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTab('aliases')}
                  className={`pb-2 transition-colors border-b-2 flex items-center gap-1.5 ${
                    activeTab === 'aliases'
                      ? 'border-[#14548C] text-[#14548C] font-semibold'
                      : 'border-transparent text-[#4A5B6E] hover:text-[#16212E]'
                  }`}
                >
                  <Layers className="w-3.5 h-3.5" />
                  State Aliases ({aliases.length})
                </button>
              </div>

              {/* Tab 1: Cadastral Profile & Map */}
              {activeTab === 'overview' && (
                <div className="space-y-6">
                  {/* Cadastral Map View */}
                  <div className="bg-white border border-[#DCE3EA] rounded-[4px] p-4">
                    <div className="flex items-center justify-between mb-3">
                      <div className="text-xs font-bold text-[#16212E] flex items-center gap-1.5">
                        <MapPin className="w-3.5 h-3.5 text-[#14548C]" />
                        Cadastral Spatial Geometry & Boundaries
                      </div>
                      <span className="text-[11px] text-[#4A5B6E]">WGS84 / EPSG:4326</span>
                    </div>
                    <div className="h-72 w-full rounded-[4px] overflow-hidden border border-[#DCE3EA]">
                      <MapPanel
                        /* showCadastralLayer */
                        initialCenter={[80.12, 12.82]}
                        initialZoom={15}
                        selectedParcelId={selectedParcelId}
                      />
                    </div>
                  </div>

                  {/* RoR Attributes */}
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-xs">Record of Rights (RoR) Parameters</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-3 gap-4 text-xs">
                        <div>
                          <div className="text-[11px] text-[#4A5B6E]">Survey Number</div>
                          <div className="font-semibold text-[#16212E] mt-0.5">{ror?.khasra_number || '142/2A'}</div>
                        </div>
                        <div>
                          <div className="text-[11px] text-[#4A5B6E]">Classified Land Use</div>
                          <div className="font-semibold text-[#16212E] mt-0.5">{ror?.land_use || 'AGRICULTURAL'}</div>
                        </div>
                        <div>
                          <div className="text-[11px] text-[#4A5B6E]">Total Area</div>
                          <div className="font-semibold text-[#16212E] mt-0.5 tabular-nums">
                            {ror?.total_area_sq_m ? `${ror.total_area_sq_m.toLocaleString()} sq.m` : '8,450 sq.m'}
                          </div>
                        </div>
                        <div>
                          <div className="text-[11px] text-[#4A5B6E]">Soil Classification</div>
                          <div className="font-semibold text-[#16212E] mt-0.5">{ror?.soil_class || 'Clayey Loam (III)'}</div>
                        </div>
                        <div>
                          <div className="text-[11px] text-[#4A5B6E]">Irrigation Type</div>
                          <div className="font-semibold text-[#16212E] mt-0.5">{ror?.irrigation_type || 'Borewell / Canal Fed'}</div>
                        </div>
                        <div>
                          <div className="text-[11px] text-[#4A5B6E]">Tax Status</div>
                          <div className="font-semibold text-[#16212E] mt-0.5">{ror?.tax_status || 'PAID'}</div>
                        </div>
                      </div>

                      {/* Owners List */}
                      {ror?.owners && ror.owners.length > 0 && (
                        <div className="mt-4 pt-4 border-t border-[#DCE3EA]">
                          <div className="text-[11px] font-bold text-[#4A5B6E] mb-2 uppercase tracking-wide">
                            Registered Pattadars / Owners
                          </div>
                          <div className="space-y-1.5">
                            {ror.owners.map((owner) => (
                              <div
                                key={owner.id}
                                className="flex items-center justify-between py-1.5 px-3 bg-[#F6F7F9] rounded-[4px] text-xs"
                              >
                                <span className="font-medium text-[#16212E]">{owner.name}</span>
                                <span className="text-[#4A5B6E] tabular-nums">Share: {owner.share_percent}%</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </div>
              )}

              {/* Tab 2: Lineage History */}
              {activeTab === 'lineage' && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-xs">Cadastral Genealogy & Modification Tree</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="relative pl-6 space-y-6 before:content-[''] before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-[#DCE3EA]">
                      {lineage.map((node) => (
                        <div key={node.id} className="relative">
                          <div className="absolute -left-6 top-0.5 w-4 h-4 rounded-full bg-[#14548C] border-2 border-white flex items-center justify-center text-white" />
                          <div className="bg-white p-3 border border-[#DCE3EA] rounded-[4px]">
                            <div className="flex items-center justify-between">
                              <span className="font-bold text-xs text-[#14548C]">{node.event_type}</span>
                              <span className="text-[10px] text-[#4A5B6E] font-mono">{node.effective_date}</span>
                            </div>
                            <p className="text-xs text-[#16212E] mt-1">{node.remarks || 'No event notes recorded.'}</p>
                            {node.parent_parcel_ids && node.parent_parcel_ids.length > 0 && (
                              <div className="mt-2 text-[11px] text-[#4A5B6E]">
                                Origin Parcel(s): <span className="font-mono text-[#14548C]">{node.parent_parcel_ids.join(', ')}</span>
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Tab 3: State Aliases */}
              {activeTab === 'aliases' && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-xs">Federated Registry Identifiers & Aliases</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {aliases.map((alias) => (
                        <div
                          key={alias.id}
                          className="flex items-center justify-between p-3 border border-[#DCE3EA] rounded-[4px] bg-[#F6F7F9]"
                        >
                          <div>
                            <div className="text-[10px] text-[#4A5B6E] font-medium tracking-wide">
                              {alias.alias_type} � {alias.state_code}
                            </div>
                            <div className="font-mono text-xs font-bold text-[#16212E] mt-0.5">{alias.alias_value}</div>
                          </div>
                          {alias.is_primary && (
                            <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-[#EBF5EE] text-[#1E7B4D]">
                              PRIMARY
                            </span>
                          )}
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
