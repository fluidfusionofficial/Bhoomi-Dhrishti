'use client';

import * as React from 'react';
import { Home, ChevronRight, ArrowLeft } from 'lucide-react';
import { useRole, OfficerNavTab } from '@/context/RoleContext';

const TAB_LABELS: Record<OfficerNavTab, string> = {
  home: 'Dashboard',
  analytics: 'Executive Analytics',
  cadastral: 'Cadastral Map',
  parcels: 'Parcels & Lineage',
  queue: 'Casework Queue',
  revenue: 'Revenue Records',
  registration: 'Deeds & EC',
  planning: 'Planning & Zoning',
  resolution: 'Entity Resolution',
  spatial: 'Topology Conflicts',
  trust: 'Trust & Fraud',
  satellite: 'Satellite Watch',
  workflows: 'Workflows',
  search: 'Global Search',
};

interface BreadcrumbProps {
  activeTab: OfficerNavTab;
  onNavigate: (tab: OfficerNavTab) => void;
}

export function Breadcrumb({ activeTab, onNavigate }: BreadcrumbProps) {
  const { config } = useRole();
  const isHome = activeTab === 'home';

  return (
    <div className="flex items-center gap-1.5 px-4 py-1.5 bg-white border-b border-[#E3E8EF] text-xs flex-shrink-0 no-print">
      {/* Back button — only when not on home */}
      {!isHome && (
        <button
          onClick={() => onNavigate('home')}
          className="flex items-center gap-1 text-[#14548C] hover:text-[#103F68] font-semibold mr-1 px-1.5 py-0.5 rounded hover:bg-[#E2ECF5] transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Back</span>
        </button>
      )}

      {/* Home crumb */}
      <button
        onClick={() => onNavigate('home')}
        className={`flex items-center gap-1 px-1.5 py-0.5 rounded transition-colors ${
          isHome ? 'text-[#16212E] font-bold' : 'text-[#4A5B6E] hover:text-[#14548C] hover:bg-[#E2ECF5]'
        }`}
      >
        <Home className="w-3 h-3" />
        <span>{config.title}</span>
      </button>

      {/* Current page crumb */}
      {!isHome && (
        <>
          <ChevronRight className="w-3 h-3 text-[#B9C5D1]" />
          <span className="text-[#16212E] font-bold px-1.5 py-0.5">
            {TAB_LABELS[activeTab] || activeTab}
          </span>
        </>
      )}
    </div>
  );
}
