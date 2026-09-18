'use client';

import React, { useState, useMemo } from 'react';
import { ZoomIn, ZoomOut, Layers, Compass, X, ChevronRight, Map as MapIcon } from 'lucide-react';
import {
  CadastralMap,
  PARCEL_DATA,
  type ParcelData,
  type LayerState,
} from './CadastralMap';

// ── Helpers ────────────────────────────────────────────────────────────────────

function statusPillClass(status: string): string {
  if (status === 'Conflict') return 'bg-[#dc2626] text-white';
  if (status === 'Warning')  return 'bg-[#d97706] text-white';
  if (status === 'Pending')  return 'bg-[#2456a6] text-white';
  return 'bg-[#16a34a] text-white';
}

function riskBadgeClass(risk: string): string {
  if (risk === 'High')   return 'bg-[#fdeaea] text-[#dc2626]';
  if (risk === 'Medium') return 'bg-[#fdf1e0] text-[#d97706]';
  return 'bg-[#e7f6ec] text-[#16a34a]';
}

function Toggle({ on, onToggle }: { on: boolean; onToggle: () => void }) {
  return (
    <div
      onClick={onToggle}
      className="flex-shrink-0 cursor-pointer"
      style={{
        width: 34,
        height: 20,
        borderRadius: 20,
        background: on ? '#118a80' : '#cbd3de',
        position: 'relative',
        transition: 'background .18s',
      }}
    >
      <div
        style={{
          position: 'absolute',
          top: 2,
          left: on ? 16 : 2,
          width: 16,
          height: 16,
          borderRadius: '50%',
          background: '#fff',
          boxShadow: '0 1px 2px rgba(11,36,71,.08)',
          transition: 'left .18s',
        }}
      />
    </div>
  );
}

// ── Layer row ──────────────────────────────────────────────────────────────────

function LayerRow({
  label,
  color,
  on,
  onToggle,
}: {
  label: string;
  color: string;
  on: boolean;
  onToggle: () => void;
}) {
  return (
    <div className="flex items-center gap-2.5 py-1.5 cursor-pointer hover:[&_span]:text-[#1b4079]" onClick={onToggle}>
      <Toggle on={on} onToggle={() => {}} />
      <span className="text-[13px] font-semibold text-[#425066] flex-1 transition-colors">{label}</span>
      <div
        className="w-3.5 h-3.5 rounded-[4px] flex-shrink-0 border border-black/[.08]"
        style={{ background: color }}
      />
    </div>
  );
}

// ── Component ──────────────────────────────────────────────────────────────────

