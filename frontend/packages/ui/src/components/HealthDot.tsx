'use client';

import * as React from 'react';
import { cn } from '../lib/utils';

export type ServiceHealthStatus = 'healthy' | 'unhealthy' | 'degraded' | 'checking';

export interface ServiceHealthItem {
  id: string;
  name: string;
  status: ServiceHealthStatus;
  port?: number;
  endpoint?: string;
  latencyMs?: number;
  message?: string;
}

export interface HealthDotProps {
  item: ServiceHealthItem;
  className?: string;
}

export function HealthDot({ item, className }: HealthDotProps) {
  const dotColor = {
    healthy: 'bg-[#1E7B4D]',
    unhealthy: 'bg-[#A32E2E]',
    degraded: 'bg-[#B8720B]',
    checking: 'bg-[#5B6472]',
  }[item.status];

  return (
    <div
      className={cn(
        'group relative flex items-center gap-2 p-2 rounded-[4px] border border-[#DCE3EA] bg-white hover:bg-[#F4F7FB] transition-colors',
        className
      )}
      title={`${item.name}: ${item.status}${item.latencyMs != null ? ` (${item.latencyMs}ms)` : ''}`}
    >
      <span className={cn('w-2.5 h-2.5 rounded-full flex-shrink-0', dotColor)} />
      <div className="flex flex-col min-w-0 flex-1">
        <span className="text-xs font-medium text-[#16212E] truncate">{item.name}</span>
        {item.latencyMs != null && (
          <span className="text-[10px] text-[#4A5B6E] tabular-nums">
            {item.latencyMs}ms
          </span>
        )}
      </div>
    </div>
  );
}

export interface HealthGridProps {
  services: ServiceHealthItem[];
  className?: string;
}

export function HealthGrid({ services, className }: HealthGridProps) {
  const healthyCount = services.filter((s) => s.status === 'healthy').length;
  const totalCount = services.length;

  return (
    <div className={cn('space-y-3', className)}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-[#1E7B4D]" />
          <span className="text-xs font-semibold text-[#16212E] uppercase tracking-wider">
            System Services Health
          </span>
        </div>
        <span className="text-xs font-medium text-[#4A5B6E] tabular-nums">
          {healthyCount} / {totalCount} Operational
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2">
        {services.map((svc) => (
          <HealthDot key={svc.id} item={svc} />
        ))}
      </div>
    </div>
  );
}