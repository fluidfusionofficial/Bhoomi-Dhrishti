'use client';

import * as React from 'react';
import {
  BarChart3,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle2,
  Scale,
  FileCheck2,
  Layers,
  ShieldAlert,
  Users,
  MapPin,
  Clock,
  Building2,
  Printer,
} from 'lucide-react';

interface DistrictKPI {
  label: string;
  value: string;
  delta: string;
  trend: 'up' | 'down' | 'neutral';
  icon: React.ElementType;
  color: string;
  bgColor: string;
}

interface DepartmentStatus {
  department: string;
  pending: number;
  resolved_this_month: number;
  avg_turnaround_days: number;
  sla_compliance: number;
}

interface ConflictSummary {
  type: string;
  count: number;
  high_severity: number;
  trend: 'up' | 'down' | 'flat';
}

const DISTRICT_KPIS: DistrictKPI[] = [
  { label: 'Total Parcels', value: '15,842', delta: '+312 this month', trend: 'up', icon: MapPin, color: '#14548C', bgColor: '#E2ECF5' },
  { label: 'Revenue Collection', value: '₹4.2Cr', delta: '+18.4% YoY', trend: 'up', icon: Scale, color: '#1E7B4D', bgColor: '#E7F6EC' },
  { label: 'Mutation Backlog', value: '47', delta: '-12 from last month', trend: 'down', icon: Clock, color: '#B8720B', bgColor: '#FDF1E0' },
  { label: 'Active Disputes', value: '23', delta: '6 critical', trend: 'up', icon: AlertTriangle, color: '#A32E2E', bgColor: '#FDEAEA' },
  { label: 'Scheme Coverage', value: '78.4%', delta: 'PMKSY + SVAMITVA', trend: 'up', icon: Users, color: '#0F766E', bgColor: '#E6F6F4' },
  { label: 'Trust Score (District)', value: '94.2', delta: 'Avg across parcels', trend: 'neutral', icon: ShieldAlert, color: '#0B2E4E', bgColor: '#E2ECF5' },
];

const DEPARTMENT_STATUS: DepartmentStatus[] = [
  { department: 'Revenue (Tehsildar)', pending: 12, resolved_this_month: 34, avg_turnaround_days: 4.6, sla_compliance: 93.1 },
  { department: 'Registration (Sub-Registrar)', pending: 5, resolved_this_month: 18, avg_turnaround_days: 1.2, sla_compliance: 98.4 },
  { department: 'Planning (Town Planner)', pending: 6, resolved_this_month: 8, avg_turnaround_days: 8.4, sla_compliance: 87.2 },
  { department: 'Survey (Surveyor)', pending: 4, resolved_this_month: 11, avg_turnaround_days: 6.8, sla_compliance: 91.5 },
];

const CONFLICT_SUMMARY: ConflictSummary[] = [
  { type: 'Boundary Overlaps', count: 18, high_severity: 4, trend: 'down' },
  { type: 'Slivers & Gaps', count: 15, high_severity: 2, trend: 'flat' },
  { type: 'Revenue–Registration Mismatch', count: 8, high_severity: 3, trend: 'up' },
  { type: 'Ownership Disputes', count: 6, high_severity: 6, trend: 'flat' },
];

const TOP_PENDENCIES = [
  { officer: 'Tehsildar, Chengalpattu', type: 'Mutation Sanction', count: 5, oldest_days: 18 },
  { officer: 'SRO, Kanchipuram', type: 'Deed Registration', count: 3, oldest_days: 8 },
  { officer: 'Town Planner, Sriperumbudur', type: 'Building Permit', count: 4, oldest_days: 22 },
  { officer: 'Surveyor, Tiruvannamalai', type: 'Demarcation', count: 3, oldest_days: 14 },
];

