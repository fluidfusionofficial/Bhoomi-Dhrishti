import * as React from 'react';
import { Lock } from 'lucide-react';
import { cn } from '../lib/utils';

interface TieredAccessProps {
  hasAccess: boolean;
  children: React.ReactNode;
  message?: string;
  className?: string;
}

export function TieredAccess({
  hasAccess,
  children,
  message = 'This information requires authentication',
  className,
}: TieredAccessProps) {
  if (hasAccess) {
    return <>{children}</>;
  }

  return (
    <div className={cn('relative', className)}>
      <div className="blur-sm select-none pointer-events-none">{children}</div>
      <div className="absolute inset-0 flex items-center justify-center bg-white/90">
        <div className="flex flex-col items-center gap-2 text-center px-4">
          <Lock className="h-8 w-8 text-[#1B4F72]" />
          <p className="text-sm font-medium text-neutral-700">{message}</p>
        </div>
      </div>
    </div>
  );
}
