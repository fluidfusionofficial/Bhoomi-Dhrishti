'use client';

import React from 'react';
import {
  Map, MapPin, FileSpreadsheet, FileCheck2, Building2, Layers,
  ShieldAlert, Satellite, GitBranch, Search, BarChart3, Scale,
  ArrowRight, Clock, CheckCircle2, AlertTriangle, Globe, Users,
  Eye, Zap, Database, TrendingUp, ChevronRight, Landmark,
} from 'lucide-react';
import { useRole, OfficerNavTab } from '@/context/RoleContext';
import { useFreshness } from '@/context/FreshnessContext';

interface QuickAction {
  tab: OfficerNavTab;
  label: string;
  description: string;
  icon: React.ElementType;
  color: string;
  bgColor: string;
}

interface StatCard {
  label: string;
  value: string;
  sub: string;
  icon: React.ElementType;
  color: string;
  bgColor: string;
  tab: OfficerNavTab;
}

interface RecentItem {
  id: string;
  title: string;
  sub: string;
  time: string;
  status: 'ok' | 'warning' | 'critical';
  dept: string;
}

function getQuickActions(role: string): QuickAction[] {
  const common: QuickAction[] = [
    { tab: 'parcels', label: 'Search Parcels', description: 'Look up any parcel by ULPIN, survey number, or owner name', icon: Search, color: '#14548C', bgColor: '#E2ECF5' },
    { tab: 'cadastral', label: 'Cadastral Map', description: 'Open the Three-Tier GIS engine with satellite imagery', icon: Map, color: '#0F766E', bgColor: '#E6F6F4' },
  ];

  switch (role) {
    case 'tehsildar':
      return [
        { tab: 'revenue', label: 'Revenue Casework', description: 'View mutation register, RoR records, and pattadar transfers', icon: FileSpreadsheet, color: '#14548C', bgColor: '#E2ECF5' },
        { tab: 'queue', label: 'Casework Queue', description: 'Review pending identity matches, mutations, and conflicts', icon: Clock, color: '#B8720B', bgColor: '#FDF1E0' },
        ...common,
        { tab: 'trust', label: 'Trust & Fraud', description: 'Inspect anomaly scores and circular chain detection', icon: ShieldAlert, color: '#A32E2E', bgColor: '#FDEAEA' },
        { tab: 'workflows', label: 'Workflows', description: 'Launch cross-departmental workflow simulations', icon: GitBranch, color: '#1E7B4D', bgColor: '#E7F6EC' },
      ];
    case 'sub-registrar':
      return [
        { tab: 'registration', label: 'Deeds & EC', description: 'View registered deeds, encumbrance certificates, and stamp duty calculator', icon: FileCheck2, color: '#7C3AED', bgColor: '#EDE9FE' },
        { tab: 'queue', label: 'Casework Queue', description: 'Review pending identity matches and deed verification', icon: Clock, color: '#B8720B', bgColor: '#FDF1E0' },
        ...common,
        { tab: 'trust', label: 'Suspicious Transfers', description: 'Flag and review suspicious transfer patterns', icon: ShieldAlert, color: '#A32E2E', bgColor: '#FDEAEA' },
        { tab: 'workflows', label: 'Workflows', description: 'Launch encumbrance locking and mutation workflows', icon: GitBranch, color: '#1E7B4D', bgColor: '#E7F6EC' },
      ];
    case 'town-planner':
      return [
        { tab: 'planning', label: 'Planning & Zoning', description: 'Zoning compliance, building permits, and property tax linkage', icon: Building2, color: '#B45309', bgColor: '#FEF3C7' },
        ...common,
        { tab: 'spatial', label: 'Spatial Analysis', description: 'Topology conflicts, boundary overlaps, and restriction zones', icon: Layers, color: '#0369A1', bgColor: '#E0F2FE' },
        { tab: 'satellite', label: 'Satellite Watch', description: 'Sentinel-2 unauthorized conversion detection', icon: Satellite, color: '#A32E2E', bgColor: '#FDEAEA' },
        { tab: 'workflows', label: 'Workflows', description: 'Launch violation detection workflow simulations', icon: GitBranch, color: '#1E7B4D', bgColor: '#E7F6EC' },
      ];
    case 'surveyor':
      return [
        { tab: 'spatial', label: 'Topology Conflicts', description: 'Resolve overlaps, gaps, slivers in cadastral boundaries', icon: Layers, color: '#0369A1', bgColor: '#E0F2FE' },
        ...common,
        { tab: 'satellite', label: 'Satellite Watch', description: 'Encroachment detection via Sentinel-2 imagery', icon: Satellite, color: '#A32E2E', bgColor: '#FDEAEA' },
        { tab: 'workflows', label: 'Workflows', description: 'Launch dynamic partitioning workflow', icon: GitBranch, color: '#1E7B4D', bgColor: '#E7F6EC' },
      ];
    case 'collector':
      return [
        { tab: 'analytics', label: 'Executive Analytics', description: 'District KPIs, heatmaps, department performance, and scheme coverage', icon: BarChart3, color: '#0B2E4E', bgColor: '#E2ECF5' },
        { tab: 'queue', label: 'Pendency Board', description: 'Cross-department pending casework requiring escalation', icon: Clock, color: '#B8720B', bgColor: '#FDF1E0' },
        ...common,
        { tab: 'trust', label: 'Trust & Fraud', description: 'District-wide anomaly patterns and network graph', icon: ShieldAlert, color: '#A32E2E', bgColor: '#FDEAEA' },
        { tab: 'workflows', label: 'Workflows', description: 'All four cross-departmental workflow simulations', icon: GitBranch, color: '#1E7B4D', bgColor: '#E7F6EC' },
      ];
    default:
      return common;
  }
}

