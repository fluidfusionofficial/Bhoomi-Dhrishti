'use client';

import * as React from 'react';
import { OfficerSidebar, OfficerNavTab } from '@/components/layout/OfficerSidebar';
import AppHeader from '@/components/layout/AppHeader';
import KpiStrip from '@/components/layout/KpiStrip';
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

export default function OfficerConsolePage() {
  const [activeTab, setActiveTab] = React.useState<OfficerNavTab>('home');
  const [selectedParcelForInspector, setSelectedParcelForInspector] = React.useState<string | null>(null);

  // Pending counts for sidebar badges
  const pendingCounts: Partial<Record<OfficerNavTab, number>> = {
    home: 4,
    queue: 3,
    revenue: 3,
    registration: 1,
    resolution: 2,
    spatial: 3,
    trust: 2,
    satellite: 1,
  };

  const handleSelectParcelFromSearch = (parcelId: string) => {
    setSelectedParcelForInspector(parcelId);
    setActiveTab('parcels');
  };

  return (
    <div className="h-screen w-screen flex flex-col overflow-hidden bg-[#F4F7FB]">
      <AppHeader onSearch={handleSelectParcelFromSearch} />
      <KpiStrip onNavigate={(tab) => setActiveTab(tab as OfficerNavTab)} />

      {/* Main View Area: Left Rail + Center Work Area */}
      <div className="flex-1 flex min-h-0 overflow-hidden">
        <OfficerSidebar
          activeTab={activeTab}
          onTabChange={setActiveTab}
          pendingCounts={pendingCounts}
        />

        <main className="flex-1 flex flex-col min-w-0 overflow-hidden bg-[#F4F7FB]">
          {activeTab === 'home'      && <HomeView      onNavigateTab={(tab) => setActiveTab(tab)} />}
          {activeTab === 'cadastral' && <CadastralView onNavigateTab={(tab) => setActiveTab(tab)} />}
          {activeTab === 'queue'     && <QueueView     onNavigateTab={(tab) => setActiveTab(tab)} />}
          {activeTab === 'parcels' && <ParcelsView />}
          {activeTab === 'revenue' && <RevenueView />}
          {activeTab === 'registration' && <RegistrationView />}
          {activeTab === 'resolution' && <ResolutionView />}
          {activeTab === 'spatial' && <SpatialView />}
          {activeTab === 'trust' && <TrustFraudView />}
          {activeTab === 'satellite' && <SatelliteView />}
          {activeTab === 'workflows' && <WorkflowsView />}
          {activeTab === 'search' && (
            <GlobalSearchView onSelectParcel={handleSelectParcelFromSearch} />
          )}
        </main>
      </div>
    </div>
  );
}
