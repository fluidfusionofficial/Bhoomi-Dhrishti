'use client';

import * as React from 'react';
import { cn } from '../lib/utils';
import { Building2, ShieldCheck, MapPin, User } from 'lucide-react';

export interface JurisdictionBarProps extends React.HTMLAttributes<HTMLDivElement> {
  stateName?: string;
  stateCode?: string;
  districtName?: string;
  districtCode?: string;
  officerName?: string;
  officerRole?: string;
  jurisdictionScope?: string;
}

export function JurisdictionBar({
  stateName = 'Tamil Nadu',
  stateCode = 'TN',
  districtName = 'Tiruvannamalai',
  districtCode = '607',
  officerName = 'R. Sundaram',
  officerRole = 'Revenue Divisional Officer',
  jurisdictionScope = 'District Jurisdiction Scoped',
  className,
  ...props
}: JurisdictionBarProps) {
  return (
    <div
      className={cn(
        'w-full bg-[#0B2E4E] text-white px-6 py-2.5 flex items-center justify-between border-b border-[#14548C] text-xs font-medium',
        className
      )}
      {...props}
    >
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2">
          <Building2 className="w-4 h-4 text-[#E2ECF5]" />
          <span className="text-[#E2ECF5] uppercase tracking-wider font-semibold text-[11px]">
            Jurisdiction Scope
          </span>
          <span className="bg-[#14548C] px-2 py-0.5 rounded-[4px] font-semibold text-white">
            {stateName} ({stateCode})
          </span>
          <span className="text-[#DCE3EA]">/</span>
          <span className="bg-[#14548C] px-2 py-0.5 rounded-[4px] font-semibold text-white">
            {districtName} (LGD: {districtCode})
          </span>
        </div>

        <div className="hidden md:flex items-center gap-1.5 text-[#E2ECF5]/80">
          <MapPin className="w-3.5 h-3.5" />
          <span>{jurisdictionScope}</span>
        </div>
      </div>

      <div className="flex items-center gap-5">
        <div className="flex items-center gap-1.5 text-[#E2ECF5]">
          <ShieldCheck className="w-4 h-4 text-[#1E7B4D]" />
          <span className="hidden sm:inline">Role:</span>
          <span className="font-semibold text-white">{officerRole}</span>
        </div>

        <div className="flex items-center gap-2 pl-3 border-l border-[#14548C]">
          <div className="w-6 h-6 rounded-full bg-[#14548C] text-white flex items-center justify-center font-bold text-[11px]">
            {officerName.split(' ').map(n => n[0]).join('').slice(0, 2)}
          </div>
          <span className="font-semibold text-white">{officerName}</span>
        </div>
      </div>
    </div>
  );
}