export function AnalyticsView() {
  return (
    <div className="flex-1 overflow-y-auto p-5 space-y-5">
      {/* Title */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-bold text-[#16212E]">Executive Dashboard — Chengalpattu District</h2>
          <p className="text-[11px] text-[#4A5B6E] mt-0.5">Cross-department KPIs, conflict summaries, and pendency analysis</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => window.print()}
            className="flex items-center gap-1.5 text-[10px] font-semibold text-[#14548C] bg-[#E2ECF5] hover:bg-[#d0dff0] px-2.5 py-1.5 rounded-md transition-colors no-print"
          >
            <Printer className="w-3 h-3" /> Export Report
          </button>
          <span className="text-[10px] font-mono text-[#4A5B6E] bg-[#F1F4F8] px-3 py-1.5 rounded-md">
            Updated: {new Date().toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })}
          </span>
        </div>
      </div>

      {/* KPI Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
        {DISTRICT_KPIS.map((kpi) => {
          const Icon = kpi.icon;
          return (
            <div key={kpi.label} className="bg-white border border-[#DCE3EA] rounded-md p-4 flex items-start gap-3">
              <div
                className="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0"
                style={{ backgroundColor: kpi.bgColor }}
              >
                <Icon className="w-5 h-5" style={{ color: kpi.color }} />
              </div>
              <div>
                <div className="text-lg font-serif font-bold text-[#16212E] leading-tight">{kpi.value}</div>
                <div className="text-[10px] text-[#4A5B6E] font-semibold uppercase tracking-wider mt-0.5">{kpi.label}</div>
                <div className="text-[11px] mt-1 flex items-center gap-1">
                  {kpi.trend === 'up' && <TrendingUp className="w-3 h-3 text-[#1E7B4D]" />}
                  {kpi.trend === 'down' && <TrendingDown className="w-3 h-3 text-[#1E7B4D]" />}
                  <span className="text-[#4A5B6E]">{kpi.delta}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Two-column: Department Status + Conflict Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Department Performance */}
        <div className="bg-white border border-[#DCE3EA] rounded-md overflow-hidden">
          <div className="px-4 py-3 border-b border-[#DCE3EA]">
            <h3 className="text-sm font-bold text-[#16212E]">Department Performance</h3>
            <p className="text-[11px] text-[#4A5B6E] mt-0.5">SLA compliance and turnaround by department</p>
          </div>
          <table className="w-full text-xs">
            <thead>
              <tr className="bg-[#F7F9FC] text-[#4A5B6E] text-left">
                <th className="px-4 py-2 font-semibold">Department</th>
                <th className="px-4 py-2 font-semibold text-right">Pending</th>
                <th className="px-4 py-2 font-semibold text-right">Avg Days</th>
                <th className="px-4 py-2 font-semibold text-right">SLA %</th>
              </tr>
            </thead>
            <tbody>
              {DEPARTMENT_STATUS.map((d) => (
                <tr key={d.department} className="border-t border-[#F1F4F8] hover:bg-[#F7F9FC]">
                  <td className="px-4 py-2.5 font-semibold text-[#16212E]">{d.department}</td>
                  <td className="px-4 py-2.5 text-right font-serif tabular-nums font-semibold text-[#B8720B]">{d.pending}</td>
                  <td className="px-4 py-2.5 text-right font-serif tabular-nums">{d.avg_turnaround_days}d</td>
                  <td className="px-4 py-2.5 text-right">
                    <span
                      className={`font-serif font-bold tabular-nums ${
                        d.sla_compliance >= 95 ? 'text-[#1E7B4D]' : d.sla_compliance >= 90 ? 'text-[#B8720B]' : 'text-[#A32E2E]'
                      }`}
                    >
                      {d.sla_compliance}%
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Cross-Department Conflict Summary */}
        <div className="bg-white border border-[#DCE3EA] rounded-md overflow-hidden">
          <div className="px-4 py-3 border-b border-[#DCE3EA]">
            <h3 className="text-sm font-bold text-[#16212E]">Cross-Department Conflicts</h3>
            <p className="text-[11px] text-[#4A5B6E] mt-0.5">Inter-departmental data disagreements</p>
          </div>
          <div className="divide-y divide-[#F1F4F8]">
            {CONFLICT_SUMMARY.map((c) => (
              <div key={c.type} className="px-4 py-3 flex items-center justify-between hover:bg-[#F7F9FC]">
                <div>
                  <div className="text-xs font-semibold text-[#16212E]">{c.type}</div>
                  <div className="text-[11px] text-[#4A5B6E] mt-0.5">
                    {c.high_severity} critical · Trend: {c.trend === 'up' ? 'increasing' : c.trend === 'down' ? 'decreasing' : 'stable'}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-lg font-serif font-bold text-[#16212E] tabular-nums">{c.count}</span>
                  {c.trend === 'up' && <TrendingUp className="w-3.5 h-3.5 text-[#A32E2E]" />}
                  {c.trend === 'down' && <TrendingDown className="w-3.5 h-3.5 text-[#1E7B4D]" />}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Pendency Escalation Table */}
      <div className="bg-white border border-[#DCE3EA] rounded-md overflow-hidden">
        <div className="px-4 py-3 border-b border-[#DCE3EA] flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-[#16212E]">Pendency Escalation Board</h3>
            <p className="text-[11px] text-[#4A5B6E] mt-0.5">Officers with oldest pending casework requiring collector intervention</p>
          </div>
          <span className="text-[10px] text-[#A32E2E] font-bold bg-[#FDEAEA] px-2.5 py-1 rounded-full">
            {TOP_PENDENCIES.reduce((acc, p) => acc + p.count, 0)} Total Pending
          </span>
        </div>
        <table className="w-full text-xs">
          <thead>
            <tr className="bg-[#F7F9FC] text-[#4A5B6E] text-left">
              <th className="px-4 py-2.5 font-semibold">Officer / Office</th>
              <th className="px-4 py-2.5 font-semibold">Case Type</th>
              <th className="px-4 py-2.5 font-semibold text-right">Count</th>
              <th className="px-4 py-2.5 font-semibold text-right">Oldest (days)</th>
              <th className="px-4 py-2.5 font-semibold">Urgency</th>
            </tr>
          </thead>
          <tbody>
            {TOP_PENDENCIES.map((p) => (
              <tr key={p.officer} className="border-t border-[#F1F4F8] hover:bg-[#F7F9FC]">
                <td className="px-4 py-2.5 font-semibold text-[#16212E]">{p.officer}</td>
                <td className="px-4 py-2.5 text-[#4A5B6E]">{p.type}</td>
                <td className="px-4 py-2.5 text-right font-serif font-bold tabular-nums">{p.count}</td>
                <td className="px-4 py-2.5 text-right font-serif tabular-nums">{p.oldest_days}d</td>
                <td className="px-4 py-2.5">
                  <span
                    className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                      p.oldest_days > 15
                        ? 'bg-[#FDEAEA] text-[#A32E2E]'
                        : p.oldest_days > 7
                        ? 'bg-[#FDF1E0] text-[#B8720B]'
                        : 'bg-[#E7F6EC] text-[#1E7B4D]'
                    }`}
                  >
                    {p.oldest_days > 15 ? 'CRITICAL' : p.oldest_days > 7 ? 'HIGH' : 'NORMAL'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* District Heatmap — Transaction & Dispute Density */}
      <div className="bg-white border border-[#DCE3EA] rounded-md p-4">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-bold text-[#16212E]">District Heatmap — Transaction & Dispute Density</h3>
            <p className="text-[11px] text-[#4A5B6E] mt-0.5">Block-wise land transaction volumes, pending mutations, and active disputes</p>
          </div>
          <span className="text-[10px] font-mono text-[#4A5B6E] bg-[#F1F4F8] px-2.5 py-1 rounded-md">Q3 2026</span>
        </div>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {[
            { block: 'Chengalpattu', transactions: 342, mutations_pending: 12, disputes: 6, intensity: 'high' },
            { block: 'Thiruporur', transactions: 218, mutations_pending: 5, disputes: 2, intensity: 'medium' },
            { block: 'Maduranthakam', transactions: 156, mutations_pending: 8, disputes: 4, intensity: 'medium' },
            { block: 'Sriperumbudur', transactions: 489, mutations_pending: 18, disputes: 8, intensity: 'critical' },
            { block: 'Kanchipuram', transactions: 274, mutations_pending: 7, disputes: 3, intensity: 'medium' },
            { block: 'Uthiramerur', transactions: 98, mutations_pending: 3, disputes: 1, intensity: 'low' },
            { block: 'Tiruvannamalai', transactions: 187, mutations_pending: 9, disputes: 5, intensity: 'high' },
            { block: 'Kilpennathur', transactions: 64, mutations_pending: 2, disputes: 0, intensity: 'low' },
          ].map((b) => (
            <div
              key={b.block}
              className={`rounded-lg p-3 border-2 ${
                b.intensity === 'critical' ? 'border-[#A32E2E] bg-[#FDEAEA]' :
                b.intensity === 'high' ? 'border-[#B8720B] bg-[#FDF1E0]' :
                b.intensity === 'medium' ? 'border-[#14548C] bg-[#E2ECF5]' :
                'border-[#1E7B4D] bg-[#E7F6EC]'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-[#16212E]">{b.block}</span>
                <span className={`text-[9px] font-bold uppercase px-1.5 py-0.5 rounded-full ${
                  b.intensity === 'critical' ? 'bg-[#A32E2E] text-white' :
                  b.intensity === 'high' ? 'bg-[#B8720B] text-white' :
                  b.intensity === 'medium' ? 'bg-[#14548C] text-white' :
                  'bg-[#1E7B4D] text-white'
                }`}>{b.intensity}</span>
              </div>
              <div className="space-y-1 text-[11px]">
                <div className="flex justify-between">
                  <span className="text-[#4A5B6E]">Transactions:</span>
                  <span className="font-serif tabular-nums font-bold text-[#16212E]">{b.transactions}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#4A5B6E]">Mutations Pending:</span>
                  <span className="font-serif tabular-nums font-semibold text-[#B8720B]">{b.mutations_pending}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#4A5B6E]">Active Disputes:</span>
                  <span className={`font-serif tabular-nums font-semibold ${b.disputes > 5 ? 'text-[#A32E2E]' : 'text-[#16212E]'}`}>{b.disputes}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Land Conversion Trends */}
      <div className="bg-white border border-[#DCE3EA] rounded-md p-4">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-bold text-[#16212E]">Land Conversion Trends — 6 Quarter Rolling</h3>
            <p className="text-[11px] text-[#4A5B6E] mt-0.5">Agricultural to non-agricultural land conversion by block</p>
          </div>
        </div>
        <table className="w-full text-xs">
          <thead>
            <tr className="bg-[#F7F9FC] text-[#4A5B6E] text-left">
              <th className="px-4 py-2.5 font-semibold">Block / Taluk</th>
              <th className="px-4 py-2.5 font-semibold text-right">Ag. Land (Ha)</th>
              <th className="px-4 py-2.5 font-semibold text-right">Converted (Ha)</th>
              <th className="px-4 py-2.5 font-semibold text-right">Conversion %</th>
              <th className="px-4 py-2.5 font-semibold">Primary Use</th>
              <th className="px-4 py-2.5 font-semibold">Trend</th>
            </tr>
          </thead>
          <tbody>
            {[
              { block: 'Sriperumbudur', total: 4200, converted: 380, pct: 9.0, use: 'Industrial / SEZ', trend: 'accelerating' },
              { block: 'Chengalpattu', total: 3800, converted: 210, pct: 5.5, use: 'Residential Layouts', trend: 'steady' },
              { block: 'Mamallapuram', total: 1200, converted: 95, pct: 7.9, use: 'Tourism / Commercial', trend: 'accelerating' },
              { block: 'Tiruvannamalai', total: 6800, converted: 120, pct: 1.8, use: 'Mixed (Resi + Commercial)', trend: 'slow' },
              { block: 'Kanchipuram', total: 2900, converted: 145, pct: 5.0, use: 'Residential', trend: 'steady' },
              { block: 'Kilpennathur', total: 5200, converted: 42, pct: 0.8, use: 'Minimal', trend: 'stable' },
            ].map((r) => (
              <tr key={r.block} className="border-t border-[#F1F4F8] hover:bg-[#F7F9FC]">
                <td className="px-4 py-2.5 font-semibold text-[#16212E]">{r.block}</td>
                <td className="px-4 py-2.5 text-right font-serif tabular-nums">{r.total.toLocaleString()}</td>
                <td className="px-4 py-2.5 text-right font-serif tabular-nums font-bold text-[#A32E2E]">{r.converted}</td>
                <td className="px-4 py-2.5 text-right font-serif tabular-nums font-bold" style={{ color: r.pct > 5 ? '#A32E2E' : r.pct > 2 ? '#B8720B' : '#1E7B4D' }}>{r.pct}%</td>
                <td className="px-4 py-2.5 text-[#4A5B6E]">{r.use}</td>
                <td className="px-4 py-2.5">
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                    r.trend === 'accelerating' ? 'bg-[#FDEAEA] text-[#A32E2E]' :
                    r.trend === 'steady' ? 'bg-[#FDF1E0] text-[#B8720B]' :
                    r.trend === 'slow' ? 'bg-[#E2ECF5] text-[#14548C]' :
                    'bg-[#E7F6EC] text-[#1E7B4D]'
                  }`}>
                    {r.trend.toUpperCase()}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Scheme Coverage Strip */}
      <div className="bg-white border border-[#DCE3EA] rounded-md p-4">
        <h3 className="text-sm font-bold text-[#16212E] mb-3">Central Scheme Coverage</h3>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {[
            { scheme: 'SVAMITVA', coverage: 82.4, target: 100, color: '#14548C' },
            { scheme: 'PMKSY', coverage: 71.2, target: 85, color: '#0F766E' },
            { scheme: 'DILRMP', coverage: 94.8, target: 100, color: '#1E7B4D' },
            { scheme: 'NSDI Integration', coverage: 66.5, target: 90, color: '#B45309' },
          ].map((s) => (
            <div key={s.scheme} className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-[#16212E]">{s.scheme}</span>
                <span className="font-serif font-bold tabular-nums" style={{ color: s.color }}>{s.coverage}%</span>
              </div>
              <div className="h-2 bg-[#F1F4F8] rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full transition-all"
                  style={{ width: `${(s.coverage / s.target) * 100}%`, backgroundColor: s.color }}
                />
              </div>
              <div className="text-[10px] text-[#4A5B6E]">Target: {s.target}%</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
