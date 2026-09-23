'use client';

import React, { useState, useMemo, useRef, useEffect } from 'react';
import {
  Search, X, Layers, SlidersHorizontal, ChevronRight, Map as MapIcon,
  AlertTriangle, CheckCircle2, Clock, FileText, Landmark, Coins,
  Building2, Leaf, LayoutGrid, Globe,
} from 'lucide-react';
import {
  CadastralMap,
  PARCEL_DATA,
  type ParcelData,
  type LayerState,
} from './CadastralMap';

// ── Derived synthetic record data for the profile panel ───────────────────────

function deriveRecords(p: ParcelData) {
  const isConflict = p.status === 'Conflict';
  const isWarning  = p.status === 'Warning';
  const isPending  = p.status === 'Pending';
  const highRisk   = p.risk_level === 'High';

  return {
    ror: {
      label: isConflict ? 'Dispute Recorded' : isPending ? 'Pending Mutation' : 'Active — No Disputes',
      cls:   isConflict ? 'conflict' : isPending ? 'warning' : 'ok',
      detail: `Pattadar: ${p.owner} · Survey: ${p.survey_number}`,
    },
    registration: {
      label: isConflict ? 'Encumbrance Found' : isWarning ? 'EC Warning' : 'Clear — No Encumbrance',
      cls:   isConflict ? 'conflict' : isWarning ? 'warning' : 'ok',
      detail: isWarning ? 'Mortgage registered 2019 · SRO Chengalpattu' : 'Last EC issued 2024',
    },
    survey: {
      label: highRisk ? 'Re-survey Pending' : 'Survey Settled',
      cls:   highRisk ? 'warning' : 'ok',
      detail: `Survey No. ${p.survey_number} · FMB available · ${p.area.toFixed(2)} acres`,
    },
    tax: {
      label: isWarning ? 'Tax Arrears' : 'Tax Paid — Current',
      cls:   isWarning ? 'warning' : 'ok',
      detail: isWarning ? 'Due: ₹4,200 (FY 2023–24)' : 'FY 2024–25 paid · Receipt available',
    },
    planning: {
      label: isConflict ? 'Use Change Detected' : 'Compliant with Master Plan',
      cls:   isConflict ? 'conflict' : 'ok',
      detail: `Zone: ${p.land_use} · Tirupporur Master Plan 2041`,
    },
  };
}

// ── Small helpers ─────────────────────────────────────────────────────────────

function statusColor(s: string) {
  if (s === 'Conflict') return '#dc2626';
  if (s === 'Warning')  return '#d97706';
  if (s === 'Pending')  return '#2456a6';
  return '#16a34a';
}

function riskBg(r: string) {
  if (r === 'High')   return 'bg-[#fdeaea] text-[#dc2626]';
  if (r === 'Medium') return 'bg-[#fdf1e0] text-[#d97706]';
  return 'bg-[#e7f6ec] text-[#16a34a]';
}

function clsCls(c: string) {
  if (c === 'conflict') return 'text-[#dc2626]';
  if (c === 'warning')  return 'text-[#d97706]';
  return 'text-[#16a34a]';
}