export function HomeView({ onNavigateTab }: { onNavigateTab: (tab: any) => void }) {
  const [layers, setLayers] = useState<LayerState>({
    parcels: true,
    ulpin: true,
    roads: false,
    ownership: true,
    landUse: false,
    zoning: false,
    propertyTax: false,
    topologyConflicts: true,
  });

  const [statusFilter, setStatusFilter] = useState('all');
  const [riskFilter, setRiskFilter]     = useState('all');

  const [selectedParcel, setSelectedParcel] = useState<ParcelData | null>(null);
  const [drawerOpen, setDrawerOpen]         = useState(false);

  const toggleLayer = (key: keyof LayerState) =>
    setLayers((prev) => ({ ...prev, [key]: !prev[key] }));

  const handleParcelSelect = (parcel: ParcelData) => {
    setSelectedParcel(parcel);
    setDrawerOpen(true);
  };

  const visibleCount = useMemo(() => {
    return PARCEL_DATA.filter((p) => {
      if (statusFilter !== 'all' && p.status.toLowerCase() !== statusFilter) return false;
      if (riskFilter   !== 'all' && p.risk_level.toLowerCase() !== riskFilter)  return false;
      return true;
    }).length;
  }, [statusFilter, riskFilter]);

  return (
    <div className="flex-1 flex overflow-hidden">

      {/* ── LEFT LAYER PANEL ───────────────────────────────────────────────── */}
      <div className="w-[274px] flex-shrink-0 bg-white border-r border-[#e3e8ef] flex flex-col z-10 shadow-[0_1px_2px_rgba(11,36,71,.06)] overflow-y-auto">

        {/* MAP LAYERS */}
        <div className="border-b border-[#f1f4f8] px-4 py-3.5">
          <h3 className="text-[11px] font-extrabold text-[#6b7688] uppercase tracking-[.07em] mb-3 flex items-center gap-2">
            MAP LAYERS <span className="flex-1 h-px bg-[#e3e8ef]" />
          </h3>

          <div className="text-[10px] font-extrabold text-[#9aa4b3] uppercase tracking-[.08em] mb-2">Base Spatial</div>
          <LayerRow label="Parcel Geometries"  color="#3b6fbf" on={layers.parcels}  onToggle={() => toggleLayer('parcels')} />
          <LayerRow label="ULPIN Labels"        color="#9aa4b3" on={layers.ulpin}    onToggle={() => toggleLayer('ulpin')} />
          <LayerRow label="Roads & Admin"       color="#cbd3de" on={layers.roads}    onToggle={() => toggleLayer('roads')} />

          <div className="text-[10px] font-extrabold text-[#0f766e] uppercase tracking-[.08em] mt-3 mb-2">Core Governance</div>
          <LayerRow label="Ownership Status"     color="#3b6fbf" on={layers.ownership}  onToggle={() => toggleLayer('ownership')} />
          <LayerRow label="Land Use"             color="#16a34a" on={layers.landUse}    onToggle={() => toggleLayer('landUse')} />
          <LayerRow label="Zoning / Master Plan" color="#7c3aed" on={layers.zoning}     onToggle={() => toggleLayer('zoning')} />

          <div className="text-[10px] font-extrabold text-[#d97706] uppercase tracking-[.08em] mt-3 mb-2">Services &amp; Use-Case</div>
          <LayerRow label="Property Tax"       color="#d97706" on={layers.propertyTax}       onToggle={() => toggleLayer('propertyTax')} />
          <LayerRow label="Topology Conflicts" color="#dc2626" on={layers.topologyConflicts}  onToggle={() => toggleLayer('topologyConflicts')} />
        </div>

        {/* FILTERS */}
        <div className="px-4 py-3.5">
          <h3 className="text-[11px] font-extrabold text-[#6b7688] uppercase tracking-[.07em] mb-3 flex items-center gap-2">
            FILTERS <span className="flex-1 h-px bg-[#e3e8ef]" />
          </h3>

          <div className="mb-3.5">
            <div className="text-[11.5px] font-bold text-[#425066] mb-1.5">Status</div>
            <div className="flex flex-wrap gap-1.5">
              {['all', 'verified', 'conflict', 'warning', 'pending'].map((f) => (
                <button
                  key={f}
                  onClick={() => setStatusFilter(f)}
                  className={`text-[11.5px] font-semibold px-[11px] py-[5px] rounded-[20px] transition-colors ${
                    statusFilter === f
                      ? 'bg-[#1b4079] text-white'
                      : 'bg-[#f1f4f8] text-[#425066] hover:bg-[#e3e8ef]'
                  }`}
                >
                  {f.charAt(0).toUpperCase() + f.slice(1)}
                </button>
              ))}
            </div>
          </div>

          <div className="mb-3.5">
            <div className="text-[11.5px] font-bold text-[#425066] mb-1.5">Risk</div>
            <div className="flex flex-wrap gap-1.5">
              {['all', 'low', 'medium', 'high'].map((f) => (
                <button
                  key={f}
                  onClick={() => setRiskFilter(f)}
                  className={`text-[11.5px] font-semibold px-[11px] py-[5px] rounded-[20px] transition-colors ${
                    riskFilter === f
                      ? 'bg-[#1b4079] text-white'
                      : 'bg-[#f1f4f8] text-[#425066] hover:bg-[#e3e8ef]'
                  }`}
                >
                  {f.charAt(0).toUpperCase() + f.slice(1)}
                </button>
              ))}
            </div>
          </div>

          <button
            onClick={() => { setStatusFilter('all'); setRiskFilter('all'); }}
            className="w-full text-[12px] font-semibold text-[#2456a6] bg-[#eef3fb] py-1.5 rounded-[6px] hover:brightness-95 transition-[filter]"
          >
            Reset Filters
          </button>
          <div className="text-[11.5px] text-[#6b7688] text-center mt-2.5 font-semibold">
            {visibleCount} of {PARCEL_DATA.length} parcels shown
          </div>
        </div>
      </div>

      {/* ── CENTER MAP ─────────────────────────────────────────────────────── */}
      <div className="flex-1 relative min-w-0 overflow-hidden">

        {/* MapLibre GL interactive map */}
        <CadastralMap
          layers={layers}
          statusFilter={statusFilter}
          riskFilter={riskFilter}
          selectedParcelId={selectedParcel?.parcel_id ?? null}
          onParcelSelect={handleParcelSelect}
        />

        {/* TOP-LEFT: Map Title Overlay */}
        <div className="absolute top-3.5 left-3.5 z-50 bg-white/[.94] backdrop-blur-sm px-3.5 py-2.5 rounded-[10px] shadow-[0_4px_12px_rgba(11,36,71,.10)] border border-[#e3e8ef] pointer-events-none">
          <div className="text-[12.5px] font-extrabold text-[#12315e] tracking-[.02em]">Demo Village · Chengalpattu</div>
          <div className="text-[10.5px] text-[#6b7688] mt-px">Tamil Nadu · Active Parcels: {PARCEL_DATA.length}</div>
          <div className="mt-1.5 inline-flex items-center gap-1 text-[9.5px] font-bold text-[#d97706] bg-[#fdf1e0] px-2 py-0.5 rounded-xl uppercase tracking-[.04em]">
            ⚠ SYNTHETIC DATA
          </div>
        </div>

        {/* TOP-RIGHT: Map Action Buttons */}
        <div className="absolute top-3.5 right-3.5 z-50 flex flex-col gap-2">
          {[
            { Icon: ZoomIn,  label: 'Zoom in' },
            { Icon: ZoomOut, label: 'Zoom out' },
            { Icon: Layers,  label: 'Layers' },
            { Icon: Compass, label: 'Reset bearing' },
          ].map(({ Icon, label }) => (
            <button
              key={label}
              title={label}
              className="w-10 h-10 bg-white rounded-[9px] shadow-[0_4px_12px_rgba(11,36,71,.10)] grid place-items-center text-[#425066] border border-[#e3e8ef] hover:bg-[#eef3fb] hover:text-[#1b4079] transition-colors"
            >
              <Icon className="w-[18px] h-[18px]" />
            </button>
          ))}
        </div>

        {/* BOTTOM-LEFT: Legend */}
        <div className="absolute bottom-5 left-3.5 z-50 bg-white/[.96] backdrop-blur-sm px-3.5 py-3 rounded-[10px] shadow-[0_4px_12px_rgba(11,36,71,.10)] border border-[#e3e8ef] min-w-[150px] pointer-events-none">
          <h4 className="text-[10.5px] font-extrabold text-[#6b7688] uppercase tracking-[.06em] mb-2">PARCEL STATUS</h4>
          {[
            { color: '#16a34a', label: 'Verified' },
            { color: '#d97706', label: 'Warning' },
            { color: '#dc2626', label: 'Conflict / Dispute' },
            { color: '#2456a6', label: 'Pending' },
          ].map(({ color, label }) => (
            <div key={label} className="flex items-center gap-2.5 py-0.5 text-[12px] text-[#425066] font-medium">
              <div
                className="w-[15px] h-[15px] rounded-[4px] flex-shrink-0 border-[1.5px] border-black/10"
                style={{ background: color }}
              />
              {label}
            </div>
          ))}
        </div>

        {/* RIGHT DRAWER */}
        <div
          className={`absolute top-0 right-0 bottom-0 w-[370px] bg-white z-[1100] flex flex-col shadow-[-8px_0_28px_rgba(11,36,71,.14)] transition-transform duration-[280ms] ease-[cubic-bezier(.4,0,.2,1)] ${
            drawerOpen ? 'translate-x-0' : 'translate-x-full'
          }`}
        >
          {selectedParcel && (
            <>
              {/* Drawer Header */}
              <div className="bg-gradient-to-br from-[#12315e] to-[#0b2447] text-white px-[18px] pt-4 pb-[18px] flex-shrink-0 relative">
                <div className="text-[10.5px] font-bold text-[#8fb4e6] uppercase tracking-[.08em]">Selected Parcel</div>
                <div className="text-[22px] font-extrabold tracking-[.02em] mt-0.5 flex items-center gap-2.5 flex-wrap">
                  {selectedParcel.parcel_id}
                  <span className={`text-[11px] font-bold px-2.5 py-0.5 rounded-[14px] uppercase tracking-[.03em] ${statusPillClass(selectedParcel.status)}`}>
                    {selectedParcel.status_detail}
                  </span>
                </div>
                <button
                  onClick={() => setDrawerOpen(false)}
                  className="absolute top-3.5 right-3.5 text-[#b9cbe6] w-[30px] h-[30px] rounded-[7px] grid place-items-center hover:bg-white/[.12] hover:text-white transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>

                {/* ULPIN Block */}
                <div className="mt-3.5 bg-white/[.09] border-[1.5px] border-[#7fe9db]/40 rounded-[10px] px-3.5 py-3">
                  <div className="text-[10px] font-bold text-[#7fe9db] uppercase tracking-[.09em] flex items-center gap-1.5">
                    <MapIcon className="w-3 h-3" />
                    ULPIN · Common Parcel Identity
                  </div>
                  <div className="bd-mono text-[20px] font-extrabold text-white tracking-[.04em] mt-1">
                    {selectedParcel.ulpin}
                  </div>
                  <div className="text-[10.5px] text-[#a9c6ea] mt-1">
                    {selectedParcel.taluk} Taluk · {selectedParcel.district} District
                  </div>
                </div>
              </div>

              {/* Drawer Body */}
              <div className="flex-1 overflow-y-auto px-[18px] py-4">
                {/* Field Grid */}
                <div className="grid grid-cols-2 gap-px bg-[#e3e8ef] rounded-[10px] overflow-hidden border border-[#e3e8ef] mb-4">
                  {[
                    { label: 'Area',       value: `${selectedParcel.area.toFixed(2)} acres` },
                    { label: 'Land Use',   value: selectedParcel.land_use },
                    { label: 'Village',    value: selectedParcel.village },
                    { label: 'Survey No.', value: selectedParcel.survey_number },
                  ].map(({ label, value }) => (
                    <div key={label} className="bg-white px-3 py-2.5">
                      <div className="text-[10px] font-bold text-[#6b7688] uppercase tracking-[.05em]">{label}</div>
                      <div className="text-[13px] font-bold text-[#1f2733] mt-0.5">{value}</div>
                    </div>
                  ))}
                  <div className="bg-white px-3 py-2.5 col-span-2">
                    <div className="text-[10px] font-bold text-[#6b7688] uppercase tracking-[.05em]">Owner / Pattadar</div>
                    <div className="text-[14px] font-bold text-[#1f2733] mt-0.5">{selectedParcel.owner}</div>
                  </div>
                </div>

                {/* Risk Badge */}
                <div className="flex items-center gap-2 mb-4 flex-wrap">
                  <div className={`inline-flex items-center gap-1.5 text-[11px] font-bold px-2.5 py-1 rounded-xl ${riskBadgeClass(selectedParcel.risk_level)}`}>
                    {selectedParcel.risk_level} RISK
                  </div>
                  <div className={`inline-flex items-center gap-1.5 text-[11px] font-bold px-2.5 py-1 rounded-xl ${statusPillClass(selectedParcel.status)}`}>
                    {selectedParcel.status}
                  </div>
                </div>

                {/* Explore Button */}
                <button
                  onClick={() => onNavigateTab('parcels')}
                  className="w-full bg-gradient-to-br from-[#2456a6] to-[#1b4079] text-white font-bold text-[14px] py-3.5 rounded-[10px] shadow-[0_4px_12px_rgba(11,36,71,.10)] flex items-center justify-center gap-2.5 hover:brightness-110 hover:-translate-y-px hover:shadow-[0_12px_32px_rgba(11,36,71,.16)] transition-all"
                >
                  Explore Full Profile
                  <ChevronRight className="w-4 h-4" />
                </button>

                {/* Mini Connectivity */}
                <div className="mt-4">
                  <div className="text-[11px] font-extrabold text-[#6b7688] uppercase tracking-[.06em] mb-2.5 text-center">
                    CONNECTED DATASETS
                  </div>
                  <div className="flex flex-col items-center gap-0">
                    <div className="bd-mono font-extrabold text-[13px] text-white bg-[#1b4079] px-4 py-1.5 rounded-lg shadow-sm">
                      {selectedParcel.parcel_id}
                    </div>
                    <div className="text-[#cbd3de] text-base leading-none my-1">↓</div>
                    <div className="bd-mono font-extrabold text-[13px] text-white bg-[#118a80] px-4 py-1.5 rounded-lg shadow-sm">
                      {selectedParcel.ulpin}
                    </div>
                    <div className="text-[#cbd3de] text-base leading-none my-1">↓</div>
                    <div className="flex flex-wrap gap-1.5 justify-center">
                      {['Revenue', 'Registration', 'Survey', 'Tax', 'Planning'].map((ds) => (
                        <div
                          key={ds}
                          className="text-[10.5px] font-semibold text-[#425066] bg-[#f1f4f8] px-2.5 py-1 rounded-xl border border-[#e3e8ef]"
                        >
                          {ds}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </>
          )}

          {/* Empty drawer state (no parcel selected yet but drawer opened) */}
          {!selectedParcel && (
            <div className="flex-1 flex items-center justify-center text-[#6b7688] text-sm text-center px-6">
              Click a parcel on the map to view its details here.
            </div>
          )}
        </div>

        {/* Re-open drawer button (shown when drawer is closed) */}
        {!drawerOpen && (
          <button
            onClick={() => setDrawerOpen(true)}
            className="absolute top-1/2 right-0 -translate-y-1/2 z-[1100] bg-[#0b2447] text-white px-2 py-3 rounded-l-lg shadow-lg text-xs font-bold flex flex-col items-center gap-1 hover:bg-[#12315e] transition-colors"
          >
            <ChevronRight className="w-4 h-4 rotate-180" />
            <span style={{ writingMode: 'vertical-lr', transform: 'rotate(180deg)', fontSize: 10 }}>
              {selectedParcel ? selectedParcel.parcel_id : 'Detail'}
            </span>
          </button>
        )}
      </div>
    </div>
  );
}
