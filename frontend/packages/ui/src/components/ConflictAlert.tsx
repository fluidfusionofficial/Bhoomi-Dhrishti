import * as React from 'react';
import { AlertTriangle, X } from 'lucide-react';
import { cn } from '../lib/utils';

interface ConflictAlertProps {
  title: string;
  description: string;
  onDismiss?: () => void;
  className?: string;
}

export function ConflictAlert({ title, description, onDismiss, className }: ConflictAlertProps) {
  return (
    <div
      className={cn(
        'relative rounded-lg border border-[#F39C12] bg-[#FFF8E1] p-4',
        className
      )}
      role="alert"
    >
      <div className="flex gap-3">
        <AlertTriangle className="h-5 w-5 flex-shrink-0 text-[#F39C12]" />
        <div className="flex-1">
          <h4 className="text-sm font-semibold text-[#D68910]">{title}</h4>
          <p className="mt-1 text-sm text-neutral-700">{description}</p>
        </div>
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="absolute right-2 top-2 rounded-sm p-1 text-neutral-500 hover:bg-neutral-200 hover:text-neutral-900"
            aria-label="Dismiss"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>
    </div>
  );
}