function clsIcon(c: string) {
  if (c === 'conflict') return <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0 text-[#dc2626]" />;
  if (c === 'warning')  return <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0 text-[#d97706]" />;
  return <CheckCircle2 className="w-3.5 h-3.5 flex-shrink-0 text-[#16a34a]" />;
}

// ── Layer toggle mini-row ─────────────────────────────────────────────────────

function LayerToggle({
  label, color, on, onToggle,
}: { label: string; color: string; on: boolean; onToggle: () => void }) {
  return (
    <div className="flex items-center gap-2.5 py-1.5 cursor-pointer" onClick={onToggle}>
      <div
        className="w-8 h-[18px] rounded-[20px] relative flex-shrink-0 transition-colors duration-150"
        style={{ background: on ? '#118a80' : '#cbd3de' }}
      >
        <div
          className="absolute top-0.5 w-3.5 h-3.5 rounded-full bg-white shadow-sm transition-transform duration-150"
          style={{ left: on ? '14px' : '2px' }}
        />
      </div>
      <span className="text-[12px] font-semibold text-[#425066] flex-1">{label}</span>
      <div
        className="w-3 h-3 rounded-[3px] flex-shrink-0 border border-black/10"
        style={{ background: color }}
      />
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export function CadastralView({
  onNavigateTab,
}: {
  onNavigateTab: (tab: any) => void;
}) {
  const [layers, setLayers] = useState<LayerState>({
    // Tier 1: Base Spatial
    parcels: true, ulpin: true, villageBoundary: false,
    // Tier 2: Governance
    ownership: true, landUse: false, zoning: false,
    registration: false, encumbrance: false, litigation: false,
    topologyConflicts: true,
    // Tier 3: Use-Case & Utility
    propertyTax: false, utilityLines: false, infrastructureRoW: false, envBuffers: false,
  });
  const [statusFilter, setStatusFilter] = useState('all');
  const [riskFilter,   setRiskFilter]   = useState('all');

  const [selectedParcel, setSelectedParcel] = useState<ParcelData | null>(null);
  const [panelOpen, setPanelOpen]           = useState(false);
  const [activeTab, setActiveTab]           = useState<'overview' | 'records' | 'risk'>('overview');

  const [showLayers,  setShowLayers]  = useState(false);
  const [showFilters, setShowFilters] = useState(false);

  // Globe map ref — lets us fly back to space orbit
  const mapInstanceRef = useRef<any>(null);
  const handleMapReady = (map: any) => { mapInstanceRef.current = map; };
  const flyToOrbit = () => {
    const m = mapInstanceRef.current;
    if (!m) return;
    // Re-assert globe projection (MapLibre GL 4.x may need explicit re-apply)
    try { (m as any).setProjection({ type: 'globe' }); } catch (_) {}
    m.flyTo({ center: [78.9629, 20.5937], zoom: 2.5, duration: 4500, curve: 1.8, essential: true });
  };
  const flyToParcels = () => {
    const m = mapInstanceRef.current;
    if (!m) return;
    m.flyTo({ center: [80.187375, 12.729005], zoom: 13, duration: 4000, curve: 1.6, essential: true });
  };

  const [searchQuery,   setSearchQuery]   = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const searchRef = useRef<HTMLDivElement>(null);

  // Close dropdowns on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const searchResults = useMemo(() => {
    if (searchQuery.trim().length < 2) return [];
    const q = searchQuery.toLowerCase();
    return PARCEL_DATA.filter(
      (p) =>
        p.parcel_id.toLowerCase().includes(q) ||
        p.ulpin.toLowerCase().includes(q) ||
        p.owner.toLowerCase().includes(q) ||
        p.survey_number.toLowerCase().includes(q)
    ).slice(0, 6);
  }, [searchQuery]);

  const visibleCount = useMemo(() => {
    return PARCEL_DATA.filter((p) => {
      if (statusFilter !== 'all' && p.status.toLowerCase() !== statusFilter) return false;
      if (riskFilter   !== 'all' && p.risk_level.toLowerCase() !== riskFilter)  return false;
      return true;
    }).length;
  }, [statusFilter, riskFilter]);

  const toggleLayer = (key: keyof LayerState) =>
    setLayers((prev) => ({ ...prev, [key]: !prev[key] }));

  const handleParcelSelect = (parcel: ParcelData) => {
    setSelectedParcel(parcel);
    setPanelOpen(true);
    setActiveTab('overview');
    setSearchQuery('');
    setShowSuggestions(false);
  };

  const records = selectedParcel ? deriveRecords(selectedParcel) : null;

  const filterDesc = [
    statusFilter !== 'all' ? `Status: ${statusFilter}` : '',
    riskFilter   !== 'all' ? `Risk: ${riskFilter}` : '',
  ].filter(Boolean).join(' · ') || 'All parcels';

  return (
    <div className="flex-1 relative overflow-hidden">

      {/* ── Full-screen globe map ──────────────────────────────────────────── */}
      <CadastralMap
        globe
        onMapReady={handleMapReady}
        layers={layers}
        statusFilter={statusFilter}
        riskFilter={riskFilter}
        selectedParcelId={selectedParcel?.parcel_id ?? null}
        onParcelSelect={handleParcelSelect}
      />

      {/* ── TOP-LEFT: District badge ──────────────────────────────────────── */}
      <div className="absolute top-3 left-3 z-50 bg-white/[.94] backdrop-blur-sm px-3.5 py-2.5 rounded-[10px] shadow-[0_4px_12px_rgba(11,36,71,.12)] border border-[#e3e8ef] pointer-events-none">
        <div className="flex items-center gap-2">
          <MapIcon className="w-3.5 h-3.5 text-[#1b4079]" />
          <span className="text-[12.5px] font-extrabold text-[#12315e]">Tirupporur Village · Chengalpattu</span>
        </div>
        <div className="text-[10.5px] text-[#6b7688] mt-0.5">Tamil Nadu · {PARCEL_DATA.length} parcels registered</div>
        <div className="mt-1.5 inline-flex items-center gap-1 text-[9.5px] font-bold text-[#d97706] bg-[#fdf1e0] px-2 py-0.5 rounded-xl uppercase tracking-[.04em]">
          ⚠ SYNTHETIC DEMO DATA
        </div>
      </div>

      {/* ── TOP-CENTER: Search bar ────────────────────────────────────────── */}
      <div
        ref={searchRef}
        className="absolute top-3 left-1/2 -translate-x-1/2 z-50 w-[420px]"
      >
        <div className="relative">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[#6b7688] pointer-events-none" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => { setSearchQuery(e.target.value); setShowSuggestions(true); }}
            onFocus={() => setShowSuggestions(true)}
            placeholder="Search ULPIN, survey no., owner name…"
            className="w-full h-10 pl-10 pr-10 text-[13px] rounded-[10px] bg-white/[.96] backdrop-blur-sm shadow-[0_4px_12px_rgba(11,36,71,.14)] border border-[#e3e8ef] text-[#1f2733] placeholder-[#9aa4b3] focus:outline-none focus:border-[#118a80] focus:ring-2 focus:ring-[#118a80]/20 transition-all"
          />
          {searchQuery && (
            <button
              onClick={() => { setSearchQuery(''); setShowSuggestions(false); }}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-[#9aa4b3] hover:text-[#425066]"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Suggestions dropdown */}
        {showSuggestions && searchQuery.trim().length >= 2 && (
          <div className="absolute top-12 left-0 right-0 bg-white rounded-[10px] shadow-[0_12px_32px_rgba(11,36,71,.18)] border border-[#e3e8ef] overflow-hidden z-[200]">
            {searchResults.length === 0 ? (
              <div className="px-4 py-3 text-[12.5px] text-[#6b7688] text-center">No parcels match "{searchQuery}"</div>
            ) : (
              <>
                <div className="px-3.5 py-2 text-[10.5px] font-bold text-[#6b7688] uppercase tracking-[.05em] bg-[#f7f9fc] border-b border-[#f1f4f8]">
                  {searchResults.length} result{searchResults.length !== 1 ? 's' : ''} found
                </div>
                {searchResults.map((p) => (
                  <div
                    key={p.parcel_id}
                    onClick={() => handleParcelSelect(p)}
                    className="flex items-center gap-3 px-3.5 py-2.5 cursor-pointer hover:bg-[#eef3fb] border-b border-[#f1f4f8] last:border-0 transition-colors"
                  >
                    <span className="bd-mono text-[11px] font-bold text-[#1b4079] bg-[#eef3fb] px-2 py-0.5 rounded-md flex-shrink-0">
                      {p.parcel_id}
                    </span>
                    <div className="flex-1 min-w-0">
                      <div className="text-[12.5px] font-semibold text-[#1f2733] truncate">{p.ulpin}</div>
                      <div className="text-[11px] text-[#6b7688] truncate">Survey {p.survey_number} · {p.owner}</div>
                    </div>
                    <span
                      className="text-[10px] font-bold px-2 py-0.5 rounded-xl flex-shrink-0"
                      style={{ background: `${statusColor(p.status)}22`, color: statusColor(p.status) }}
                    >
                      {p.status}
                    </span>
                  </div>
                ))}
              </>
            )}
          </div>
        )}
      </div>

      {/* ── TOP-RIGHT: Globe controls + Layer + Filter ────────────────────── */}
      <div className="absolute top-3 right-3 z-50 flex items-center gap-2">

        {/* Globe orbit button */}
        <button
          onClick={flyToOrbit}
          title="Zoom out to globe view"
          className="flex items-center gap-2 h-10 px-3.5 rounded-[10px] bg-[#0b2447]/[.88] backdrop-blur-sm text-[#7fe9db] border border-[#7fe9db]/30 text-[12.5px] font-semibold hover:bg-[#12315e]/90 transition-colors shadow-[0_4px_12px_rgba(11,36,71,.22)]"
        >
          <Globe className="w-4 h-4" />
          Globe View
        </button>

        {/* Fly to parcels button */}
        <button
          onClick={flyToParcels}
          title="Fly to Chengalpattu parcels"
          className="flex items-center gap-2 h-10 px-3.5 rounded-[10px] bg-[#0b2447]/[.88] backdrop-blur-sm text-[#aac4e8] border border-white/10 text-[12.5px] font-semibold hover:bg-[#12315e]/90 transition-colors shadow-[0_4px_12px_rgba(11,36,71,.22)]"
        >
          <MapIcon className="w-4 h-4" />
          Fly to Parcels
        </button>

        {/* Layer control */}
        <div className="relative">
          <button
            onClick={() => { setShowLayers((v) => !v); setShowFilters(false); }}
            className={`flex items-center gap-2 h-10 px-3.5 rounded-[10px] shadow-[0_4px_12px_rgba(11,36,71,.12)] border text-[12.5px] font-semibold transition-colors ${
              showLayers
                ? 'bg-[#1b4079] text-white border-[#1b4079]'
                : 'bg-white/[.96] text-[#425066] border-[#e3e8ef] hover:bg-[#eef3fb]'
            }`}
          >
            <Layers className="w-4 h-4" />
            Layers
          </button>

          {showLayers && (
            <div className="absolute top-12 right-0 w-[272px] bg-white rounded-[10px] shadow-[0_12px_32px_rgba(11,36,71,.18)] border border-[#e3e8ef] p-3.5 z-[200] max-h-[80vh] overflow-y-auto">

              {/* Tier 1: Base Spatial */}
              <div className="flex items-center gap-1.5 mb-2">
                <div className="w-2 h-2 rounded-full bg-[#3b6fbf] flex-shrink-0" />
                <span className="text-[10px] font-extrabold text-[#1b4079] uppercase tracking-[.08em]">Tier 1 — Base Spatial</span>
              </div>
              <LayerToggle label="Parcel Geometries"     color="#3b6fbf" on={layers.parcels}         onToggle={() => toggleLayer('parcels')} />
              <LayerToggle label="ULPIN / Parcel Labels" color="#9aa4b3" on={layers.ulpin}           onToggle={() => toggleLayer('ulpin')} />
              <LayerToggle label="Village / Ward Boundary" color="#c9b48a" on={layers.villageBoundary} onToggle={() => toggleLayer('villageBoundary')} />

              {/* Tier 2: Essential Governance */}
              <div className="flex items-center gap-1.5 mt-3.5 mb-2">
                <div className="w-2 h-2 rounded-full bg-[#0f766e] flex-shrink-0" />
                <span className="text-[10px] font-extrabold text-[#0f766e] uppercase tracking-[.08em]">Tier 2 — Governance</span>
              </div>
              <LayerToggle label="Ownership Status (RoR)" color="#3b6fbf" on={layers.ownership}       onToggle={() => toggleLayer('ownership')} />
              <LayerToggle label="Land Use Classification" color="#16a34a" on={layers.landUse}         onToggle={() => toggleLayer('landUse')} />
              <LayerToggle label="Zoning / Master Plan"   color="#2563eb" on={layers.zoning}          onToggle={() => toggleLayer('zoning')} />
              <LayerToggle label="Registered Deeds"       color="#7c3aed" on={layers.registration}    onToggle={() => toggleLayer('registration')} />
              <LayerToggle label="Encumbrance (EC)"       color="#d97706" on={layers.encumbrance}     onToggle={() => toggleLayer('encumbrance')} />
              <LayerToggle label="Court Litigation / Stay" color="#7c3aed" on={layers.litigation}     onToggle={() => toggleLayer('litigation')} />
              <LayerToggle label="Topology Conflicts"     color="#dc2626" on={layers.topologyConflicts} onToggle={() => toggleLayer('topologyConflicts')} />

              {/* Tier 3: Use-Case & Utility */}
              <div className="flex items-center gap-1.5 mt-3.5 mb-2">
                <div className="w-2 h-2 rounded-full bg-[#d97706] flex-shrink-0" />
                <span className="text-[10px] font-extrabold text-[#92400e] uppercase tracking-[.08em]">Tier 3 — Use-Case & Utility</span>
              </div>
              <LayerToggle label="Property Tax Tagging"   color="#d97706" on={layers.propertyTax}     onToggle={() => toggleLayer('propertyTax')} />
              <LayerToggle label="Utility Lines (W/E/G)"  color="#0891b2" on={layers.utilityLines}    onToggle={() => toggleLayer('utilityLines')} />
              <LayerToggle label="Infrastructure RoW"     color="#78716c" on={layers.infrastructureRoW} onToggle={() => toggleLayer('infrastructureRoW')} />
              <LayerToggle label="Env. Buffers (CRZ/Forest)" color="#15803d" on={layers.envBuffers}   onToggle={() => toggleLayer('envBuffers')} />
            </div>
          )}
        </div>

        {/* Filter control */}
        <div className="relative">
          <button
            onClick={() => { setShowFilters((v) => !v); setShowLayers(false); }}
            className={`flex items-center gap-2 h-10 px-3.5 rounded-[10px] shadow-[0_4px_12px_rgba(11,36,71,.12)] border text-[12.5px] font-semibold transition-colors ${
              showFilters || (statusFilter !== 'all' || riskFilter !== 'all')
                ? 'bg-[#1b4079] text-white border-[#1b4079]'
                : 'bg-white/[.96] text-[#425066] border-[#e3e8ef] hover:bg-[#eef3fb]'
            }`}
          >
            <SlidersHorizontal className="w-4 h-4" />
            Filter
            {(statusFilter !== 'all' || riskFilter !== 'all') && (
              <span className="w-5 h-5 rounded-full bg-[#14a89a] text-white text-[10px] font-bold grid place-items-center">
                {(statusFilter !== 'all' ? 1 : 0) + (riskFilter !== 'all' ? 1 : 0)}
              </span>
            )}
          </button>

          {showFilters && (
            <div className="absolute top-12 right-0 w-[280px] bg-white rounded-[10px] shadow-[0_12px_32px_rgba(11,36,71,.18)] border border-[#e3e8ef] p-3.5 z-[200]">
              <div className="text-[11px] font-bold text-[#425066] mb-1.5">Status</div>
              <div className="flex flex-wrap gap-1.5 mb-3">
                {['all', 'verified', 'conflict', 'warning', 'pending'].map((f) => (
                  <button
                    key={f}
                    onClick={() => setStatusFilter(f)}
                    className={`text-[11px] font-semibold px-2.5 py-1 rounded-[20px] transition-colors ${
                      statusFilter === f ? 'bg-[#1b4079] text-white' : 'bg-[#f1f4f8] text-[#425066] hover:bg-[#e3e8ef]'
                    }`}
                  >
                    {f.charAt(0).toUpperCase() + f.slice(1)}
                  </button>
                ))}
              </div>
              <div className="text-[11px] font-bold text-[#425066] mb-1.5">Risk</div>
              <div className="flex flex-wrap gap-1.5 mb-3">
                {['all', 'low', 'medium', 'high'].map((f) => (
                  <button
                    key={f}
                    onClick={() => setRiskFilter(f)}
                    className={`text-[11px] font-semibold px-2.5 py-1 rounded-[20px] transition-colors ${
                      riskFilter === f ? 'bg-[#1b4079] text-white' : 'bg-[#f1f4f8] text-[#425066] hover:bg-[#e3e8ef]'
                    }`}
                  >
                    {f.charAt(0).toUpperCase() + f.slice(1)}
                  </button>
                ))}
              </div>
              {(statusFilter !== 'all' || riskFilter !== 'all') && (
                <button
                  onClick={() => { setStatusFilter('all'); setRiskFilter('all'); }}
                  className="w-full text-[11.5px] font-semibold text-[#2456a6] bg-[#eef3fb] py-1.5 rounded-[6px] hover:brightness-95 transition-[filter]"
                >
                  Reset Filters
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      {/* ── BOTTOM-LEFT: Three-Tier Legend ───────────────────────────────── */}
      <div className="absolute bottom-12 left-3 z-50 bg-white/[.96] backdrop-blur-sm px-3.5 py-3 rounded-[10px] shadow-[0_4px_12px_rgba(11,36,71,.10)] border border-[#e3e8ef] pointer-events-none min-w-[180px]">
        {/* Always show parcel status */}
        <h4 className="text-[10px] font-extrabold text-[#1b4079] uppercase tracking-[.06em] mb-1.5">Tier 1 — Parcel Status</h4>
        {[
          { color: '#16a34a', border: '#00ff88', label: 'Verified' },
          { color: '#d97706', border: '#ffa500', label: 'Warning' },
          { color: '#dc2626', border: '#ff4400', label: 'Conflict / Dispute' },
          { color: '#2456a6', border: '#44aaff', label: 'Pending' },
        ].map(({ color, border, label }) => (
          <div key={label} className="flex items-center gap-2 py-0.5 text-[11px] text-[#425066] font-medium">
            <div className="w-3 h-3 rounded-[3px] flex-shrink-0 border-2" style={{ background: `${color}55`, borderColor: border }} />
            {label}
          </div>
        ))}

        {/* Tier 2 legend entries — show when any governance layer is on */}
        {(layers.zoning || layers.encumbrance || layers.litigation || layers.registration) && (
          <>
            <div className="border-t border-[#f1f4f8] mt-2 pt-2">
              <h4 className="text-[10px] font-extrabold text-[#0f766e] uppercase tracking-[.06em] mb-1.5">Tier 2 — Governance</h4>
              {layers.zoning && (
                <>
                  <div className="flex items-center gap-2 py-0.5 text-[11px] text-[#425066]"><div className="w-3 h-3 rounded-[3px] border-2 border-[#2563eb]" style={{ background: '#2563eb33' }} />Residential Zone</div>
                  <div className="flex items-center gap-2 py-0.5 text-[11px] text-[#425066]"><div className="w-3 h-3 rounded-[3px] border-2 border-[#65a30d]" style={{ background: '#65a30d33' }} />Agricultural Zone</div>
                  <div className="flex items-center gap-2 py-0.5 text-[11px] text-[#425066]"><div className="w-3 h-3 rounded-[3px] border-2 border-[#c026d3]" style={{ background: '#c026d333' }} />Commercial Zone</div>
                </>
              )}
              {layers.encumbrance && <div className="flex items-center gap-2 py-0.5 text-[11px] text-[#425066]"><div className="w-3 h-3 rounded-[3px] border-2 border-dashed border-[#d97706]" style={{ background: '#d9770633' }} />Encumbrance (EC)</div>}
              {layers.litigation && <div className="flex items-center gap-2 py-0.5 text-[11px] text-[#425066]"><div className="w-3 h-3 rounded-[3px] border-2 border-dashed border-[#7c3aed]" style={{ background: '#7c3aed33' }} />Court Litigation / Stay</div>}
              {layers.registration && <div className="flex items-center gap-2 py-0.5 text-[11px] text-[#425066]"><div className="w-3 h-3 rounded-full bg-[#7c3aed]" />Registered Deed</div>}
            </div>
          </>
        )}

        {/* Tier 3 legend entries */}
        {(layers.utilityLines || layers.infrastructureRoW || layers.envBuffers) && (
          <>
            <div className="border-t border-[#f1f4f8] mt-2 pt-2">
              <h4 className="text-[10px] font-extrabold text-[#92400e] uppercase tracking-[.06em] mb-1.5">Tier 3 — Utility</h4>
              {layers.utilityLines && (
                <>
                  <div className="flex items-center gap-2 py-0.5 text-[11px] text-[#425066]"><div className="h-[3px] w-6 rounded" style={{ background: '#0891b2' }} />Water Main</div>
                  <div className="flex items-center gap-2 py-0.5 text-[11px] text-[#425066]"><div className="h-[3px] w-6 rounded" style={{ background: '#f59e0b' }} />Electricity Line</div>
                  <div className="flex items-center gap-2 py-0.5 text-[11px] text-[#425066]"><div className="h-[3px] w-6 rounded border-t-2 border-dashed border-[#f97316]" />Gas Pipeline</div>
                </>
              )}
              {layers.infrastructureRoW && <div className="flex items-center gap-2 py-0.5 text-[11px] text-[#425066]"><div className="w-3 h-3 rounded-[3px]" style={{ background: '#78716c55' }} />Infra. RoW Corridor</div>}
              {layers.envBuffers && (
                <>
                  <div className="flex items-center gap-2 py-0.5 text-[11px] text-[#425066]"><div className="w-3 h-3 rounded-[3px]" style={{ background: '#0891b233' }} />Waterbody Buffer</div>
                  <div className="flex items-center gap-2 py-0.5 text-[11px] text-[#425066]"><div className="w-3 h-3 rounded-[3px]" style={{ background: '#15803d33' }} />Forest Buffer</div>
                </>
              )}
            </div>
          </>
        )}
      </div>

      {/* ── BOTTOM STATUS BAR ─────────────────────────────────────────────── */}
      <div className="absolute bottom-0 left-0 right-0 z-50 h-9 bg-[#0b2447]/[.88] backdrop-blur-sm flex items-center gap-5 px-4 text-[11px] text-[#a9c6ea] font-medium border-t border-white/10">
        <span className="flex items-center gap-1.5">
          <LayoutGrid className="w-3.5 h-3.5 text-[#7fe9db]" />
          <span className="text-white font-semibold">{visibleCount}</span>
          <span>/ {PARCEL_DATA.length} parcels visible</span>
        </span>
        <span className="text-[#6d8cb8]">·</span>
        <span>Filter: <span className="text-white">{filterDesc}</span></span>
        {selectedParcel && (
          <>
            <span className="text-[#6d8cb8]">·</span>
            <span>
              Selected: <span className="bd-mono text-[#7fe9db] font-bold">{selectedParcel.parcel_id}</span>
              <span className="ml-1.5">{selectedParcel.owner}</span>
            </span>
          </>
        )}
        <span className="ml-auto text-[#4a6a8c]">© Esri · Maxar · Earthstar Geographics · OpenStreetMap</span>
      </div>

      {/* ── CLOSE layer/filter menus on backdrop click ────────────────────── */}
      {(showLayers || showFilters) && (
        <div
          className="absolute inset-0 z-[100]"
          onClick={() => { setShowLayers(false); setShowFilters(false); }}
        />
      )}

      {/* ── RIGHT PANEL: Full parcel profile ──────────────────────────────── */}
      <div
        className={`absolute top-0 right-0 bottom-9 w-[420px] bg-white z-[1100] flex flex-col shadow-[-8px_0_32px_rgba(11,36,71,.18)] transition-transform duration-[280ms] ease-[cubic-bezier(.4,0,.2,1)] ${
          panelOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        {selectedParcel && (
          <>
            {/* Panel header */}
            <div className="bg-gradient-to-br from-[#12315e] to-[#0b2447] text-white px-5 pt-4 pb-5 flex-shrink-0 relative">
              <div className="text-[10.5px] font-bold text-[#8fb4e6] uppercase tracking-[.1em] mb-1">Cadastral Parcel Profile</div>
              <div className="flex items-start gap-3">
                <div className="flex-1 min-w-0">
                  <div className="text-[22px] font-extrabold tracking-[.02em] leading-none">{selectedParcel.parcel_id}</div>
                  <div className="bd-mono text-[13px] text-[#7fe9db] font-bold mt-1">{selectedParcel.ulpin}</div>
                </div>
                <span
                  className="text-[11px] font-bold px-3 py-1 rounded-[14px] uppercase tracking-[.03em] flex-shrink-0 mt-0.5"
                  style={{ background: `${statusColor(selectedParcel.status)}33`, color: statusColor(selectedParcel.status), border: `1.5px solid ${statusColor(selectedParcel.status)}66` }}
                >
                  {selectedParcel.status}
                </span>
              </div>
              <div className="flex items-center gap-2 mt-2.5 flex-wrap">
                <span className={`text-[11px] font-bold px-2.5 py-0.5 rounded-xl ${riskBg(selectedParcel.risk_level)}`}>
                  {selectedParcel.risk_level} RISK
                </span>
                <span className="text-[11px] text-[#8fb4e6]">
                  {selectedParcel.survey_number} · {selectedParcel.area.toFixed(2)} acres
                </span>
              </div>
              <button
                onClick={() => setPanelOpen(false)}
                className="absolute top-4 right-4 w-8 h-8 rounded-[7px] text-[#b9cbe6] hover:bg-white/[.12] hover:text-white grid place-items-center transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Tab bar */}
            <div className="flex border-b border-[#e3e8ef] bg-[#f7f9fc] flex-shrink-0">
              {(['overview', 'records', 'risk'] as const).map((t) => (
                <button
                  key={t}
                  onClick={() => setActiveTab(t)}
                  className={`flex-1 py-2.5 text-[12px] font-semibold transition-colors capitalize ${
                    activeTab === t
                      ? 'text-[#1b4079] border-b-2 border-[#1b4079] bg-white'
                      : 'text-[#6b7688] hover:text-[#1b4079] hover:bg-white/50'
                  }`}
                >
                  {t === 'records' ? 'Linked Records' : t === 'risk' ? 'Risk & Trust' : 'Overview'}
                </button>
              ))}
            </div>

            {/* Tab content */}
            <div className="flex-1 overflow-y-auto">

              {/* ── Overview tab ─────────────────────────────────────────── */}
              {activeTab === 'overview' && (
                <div className="p-4 space-y-4">
                  <div className="grid grid-cols-2 gap-px bg-[#e3e8ef] rounded-[10px] overflow-hidden border border-[#e3e8ef]">
                    {[
                      { label: 'Survey Number', value: selectedParcel.survey_number },
                      { label: 'Area',           value: `${selectedParcel.area.toFixed(2)} acres` },
                      { label: 'Land Use',       value: selectedParcel.land_use },
                      { label: 'Village',        value: selectedParcel.village },
                      { label: 'Taluk',          value: selectedParcel.taluk },
                      { label: 'District',       value: selectedParcel.district },
                    ].map(({ label, value }) => (
                      <div key={label} className="bg-white px-3 py-2.5">
                        <div className="text-[10px] font-bold text-[#6b7688] uppercase tracking-[.05em]">{label}</div>
                        <div className="text-[13px] font-bold text-[#1f2733] mt-0.5">{value}</div>
                      </div>
                    ))}
                    <div className="bg-white px-3 py-2.5 col-span-2">
                      <div className="text-[10px] font-bold text-[#6b7688] uppercase tracking-[.05em]">Pattadar / Owner</div>
                      <div className="text-[14px] font-bold text-[#1f2733] mt-0.5">{selectedParcel.owner}</div>
                    </div>
                  </div>

                  <div className="bg-[#f7f9fc] rounded-[10px] p-3.5 border border-[#e3e8ef]">
                    <div className="text-[11px] font-extrabold text-[#6b7688] uppercase tracking-[.06em] mb-2.5">Parcel Identity Chain</div>
                    <div className="flex flex-col items-center gap-1">
                      <div className="bd-mono font-extrabold text-[13px] text-white bg-[#1b4079] px-4 py-1.5 rounded-lg shadow-sm">{selectedParcel.parcel_id}</div>
                      <div className="text-[#cbd3de] text-base leading-none">↓</div>
                      <div className="bd-mono font-extrabold text-[13px] text-white bg-[#118a80] px-4 py-1.5 rounded-lg shadow-sm">{selectedParcel.ulpin}</div>
                      <div className="text-[#cbd3de] text-base leading-none">↓</div>
                      <div className="flex flex-wrap gap-1.5 justify-center">
                        {['Revenue RoR', 'Registration', 'Survey FMB', 'Property Tax', 'Master Plan'].map((d) => (
                          <span key={d} className="text-[10.5px] font-semibold text-[#425066] bg-white px-2.5 py-1 rounded-xl border border-[#e3e8ef]">{d}</span>
                        ))}
                      </div>
                    </div>
                  </div>

                  <button
                    onClick={() => onNavigateTab('parcels')}
                    className="w-full bg-gradient-to-br from-[#2456a6] to-[#1b4079] text-white font-bold text-[13.5px] py-3.5 rounded-[10px] shadow-md flex items-center justify-center gap-2 hover:brightness-110 hover:-translate-y-px transition-all"
                  >
                    Open Full Profile in Parcels View
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              )}

              {/* ── Linked Records tab ───────────────────────────────────── */}
              {activeTab === 'records' && records && (
                <div className="p-4 space-y-2.5">
                  {/* Tier badge header */}
                  <div className="text-[10px] font-extrabold text-[#9aa4b3] uppercase tracking-[.08em]">Tier 2 — Governance Records</div>
                  {[
                    { icon: <FileText className="w-4 h-4" />,  title: 'Revenue RoR',               r: records.ror,          source: 'Tamil Nilam Revenue System' },
                    { icon: <Landmark className="w-4 h-4" />,  title: 'Registered Deed (SRO)',      r: records.registration, source: 'NGDRS / SRO Portal' },
                    { icon: <Leaf className="w-4 h-4" />,      title: 'Encumbrance Certificate',    r: { label: records.registration.label, cls: records.registration.cls, detail: records.registration.detail }, source: 'NGDRS EC Search' },
                    { icon: <Building2 className="w-4 h-4" />, title: 'Planning / Zoning',          r: records.planning,     source: 'DTCP Master Plan Portal' },
                  ].map(({ icon, title, r, source }) => (
                    <div
                      key={title}
                      className="bg-white rounded-[10px] border border-[#e3e8ef] p-3.5 shadow-[0_1px_2px_rgba(11,36,71,.06)]"
                      style={{ borderLeft: `4px solid ${r.cls === 'conflict' ? '#dc2626' : r.cls === 'warning' ? '#d97706' : '#16a34a'}` }}
                    >
                      <div className="flex items-center gap-2.5 mb-1">
                        <div
                          className="w-7 h-7 rounded-[7px] grid place-items-center flex-shrink-0"
                          style={{ background: r.cls === 'conflict' ? '#fdeaea' : r.cls === 'warning' ? '#fdf1e0' : '#e7f6ec',
                                   color:      r.cls === 'conflict' ? '#dc2626' : r.cls === 'warning' ? '#d97706' : '#16a34a' }}
                        >
                          {icon}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="text-[12px] font-extrabold text-[#1f2733] uppercase tracking-[.03em]">{title}</div>
                        </div>
                        <div className={`flex items-center gap-1 text-[11px] font-bold ${clsCls(r.cls)}`}>
                          {clsIcon(r.cls)}
                          {r.label}
                        </div>
                      </div>
                      <div className="text-[11.5px] text-[#6b7688] pl-9">{r.detail}</div>
                      <div className="text-[10px] text-[#9aa4b3] pl-9 mt-1 flex items-center gap-1">
                        <Globe className="w-2.5 h-2.5" />
                        {source} · CACHED
                      </div>
                    </div>
                  ))}

                  {/* Court Litigation */}
                  {(selectedParcel?.status === 'Conflict' || selectedParcel?.risk_level === 'High') && (
                    <div className="bg-white rounded-[10px] border border-[#e3e8ef] p-3.5 shadow-[0_1px_2px_rgba(11,36,71,.06)]" style={{ borderLeft: '4px solid #7c3aed' }}>
                      <div className="flex items-center gap-2.5 mb-1">
                        <div className="w-7 h-7 rounded-[7px] grid place-items-center flex-shrink-0 bg-[#ede9fe] text-[#7c3aed]">
                          <AlertTriangle className="w-4 h-4" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="text-[12px] font-extrabold text-[#1f2733] uppercase tracking-[.03em]">Court Litigation / Stay</div>
                        </div>
                        <div className="flex items-center gap-1 text-[11px] font-bold text-[#7c3aed]">
                          <AlertTriangle className="w-3.5 h-3.5" /> ACTIVE STAY
                        </div>
                      </div>
                      <div className="text-[11.5px] text-[#6b7688] pl-9">Case OS-421/2024 · Chengalpattu District Court · Ownership Dispute</div>
                      <div className="text-[10px] text-[#9aa4b3] pl-9 mt-1 flex items-center gap-1">
                        <Globe className="w-2.5 h-2.5" />
                        eCourts NJDG Portal · CACHED
                      </div>
                    </div>
                  )}

                  <div className="text-[10px] font-extrabold text-[#9aa4b3] uppercase tracking-[.08em] pt-1">Tier 3 — Use-Case & Utility</div>
                  {[
                    { icon: <Coins className="w-4 h-4" />,      title: 'Property Tax',              r: records.tax,   source: 'CMDA / Panchayat Tax Portal' },
                    { icon: <Leaf className="w-4 h-4" />,       title: 'Survey & FMB',              r: records.survey, source: 'DILRMP / SVAMITVA Survey DB' },
                  ].map(({ icon, title, r, source }) => (
                    <div
                      key={title}
                      className="bg-white rounded-[10px] border border-[#e3e8ef] p-3.5 shadow-[0_1px_2px_rgba(11,36,71,.06)]"
                      style={{ borderLeft: `4px solid ${r.cls === 'conflict' ? '#dc2626' : r.cls === 'warning' ? '#d97706' : '#16a34a'}` }}
                    >
                      <div className="flex items-center gap-2.5 mb-1">
                        <div
                          className="w-7 h-7 rounded-[7px] grid place-items-center flex-shrink-0"
                          style={{ background: r.cls === 'conflict' ? '#fdeaea' : r.cls === 'warning' ? '#fdf1e0' : '#e7f6ec',
                                   color:      r.cls === 'conflict' ? '#dc2626' : r.cls === 'warning' ? '#d97706' : '#16a34a' }}
                        >
                          {icon}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="text-[12px] font-extrabold text-[#1f2733] uppercase tracking-[.03em]">{title}</div>
                        </div>
                        <div className={`flex items-center gap-1 text-[11px] font-bold ${clsCls(r.cls)}`}>
                          {clsIcon(r.cls)}
                          {r.label}
                        </div>
                      </div>
                      <div className="text-[11.5px] text-[#6b7688] pl-9">{r.detail}</div>
                      <div className="text-[10px] text-[#9aa4b3] pl-9 mt-1 flex items-center gap-1">
                        <Globe className="w-2.5 h-2.5" />
                        {source} · CACHED
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* ── Risk & Trust tab ─────────────────────────────────────── */}
              {activeTab === 'risk' && (
                <div className="p-4 space-y-4">
                  <div className="bg-white rounded-[10px] border border-[#e3e8ef] p-4 shadow-[0_1px_2px_rgba(11,36,71,.06)]">
                    <div className="text-[11px] font-extrabold text-[#6b7688] uppercase tracking-[.06em] mb-3">Trust Score Breakdown</div>
                    {[
                      { label: 'Ownership Consistency',  score: selectedParcel.status === 'Conflict' ? 28 : selectedParcel.status === 'Warning' ? 62 : 94, weight: '35%' },
                      { label: 'Transaction Velocity',   score: selectedParcel.risk_level === 'High' ? 34 : selectedParcel.risk_level === 'Medium' ? 65 : 88, weight: '25%' },
                      { label: 'Area Agreement',         score: selectedParcel.status === 'Warning' ? 55 : 91, weight: '20%' },
                      { label: 'Encumbrance Clarity',    score: selectedParcel.status === 'Conflict' ? 40 : 85, weight: '20%' },
                    ].map(({ label, score, weight }) => (
                      <div key={label} className="mb-2.5">
                        <div className="flex justify-between text-[11.5px] mb-1">
                          <span className="text-[#425066] font-medium">{label}</span>
                          <span className="text-[#9aa4b3] text-[10.5px]">weight {weight}</span>
                        </div>
                        <div className="h-2 bg-[#f1f4f8] rounded-full overflow-hidden">
                          <div
                            className="h-full rounded-full transition-all duration-500"
                            style={{
                              width: `${score}%`,
                              background: score >= 80 ? '#16a34a' : score >= 50 ? '#d97706' : '#dc2626',
                            }}
                          />
                        </div>
                        <div className="text-right text-[10.5px] font-bold mt-0.5" style={{ color: score >= 80 ? '#16a34a' : score >= 50 ? '#d97706' : '#dc2626' }}>
                          {score}/100
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="bg-white rounded-[10px] border border-[#e3e8ef] p-4 shadow-[0_1px_2px_rgba(11,36,71,.06)]">
                    <div className="text-[11px] font-extrabold text-[#6b7688] uppercase tracking-[.06em] mb-3">Risk Flags</div>
                    {selectedParcel.status === 'Conflict' ? (
                      <div className="space-y-2">
                        <div className="flex items-start gap-2 text-[12px] bg-[#fdeaea] text-[#dc2626] rounded-[8px] px-3 py-2.5 font-semibold">
                          <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0 mt-px" />
                          Ownership dispute filed — court order pending
                        </div>
                        <div className="flex items-start gap-2 text-[12px] bg-[#fdeaea] text-[#dc2626] rounded-[8px] px-3 py-2.5 font-semibold">
                          <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0 mt-px" />
                          Boundary overlap detected with adjacent parcel
                        </div>
                      </div>
                    ) : selectedParcel.status === 'Warning' ? (
                      <div className="space-y-2">
                        <div className="flex items-start gap-2 text-[12px] bg-[#fdf1e0] text-[#d97706] rounded-[8px] px-3 py-2.5 font-semibold">
                          <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0 mt-px" />
                          {selectedParcel.status_detail}
                        </div>
                      </div>
                    ) : selectedParcel.status === 'Pending' ? (
                      <div className="flex items-start gap-2 text-[12px] bg-[#eef3fb] text-[#2456a6] rounded-[8px] px-3 py-2.5 font-semibold">
                        <Clock className="w-3.5 h-3.5 flex-shrink-0 mt-px" />
                        Mutation pending — awaiting Tahsildar sanction
                      </div>
                    ) : (
                      <div className="flex items-start gap-2 text-[12px] bg-[#e7f6ec] text-[#16a34a] rounded-[8px] px-3 py-2.5 font-semibold">
                        <CheckCircle2 className="w-3.5 h-3.5 flex-shrink-0 mt-px" />
                        No active risk flags — parcel records consistent
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </>
        )}

        {/* Empty state when panel is open but nothing selected */}
        {!selectedParcel && (
          <div className="flex-1 flex items-center justify-center text-[#6b7688] text-sm text-center px-6">
            Click any parcel on the map to inspect its full profile.
          </div>
        )}
      </div>

      {/* Re-open panel button */}
      {!panelOpen && selectedParcel && (
        <button
          onClick={() => setPanelOpen(true)}
          className="absolute top-1/2 right-0 -translate-y-1/2 z-[1100] bg-[#0b2447] text-white px-2 py-3 rounded-l-lg shadow-lg flex flex-col items-center gap-1 hover:bg-[#12315e] transition-colors"
        >
          <ChevronRight className="w-4 h-4 rotate-180" />
          <span style={{ writingMode: 'vertical-lr', transform: 'rotate(180deg)', fontSize: 10, fontWeight: 700 }}>
            {selectedParcel.parcel_id}
          </span>
        </button>
      )}
    </div>
  );
}
