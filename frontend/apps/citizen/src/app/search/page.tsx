'use client';

import * as React from 'react';
import Link from 'next/link';
import {
  searchParcelsCitizen,
  getSearchSuggestions,
  searchNaturalLanguage,
} from '@bhoomi/api-client';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  StatusBadge,
  EmptyState,
  ErrorState,
} from '@bhoomi/ui';
import {
  Search,
  Sparkles,
  ChevronRight,
  Filter,
  MapPin,
  Loader2,
  HelpCircle,
  X,
} from 'lucide-react';
import { CitizenHeader } from '@/components/CitizenHeader';
import { BottomNav } from '@/components/BottomNav';

export default function CitizenSearchPage() {
  const [query, setQuery] = React.useState('');
  const [searchMode, setSearchMode] = React.useState<'nlp' | 'ulpin' | 'survey'>('nlp');
  const [suggestions, setSuggestions] = React.useState<string[]>([]);
  const [results, setResults] = React.useState<any[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [searched, setSearched] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  // Autocomplete suggestions
  React.useEffect(() => {
    if (query.trim().length < 2) {
      setSuggestions([]);
      return;
    }
    const timer = setTimeout(async () => {
      try {
        const sugg = await getSearchSuggestions(query);
        if (Array.isArray(sugg)) setSuggestions(sugg);
      } catch {
        setSuggestions([]);
      }
    }, 250);
    return () => clearTimeout(timer);
  }, [query]);

  const handleSearch = async (overrideQuery?: string) => {
    const q = (overrideQuery || query).trim();
    if (!q) return;

    setLoading(true);
    setError(null);
    setSearched(true);
    setSuggestions([]);

    try {
      if (searchMode === 'nlp') {
        const res = await searchNaturalLanguage(q);
        const list = res?.parcels || res?.results || (Array.isArray(res) ? res : []);
        setResults(list);
      } else {
        const payload: Record<string, any> = {};
        if (searchMode === 'ulpin') payload.ulpin = q;
        if (searchMode === 'survey') payload.survey_number = q;
        const res = await searchParcelsCitizen(payload);
        const list = res?.parcels || res?.results || (Array.isArray(res) ? res : []);
        setResults(list);
      }
    } catch (err: any) {
      // If endpoint is not yet connected in backend dev mode, show graceful response
      setError(
        err?.message ||
          'Search could not be completed. Check the survey number or search query.'
      );
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const exampleChips = [
    'Survey No. 42 Tiruvannamalai',
    'Agricultural land in Kilpennathur',
    'TN607001002421B',
  ];

  return (
    <div className="min-h-screen bg-[#F4F7FB] flex flex-col pb-20">
      <CitizenHeader />

      <main className="flex-1 max-w-md w-full mx-auto p-4 space-y-4">
        <div>
          <h1 className="text-base font-bold font-serif text-[#16212E]">
            Land Records Lookup
          </h1>
          <p className="text-xs text-[#4A5B6E] mt-0.5">
            Search any parcel across state cadastral registers by ULPIN or plain query.
          </p>
        </div>

        {/* Search Mode Toggle */}
        <div className="flex bg-white p-1 rounded-md border border-[#DCE3EA] text-xs font-semibold">
          <button
            type="button"
            onClick={() => setSearchMode('nlp')}
            className={`flex-1 py-1.5 rounded-[4px] transition-colors flex items-center justify-center gap-1 ${
              searchMode === 'nlp'
                ? 'bg-[#14548C] text-white'
                : 'text-[#4A5B6E] hover:text-[#16212E]'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Plain Language</span>
          </button>
          <button
            type="button"
            onClick={() => setSearchMode('ulpin')}
            className={`flex-1 py-1.5 rounded-[4px] transition-colors ${
              searchMode === 'ulpin'
                ? 'bg-[#14548C] text-white'
                : 'text-[#4A5B6E] hover:text-[#16212E]'
            }`}
          >
            By ULPIN
          </button>
          <button
            type="button"
            onClick={() => setSearchMode('survey')}
            className={`flex-1 py-1.5 rounded-[4px] transition-colors ${
              searchMode === 'survey'
                ? 'bg-[#14548C] text-white'
                : 'text-[#4A5B6E] hover:text-[#16212E]'
            }`}
          >
            Survey No.
          </button>
        </div>

        {/* Main Search Input Bar */}
        <div className="relative">
          <div className="relative flex items-center">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              placeholder={
                searchMode === 'nlp'
                  ? 'e.g. Find parcel 42 in Tiruvannamalai'
                  : searchMode === 'ulpin'
                  ? 'Enter 14-digit ULPIN'
                  : 'Enter Survey / Khasra Number'
              }
              className="w-full pl-3 pr-24 py-2.5 bg-white border border-[#B9C5D1] rounded-md text-xs text-[#16212E] placeholder:text-[#4A5B6E] focus:outline-none focus:ring-2 focus:ring-[#14548C]"
            />
            {query && (
              <button
                type="button"
                onClick={() => setQuery('')}
                className="absolute right-14 text-[#4A5B6E] hover:text-[#16212E] p-1"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
            <Button
              size="sm"
              onClick={() => handleSearch()}
              disabled={loading || !query.trim()}
              className="absolute right-1.5 h-7 px-3 text-xs"
            >
              {loading ? (
                <Loader2 className="w-3 h-3 animate-spin" />
              ) : (
                'Search'
              )}
            </Button>
          </div>

          {/* Suggestions Dropdown */}
          {suggestions.length > 0 && (
            <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-[#B9C5D1] rounded-md shadow-lg z-20 divide-y divide-[#DCE3EA]">
              {suggestions.map((s, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => {
                    setQuery(s);
                    handleSearch(s);
                  }}
                  className="w-full text-left px-3 py-2 text-xs text-[#16212E] hover:bg-[#E2ECF5] flex items-center justify-between"
                >
                  <span>{s}</span>
                  <ChevronRight className="w-3.5 h-3.5 text-[#4A5B6E]" />
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Quick Example Chips */}
        <div className="flex items-center gap-1.5 flex-wrap text-xs">
          <span className="text-[11px] text-[#4A5B6E]">Try:</span>
          {exampleChips.map((chip, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => {
                setQuery(chip);
                handleSearch(chip);
              }}
              className="px-2 py-0.5 bg-[#E2ECF5] hover:bg-[#14548C] hover:text-white text-[#0B2E4E] rounded-[4px] text-[11px] transition-colors"
            >
              {chip}
            </button>
          ))}
        </div>

        {/* Search Results */}
        <div className="space-y-3 pt-2">
          {loading ? (
            <div className="space-y-3">
              {[1, 2].map((i) => (
                <div
                  key={i}
                  className="h-28 bg-white border border-[#DCE3EA] rounded-md animate-pulse p-4"
                />
              ))}
            </div>
          ) : error ? (
            <ErrorState
              title="Search issue"
              description={error}
              onRetry={() => handleSearch()}
            />
          ) : searched && results.length === 0 ? (
            <EmptyState
              title="No parcels match this inquiry"
              description="Check the spelling, verify the survey number format, or try searching by 14-digit ULPIN."
            />
          ) : (
            results.map((p, idx) => (
              <Link
                key={p.parcel_id || p.id || p.ulpin || idx}
                href={`/parcels/${p.parcel_id || p.id || p.ulpin || 'sample'}`}
                className="block group"
              >
                <Card className="p-3.5 hover:border-[#14548C] transition-colors space-y-2">
                  <div className="flex items-start justify-between">
                    <div>
                      <span className="text-[10px] text-[#4A5B6E] uppercase font-semibold">
                        ULPIN
                      </span>
                      <div className="text-sm font-serif font-bold text-[#16212E]">
                        {p.ulpin || 'TN-607-001-042'}
                      </div>
                    </div>
                    <StatusBadge
                      status={p.has_dispute ? 'disputed' : 'approved'}
                      variant={p.has_dispute ? 'rejected' : 'approved'}
                    >
                      {p.has_dispute ? 'Dispute' : 'Verified'}
                    </StatusBadge>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-xs border-t border-[#DCE3EA] pt-2">
                    <div>
                      <span className="text-[#4A5B6E]">Survey:</span>
                      <span className="ml-1 font-serif font-semibold text-[#16212E]">
                        {p.survey_number || p.khasra_number || '42/1B'}
                      </span>
                    </div>
                    <div>
                      <span className="text-[#4A5B6E]">District:</span>
                      <span className="ml-1 font-semibold text-[#16212E]">
                        {p.district_name || 'Tiruvannamalai'}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center justify-between text-xs text-[#14548C] font-semibold pt-1">
                    <span>View Official Profile</span>
                    <ChevronRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                  </div>
                </Card>
              </Link>
            ))
          )}
        </div>
      </main>

      <BottomNav />
    </div>
  );
}