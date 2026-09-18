import * as React from 'react';
import { cn } from '../lib/utils';

export interface StatusBadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  status?: string;
  variant?: 'approved' | 'pending' | 'rejected' | 'info';
  children?: React.ReactNode;
}

export function normalizeStatusVariant(status?: string): 'approved' | 'pending' | 'rejected' | 'info' {
  if (!status) return 'info';
  const s = status.toLowerCase().replace(/[\s-_]+/g, '');
  if (['approved', 'verified', 'active', 'healthy', 'completed', 'resolved', 'success', 'passed'].includes(s)) {
    return 'approved';
  }
  if (['pending', 'inreview', 'underreview', 'submitted', 'awaiting', 'processing', 'queued'].includes(s)) {
    return 'pending';
  }
  if (['rejected', 'disputed', 'conflict', 'failed', 'error', 'unauthorized', 'critical'].includes(s)) {
    return 'rejected';
  }
  return 'info';
}

export function StatusBadge({
  status,
  variant,
  className,
  children,
  ...props
}: StatusBadgeProps) {
  const resolvedVariant = variant || normalizeStatusVariant(status);
  const label = children || status || resolvedVariant;

  const variantStyles = {
    approved: 'bg-[#1E7B4D] text-white',
    pending: 'bg-[#B8720B] text-white',
    rejected: 'bg-[#A32E2E] text-white',
    info: 'bg-[#5B6472] text-white',
  }[resolvedVariant];

  return (
    <span
      className={cn(
        'inline-flex items-center justify-center px-2 py-0.5 text-xs font-semibold rounded-[4px] tracking-wide uppercase whitespace-nowrap',
        variantStyles,
        className
      )}
      {...props}
    >
      {label}
    </span>
  );
}

/**
 * Trust Engine anomaly score pill (0.0 to 1.0 continuous risk value)
 * Sequential scale: blue-100 -> status-pending ochre -> status-rejected brick red
 */
export function AnomalyScorePill({
  score,
  className,
}: {
  score: number;
  className?: string;
}) {
  const clamped = Math.max(0, Math.min(1, score));
  let bg = '#E2ECF5';
  let text = '#0B2E4E';

  if (clamped >= 0.7) {
    bg = '#A32E2E';
    text = '#FFFFFF';
  } else if (clamped >= 0.35) {
    bg = '#B8720B';
    text = '#FFFFFF';
  } else {
    bg = '#E2ECF5';
    text = '#0B2E4E';
  }

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-2 py-0.5 text-xs font-semibold rounded-[4px] tabular-nums',
        className
      )}
      style={{ backgroundColor: bg, color: text }}
    >
      <span className="font-serif font-bold">{clamped.toFixed(2)}</span>
      <span className="text-[10px] uppercase font-sans tracking-tight opacity-90">
        {clamped >= 0.7 ? 'High Risk' : clamped >= 0.35 ? 'Medium' : 'Low Risk'}
      </span>
    </span>
  );
}