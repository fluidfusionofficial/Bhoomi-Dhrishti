'use client';

import * as React from 'react';
import { RoleProvider, useRole, OfficerNavTab } from '@/context/RoleContext';
import { FreshnessProvider } from '@/context/FreshnessContext';
import { OfficerSidebar } from '@/components/layout/OfficerSidebar';
import AppHeader from '@/components/layout/AppHeader';
import KpiStrip from '@/components/layout/KpiStrip';
import { Breadcrumb } from '@/components/layout/Breadcrumb';
import { HomeView } from '@/components/dashboard/HomeView';
import { QueueView } from '@/components/dashboard/QueueView';
import { CadastralView } from '@/components/dashboard/CadastralView';
import { ParcelsView } from '@/components/dashboard/ParcelsView';
import { RevenueView } from '@/components/dashboard/RevenueView';
import { RegistrationView } from '@/components/dashboard/RegistrationView';
import { ResolutionView } from '@/components/dashboard/ResolutionView';
import { SpatialView } from '@/components/dashboard/SpatialView';
import { TrustFraudView } from '@/components/dashboard/TrustFraudView';
import { SatelliteView } from '@/components/dashboard/SatelliteView';
import { WorkflowsView } from '@/components/dashboard/WorkflowsView';
import { GlobalSearchView } from '@/components/dashboard/GlobalSearchView';
import { PlanningView } from '@/components/dashboard/PlanningView';
import { AnalyticsView } from '@/components/dashboard/AnalyticsView';

function OfficerConsoleInner() {
  const { config, isTabAllowed } = useRole();
  const [activeTab, setActiveTab] = React.useState<OfficerNavTab>(config.defaultTab);
  const [selectedParcelForInspector, setSelectedParcelForInspector] = React.useState<string | null>(null);

  const safeSetTab = React.useCallback(
    (tab: OfficerNavTab | string) => {
      const t = tab as OfficerNavTab;
      if (isTabAllowed(t)) {
        setActiveTab(t);
      }
    },
    [isTabAllowed]
  );

  const pendingCounts: Partial<Record<OfficerNavTab, number>> = {
    home: 4,
    queue: 3,
    revenue: 3,
    registration: 1,
    resolution: 2,
    spatial: 3,
    trust: 2,
    satellite: 1,
    planning: 4,
  };

  const handleSelectParcelFromSearch = (parcelId: string) => {
    setSelectedParcelForInspector(parcelId);
    safeSetTab('parcels');
  };

  return (
    <div className="h-screen w-screen flex flex-col overflow-hidden bg-[#F4F7FB]">
      <AppHeader onSearch={handleSelectParcelFromSearch} onGoHome={() => safeSetTab('home')} />
      <KpiStrip onNavigate={(tab) => safeSetTab(tab)} />
      <Breadcrumb activeTab={activeTab} onNavigate={(tab) => safeSetTab(tab)} />

      <div className="flex-1 flex min-h-0 overflow-hidden">
        <OfficerSidebar
          activeTab={activeTab}
          onTabChange={setActiveTab}
          pendingCounts={pendingCounts}
        />

        <main className="flex-1 flex flex-col min-w-0 overflow-hidden bg-[#F4F7FB]">
          {activeTab === 'home'         && <HomeView onNavigateTab={(tab) => safeSetTab(tab)} />}
          {activeTab === 'analytics'    && <AnalyticsView />}
          {activeTab === 'cadastral'    && <CadastralView onNavigateTab={(tab) => safeSetTab(tab)} />}
          {activeTab === 'queue'        && <QueueView onNavigateTab={(tab) => safeSetTab(tab)} />}
          {activeTab === 'parcels'      && <ParcelsView />}
          {activeTab === 'revenue'      && <RevenueView />}
          {activeTab === 'registration' && <RegistrationView />}
          {activeTab === 'planning'     && <PlanningView />}
          {activeTab === 'resolution'   && <ResolutionView />}
          {activeTab === 'spatial'      && <SpatialView />}
          {activeTab === 'trust'        && <TrustFraudView />}
          {activeTab === 'satellite'    && <SatelliteView />}
          {activeTab === 'workflows'    && <WorkflowsView />}
          {activeTab === 'search'       && (
            <GlobalSearchView onSelectParcel={handleSelectParcelFromSearch} />
          )}
        </main>
      </div>
    </div>
  );
}

export default function OfficerConsolePage() {
  return (
    <RoleProvider>
      <FreshnessProvider>
        <OfficerConsoleInner />
      </FreshnessProvider>
    </RoleProvider>
  );
}
