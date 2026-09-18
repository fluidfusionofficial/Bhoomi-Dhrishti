'use client';

import * as React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Home, Search, PlusCircle, FileText, Eye } from 'lucide-react';
import { cn } from '@bhoomi/ui';

export function BottomNav() {
  const pathname = usePathname();

  const navItems = [
    { label: 'Home', href: '/', icon: Home, match: (p: string) => p === '/' },
    {
      label: 'My Land',
      href: '/search',
      icon: Search,
      match: (p: string) => p.startsWith('/search') || p.startsWith('/parcels'),
    },
    {
      label: 'Apply',
      href: '/applications/new',
      icon: PlusCircle,
      match: (p: string) => p.startsWith('/applications/new'),
    },
    {
      label: 'Applications',
      href: '/applications',
      icon: FileText,
      match: (p: string) => p === '/applications' || p.startsWith('/access-log'),
    },
  ];

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-30 bg-white border-t border-[#DCE3EA] shadow-none h-16 safe-area-bottom">
      <div className="max-w-md mx-auto h-full grid grid-cols-4">
        {navItems.map((item) => {
          const isActive = item.match(pathname);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex flex-col items-center justify-center gap-1 transition-colors relative',
                isActive
                  ? 'text-[#14548C] font-semibold'
                  : 'text-[#4A5B6E] hover:text-[#16212E]'
              )}
            >
              {isActive && (
                <span className="absolute top-0 w-8 h-[3px] bg-[#14548C] rounded-full" />
              )}
              <Icon className="w-5 h-5" />
              <span className="text-[11px] leading-none tracking-tight">
                {item.label}
              </span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}