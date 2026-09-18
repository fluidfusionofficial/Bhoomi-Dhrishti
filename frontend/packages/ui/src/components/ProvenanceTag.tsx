import * as React from 'react';
import { cn } from '../lib/utils';

interface ProvenanceTagProps {
  source: string;
  department: string;
  asOfDate: string;
  className?: string;
}

export function ProvenanceTag({ source, department, asOfDate, className }: ProvenanceTagProps) {
  const formattedDate = new Date(asOfDate).toLocaleDateString('en-IN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });

  return (
    <div
      className={cn(
        'inline-flex items-center gap-1 rounded-md bg-neutral-100 px-2 py-1 text-xs text-neutral-600',
        className
      )}
    >
      <span className="font-medium">As per {source}</span>
      <span className="text-neutral-400">•</span>
      <span>{department}</span>
      <span className="text-neutral-400">•</span>
      <span>as of {formattedDate}</span>
    </div>
  );
}
