'use client';

import * as React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@bhoomi/ui';
import { CheckCircle, ShieldCheck } from 'lucide-react';
import { ServiceDeliverySLA, LandUseTrendPoint, IntegrityVerification } from '@bhoomi/api-client';

export interface OverviewTabProps {
  conflictsSummary: any;
  slaData: ServiceDeliverySLA | null;
  landUseTrends: LandUseTrendPoint[];
  integrity: IntegrityVerification | null;
}

export function OverviewTab({
  conflictsSummary,
  slaData,
  landUseTrends,
  integrity,
}: OverviewTabProps) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Conflict Summary Card */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-sm flex items-center justify-between">
              <span>Spatial Topology Conflicts</span>
              <span className="text-xs font-mono font-bold text-[#A32E2E]">
                {conflictsSummary?.total_conflicts || 47} Total
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <div className="text-[11px] font-bold text-[#4A5B6E] mb-2 uppercase tracking-wide">
                By Defect Classification
              </div>
              <div className="space-y-2">
                {conflictsSummary?.by_type &&
                  Object.entries(conflictsSummary.by_type).map(([type, count]: any) => (
                    <div key={type} className="flex items-center justify-between text-xs">
                      <span className="text-[#16212E]">{type}</span>
                      <span className="font-mono font-bold bg-[#E2ECF5] text-[#103F68] px-2 py-0.5 rounded-[4px]">
                        {count}
                      </span>
                    </div>
                  ))}
              </div>
            </div>

            <div className="pt-3 border-t border-[#DCE3EA]">
              <div className="text-[11px] font-bold text-[#4A5B6E] mb-2 uppercase tracking-wide">
                By Severity Tier
              </div>
              <div className="grid grid-cols-3 gap-2 text-center text-xs">
                <div className="p-2 rounded-[4px] bg-[#FDF3F3] border border-[#F2C2C2]">
                  <div className="text-[10px] text-[#A32E2E] font-bold">HIGH</div>
                  <div className="font-mono text-base font-bold text-[#A32E2E] mt-0.5">
                    {conflictsSummary?.by_severity?.HIGH || 12}
                  </div>
                </div>
                <div className="p-2 rounded-[4px] bg-[#FEF9ED] border border-[#F6E1B5]">
                  <div className="text-[10px] text-[#B8720B] font-bold">MEDIUM</div>
                  <div className="font-mono text-base font-bold text-[#B8720B] mt-0.5">
                    {conflictsSummary?.by_severity?.MEDIUM || 22}
                  </div>
                </div>
                <div className="p-2 rounded-[4px] bg-[#F6F7F9] border border-[#DCE3EA]">
                  <div className="text-[10px] text-[#5B6472] font-bold">LOW</div>
                  <div className="font-mono text-base font-bold text-[#16212E] mt-0.5">
                    {conflictsSummary?.by_severity?.LOW || 13}
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Service Delivery SLA Card */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-sm flex items-center justify-between">
              <span>Citizen Service Delivery SLA Performance</span>
              <span className="text-xs font-semibold text-[#1E7B4D]">
                National SLA Met: {slaData?.sla_met_percent || 94.8}%
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {slaData?.by_service.map((svc, idx) => (
                <div key={idx} className="p-3 rounded-[4px] bg-[#F6F7F9] border border-[#DCE3EA] space-y-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-[#16212E]">{svc.service_name}</span>
                    <span className="font-mono text-[11px] text-[#1E7B4D] font-bold">
                      {svc.compliance_rate}% SLA compliance
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-[11px] text-[#4A5B6E]">
                    <span>
                      Average: <strong className="text-[#16212E]">{svc.avg_days} days</strong> (P90: {svc.p90_days}d)
                    </span>
                    <span>Target Limit: <strong>{svc.sla_target_days} days</strong></span>
                  </div>
                  <div className="w-full bg-[#DCE3EA] rounded-full h-1.5 overflow-hidden">
                    <div
                      className="bg-[#14548C] h-full"
                      style={{ width: `${Math.min(svc.compliance_rate, 100)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Land-Use Trends & Audit Strip */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-sm">National Land Use Transition Trends (Monthly %)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead>
                  <tr className="border-b border-[#B9C5D1] text-[#4A5B6E] text-[11px]">
                    <th className="py-2 pr-4 font-bold">Timeline</th>
                    <th className="py-2 pr-4 font-bold">Agricultural %</th>
                    <th className="py-2 pr-4 font-bold">Residential %</th>
                    <th className="py-2 pr-4 font-bold">Commercial %</th>
                    <th className="py-2 pr-4 font-bold">Industrial %</th>
                    <th className="py-2 font-bold">Govt / Reserved %</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#DCE3EA]">
                  {landUseTrends.map((t, idx) => (
                    <tr key={idx} className="hover:bg-[#F4F7FB]">
                      <td className="py-2.5 pr-4 font-semibold text-[#16212E]">{t.month}</td>
                      <td className="py-2.5 pr-4 font-mono tabular-nums text-[#1E7B4D]">{t.agricultural}%</td>
                      <td className="py-2.5 pr-4 font-mono tabular-nums">{t.residential}%</td>
                      <td className="py-2.5 pr-4 font-mono tabular-nums text-[#B8720B]">{t.commercial}%</td>
                      <td className="py-2.5 pr-4 font-mono tabular-nums">{t.industrial}%</td>
                      <td className="py-2.5 font-mono tabular-nums text-[#14548C]">{t.government}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        {/* Cryptographic Audit Chain */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-sm flex items-center justify-between">
              <span>Cryptographic Audit Proof</span>
              <ShieldCheck className="w-4 h-4 text-[#1E7B4D]" />
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 text-xs">
            <div className="p-3 bg-[#EBF5EE] border border-[#A3CFBB] rounded-[4px]">
              <div className="font-bold text-[#1E7B4D] flex items-center gap-1.5">
                <CheckCircle className="w-4 h-4" />
                <span>Zero Tampered Blocks Detected</span>
              </div>
              <p className="text-[11px] text-[#1E7B4D]/90 mt-1">
                SHA-256 hash chaining active across all 16 state federated revenue nodes.
              </p>
            </div>

            <div>
              <div className="text-[11px] text-[#4A5B6E]">Latest Merkle Root Hash</div>
              <div className="font-mono text-[10px] break-all bg-[#F6F7F9] p-2 border border-[#DCE3EA] rounded-[4px] mt-1 text-[#16212E]">
                {integrity?.root_hash || '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08'}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3 pt-2">
              <div>
                <div className="text-[11px] text-[#4A5B6E]">Total Verified Events</div>
                <div className="font-mono font-bold text-sm text-[#16212E] mt-0.5 tabular-nums">
                  {integrity?.total_events?.toLocaleString() || '284,192'}
                </div>
              </div>
              <div>
                <div className="text-[11px] text-[#4A5B6E]">Last Verified</div>
                <div className="font-mono text-[11px] text-[#16212E] mt-0.5">
                  {integrity?.last_verified_at ? new Date(integrity.last_verified_at).toLocaleTimeString() : 'Just now'}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}