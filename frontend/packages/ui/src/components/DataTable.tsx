'use client';

import * as React from 'react';
import { cn } from '../lib/utils';
import { ChevronDown, ChevronUp, ChevronsUpDown, ChevronLeft, ChevronRight } from 'lucide-react';

export interface Column<T> {
  key: string;
  header: string;
  render?: (row: T, index: number) => React.ReactNode;
  sortable?: boolean;
  isNumeric?: boolean;
  align?: 'left' | 'right' | 'center';
  width?: string;
}

export interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  keyExtractor: (row: T, index: number) => string;
  onRowClick?: (row: T) => void;
  selectedKey?: string;
  emptyMessage?: string;
  className?: string;
  maxHeight?: string;
}

export function DataTable<T extends Record<string, any>>({
  columns,
  data,
  keyExtractor,
  onRowClick,
  selectedKey,
  emptyMessage = 'No records found in this view',
  className,
  maxHeight,
}: DataTableProps<T>) {
  const PAGE_SIZE = 15;
  const [sortCol, setSortCol] = React.useState<string | null>(null);
  const [sortDir, setSortDir] = React.useState<'asc' | 'desc'>('asc');
  const [currentPage, setCurrentPage] = React.useState(0);

  const handleSort = (colKey: string) => {
    if (sortCol === colKey) {
      if (sortDir === 'asc') setSortDir('desc');
      else {
        setSortCol(null);
        setSortDir('asc');
      }
    } else {
      setSortCol(colKey);
      setSortDir('asc');
    }
  };

  // Reset to first page when data changes
  React.useEffect(() => {
    setCurrentPage(0);
  }, [data]);

  const sortedData = React.useMemo(() => {
    if (!sortCol) return data;
    const col = columns.find((c) => c.key === sortCol);
    return [...data].sort((a, b) => {
      const aVal = a[sortCol];
      const bVal = b[sortCol];
      if (aVal == null) return 1;
      if (bVal == null) return -1;
      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return sortDir === 'asc' ? aVal - bVal : bVal - aVal;
      }
      const strA = String(aVal).toLowerCase();
      const strB = String(bVal).toLowerCase();
      return sortDir === 'asc' ? strA.localeCompare(strB) : strB.localeCompare(strA);
    });
  }, [data, sortCol, sortDir, columns]);

  const totalPages = Math.max(1, Math.ceil(sortedData.length / PAGE_SIZE));
  const safeCurrentPage = Math.min(currentPage, totalPages - 1);
  const paginatedData = sortedData.slice(safeCurrentPage * PAGE_SIZE, (safeCurrentPage + 1) * PAGE_SIZE);
  const rangeStart = sortedData.length === 0 ? 0 : safeCurrentPage * PAGE_SIZE + 1;
  const rangeEnd = Math.min((safeCurrentPage + 1) * PAGE_SIZE, sortedData.length);

  return (
    <div
      className={cn(
        'w-full rounded-none border border-[#DCE3EA] bg-white overflow-auto relative',
        className
      )}
      style={maxHeight ? { maxHeight } : undefined}
    >
      <table className="w-full text-left border-collapse">
        <thead className="sticky top-0 bg-[#F6F7F9] z-10 border-b border-[#B9C5D1]">
          <tr>
            {columns.map((col) => {
              const isSorted = sortCol === col.key;
              return (
                <th
                  key={col.key}
                  style={col.width ? { width: col.width } : undefined}
                  className={cn(
                    'px-4 py-2.5 text-xs font-semibold text-[#16212E] tracking-tight whitespace-nowrap select-none',
                    col.align === 'right' ? 'text-right' : col.align === 'center' ? 'text-center' : 'text-left',
                    col.sortable ? 'cursor-pointer hover:bg-[#E2ECF5]/50' : ''
                  )}
                  onClick={() => col.sortable && handleSort(col.key)}
                >
                  <div
                    className={cn(
                      'inline-flex items-center gap-1.5',
                      col.align === 'right' ? 'justify-end w-full' : ''
                    )}
                  >
                    <span>{col.header}</span>
                    {col.sortable && (
                      <span className="text-[#4A5B6E]">
                        {isSorted ? (
                          sortDir === 'asc' ? (
                            <ChevronUp className="w-3.5 h-3.5 text-[#14548C]" />
                          ) : (
                            <ChevronDown className="w-3.5 h-3.5 text-[#14548C]" />
                          )
                        ) : (
                          <ChevronsUpDown className="w-3.5 h-3.5 opacity-40 hover:opacity-100" />
                        )}
                      </span>
                    )}
                  </div>
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody className="divide-y divide-[#DCE3EA]">
          {paginatedData.length === 0 ? (
            <tr>
              <td
                colSpan={columns.length}
                className="px-4 py-8 text-center text-sm text-[#4A5B6E]"
              >
                {emptyMessage}
              </td>
            </tr>
          ) : (
            paginatedData.map((row, index) => {
              const key = keyExtractor(row, index);
              const isSelected = selectedKey === key;
              return (
                <tr
                  key={key}
                  onClick={() => onRowClick && onRowClick(row)}
                  className={cn(
                    'transition-colors',
                    isSelected
                      ? 'bg-[#E2ECF5]'
                      : 'hover:bg-[#F4F7FB] even:bg-[#F6F7F9]/40',
                    onRowClick ? 'cursor-pointer' : ''
                  )}
                >
                  {columns.map((col) => {
                    const value = col.render ? col.render(row, index) : row[col.key];
                    return (
                      <td
                        key={col.key}
                        className={cn(
                          'px-4 py-3 text-sm text-[#16212E] align-middle',
                          col.isNumeric ? 'tabular-nums' : '',
                          col.align === 'right'
                            ? 'text-right'
                            : col.align === 'center'
                            ? 'text-center'
                            : 'text-left'
                        )}
                      >
                        {value != null ? value : '—'}
                      </td>
                    );
                  })}
                </tr>
              );
            })
          )}
        </tbody>
      </table>

      {/* Pagination Footer */}
      {sortedData.length > PAGE_SIZE && (
        <div className="flex items-center justify-between px-4 py-2.5 border-t border-[#DCE3EA] bg-[#F6F7F9] text-xs text-[#4A5B6E]">
          <span className="tabular-nums">
            Showing {rangeStart}-{rangeEnd} of {sortedData.length}
          </span>
          <div className="flex items-center gap-1.5">
            <button
              type="button"
              disabled={safeCurrentPage === 0}
              onClick={() => setCurrentPage((p) => Math.max(0, p - 1))}
              className={cn(
                'inline-flex items-center justify-center w-7 h-7 rounded border border-[#DCE3EA] transition-colors',
                safeCurrentPage === 0
                  ? 'opacity-40 cursor-not-allowed bg-[#F6F7F9]'
                  : 'bg-white hover:bg-[#E2ECF5] cursor-pointer'
              )}
              aria-label="Previous page"
            >
              <ChevronLeft className="w-3.5 h-3.5" />
            </button>
            <span className="px-2 font-semibold tabular-nums text-[#16212E]">
              {safeCurrentPage + 1} / {totalPages}
            </span>
            <button
              type="button"
              disabled={safeCurrentPage >= totalPages - 1}
              onClick={() => setCurrentPage((p) => Math.min(totalPages - 1, p + 1))}
              className={cn(
                'inline-flex items-center justify-center w-7 h-7 rounded border border-[#DCE3EA] transition-colors',
                safeCurrentPage >= totalPages - 1
                  ? 'opacity-40 cursor-not-allowed bg-[#F6F7F9]'
                  : 'bg-white hover:bg-[#E2ECF5] cursor-pointer'
              )}
              aria-label="Next page"
            >
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}