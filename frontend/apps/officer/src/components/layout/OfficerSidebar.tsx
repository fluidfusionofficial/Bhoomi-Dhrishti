'use client';

import * as React from 'react';
import {
  Home,
  MapPin,
  Map,
  Inbox,
  FileSpreadsheet,
  FileCheck2,
  GitMerge,
  Layers,
  ShieldAlert,
  Satellite,
  Workflow,
  Search,
} from 'lucide-react';
import { cn } from '@bhoomi/ui';

export type OfficerNavTab =
  | 'home'
  | 'cadastral'
  | 'parcels'
  | 'queue'
  | 'revenue'
  | 'registration'
  | 'resolution'
  | 'spatial'
  | 'trust'
  | 'satellite'
  | 'workflows'
  | 'search';

export interface OfficerSidebarProps {
  activeTab: OfficerNavTab;
  onTabChange: (tab: OfficerNavTab) => void;
  pendingCounts?: Partial<Record<OfficerNavTab, number>>;
}

export const OFFICER_NAV_ITEMS: Array<{
  id: OfficerNavTab;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  description: string;
}> = [
  { id: 'home',      label: 'Home',         icon: Home,   description: 'Officer Queue Dashboard' },
  { id: 'cadastral', label: 'Cadastral Map', icon: Map,    description: 'Full-Screen GIS Cadastral View' },
  { id: 'parcels',   label: 'Parcels',       icon: MapPin, description: 'Search & Cadastral Lineage' },
  { id: 'queue', label: 'Queue', icon: Inbox, description: 'Active Casework Queue' },
  { id: 'revenue', label: 'Revenue', icon: FileSpreadsheet, description: 'RoR & Mutation Casework' },
  { id: 'registration', label: 'Registration', icon: FileCheck2, description: 'Deeds & Encumbrance (EC)' },
  { id: 'resolution', label: 'Resolution', icon: GitMerge, description: 'Entity-Resolution Queue' },
  { id: 'spatial', label: 'Spatial', icon: Layers, description: 'Topology Conflicts & Detect' },
  { id: 'trust', label: 'Trust & Fraud', icon: ShieldAlert, description: 'Anomalies & Network Graph' },
  { id: 'satellite', label: 'Satellite', icon: Satellite, description: 'Unauthorized Conversion' },
  { id: 'workflows', label: 'Workflows', icon: Workflow, description: 'Guided Workflow Launcher' },
  { id: 'search', label: 'Search', icon: Search, description: 'Global Ledger Lookup' },
];

export function OfficerSidebar({
  activeTab,
  onTabChange,
  pendingCounts = {},
}: OfficerSidebarProps) {
  return (
    <aside className="group flex-shrink-0 w-12 hover:w-[220px] transition-[width] duration-200 ease-in-out overflow-hidden bg-[#0B2447] text-[#E2ECF5] flex flex-col select-none border-r border-[#103F68]">
      {/* Brand Header */}
      <div className="h-14 flex items-center px-3 border-b border-[#14548C]/60">
        <div className="w-8 h-8 flex-shrink-0 rounded-[5px] bg-gradient-to-br from-[#14a89a] to-[#0f766e] text-white grid place-items-center font-bold text-sm">
          BD
        </div>
        <div className="ml-3 opacity-0 group-hover:opacity-100 transition-opacity duration-150 delay-75 whitespace-nowrap overflow-hidden">
          <div className="text-xs font-bold text-white leading-none">Bhoomi Dhrishti</div>
          <div className="text-[10px] text-[#E2ECF5]/80 mt-0.5">Officer Console · DoLR</div>
        </div>
      </div>

      {/* Navigation Items */}
      <nav className="flex-1 py-3 overflow-y-auto overflow-x-hidden">
        {OFFICER_NAV_ITEMS.map((item) => {
          const isActive = activeTab === item.id;
          const Icon = item.icon;
          const count = pendingCounts[item.id];

          return (
            <button
              key={item.id}
              type="button"
              title={item.description}
              onClick={() => onTabChange(item.id)}
              className={cn(
                'w-full flex items-center gap-3 px-3 py-2.5 overflow-hidden whitespace-nowrap transition-colors',
                isActive
                  ? 'bg-[#14548C] text-white'
                  : 'text-[#E2ECF5]/80 hover:bg-[#14548C]/40 hover:text-white'
              )}
            >
              <Icon className="w-5 h-5 flex-shrink-0" />
              <span className="text-xs font-semibold truncate flex-1 opacity-0 group-hover:opacity-100 transition-opacity duration-150 delay-75">
                {item.label}
              </span>
              {count != null && count > 0 && (
                <span
                  className={cn(
                    'text-[10px] font-bold px-1.5 rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-150 delay-75',
                    isActive ? 'bg-white text-[#14548C]' : 'bg-[#B8720B] text-white'
                  )}
                >
                  {count}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="border-t border-[#14548C]/60 bg-[#07223B] px-3 py-2.5 overflow-hidden whitespace-nowrap">
        <div className="text-[10px] text-[#E2ECF5]/60 opacity-0 group-hover:opacity-100 transition-opacity duration-150">
          v1.0.0 · Keycloak SSO
        </div>
      </div>
    </aside>
  );
}
