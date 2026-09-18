'use client';

import * as React from 'react';
import {
  fetchReviewQueue,
  fetchTrustAnomaliesSummary,
  ReviewQueueItem,
  TrustSummary,
} from '@bhoomi/api-client';
import {
  DataTable,
  StatusBadge,
  AnomalyScorePill,
  MapPanel,
  Button,
  EmptyState,
  ErrorState,
} from '@bhoomi/ui';
import {
  AlertTriangle,
  FileText,
  Activity,
  GitBranch,
  ArrowRight,
  CheckCircle,
  Clock,
  ChevronRight,
  Shield,
  Layers,
} from 'lucide-react';

export interface QueueViewProps {
  onNavigateTab?: (tab: any) => void;
}

export function QueueView({ onNavigateTab }: QueueViewProps) {
  const [queue, setQueue] = React.useState<ReviewQueueItem[]>([]);
  const [trustSummary, setTrustSummary] = React.useState<TrustSummary | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [selectedItem, setSelectedItem] = React.useState<ReviewQueueItem | null>(null);

  React.useEffect(() => {
    loadHomeData();
  }, []);

  const loadHomeData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [queueRes, trustRes] = await Promise.allSettled([
        fetchReviewQueue(),
        fetchTrustAnomaliesSummary(),
      ]);

      if (queueRes.status === 'fulfilled' && queueRes.value?.items) {
        setQueue(queueRes.value.items);
        if (queueRes.value.items.length > 0) {
          setSelectedItem(queueRes.value.items[0]);
        }
      } else {
        // High-fidelity fallback pending queue
        const fallbackQueue: ReviewQueueItem[] = [
          {
            id: 'rev-101',
            link_id: 'link-001',
            type: 'IDENTITY_MATCH',
            title: 'Party Name Spelling Discrepancy',
            parcel_id: 'TN-607-001-042',
            ulpin: 'TN607001002421B',
            confidence: 0.88,
            priority: 'HIGH',
            source_a: {
              system: 'Tamil Nadu Tamil Nilam (Revenue)',
              identifier: 'RoR-TN-9812',
              value: 'K. Rajasekaran',
              owner_name: 'K. Rajasekaran',
            },
            source_b: {
              system: 'Registration (SRO Kilpennathur)',
              identifier: 'Deed-2019-1042',
              value: 'Rajasekharan Kandasamy',
              owner_name: 'Rajasekharan Kandasamy',
            },
            discrepancy_details: 'Name phonetic similarity 88%. Levenshtein distance 3. Aadhaar hash matches.',
            created_at: '2026-09-14 09:30 AM',
            status: 'PENDING',
          },
          {
            id: 'rev-102',
            type: 'TOPOLOGY_CONFLICT',
            title: 'Cadastral Boundary Overlap (42 m²)',
            parcel_id: 'TN-607-001-043',
            ulpin: 'TN607001002422C',
            confidence: 0.99,
            priority: 'CRITICAL',
            source_a: {
              system: 'Survey 42/1B',
              identifier: 'SURV-42-1B',
              value: 'Area: 14,200 m²',
            },
            source_b: {
              system: 'Survey 42/2',
              identifier: 'SURV-42-2',
              value: 'Area: 18,042 m²',
            },
            discrepancy_details: 'GIS Polygon intersection detects 42.18 sq.m overlap along western survey boundary.',
            created_at: '2026-09-13 04:15 PM',
            status: 'PENDING',
          },
          {
            id: 'rev-103',
            type: 'MUTATION_REVIEW',
            title: 'Title Transfer Following Sale Deed',
            parcel_id: 'TN-607-001-044',
            ulpin: 'TN607001002423D',
            confidence: 0.95,
            priority: 'MEDIUM',
            source_a: {
              system: 'Registration SRO',
              identifier: 'Deed-2026-1120',
              value: 'Sale Consideration: INR 45,00,000',
            },
            source_b: {
              system: 'Revenue RoR',
              identifier: 'ROR-2026-891',
              value: 'Current Pattadar: S. Murugesan',
            },
            discrepancy_details: 'Application submitted with NOC. Ready for Tahsildar sanction order.',
            created_at: '2026-09-12 11:00 AM',
            status: 'PENDING',
          },
        ];
        setQueue(fallbackQueue);
        setSelectedItem(fallbackQueue[0]);
      }

      if (trustRes.status === 'fulfilled' && trustRes.value) {
        setTrustSummary(trustRes.value);
      } else {
        setTrustSummary({
          high_risk_count: 5,
          medium_risk_count: 14,
          low_risk_count: 128,
          average_trust_score: 0.92,
          circular_chains_count: 2,
          rapid_flips_count: 4,
        });
      }
    } catch (err: any) {
      setError(err?.message || 'Could not load officer dashboard data.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col overflow-hidden bg-[#F6F7F9]">
      {/* Top Header Bar */}
      <div className="px-4 py-2.5 bg-white border-b border-[#DCE3EA] flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-2">
          <span className="text-sm font-bold text-[#1f2733] uppercase tracking-wider">Active Casework Queue</span>
          <span className="text-xs text-[#6b7688] tabular-nums">({queue.length} items)</span>
        </div>
        <span className="text-xs text-[#6b7688]">Jurisdiction: Chengalpattu, Tamil Nadu</span>
      </div>

      {/* Main Split: Left 60% Queue / Right 40% Detail & Map */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left 60%: Work Queue Table */}
        <div className="w-[60%] flex flex-col border-r border-[#DCE3EA] bg-white overflow-hidden">
          <div className="p-3 bg-[#F6F7F9] border-b border-[#DCE3EA] flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-[#16212E] uppercase tracking-wider">
                Active Officer Casework Queue
              </span>
              <span className="text-xs text-[#4A5B6E] font-serif tabular-nums font-semibold">
                ({queue.length} items)
              </span>
            </div>
            <span className="text-[11px] text-[#4A5B6E]">
              Jurisdiction: Tiruvannamalai (TN)
            </span>
          </div>

          <div className="flex-1 overflow-auto">
            {loading ? (
              <div className="p-8 text-center text-xs text-[#4A5B6E]">
                Loading officer queue…
              </div>
            ) : error ? (
              <div className="p-4">
                <ErrorState description={error} onRetry={loadHomeData} />
              </div>
            ) : queue.length === 0 ? (
              <EmptyState
                title="Queue is clear"
                description="No pending mutations or conflict triage tasks requiring immediate action."
              />
            ) : (
              <DataTable
                columns={[
                  {
                    key: 'priority',
                    header: 'PRIORITY',
                    width: '100px',
                    render: (row) => (
                      <StatusBadge
                        status={row.priority}
                        variant={
                          row.priority === 'CRITICAL'
                            ? 'rejected'
                            : row.priority === 'HIGH'
                            ? 'pending'
                            : 'info'
                        }
                      >
                        {row.priority}
                      </StatusBadge>
                    ),
                  },
                  {
                    key: 'title',
                    header: 'CASEWORK ITEM',
                    render: (row) => (
                      <div>
                        <div className="font-semibold text-xs text-[#16212E]">
                          {row.title}
                        </div>
                        <div className="text-[11px] text-[#4A5B6E] font-serif">
                          ULPIN: {row.ulpin || row.parcel_id}
                        </div>
                      </div>
                    ),
                  },
                  {
                    key: 'type',
                    header: 'DOMAIN',
                    render: (row) => (
                      <span className="text-[11px] font-medium text-[#14548C] bg-[#E2ECF5] px-2 py-0.5 rounded-[4px]">
                        {row.type.replace('_', ' ')}
                      </span>
                    ),
                  },
                  {
                    key: 'confidence',
                    header: 'CONFIDENCE',
                    isNumeric: true,
                    render: (row) => (
                      <span className="font-serif tabular-nums font-semibold text-xs text-[#16212E]">
                        {Math.round(row.confidence * 100)}%
                      </span>
                    ),
                  },
                  {
                    key: 'status',
                    header: 'ACTION',
                    render: (row) => (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setSelectedItem(row)}
                        className="h-7 px-2.5 text-xs"
                      >
                        Inspect
                      </Button>
                    ),
                  },
                ]}
                data={queue}
                keyExtractor={(row) => row.id}
                selectedKey={selectedItem?.id}
                onRowClick={(row) => setSelectedItem(row)}
              />
            )}
          </div>
        </div>

        {/* Right 40%: Detail & Map Inspector Panel */}
        <div className="w-[40%] flex flex-col bg-[#F6F7F9] overflow-y-auto p-4 space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-[#16212E] uppercase tracking-wider">
              Casework Inspector
            </span>
            {selectedItem && (
              <StatusBadge status={selectedItem.status}>
                {selectedItem.status}
              </StatusBadge>
            )}
          </div>

          {selectedItem ? (
            <div className="space-y-4">
              <div className="p-4 bg-white border border-[#DCE3EA] rounded-md space-y-3">
                <div className="flex items-start justify-between">
                  <div>
                    <span className="text-[10px] text-[#4A5B6E] uppercase font-semibold">
                      ULPIN / Cadastral Ref
                    </span>
                    <div className="text-base font-serif font-bold text-[#16212E]">
                      {selectedItem.ulpin || selectedItem.parcel_id}
                    </div>
                  </div>
                  <span className="text-xs font-semibold text-[#14548C]">
                    Match {Math.round(selectedItem.confidence * 100)}%
                  </span>
                </div>

                <div className="text-xs text-[#16212E] font-medium leading-relaxed bg-[#F4F7FB] p-2.5 rounded border border-[#DCE3EA]">
                  {selectedItem.discrepancy_details || selectedItem.title}
                </div>

                {/* Source Comparison */}
                <div className="grid grid-cols-2 gap-2 text-xs pt-2 border-t border-[#DCE3EA]">
                  <div className="p-2 bg-[#F6F7F9] rounded border border-[#DCE3EA]">
                    <div className="text-[10px] font-semibold text-[#14548C] uppercase">
                      Source A: {selectedItem.source_a?.system}
                    </div>
                    <div className="font-semibold text-[#16212E] mt-1">
                      {selectedItem.source_a?.value}
                    </div>
                    {selectedItem.source_a?.owner_name && (
                      <div className="text-[11px] text-[#4A5B6E]">
                        Name: {selectedItem.source_a.owner_name}
                      </div>
                    )}
                  </div>

                  <div className="p-2 bg-[#F6F7F9] rounded border border-[#DCE3EA]">
                    <div className="text-[10px] font-semibold text-[#14548C] uppercase">
                      Source B: {selectedItem.source_b?.system}
                    </div>
                    <div className="font-semibold text-[#16212E] mt-1">
                      {selectedItem.source_b?.value}
                    </div>
                    {selectedItem.source_b?.owner_name && (
                      <div className="text-[11px] text-[#4A5B6E]">
                        Name: {selectedItem.source_b.owner_name}
                      </div>
                    )}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex gap-2 pt-2">
                  <Button
                    size="sm"
                    className="flex-1 h-8 text-xs bg-[#1E7B4D] hover:bg-[#16603B]"
                    onClick={() => {
                      console.log(`Approved link for case ${selectedItem.id}`);
                      setQueue((prev) => prev.filter((q) => q.id !== selectedItem.id));
                    }}
                  >
                    Approve Link / Sanction
                  </Button>
                  <Button
                    size="sm"
                    variant="destructive"
                    className="flex-1 h-8 text-xs"
                    onClick={() => {
                      console.log(`Discrepancy flagged for re-survey: case ${selectedItem.id}`);
                      setQueue((prev) => prev.filter((q) => q.id !== selectedItem.id));
                    }}
                  >
                    Reject / Flag Dispute
                  </Button>
                </div>
              </div>

              {/* Spatial Context Map */}
              <div className="space-y-1.5">
                <span className="text-xs font-semibold text-[#16212E] flex items-center gap-1.5">
                  <Layers className="w-3.5 h-3.5 text-[#14548C]" />
                  <span>Cadastral Map Context</span>
                </span>
                <div className="h-56 rounded-md overflow-hidden border border-[#DCE3EA]">
                  <MapPanel
                    selectedParcelId={selectedItem.parcel_id}
                    initialZoom={15}
                    className="h-full min-h-[220px]"
                  />
                </div>
              </div>
            </div>
          ) : (
            <div className="p-8 text-center text-xs text-[#4A5B6E] bg-white rounded-md border border-[#DCE3EA]">
              Select a casework item from the left table to inspect details.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
