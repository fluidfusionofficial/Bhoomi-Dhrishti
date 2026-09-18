import * as React from 'react';
import { cn } from '../lib/utils';

interface ConfidenceBadgeProps {
  score: number;
  className?: string;
  showLabel?: boolean;
}

export function ConfidenceBadge({ score, className, showLabel = true }: ConfidenceBadgeProps) {
  const getColor = (score: number) => {
    if (score >= 70) return 'bg-[#27AE60] text-white';
    if (score >= 40) return 'bg-[#F39C12] text-white';
    return 'bg-[#E74C3C] text-white';
  };

  const getLabel = (score: number) => {
    if (score >= 70) return 'High';
    if (score >= 40) return 'Medium';
    return 'Low';
  };

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold',
        getColor(score),
        className
      )}
    >
      {showLabel && <span>{getLabel(score)}</span>}
      <span>{score}%</span>
    </span>
  );
}
