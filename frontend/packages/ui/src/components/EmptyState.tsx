'use client';

import * as React from 'react';
import { cn } from '../lib/utils';
import { FolderOpen } from 'lucide-react';

export interface EmptyStateProps {
  title?: string;
  description: string;
  action?: React.ReactNode;
  icon?: React.ReactNode;
  className?: string;
}

export function EmptyState({
  title,
  description,
  action,
  icon,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        'w-full py-12 px-6 flex flex-col items-center justify-center text-center bg-white border border-[#DCE3EA] rounded-md',
        className
      )}
    >
      <div className="w-10 h-10 rounded-full bg-[#E2ECF5] text-[#14548C] flex items-center justify-center mb-3">
        {icon || <FolderOpen className="w-5 h-5" />}
      </div>
      {title && (
        <h4 className="text-sm font-semibold text-[#16212E] mb-1">{title}</h4>
      )}
      <p className="text-xs text-[#4A5B6E] max-w-md leading-relaxed">{description}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}