function getStats(role: string): StatCard[] {
  switch (role) {
    case 'tehsildar':
      return [
        { label: 'Pending Mutations', value: '7', sub: '3 high priority', icon: FileSpreadsheet, color: '#B8720B', bgColor: '#FDF1E0', tab: 'revenue' },
        { label: 'Topology Conflicts', value: '5', sub: '2 boundary overlaps', icon: Layers, color: '#A32E2E', bgColor: '#FDEAEA', tab: 'spatial' },
        { label: 'High Risk Parcels', value: '4', sub: 'Trust score < 40', icon: ShieldAlert, color: '#A32E2E', bgColor: '#FDEAEA', tab: 'trust' },
        { label: 'Verified This Week', value: '8', sub: 'of 15 total', icon: CheckCircle2, color: '#1E7B4D', bgColor: '#E7F6EC', tab: 'parcels' },
      ];
    case 'sub-registrar':
      return [
        { label: 'Pending Deeds', value: '5', sub: '2 mortgage deeds', icon: FileCheck2, color: '#7C3AED', bgColor: '#EDE9FE', tab: 'registration' },
        { label: 'EC Requests', value: '3', sub: 'Avg 0.2 days', icon: Scale, color: '#14548C', bgColor: '#E2ECF5', tab: 'registration' },
        { label: 'Suspicious Transfers', value: '2', sub: 'Flagged by trust engine', icon: ShieldAlert, color: '#A32E2E', bgColor: '#FDEAEA', tab: 'trust' },
        { label: 'Registered This Week', value: '12', sub: '₹2.1Cr total', icon: CheckCircle2, color: '#1E7B4D', bgColor: '#E7F6EC', tab: 'registration' },
      ];
    case 'town-planner':
      return [
        { label: 'Zone Violations', value: '4', sub: '2 commercial on ag. land', icon: AlertTriangle, color: '#A32E2E', bgColor: '#FDEAEA', tab: 'planning' },
        { label: 'Permits Pending', value: '6', sub: '3 pending > 7 days', icon: Building2, color: '#B45309', bgColor: '#FEF3C7', tab: 'planning' },
        { label: 'Land Use Changes', value: '3', sub: 'Satellite detected', icon: Satellite, color: '#0369A1', bgColor: '#E0F2FE', tab: 'satellite' },
        { label: 'Restriction Zones', value: '4', sub: 'CRZ, Heritage, SEZ', icon: Landmark, color: '#14548C', bgColor: '#E2ECF5', tab: 'planning' },
      ];
    case 'surveyor':
      return [
        { label: 'Topology Conflicts', value: '5', sub: '3 overlaps, 2 slivers', icon: Layers, color: '#A32E2E', bgColor: '#FDEAEA', tab: 'spatial' },
        { label: 'Demarcation Pending', value: '4', sub: 'DGPS upload needed', icon: Globe, color: '#0369A1', bgColor: '#E0F2FE', tab: 'spatial' },
        { label: 'Encroachments', value: '2', sub: 'Sentinel-2 flagged', icon: Satellite, color: '#B8720B', bgColor: '#FDF1E0', tab: 'satellite' },
        { label: 'Parcels Surveyed', value: '11', sub: 'This month', icon: CheckCircle2, color: '#1E7B4D', bgColor: '#E7F6EC', tab: 'parcels' },
      ];
    case 'collector':
      return [
        { label: 'Total Parcels', value: '15,842', sub: '+312 this month', icon: MapPin, color: '#14548C', bgColor: '#E2ECF5', tab: 'analytics' },
        { label: 'Revenue Collection', value: '₹4.2Cr', sub: '+18.4% YoY', icon: TrendingUp, color: '#1E7B4D', bgColor: '#E7F6EC', tab: 'analytics' },
        { label: 'Mutation Backlog', value: '47', sub: '-12 from last month', icon: Clock, color: '#B8720B', bgColor: '#FDF1E0', tab: 'analytics' },
        { label: 'Active Disputes', value: '23', sub: '6 critical', icon: AlertTriangle, color: '#A32E2E', bgColor: '#FDEAEA', tab: 'analytics' },
      ];
    default:
      return [];
  }
}

