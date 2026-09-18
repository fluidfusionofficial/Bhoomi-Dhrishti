'use client';

import React, { useState, useEffect } from 'react';
import { Grid3x3, CheckCircle2, AlertTriangle, AlertOctagon } from 'lucide-react';
import { fetchTrustAnomaliesSummary } from '@bhoomi/api-client';

export interface KpiStripProps {
  onNavigate?: (tab: string) => void;
}

export default function KpiStrip({ onNavigate }: KpiStripProps) {
  const [kpis, setKpis] = useState({ total: 15, verified: 8, conflict: 5, risk: 4 });

  useEffect(() => {
    (async () => {
      try {
        const s = await fetchTrustAnomaliesSummary();
        setKpis(prev => ({ ...prev, risk: s.high_risk_count, conflict: s.medium_risk_count }));
      } catch {
        /* keep defaults */
      }
    })();
  }, []);

  const handleNavigate = (tab: string) => {
    onNavigate?.(tab);
  };

  return (
    <div
      className="flex items-stretch overflow-x-auto flex-shrink-0 bg-white shadow-sm z-[900]"
      style={{ borderBottom: '1px solid #e3e8ef' }}
    >
      {/* Tile 1 – Total Parcels */}
      <button
        type="button"
        onClick={() => handleNavigate('parcels')}
        className="flex items-center gap-[11px] px-5 py-[11px] min-w-max cursor-pointer hover:bg-[#f7f9fc] transition-colors"
        style={{ borderRight: '1px solid #f1f4f8' }}
      >
        <div
          className="flex items-center justify-center rounded-[9px]"
          style={{ width: 34, height: 34, background: '#eef3fb', color: '#1b4079', flexShrink: 0 }}
        >
          <Grid3x3 size={18} />
        </div>
        <div className="flex flex-col items-start">
          <span style={{ fontSize: 19, fontWeight: 800, color: '#1f2733', lineHeight: 1 }}>
            {kpis.total}
          </span>
          <span
            style={{
              fontSize: 11,
              fontWeight: 600,
              color: '#6b7688',
              textTransform: 'uppercase',
              letterSpacing: '0.04em',
              marginTop: 3,
            }}
          >
            Total Parcels
          </span>
        </div>
      </button>

      {/* Tile 2 – Verified */}
      <button
        type="button"
        onClick={() => handleNavigate('parcels')}
        className="flex items-center gap-[11px] px-5 py-[11px] min-w-max cursor-pointer hover:bg-[#f7f9fc] transition-colors"
        style={{ borderRight: '1px solid #f1f4f8' }}
      >
        <div
          className="flex items-center justify-center rounded-[9px]"
          style={{ width: 34, height: 34, background: '#e7f6ec', color: '#16a34a', flexShrink: 0 }}
        >
          <CheckCircle2 size={18} />
        </div>
        <div className="flex flex-col items-start">
          <span style={{ fontSize: 19, fontWeight: 800, color: '#1f2733', lineHeight: 1 }}>
            {kpis.verified}
          </span>
          <span
            style={{
              fontSize: 11,
              fontWeight: 600,
              color: '#6b7688',
              textTransform: 'uppercase',
              letterSpacing: '0.04em',
              marginTop: 3,
            }}
          >
            Verified
          </span>
        </div>
      </button>

      {/* Tile 3 – Conflict */}
      <button
        type="button"
        onClick={() => handleNavigate('spatial')}
        className="flex items-center gap-[11px] px-5 py-[11px] min-w-max cursor-pointer hover:bg-[#f7f9fc] transition-colors"
        style={{ borderRight: '1px solid #f1f4f8' }}
      >
        <div
          className="flex items-center justify-center rounded-[9px]"
          style={{ width: 34, height: 34, background: '#fdeaea', color: '#dc2626', flexShrink: 0 }}
        >
          <AlertTriangle size={18} />
        </div>
        <div className="flex flex-col items-start">
          <span style={{ fontSize: 19, fontWeight: 800, color: '#1f2733', lineHeight: 1 }}>
            {kpis.conflict}
          </span>
          <span
            style={{
              fontSize: 11,
              fontWeight: 600,
              color: '#6b7688',
              textTransform: 'uppercase',
              letterSpacing: '0.04em',
              marginTop: 3,
            }}
          >
            Conflict
          </span>
        </div>
      </button>

      {/* Tile 4 – High Risk */}
      <button
        type="button"
        onClick={() => handleNavigate('trust')}
        className="flex items-center gap-[11px] px-5 py-[11px] min-w-max cursor-pointer hover:bg-[#f7f9fc] transition-colors"
        style={{ borderRight: '1px solid #f1f4f8' }}
      >
        <div
          className="flex items-center justify-center rounded-[9px]"
          style={{ width: 34, height: 34, background: '#fdf1e0', color: '#d97706', flexShrink: 0 }}
        >
          <AlertOctagon size={18} />
        </div>
        <div className="flex flex-col items-start">
          <span style={{ fontSize: 19, fontWeight: 800, color: '#1f2733', lineHeight: 1 }}>
            {kpis.risk}
          </span>
          <span
            style={{
              fontSize: 11,
              fontWeight: 600,
              color: '#6b7688',
              textTransform: 'uppercase',
              letterSpacing: '0.04em',
              marginTop: 3,
            }}
          >
            High Risk
          </span>
        </div>
      </button>

      {/* Right-side tagline */}
      <div
        className="flex items-center gap-[14px] min-w-max"
        style={{ marginLeft: 'auto', paddingLeft: 22, paddingRight: 22 }}
      >
        <span style={{ fontWeight: 800, fontSize: 13, color: '#12315e', letterSpacing: '0.03em' }}>
          BHOOMI DHRISHTI
        </span>
        <span style={{ fontSize: 11, color: '#6b7688', maxWidth: 230 }}>
          Integrated Parcel-Centric Land Governance
        </span>
      </div>
    </div>
  );
}
