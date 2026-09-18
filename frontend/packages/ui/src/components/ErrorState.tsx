'use client';

import * as React from 'react';
import { cn } from '../lib/utils';
import { AlertCircle, RotateCcw } from 'lucide-react';
import { Button } from './Button';

export interface ErrorStateProps {
  title?: string;
  description: string;
  onRetry?: () => void;
  retryLabel?: string;
  icon?: React.ReactNode;
  className?: string;
}

export function ErrorState({
  title = 'Action could not be completed',
  description,
  onRetry,
  retryLabel = 'Try again',
  icon,
  className,
}: ErrorStateProps) {
  return (
    <div
      className={cn(
        'w-full py-10 px-6 flex flex-col items-center justify-center text-center bg-white border border-[#A32E2E]/40 rounded-md',
        className
      )}
    >
      <div className="w-10 h-10 rounded-full bg-[#A32E2E]/10 text-[#A32E2E] flex items-center justify-center mb-3">
        {icon || <AlertCircle className="w-5 h-5" />}
      </div>
      <h4 className="text-sm font-semibold text-[#16212E] mb-1">{title}</h4>
      <p className="text-xs text-[#4A5B6E] max-w-md leading-relaxed mb-4">
        {description}
      </p>
      {onRetry && (
        <Button
          variant="outline"
          size="sm"
          onClick={onRetry}
          className="inline-flex items-center gap-1.5"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>{retryLabel}</span>
        </Button>
      )}
    </div>
  );
}