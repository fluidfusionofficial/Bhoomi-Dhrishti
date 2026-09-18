'use client';

import * as React from 'react';
import { ShieldCheck, Server, RefreshCw } from 'lucide-react';
import { Button } from '@bhoomi/ui';

export interface AdminHeaderProps {
  chainValid?: boolean;
  onRefreshAll?: () => void;
  isRefreshing?: boolean;
}

export function AdminHeader({
  chainValid = true,
  onRefreshAll,
  isRefreshing = false,
}: AdminHeaderProps) {
  return (
    <header className="bg-white border-b border-[#DCE3EA] flex-shrink-0">
      {/* 3px DoLR Tricolor Strip */}
      <div className="h-[3px] w-full flex">
        <div className="w-1/3 bg-[#FF9933]" />
        <div className="w-1/3 bg-[#FFFFFF]" />
        <div className="w-1/3 bg-[#138808]" />
      </div>

      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        {/* Left Branding */}
        <div className="flex items-center gap-3.5">
          <div className="w-9 h-9 rounded-[4px] bg-[#0B2E4E] text-white flex items-center justify-center font-serif font-bold text-sm tracking-tight">
            BD
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-bold text-[#16212E] tracking-tight leading-none">
                Bhoomi Dhrishti
              </h1>
              <span className="px-2 py-0.5 rounded-[4px] text-[10px] font-bold bg-[#E2ECF5] text-[#103F68] uppercase tracking-wider">
                Admin Console
              </span>
            </div>
            <p className="text-[11px] text-[#4A5B6E] mt-0.5">
              Department of Land Resources (DoLR) • Ministry of Rural Development, Govt. of India
            </p>
          </div>
        </div>

        {/* Right Status & Meta */}
        <div className="flex items-center gap-4">
          {/* Audit Chain Badge */}
          <div
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-[4px] text-xs font-semibold border ${
              chainValid
                ? 'bg-[#EBF5EE] text-[#1E7B4D] border-[#A3CFBB]'
                : 'bg-[#FDF3F3] text-[#A32E2E] border-[#F2C2C2]'
            }`}
          >
            <ShieldCheck className="w-4 h-4" />
            <span>Audit Chain: {chainValid ? 'VERIFIED' : 'TAMPERED'}</span>
          </div>

          {/* Node Environment */}
          <div className="hidden md:flex items-center gap-1.5 text-xs text-[#4A5B6E]">
            <Server className="w-3.5 h-3.5 text-[#14548C]" />
            <span className="font-mono text-[11px]">16 Services Active</span>
          </div>

          {/* Officer Session Badge */}
          <div className="flex items-center gap-2 pl-3 border-l border-[#DCE3EA]">
            <div className="w-7 h-7 rounded-full bg-[#14548C] text-white flex items-center justify-center text-xs font-bold font-serif">
              DL
            </div>
            <div className="text-right hidden sm:block">
              <div className="text-xs font-bold text-[#16212E] leading-tight">DoLR Administrator</div>
              <div className="text-[10px] text-[#4A5B6E] leading-tight">National Registry Node</div>
            </div>
          </div>

          {onRefreshAll && (
            <Button
              variant="outline"
              size="sm"
              onClick={onRefreshAll}
              disabled={isRefreshing}
              className="h-8 px-2.5 text-xs ml-1"
            >
              <RefreshCw className={`w-3.5 h-3.5 mr-1 ${isRefreshing ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          )}
        </div>
      </div>
    </header>
  );
}