const RECENT_ACTIVITY: RecentItem[] = [
  { id: '1', title: 'Mutation MUT-2026-0819 filed', sub: 'ULPIN TN-CHN-000001 · Sale deed transfer', time: '2 hrs ago', status: 'warning', dept: 'Revenue' },
  { id: '2', title: 'Topology conflict resolved', sub: 'Parcels P003–P008 overlap fixed', time: '4 hrs ago', status: 'ok', dept: 'Survey' },
  { id: '3', title: 'Court stay registered', sub: 'Case OS-421/2024 · P003 ownership dispute', time: '1 day ago', status: 'critical', dept: 'eCourts' },
  { id: '4', title: 'Encumbrance lien placed', sub: 'SBI Chengalpattu · ULPIN TN-CHN-000002', time: '1 day ago', status: 'warning', dept: 'Registration' },
  { id: '5', title: 'Satellite anomaly detected', sub: 'P006 agricultural → mixed use (NDBI +0.48)', time: '2 days ago', status: 'critical', dept: 'Satellite' },
  { id: '6', title: 'RoR extract issued', sub: 'Citizen request for TN-CHN-000008', time: '2 days ago', status: 'ok', dept: 'Citizen Services' },
];

export function HomeView({ onNavigateTab }: { onNavigateTab: (tab: any) => void }) {
  const { config, role } = useRole();
  const freshness = useFreshness();
  const quickActions = getQuickActions(role);
  const stats = getStats(role);

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-[1200px] mx-auto p-5 space-y-5">

        {/* ── Welcome Banner ────────────────────────────────────────────────── */}
        <div
          className="rounded-xl p-6 text-white relative overflow-hidden"
          style={{ background: `linear-gradient(135deg, ${config.color}, ${config.color}dd)` }}
        >
          <div className="relative z-10">
            <p className="text-xs font-semibold text-white/60 uppercase tracking-[0.15em]">
              Bhoomi Dhrishti · {new Date().toLocaleDateString('en-IN', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}
            </p>
            <h1 className="text-2xl font-serif font-bold mt-1 tracking-tight">
              Welcome, {config.title}
            </h1>
            <p className="text-sm text-white/80 mt-1.5 max-w-xl leading-relaxed">
              {role === 'tehsildar' && 'Your unified view of revenue records, mutation casework, and conflict triage across the Chengalpattu district. All data is cross-verified from state department systems.'}
              {role === 'sub-registrar' && 'Review registered deeds, verify encumbrance status, and use the stamp duty calculator. Data is fetched from NGDRS and state SRO portals.'}
              {role === 'town-planner' && 'Inspect zoning compliance, building permits, and property tax linkages against the Tirupporur Master Plan 2041. Satellite change detection alerts included.'}
              {role === 'surveyor' && 'Resolve topology conflicts, upload DGPS measurements, and validate cadastral boundary accuracy. Sentinel-2 encroachment alerts available.'}
              {role === 'collector' && 'Executive overview of district-wide land governance — KPIs, department performance, dispute backlogs, and cross-department conflict summaries.'}
            </p>
          </div>
          <div className="absolute top-0 right-0 w-48 h-full opacity-10">
            <div className="w-full h-full flex items-center justify-center">
              <Globe className="w-40 h-40" />
            </div>
          </div>
        </div>

        {/* ── Summary Stats ─────────────────────────────────────────────────── */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {stats.map((s) => {
            const Icon = s.icon;
            return (
              <button
                key={s.label}
                type="button"
                onClick={() => onNavigateTab(s.tab)}
                className="bg-white rounded-lg border border-[#DCE3EA] p-4 text-left hover:border-[#B9C5D1] hover:shadow-sm transition-all group"
              >
                <div className="flex items-start justify-between">
                  <div
                    className="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 group-hover:scale-105 transition-transform"
                    style={{ backgroundColor: s.bgColor }}
                  >
                    <Icon className="w-4.5 h-4.5" style={{ color: s.color }} />
                  </div>
                  <ChevronRight className="w-4 h-4 text-[#DCE3EA] group-hover:text-[#14548C] transition-colors" />
                </div>
                <div className="mt-3">
                  <div className="text-xl font-serif font-bold text-[#16212E] tabular-nums">{s.value}</div>
                  <div className="text-xs font-semibold text-[#16212E] mt-0.5">{s.label}</div>
                  <div className="text-[11px] text-[#4A5B6E] mt-0.5">{s.sub}</div>
                </div>
              </button>
            );
          })}
        </div>

        {/* ── Quick Actions + Recent Activity (two-column) ──────────────────── */}
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-5">

          {/* Quick Actions — 3 cols */}
          <div className="lg:col-span-3 space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-bold text-[#16212E]">Quick Actions</h2>
              <span className="text-[10px] text-[#4A5B6E] uppercase tracking-wider font-semibold">
                {quickActions.length} tools available
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              {quickActions.map((action) => {
                const Icon = action.icon;
                return (
                  <button
                    key={action.tab + action.label}
                    type="button"
                    onClick={() => onNavigateTab(action.tab)}
                    className="bg-white rounded-lg border border-[#DCE3EA] p-4 text-left hover:border-[#14548C] hover:shadow-sm transition-all group flex gap-3"
                  >
                    <div
                      className="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 group-hover:scale-105 transition-transform"
                      style={{ backgroundColor: action.bgColor }}
                    >
                      <Icon className="w-5 h-5" style={{ color: action.color }} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-xs font-bold text-[#16212E] group-hover:text-[#14548C] transition-colors flex items-center gap-1.5">
                        {action.label}
                        <ArrowRight className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                      </div>
                      <div className="text-[11px] text-[#4A5B6E] mt-0.5 leading-relaxed line-clamp-2">
                        {action.description}
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Recent Activity — 2 cols */}
          <div className="lg:col-span-2 space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-bold text-[#16212E]">Recent Activity</h2>
              <span className="text-[10px] text-[#4A5B6E] uppercase tracking-wider font-semibold">
                Cross-system feed
              </span>
            </div>

            <div className="bg-white rounded-lg border border-[#DCE3EA] divide-y divide-[#F1F4F8]">
              {RECENT_ACTIVITY.map((item) => (
                <div key={item.id} className="px-4 py-3 hover:bg-[#F7F9FC] transition-colors">
                  <div className="flex items-start gap-2.5">
                    <div className={`w-2 h-2 rounded-full mt-1.5 flex-shrink-0 ${
                      item.status === 'ok' ? 'bg-[#1E7B4D]' :
                      item.status === 'warning' ? 'bg-[#B8720B]' :
                      'bg-[#A32E2E]'
                    }`} />
                    <div className="flex-1 min-w-0">
                      <div className="text-xs font-semibold text-[#16212E] leading-tight">{item.title}</div>
                      <div className="text-[11px] text-[#4A5B6E] mt-0.5">{item.sub}</div>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-[10px] text-[#4A5B6E]">{item.time}</span>
                        <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-[#F1F4F8] text-[#4A5B6E]">{item.dept}</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* ── Platform Info Strip ───────────────────────────────────────────── */}
        <div className="bg-white rounded-lg border border-[#DCE3EA] p-4 flex flex-wrap items-center justify-between gap-4 text-[11px] text-[#4A5B6E]">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-1.5">
              <Database className="w-3.5 h-3.5 text-[#14548C]" />
              <span>16 microservices</span>
              <span className="w-1.5 h-1.5 rounded-full bg-[#1E7B4D]" />
              <span className="text-[#1E7B4D] font-semibold">All operational</span>
            </div>
            <div className="flex items-center gap-1.5">
              <Eye className="w-3.5 h-3.5 text-[#14548C]" />
              <span>Read-only unified view</span>
            </div>
            <div className="flex items-center gap-1.5">
              <Zap className="w-3.5 h-3.5 text-[#14548C]" />
              <span>Data freshness: <strong className={freshness === 'LIVE' ? 'text-[#1E7B4D]' : 'text-[#B8720B]'}>{freshness}</strong></span>
            </div>
          </div>
          <div className="font-mono text-[10px] text-[#9AA4B3]">
            SIH 2026 · PS-26014 · Keycloak SSO · SRID 4326
          </div>
        </div>
      </div>
    </div>
  );
}
