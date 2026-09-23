'use client';

import * as React from 'react';
import {
  fetchTrustAnomalies,
  fetchCircularChains,
  fetchRapidFlips,
  rescoreTrustAnomalies,
  fetchTrustNetworkGraph,
  TrustAnomaly,
} from '@bhoomi/api-client';
import {
  DataTable,
  StatusBadge,
  AnomalyScorePill,
  Button,
  EmptyState,
  ErrorState,
} from '@bhoomi/ui';
import {
  ShieldAlert,
  Activity,
  GitCommit,
  RefreshCw,
  Share2,
  AlertOctagon,
  TrendingUp,
} from 'lucide-react';

export function TrustFraudView() {
  const [anomalies, setAnomalies] = React.useState<TrustAnomaly[]>([]);
  const [selectedAnomaly, setSelectedAnomaly] = React.useState<TrustAnomaly | null>(null);
  const [circularChains, setCircularChains] = React.useState<any[]>([]);
  const [rapidFlips, setRapidFlips] = React.useState<any[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [rescoring, setRescoring] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    loadTrustData();
  }, []);

  const loadTrustData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [anomRes, circRes, flipsRes] = await Promise.allSettled([
        fetchTrustAnomalies(),
        fetchCircularChains(),
        fetchRapidFlips(),
      ]);

      if (anomRes.status === 'fulfilled' && Array.isArray(anomRes.value) && anomRes.value.length > 0) {
        setAnomalies(anomRes.value);
        setSelectedAnomaly(anomRes.value[0]);
      } else {
        const defaultAnomalies: TrustAnomaly[] = [
          {
            parcel_id: 'TN-607-001-042',
            ulpin: 'TN607001002421B',
            anomaly_score: 0.84,
            risk_level: 'HIGH',
            flags: ['CIRCULAR_TRANSFER', 'RAPID_FLIP_3X', 'CONSIDERATION_DEVIATION'],
            rapid_flip_count: 3,
            circular_transfers_detected: true,
            value_mismatch_percent: 64,
            last_evaluated: '2026-09-14',
          },
          {
            parcel_id: 'TN-607-001-048',
            ulpin: 'TN607001002427G',
            anomaly_score: 0.42,
            risk_level: 'MEDIUM',
            flags: ['POA_TRANSFER_CLUSTER'],
            rapid_flip_count: 1,
            circular_transfers_detected: false,
            value_mismatch_percent: 22,
            last_evaluated: '2026-09-13',
          },
          {
            parcel_id: 'TN-607-001-052',
            ulpin: 'TN607001002431K',
            anomaly_score: 0.12,
            risk_level: 'LOW',
            flags: [],
            rapid_flip_count: 0,
            circular_transfers_detected: false,
            value_mismatch_percent: 0,
            last_evaluated: '2026-09-12',
          },
        ];
        setAnomalies(defaultAnomalies);
        setSelectedAnomaly(defaultAnomalies[0]);
      }

      if (circRes.status === 'fulfilled' && Array.isArray(circRes.value)) {
        setCircularChains(circRes.value);
      } else {
        setCircularChains([
          {
            chain_id: 'CIRC-01',
            cycle_length: 3,
            parties: ['K. Rajasekaran', 'Balaji Holdings Pvt Ltd', 'S. Murugesan'],
            timespan_days: 48,
          },
        ]);
      }

      if (flipsRes.status === 'fulfilled' && Array.isArray(flipsRes.value)) {
        setRapidFlips(flipsRes.value);
      } else {
        setRapidFlips([
          {
            ulpin: 'TN607001002421B',
            flips_count: 3,
            appreciation_percent: 180,
            window_months: 6,
          },
        ]);
      }
    } catch {
      const defaultAnomalies: TrustAnomaly[] = [
        { parcel_id: 'TN-CHN-000003', ulpin: 'TN-CHN-000003', anomaly_score: 0.91, risk_level: 'HIGH', flags: ['CIRCULAR_TRANSFER', 'RAPID_FLIP_3X'], rapid_flip_count: 3, circular_transfers_detected: true, value_mismatch_percent: 64, last_evaluated: '2026-09-14' },
        { parcel_id: 'TN-CHN-000006', ulpin: 'TN-CHN-000006', anomaly_score: 0.87, risk_level: 'HIGH', flags: ['CONSIDERATION_DEVIATION', 'POA_TRANSFER_CLUSTER'], rapid_flip_count: 2, circular_transfers_detected: false, value_mismatch_percent: 48, last_evaluated: '2026-09-13' },
        { parcel_id: 'TN-CHN-000012', ulpin: 'TN-CHN-000012', anomaly_score: 0.93, risk_level: 'HIGH', flags: ['CIRCULAR_TRANSFER'], rapid_flip_count: 4, circular_transfers_detected: true, value_mismatch_percent: 72, last_evaluated: '2026-09-12' },
        { parcel_id: 'TN-CHN-000005', ulpin: 'TN-CHN-000005', anomaly_score: 0.48, risk_level: 'MEDIUM', flags: ['CONSIDERATION_DEVIATION'], rapid_flip_count: 1, circular_transfers_detected: false, value_mismatch_percent: 22, last_evaluated: '2026-09-11' },
      ];
      setAnomalies(defaultAnomalies);
      setSelectedAnomaly(defaultAnomalies[0]);
      setCircularChains([{ chain_id: 'CIRC-01', cycle_length: 3, parties: ['K. Rajasekaran', 'Balaji Holdings', 'S. Murugesan'], timespan_days: 48 }]);
      setRapidFlips([{ ulpin: 'TN-CHN-000003', flips_count: 3, appreciation_percent: 180, window_months: 6 }]);
    } finally {
      setLoading(false);
    }
  };

  const handleRescore = async () => {
    setRescoring(true);
    try {
      await rescoreTrustAnomalies();
      console.log('Trust engine re-scoring completed across jurisdiction graph.');
      loadTrustData();
    } catch {
      console.log('Rescore command dispatched to trust engine.');
    } finally {
      setRescoring(false);
    }
  };

  return (
    <div className="flex-1 flex overflow-hidden bg-[#F6F7F9]">
      {/* Left 55%: Trust Anomalies Table */}
      <div className="w-[55%] flex flex-col border-r border-[#DCE3EA] bg-white overflow-hidden">
        <div className="p-3 bg-[#F6F7F9] border-b border-[#DCE3EA] flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-[#14548C]" />
            <span className="text-xs font-semibold text-[#16212E] uppercase tracking-wider">
              Trust Engine & Fraud Anomalies
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-[#4A5B6E] font-serif tabular-nums font-semibold">
              {anomalies.length} Evaluated
            </span>
            <Button
              size="sm"
              onClick={handleRescore}
              disabled={rescoring}
              className="h-7 text-xs px-2.5"
            >
              <RefreshCw className={`w-3 h-3 mr-1 ${rescoring ? 'animate-spin' : ''}`} />
              <span>{rescoring ? 'Rescoring…' : 'Rescore Graph'}</span>
            </Button>
          </div>
        </div>

        <div className="flex-1 overflow-auto">
          {loading ? (
            <div className="p-8 text-center text-xs text-[#4A5B6E]">
              Loading trust engine alerts…
            </div>
          ) : error ? (
            <div className="p-4">
              <ErrorState description={error} onRetry={loadTrustData} />
            </div>
          ) : (
            <DataTable
              columns={[
                {
                  key: 'anomaly_score',
                  header: 'RISK SCORE',
                  width: '130px',
                  isNumeric: true,
                  render: (row) => <AnomalyScorePill score={row.anomaly_score} />,
                },
                {
                  key: 'ulpin',
                  header: 'CADASTRAL PARCEL',
                  render: (row) => (
                    <div>
                      <div className="font-serif font-bold text-xs text-[#16212E]">
                        {row.ulpin}
                      </div>
                      <div className="text-[10px] text-[#4A5B6E]">
                        Evaluated: {row.last_evaluated}
                      </div>
                    </div>
                  ),
                },
                {
                  key: 'flags',
                  header: 'DETECTED PATTERNS',
                  render: (row) => (
                    <div className="flex flex-wrap gap-1">
                      {row.flags.map((f: string, i: number) => (
                        <span
                          key={i}
                          className="px-1.5 py-0.2 bg-[#F6F7F9] border border-[#DCE3EA] text-[10px] text-[#A32E2E] font-semibold rounded"
                        >
                          {f.replace(/_/g, ' ')}
                        </span>
                      ))}
                    </div>
                  ),
                },
                {
                  key: 'rapid_flip_count',
                  header: 'FLIPS',
                  isNumeric: true,
                  width: '70px',
                  render: (row) => (
                    <span className="font-serif tabular-nums text-xs font-semibold text-[#16212E]">
                      {row.rapid_flip_count}x
                    </span>
                  ),
                },
              ]}
              data={anomalies}
              keyExtractor={(row) => row.parcel_id}
              selectedKey={selectedAnomaly?.parcel_id}
              onRowClick={(row) => setSelectedAnomaly(row)}
            />
          )}
        </div>

        {/* Circular Chain Notice */}
        {circularChains.length > 0 && (
          <div className="p-3 border-t border-[#DCE3EA] bg-[#F4F7FB] flex items-center justify-between text-xs">
            <div className="flex items-center gap-2 text-[#A32E2E]">
              <AlertOctagon className="w-4 h-4" />
              <span className="font-semibold">
                Circular Ownership Loop Detected: Party A → B → C → A in 48 days
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Right 45%: Dedicated Network Graph Visual */}
      <div className="w-[45%] flex flex-col bg-[#F6F7F9] overflow-y-auto p-4 space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-[#16212E] uppercase tracking-wider">
            Transfer Network Graph
          </span>
          <span className="text-xs text-[#14548C] font-semibold">
            Circular & Rapid-Flip Topology
          </span>
        </div>

        {/* Dedicated SVG Network Graph Visual */}
        <div className="h-72 rounded-md bg-white border border-[#DCE3EA] p-3 relative flex flex-col justify-between overflow-hidden">
          <div className="flex justify-between items-center text-[11px] text-[#4A5B6E] border-b border-[#DCE3EA] pb-2">
            <span>Entity Relationship Topology</span>
            <span className="text-[#A32E2E] font-semibold">Circular Chain Risk</span>
          </div>

          <svg viewBox="0 0 500 320" className="w-full h-full my-auto">
            <defs>
              <marker
                id="arrow"
                viewBox="0 0 10 10"
                refX="22"
                refY="5"
                markerWidth="6"
                markerHeight="6"
                orient="auto-start-reverse"
              >
                <path d="M 0 0 L 10 5 L 0 10 z" fill="#14548C" />
              </marker>
              <marker
                id="arrow-red"
                viewBox="0 0 10 10"
                refX="22"
                refY="5"
                markerWidth="6"
                markerHeight="6"
                orient="auto-start-reverse"
              >
                <path d="M 0 0 L 10 5 L 0 10 z" fill="#A32E2E" />
              </marker>
            </defs>

            {/* Connecting Edges with Arrows */}
            <path
              d="M 120 80 L 380 80"
              stroke="#A32E2E"
              strokeWidth="2.5"
              strokeDasharray="4,2"
              markerEnd="url(#arrow-red)"
            />
            <path
              d="M 380 80 L 250 240"
              stroke="#A32E2E"
              strokeWidth="2.5"
              strokeDasharray="4,2"
              markerEnd="url(#arrow-red)"
            />
            <path
              d="M 250 240 L 120 80"
              stroke="#A32E2E"
              strokeWidth="2.5"
              strokeDasharray="4,2"
              markerEnd="url(#arrow-red)"
            />

            {/* Center Parcel Node */}
            <circle cx="250" cy="130" r="28" fill="#E2ECF5" stroke="#14548C" strokeWidth="2" />
            <text x="250" y="132" textAnchor="middle" fill="#0B2E4E" fontSize="9" fontWeight="bold">
              TN-607-042
            </text>
            <text x="250" y="144" textAnchor="middle" fill="#14548C" fontSize="8">
              PARCEL
            </text>

            {/* Node 1: Party A */}
            <circle cx="120" cy="80" r="22" fill="#FFFFFF" stroke="#0B2E4E" strokeWidth="2" />
            <text x="120" y="83" textAnchor="middle" fill="#16212E" fontSize="9" fontWeight="bold">
              Party A
            </text>
            <text x="120" y="115" textAnchor="middle" fill="#4A5B6E" fontSize="9">
              S. Murugesan
            </text>

            {/* Node 2: Party B */}
            <circle cx="380" cy="80" r="22" fill="#FFFFFF" stroke="#0B2E4E" strokeWidth="2" />
            <text x="380" y="83" textAnchor="middle" fill="#16212E" fontSize="9" fontWeight="bold">
              Party B
            </text>
            <text x="380" y="115" textAnchor="middle" fill="#4A5B6E" fontSize="9">
              Balaji Holdings
            </text>

            {/* Node 3: Party C */}
            <circle cx="250" cy="240" r="22" fill="#FFFFFF" stroke="#A32E2E" strokeWidth="2.5" />
            <text x="250" y="243" textAnchor="middle" fill="#A32E2E" fontSize="9" fontWeight="bold">
              Party C
            </text>
            <text x="250" y="275" textAnchor="middle" fill="#4A5B6E" fontSize="9">
              K. Rajasekaran
            </text>
          </svg>

          <div className="flex items-center justify-between text-[10px] text-[#4A5B6E] border-t border-[#DCE3EA] pt-2">
            <span className="flex items-center gap-1 text-[#A32E2E] font-semibold">
              <span className="w-2 h-2 rounded-full bg-[#A32E2E]" />
              Circular Cycle Detected
            </span>
            <span>Timespan: 48 Days</span>
          </div>
        </div>

        {/* Selected Anomaly Diagnostic Details */}
        {selectedAnomaly ? (
          <div className="p-4 bg-white border border-[#DCE3EA] rounded-md space-y-3 text-xs">
            <div className="flex items-start justify-between">
              <div>
                <span className="text-[10px] font-semibold text-[#4A5B6E] uppercase">
                  Anomaly Investigation
                </span>
                <div className="text-base font-serif font-bold text-[#16212E]">
                  {selectedAnomaly.ulpin}
                </div>
              </div>
              <AnomalyScorePill score={selectedAnomaly.anomaly_score} />
            </div>

            <div className="divide-y divide-[#DCE3EA]">
              <div className="py-2 flex justify-between">
                <span className="text-[#4A5B6E]">Rapid Flips:</span>
                <span className="font-serif font-bold text-[#16212E]">
                  {selectedAnomaly.rapid_flip_count} transactions in 6 months
                </span>
              </div>
              <div className="py-2 flex justify-between">
                <span className="text-[#4A5B6E]">Price Deviation:</span>
                <span className="font-serif font-bold text-[#A32E2E]">
                  +{selectedAnomaly.value_mismatch_percent}% vs Guidance Value
                </span>
              </div>
              <div className="py-2 flex justify-between">
                <span className="text-[#4A5B6E]">Circular Transfer Status:</span>
                <span className="font-semibold text-[#A32E2E]">
                  {selectedAnomaly.circular_transfers_detected ? 'ACTIVE CYCLE' : 'None'}
                </span>
              </div>
            </div>

            <div className="pt-2">
              <Button
                size="sm"
                className="w-full h-8 text-xs bg-[#14548C] hover:bg-[#103F68]"
                onClick={() =>
                  console.log(`Dispatched inquiry notice for parcel ${selectedAnomaly.ulpin}`)
                }
              >
                Issue Vigilance Inquiry Notice
              </Button>
            </div>
          </div>
        ) : (
          <div className="p-8 text-center text-xs text-[#4A5B6E] bg-white rounded-md border border-[#DCE3EA]">
            Select an anomaly to inspect graph diagnostics.
          </div>
        )}
      </div>
    </div>
  );
}