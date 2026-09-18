'use client';

import * as React from 'react';
import { cn } from '../lib/utils';
import { ArrowUpRight, ArrowDownRight } from 'lucide-react';

export interface KPICardProps extends React.HTMLAttributes<HTMLDivElement> {
  title: string;
  value: string | number;
  delta?: {
    value: string | number;
    trend?: 'up' | 'down' | 'neutral';
    label?: string;
  };
  subtext?: string;
  icon?: React.ReactNode;
}

export function KPICard({
  title,
  value,
  delta,
  subtext,
  icon,
  className,
  ...props
}: KPICardProps) {
  return (
    <div
      className={cn(
        'rounded-lg border border-[#DCE3EA] bg-white p-5 flex flex-col justify-between',
        className
      )}
      {...props}
    >
      <div className="flex items-start justify-between">
        <span className="text-xs font-medium text-[#4A5B6E] tracking-tight">{title}</span>
        {icon && <div className="text-[#14548C]">{icon}</div>}
      </div>

      <div className="mt-3">
        <div className="text-3xl font-bold font-serif text-[#16212E] tracking-tight tabular-nums">
          {value}
        </div>

        {(delta || subtext) && (
          <div className="mt-2 flex items-center gap-2 text-xs">
            {delta && (
              <span
                className={cn(
                  'inline-flex items-center gap-0.5 font-medium',
                  delta.trend === 'up'
                    ? 'text-[#1E7B4D]'
                    : delta.trend === 'down'
                    ? 'text-[#A32E2E]'
                    : 'text-[#4A5B6E]'
                )}
              >
                {delta.trend === 'up' && <ArrowUpRight className="w-3.5 h-3.5" />}
                {delta.trend === 'down' && <ArrowDownRight className="w-3.5 h-3.5" />}
                <span>{delta.value}</span>
                {delta.label && <span className="text-[#4A5B6E] font-normal ml-0.5">{delta.label}</span>}
              </span>
            )}
            {subtext && !delta && (
              <span className="text-[#4A5B6E]">{subtext}</span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}