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

      {/* ── STATE DIVERSITY SHOWCASE: TAMIL NADU (RURAL) VS CHANDIGARH (URBAN) ── */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <div>
            <CardTitle className="text-sm flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-[#14548C]" />
              State Diversity & Schema Transformation Showcase (PS-26014 Scale Test)
            </CardTitle>
            <p className="text-xs text-[#4A5B6E] mt-0.5">
              Demonstrating ISO 19152 India Profile interoperability: Tamil Nadu (Rural Revenue) vs Chandigarh (Urban Local Body)
            </p>
          </div>
          <span className="text-[10px] font-bold bg-[#E2ECF5] text-[#14548C] px-2.5 py-1 rounded">
            Two Contrasting Jurisdictions Harmonized
          </span>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto border border-[#DCE3EA] rounded-md">
            <table className="w-full text-xs text-left">
              <thead className="bg-[#F8FAFC] border-b border-[#DCE3EA] text-[#4A5B6E] text-[11px] uppercase tracking-wider">
                <tr>
                  <th className="py-2.5 px-3 font-bold">Interoperability Dimension</th>
                  <th className="py-2.5 px-3 font-bold text-[#14548C]">Tamil Nadu (Rural Revenue · Tamil Nilam)</th>
                  <th className="py-2.5 px-3 font-bold text-[#0F766E]">Chandigarh (Urban Local Body · Estate / MCL)</th>
                  <th className="py-2.5 px-3 font-bold text-[#16212E]">BNDR Canonical Standard (ISO 19152)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E2E8F0] text-[11px]">
                <tr className="hover:bg-[#F8FAFC]">
                  <td className="py-2 px-3 font-bold text-[#16212E]">Administrative Hierarchy</td>
                  <td className="py-2 px-3 text-[#4A5B6E]">State → District → Taluk → Revenue Village</td>
                  <td className="py-2 px-3 text-[#4A5B6E]">UT → Municipal Ward → Sector → Block</td>
                  <td className="py-2 px-3 font-mono font-semibold text-[#14548C]">lgd_hierarchy: revenue | urban_local_body</td>
                </tr>
                <tr className="hover:bg-[#F8FAFC]">
                  <td className="py-2 px-3 font-bold text-[#16212E]">Primary Parcel Identifier</td>
                  <td className="py-2 px-3 text-[#4A5B6E]">Survey No (42/1B) + Patta No (1042)</td>
                  <td className="py-2 px-3 text-[#4A5B6E]">Municipal PID (PID-17-A12) + Plot / SCO No</td>
                  <td className="py-2 px-3 font-mono font-semibold text-[#14548C]">ulpin (14-char) + aliases[] mapping</td>
                </tr>
                <tr className="hover:bg-[#F8FAFC]">
                  <td className="py-2 px-3 font-bold text-[#16212E]">Land Tenure Model</td>
                  <td className="py-2 px-3 text-[#4A5B6E]">Ryotwari (Private) / Poramboke (Govt Commons)</td>
                  <td className="py-2 px-3 text-[#4A5B6E]">Freehold / 99-Year Leasehold / Perpetual Lease</td>
                  <td className="py-2 px-3 font-mono font-semibold text-[#14548C]">LA_RRR: right_type & restriction_type</td>
                </tr>
                <tr className="hover:bg-[#F8FAFC]">
                  <td className="py-2 px-3 font-bold text-[#16212E]">Land Classification</td>
                  <td className="py-2 px-3 text-[#4A5B6E]">Nanjai (Wet) / Punjai (Dry) / Manavari</td>
                  <td className="py-2 px-3 text-[#4A5B6E]">Commercial SCO / SCF / Industrial / Booth</td>
                  <td className="py-2 px-3 font-mono font-semibold text-[#14548C]">bndr_land_use: 24 unified classes</td>
                </tr>
                <tr className="hover:bg-[#F8FAFC]">
                  <td className="py-2 px-3 font-bold text-[#16212E]">Native Area Units</td>
                  <td className="py-2 px-3 text-[#4A5B6E]">Hectares, Ares, and Cents (1 cent = 40.46 m²)</td>
                  <td className="py-2 px-3 text-[#4A5B6E]">Square Yards (Gaj) and Marla (1 marla = 25.29 m²)</td>
                  <td className="py-2 px-3 font-mono font-semibold text-[#14548C]">area_sq_m (normalized WGS84 ST_Area)</td>
                </tr>
                <tr className="hover:bg-[#F8FAFC]">
                  <td className="py-2 px-3 font-bold text-[#16212E]">Spatial Survey Provenance</td>
                  <td className="py-2 px-3 text-[#4A5B6E]">Digitized 1968 FMB Scans (Accuracy Class D)</td>
                  <td className="py-2 px-3 text-[#4A5B6E]">SVAMITVA Drone LiDAR 2023 (Accuracy Class A)</td>
                  <td className="py-2 px-3 font-mono font-semibold text-[#14548C]">accuracy_class: A | B | C | D</td>
                </tr>
              </tbody>
            </table>
          </div>
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