'use client';

import * as React from 'react';
import { Card, CardHeader, CardTitle, CardContent, Button, DataTable, StatusBadge, Column } from '@bhoomi/ui';
import { OnboardedStateItem } from '@bhoomi/api-client';
import { RefreshCw, Play, Check } from 'lucide-react';

export interface StatesTabProps {
  states: OnboardedStateItem[];
  onTriggerSync: (code: string, dept: string) => void;
  onRunConformance: (code: string) => void;
  syncingState: string | null;
  runningConformanceState: string | null;
}

export function StatesTab({
  states,
  onTriggerSync,
  onRunConformance,
  syncingState,
  runningConformanceState,
}: StatesTabProps) {
  const stateColumns: Column<OnboardedStateItem>[] = [
    {
      key: 'name',
      header: 'State & Registry System',
      render: (item) => (
        <div>
          <div className="font-bold text-xs text-[#14548C]">{item.name}</div>
          <div className="text-[10px] text-[#4A5B6E]">Code: {item.code} • Onboarded: {item.onboarded_date}</div>
        </div>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      render: (item) => <StatusBadge status={item.status} />,
    },
    {
      key: 'parcels_ingested',
      header: 'Parcels Ingested',
      isNumeric: true,
      render: (item) => (
        <span className="font-mono text-xs tabular-nums font-semibold text-[#16212E]">
          {item.parcels_ingested.toLocaleString()}
        </span>
      ),
    },
    {
      key: 'conformance_score',
      header: 'Conformance',
      isNumeric: true,
      render: (item) => (
        <div className="flex items-center gap-2">
          <div className="w-16 bg-[#DCE3EA] rounded-full h-1.5 overflow-hidden">
            <div
              className={`h-full ${item.conformance_score >= 90 ? 'bg-[#1E7B4D]' : 'bg-[#B8720B]'}`}
              style={{ width: `${item.conformance_score}%` }}
            />
          </div>
          <span className="font-mono text-xs tabular-nums font-bold text-[#16212E]">
            {item.conformance_score}%
          </span>
        </div>
      ),
    },
    {
      key: 'actions',
      header: 'Operations',
      render: (item) => (
        <div className="flex items-center gap-1.5">
          <Button
            variant="outline"
            size="sm"
            disabled={syncingState === item.code}
            onClick={() => onTriggerSync(item.code, 'REVENUE')}
            className="h-7 text-[11px] px-2"
          >
            <RefreshCw className={`w-3 h-3 mr-1 ${syncingState === item.code ? 'animate-spin' : ''}`} />
            Sync
          </Button>
          <Button
            variant="outline"
            size="sm"
            disabled={runningConformanceState === item.code}
            onClick={() => onRunConformance(item.code)}
            className="h-7 text-[11px] px-2"
          >
            <Play className="w-3 h-3 mr-1 text-[#14548C]" />
            Test
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-sm">Federated State Registries</CardTitle>
            <p className="text-xs text-[#4A5B6E] mt-0.5">
              Monitoring interoperability APIs, real-time database sync, and OGC/BNDR standard compliance
            </p>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <DataTable
            columns={stateColumns}
            data={states}
            keyExtractor={(item) => item.code}
          />
        </CardContent>
      </Card>

      {/* Conformance Requirements Box */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">National Conformance Checklist (DoLR Standard PS-26014)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
            <div className="p-3 bg-white border border-[#DCE3EA] rounded-[4px] space-y-1">
              <div className="flex items-center gap-1.5 font-bold text-[#1E7B4D]">
                <Check className="w-4 h-4" />
                <span>OGC WFS 2.0 / WMS 1.3</span>
              </div>
              <p className="text-[11px] text-[#4A5B6E]">
                Vector tile serving and spatial coordinate reference system EPSG:4326 verified.
              </p>
            </div>
            <div className="p-3 bg-white border border-[#DCE3EA] rounded-[4px] space-y-1">
              <div className="flex items-center gap-1.5 font-bold text-[#1E7B4D]">
                <Check className="w-4 h-4" />
                <span>ULPIN 14-digit Standard</span>
              </div>
              <p className="text-[11px] text-[#4A5B6E]">
                Centroid-based spatial geohash encoding with ISO sub-division schema.
              </p>
            </div>
            <div className="p-3 bg-white border border-[#DCE3EA] rounded-[4px] space-y-1">
              <div className="flex items-center gap-1.5 font-bold text-[#1E7B4D]">
                <Check className="w-4 h-4" />
                <span>BNDR Schema Mapping</span>
              </div>
              <p className="text-[11px] text-[#4A5B6E]">
                RoR fields, mutation types, and encumbrance certificates mapped to national schema.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}