'use client';

import React, { useState, useEffect } from 'react';
import {
  Grid3x3,
  CheckCircle2,
  AlertTriangle,
  AlertOctagon,
  FileSpreadsheet,
  FileCheck2,
  Building2,
  Layers,
  Satellite,
  BarChart3,
  Scale,
  ShieldAlert,
} from 'lucide-react';
import { fetchTrustAnomaliesSummary } from '@bhoomi/api-client';
import { useRole, OfficerRole, OfficerNavTab } from '@/context/RoleContext';

interface KpiTile {
  label: string;
  value: number;
  icon: React.ElementType;
  iconBg: string;
  iconColor: string;
  navigateTo: OfficerNavTab;
}

function getKpisForRole(role: OfficerRole, data: { total: number; verified: number; conflict: number; risk: number }): KpiTile[] {
  const common: KpiTile = {
    label: 'Total Parcels',
    value: data.total,
    icon: Grid3x3,
    iconBg: '#eef3fb',
    iconColor: '#1b4079',
    navigateTo: 'parcels',
  };

  switch (role) {
    case 'tehsildar':
      return [
        common,
        { label: 'Verified', value: data.verified, icon: CheckCircle2, iconBg: '#e7f6ec', iconColor: '#16a34a', navigateTo: 'parcels' },
        { label: 'Pending Mutations', value: 7, icon: FileSpreadsheet, iconBg: '#E2ECF5', iconColor: '#14548C', navigateTo: 'revenue' },
        { label: 'Conflicts', value: data.conflict, icon: AlertTriangle, iconBg: '#fdeaea', iconColor: '#dc2626', navigateTo: 'spatial' },
        { label: 'High Risk', value: data.risk, icon: AlertOctagon, iconBg: '#fdf1e0', iconColor: '#d97706', navigateTo: 'trust' },
      ];

    case 'sub-registrar':
      return [
        common,
        { label: 'Pending Deeds', value: 5, icon: FileCheck2, iconBg: '#EDE9FE', iconColor: '#7C3AED', navigateTo: 'registration' },
        { label: 'EC Requests', value: 3, icon: Scale, iconBg: '#E2ECF5', iconColor: '#14548C', navigateTo: 'registration' },
        { label: 'Suspicious Transfers', value: 2, icon: ShieldAlert, iconBg: '#fdf1e0', iconColor: '#d97706', navigateTo: 'trust' },
      ];

    case 'town-planner':
      return [
        common,
        { label: 'Zone Violations', value: 4, icon: Building2, iconBg: '#FEF3C7', iconColor: '#B45309', navigateTo: 'planning' },
        { label: 'Permit Pending', value: 6, icon: FileCheck2, iconBg: '#E2ECF5', iconColor: '#14548C', navigateTo: 'planning' },
        { label: 'Land Use Changes', value: 3, icon: Satellite, iconBg: '#E0F2FE', iconColor: '#0369A1', navigateTo: 'satellite' },
      ];

    case 'surveyor':
      return [
        common,
        { label: 'Topology Conflicts', value: data.conflict, icon: Layers, iconBg: '#fdeaea', iconColor: '#dc2626', navigateTo: 'spatial' },
        { label: 'Demarcation Pending', value: 4, icon: Grid3x3, iconBg: '#E0F2FE', iconColor: '#0369A1', navigateTo: 'spatial' },
        { label: 'Encroachments', value: 2, icon: Satellite, iconBg: '#fdf1e0', iconColor: '#d97706', navigateTo: 'satellite' },
      ];

    case 'collector':
      return [
        common,
        { label: 'Verified', value: data.verified, icon: CheckCircle2, iconBg: '#e7f6ec', iconColor: '#16a34a', navigateTo: 'parcels' },
        { label: 'Conflicts', value: data.conflict, icon: AlertTriangle, iconBg: '#fdeaea', iconColor: '#dc2626', navigateTo: 'spatial' },
        { label: 'High Risk', value: data.risk, icon: AlertOctagon, iconBg: '#fdf1e0', iconColor: '#d97706', navigateTo: 'trust' },
        { label: 'District Score', value: 94, icon: BarChart3, iconBg: '#E2ECF5', iconColor: '#0B2E4E', navigateTo: 'analytics' },
      ];

    default:
      return [common];
  }
}

export interface KpiStripProps {
  onNavigate?: (tab: string) => void;
}

export default function KpiStrip({ onNavigate }: KpiStripProps) {
  const { role, config } = useRole();
  const [data, setData] = useState({ total: 15, verified: 8, conflict: 5, risk: 4 });

  useEffect(() => {
    (async () => {
      try {
        const s = await fetchTrustAnomaliesSummary();
        setData((prev) => ({ ...prev, risk: s.high_risk_count, conflict: s.medium_risk_count }));
      } catch {
        /* keep defaults */
      }
    })();
  }, []);

  const kpis = getKpisForRole(role, data);

  return (
    <div
      className="flex items-stretch overflow-x-auto flex-shrink-0 bg-white shadow-sm z-[900]"
      style={{ borderBottom: '1px solid #e3e8ef' }}
    >
      {kpis.map((kpi) => {
        const Icon = kpi.icon;
        return (
          <button
            key={kpi.label}
            type="button"
            onClick={() => onNavigate?.(kpi.navigateTo)}
            className="flex items-center gap-[11px] px-5 py-[11px] min-w-max cursor-pointer hover:bg-[#f7f9fc] transition-colors"
            style={{ borderRight: '1px solid #f1f4f8' }}
          >
            <div
              className="flex items-center justify-center rounded-[9px]"
              style={{ width: 34, height: 34, background: kpi.iconBg, color: kpi.iconColor, flexShrink: 0 }}
            >
              <Icon size={18} />
            </div>
            <div className="flex flex-col items-start">
              <span style={{ fontSize: 19, fontWeight: 800, color: '#1f2733', lineHeight: 1 }}>
                {kpi.value}
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
                {kpi.label}
              </span>
            </div>
          </button>
        );
      })}

      {/* Right-side role tagline */}
      <div
        className="flex items-center gap-[14px] min-w-max"
        style={{ marginLeft: 'auto', paddingLeft: 22, paddingRight: 22 }}
      >
        <span
          style={{
            display: 'inline-block',
            width: 8,
            height: 8,
            borderRadius: '50%',
            background: config.color,
          }}
        />
        <span style={{ fontWeight: 800, fontSize: 13, color: '#12315e', letterSpacing: '0.03em' }}>
          {config.title.toUpperCase()}
        </span>
        <span style={{ fontSize: 11, color: '#6b7688', maxWidth: 230 }}>
          {config.subtitle}
        </span>
      </div>
    </div>
  );
}
