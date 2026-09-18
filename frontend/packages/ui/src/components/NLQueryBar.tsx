'use client';

import * as React from 'react';
import { cn } from '../lib/utils';
import { Search, Sparkles, CornerDownLeft, Loader2 } from 'lucide-react';
import { Button } from './Button';
import { DataTable } from './DataTable';

export interface NLQueryResult {
  type?: 'scalar' | 'tabular' | 'summary';
  answer?: string;
  summary?: string;
  data?: Record<string, any>[];
  columns?: { key: string; header: string }[];
  sql_generated?: string;
  confidence?: number;
  metadata?: Record<string, any>;
}

export interface NLQueryBarProps {
  onQuerySubmit: (query: string) => Promise<NLQueryResult | null>;
  exampleQueries?: string[];
  placeholder?: string;
  className?: string;
  isLoading?: boolean;
}

export function NLQueryBar({
  onQuerySubmit,
  exampleQueries = [
    'How many parcels in Tiruvannamalai have active ownership disputes?',
    'Show top 5 villages with highest unapproved land conversion rate',
    'List all agricultural parcels mortgaged to SBI in district 607',
    'Find circular transaction chains detected in the last 30 days',
  ],
  placeholder = 'Ask a question about parcels, owners, or records in natural language…',
  className,
  isLoading = false,
}: NLQueryBarProps) {
  const [query, setQuery] = React.useState('');
  const [loading, setLoading] = React.useState(isLoading);
  const [result, setResult] = React.useState<NLQueryResult | null>(null);
  const [error, setError] = React.useState<string | null>(null);

  const handleSubmit = async (qToRun?: string) => {
    const q = qToRun || query;
    if (!q.trim() || loading) return;
    setLoading(true);
    setError(null);
    try {
      const res = await onQuerySubmit(q);
      setResult(res);
    } catch (err: any) {
      setError(err?.message || 'Could not process natural language query. Please verify the query and try again.');
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSubmit();
    }
  };

  return (
    <div className={cn('w-full space-y-3', className)}>
      <div className="relative flex items-center">
        <div className="absolute left-3.5 text-[#14548C] pointer-events-none">
          <Sparkles className="w-4 h-4" />
        </div>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={loading}
          className="w-full pl-10 pr-28 py-3 bg-white border border-[#B9C5D1] rounded-md text-sm text-[#16212E] placeholder:text-[#4A5B6E] focus:outline-none focus:ring-2 focus:ring-[#14548C] focus:border-transparent transition-all"
        />
        <div className="absolute right-2 flex items-center gap-1.5">
          <Button
            size="sm"
            onClick={() => handleSubmit()}
            disabled={loading || !query.trim()}
            className="h-8 px-3 text-xs"
          >
            {loading ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <span className="flex items-center gap-1">
                <span>Query</span>
                <CornerDownLeft className="w-3 h-3" />
              </span>
            )}
          </Button>
        </div>
      </div>

      {/* Example Query Chips */}
      {exampleQueries.length > 0 && (
        <div className="flex items-center gap-1.5 flex-wrap text-xs">
          <span className="text-[#4A5B6E] font-medium mr-1">Examples:</span>
          {exampleQueries.map((ex, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => {
                setQuery(ex);
                handleSubmit(ex);
              }}
              disabled={loading}
              className="px-2.5 py-1 bg-[#E2ECF5] text-[#0B2E4E] hover:bg-[#14548C] hover:text-white rounded-[4px] transition-colors text-left"
            >
              {ex}
            </button>
          ))}
        </div>
      )}

      {/* Result Display */}
      {error && (
        <div className="p-4 bg-white border border-[#A32E2E] rounded-md text-sm text-[#16212E]">
          <div className="font-semibold text-[#A32E2E] mb-1">Query execution issue</div>
          <div className="text-xs text-[#4A5B6E]">{error}</div>
        </div>
      )}

      {result && (
        <div className="p-4 bg-white border border-[#DCE3EA] rounded-md space-y-3">
          <div className="flex items-center justify-between border-b border-[#DCE3EA] pb-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-[#14548C]">
              Query Result
            </span>
            {result.confidence != null && (
              <span className="text-xs text-[#4A5B6E] tabular-nums font-medium">
                Confidence: {Math.round(result.confidence * 100)}%
              </span>
            )}
          </div>

          {(result.answer || result.summary) && (
            <div className="text-sm font-medium text-[#16212E] leading-relaxed bg-[#F4F7FB] p-3 rounded-[4px] border border-[#DCE3EA]">
              {result.answer || result.summary}
            </div>
          )}

          {result.data && result.data.length > 0 && (
            <div className="mt-2">
              <DataTable
                data={result.data}
                columns={
                  result.columns ||
                  Object.keys(result.data[0]).map((key) => ({
                    key,
                    header: key.replace(/_/g, ' ').toUpperCase(),
                    isNumeric: typeof result.data![0][key] === 'number',
                  }))
                }
                keyExtractor={(_, i) => String(i)}
                maxHeight="320px"
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
}