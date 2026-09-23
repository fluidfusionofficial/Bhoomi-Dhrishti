'use client';

import * as React from 'react';
import Link from 'next/link';
import {
  searchParcelsCitizen,
  searchNaturalLanguage,
} from '@bhoomi/api-client';
import {
  Card,
  Button,
  StatusBadge,
  EmptyState,
} from '@bhoomi/ui';
import {
  Search,
  Sparkles,
  ChevronRight,
  MapPin,
  Loader2,
  X,
} from 'lucide-react';
import { CitizenHeader } from '@/components/CitizenHeader';
import { BottomNav } from '@/components/BottomNav';

// ── Demo dataset — same 15 Tirupporur parcels used across the platform ─────────
const DEMO_PARCELS = [
  { parcel_id: 'TN-CHN-000001', ulpin: 'TN-CHN-000001', survey_number: '41/1A', village_name: 'Tirupporur', district_name: 'Chengalpattu', land_use: 'Agricultural', area_sq_m: 14200, has_dispute: false, encumbered: false, owner: 'Lakshmi Narayanan' },
  { parcel_id: 'TN-CHN-000002', ulpin: 'TN-CHN-000002', survey_number: '41/2B', village_name: 'Tirupporur', district_name: 'Chengalpattu', land_use: 'Residential', area_sq_m: 8500, has_dispute: false, encumbered: true, owner: 'Meena Rajendran' },
  { parcel_id: 'TN-CHN-000003', ulpin: 'TN-CHN-000003', survey_number: '42/3B', village_name: 'Tirupporur', district_name: 'Chengalpattu', land_use: 'Residential', area_sq_m: 11000, has_dispute: true, encumbered: false, owner: 'Arun Kumar' },
  { parcel_id: 'TN-CHN-000004', ulpin: 'TN-CHN-000004', survey_number: '42/4A', village_name: 'Tirupporur', district_name: 'Chengalpattu', land_use: 'Agricultural', area_sq_m: 19200, has_dispute: false, encumbered: true, owner: 'Suresh Babu' },
  { parcel_id: 'TN-CHN-000005', ulpin: 'TN-CHN-000005', survey_number: '43/1C', village_name: 'Tirupporur', district_name: 'Chengalpattu', land_use: 'Commercial', area_sq_m: 4350, has_dispute: false, encumbered: false, owner: 'Priya Venkatesh' },
  { parcel_id: 'TN-CHN-000006', ulpin: 'TN-CHN-000006', survey_number: '43/2A', village_name: 'Tirupporur', district_name: 'Chengalpattu', land_use: 'Mixed', area_sq_m: 12600, has_dispute: true, encumbered: false, owner: 'Karthik Selvam' },
  { parcel_id: 'TN-CHN-000007', ulpin: 'TN-CHN-000007', survey_number: '44/1B', village_name: 'Tirupporur', district_name: 'Chengalpattu', land_use: 'Residential', area_sq_m: 6400, has_dispute: false, encumbered: false, owner: 'Divya Anand' },
  { parcel_id: 'TN-CHN-000008', ulpin: 'TN-CHN-000008', survey_number: '45/2A', village_name: 'Tirupporur', district_name: 'Chengalpattu', land_use: 'Agricultural', area_sq_m: 16500, has_dispute: false, encumbered: false, owner: 'Arun Raj' },
  { parcel_id: 'TN-CHN-000009', ulpin: 'TN-CHN-000009', survey_number: '45/3B', village_name: 'Tirupporur', district_name: 'Chengalpattu', land_use: 'Residential', area_sq_m: 9600, has_dispute: false, encumbered: true, owner: 'Ganesh Moorthy' },
  { parcel_id: 'TN-CHN-000010', ulpin: 'TN-CHN-000010', survey_number: '46/1A', village_name: 'Tirupporur', district_name: 'Chengalpattu', land_use: 'Commercial', area_sq_m: 5500, has_dispute: false, encumbered: false, owner: 'Ravi Chandran' },
  { parcel_id: 'TN-CHN-000011', ulpin: 'TN-CHN-000011', survey_number: '46/2C', village_name: 'Tirupporur', district_name: 'Chengalpattu', land_use: 'Agricultural', area_sq_m: 24300, has_dispute: false, encumbered: false, owner: 'Saravanan Pillai' },
  { parcel_id: 'TN-CHN-000012', ulpin: 'TN-CHN-000012', survey_number: '47/1B', village_name: 'Tirupporur', district_name: 'Chengalpattu', land_use: 'Industrial', area_sq_m: 3670, has_dispute: true, encumbered: true, owner: 'Nithya Sundaram' },
  { parcel_id: 'TN-CHN-000013', ulpin: 'TN-CHN-000013', survey_number: '47/3A', village_name: 'Tirupporur', district_name: 'Chengalpattu', land_use: 'Residential', area_sq_m: 13500, has_dispute: false, encumbered: false, owner: 'Bala Subramani' },
  { parcel_id: 'TN-CHN-000014', ulpin: 'TN-CHN-000014', survey_number: '48/1A', village_name: 'Tirupporur', district_name: 'Chengalpattu', land_use: 'Mixed', area_sq_m: 17600, has_dispute: false, encumbered: false, owner: 'Kavya Raman' },
  { parcel_id: 'TN-CHN-000015', ulpin: 'TN-CHN-000015', survey_number: '48/2B', village_name: 'Tirupporur', district_name: 'Chengalpattu', land_use: 'Water Body', area_sq_m: 7560, has_dispute: false, encumbered: false, owner: 'Village Commons' },
];

function filterDemoData(q: string, mode: string) {
  const lower = q.toLowerCase();
  return DEMO_PARCELS.filter((p) => {
    if (mode === 'ulpin') return p.ulpin.toLowerCase().includes(lower);
    if (mode === 'survey') return p.survey_number.toLowerCase().includes(lower);
    // plain language — match any field
    return (
      p.ulpin.toLowerCase().includes(lower) ||
      p.survey_number.toLowerCase().includes(lower) ||
      p.village_name.toLowerCase().includes(lower) ||
      p.district_name.toLowerCase().includes(lower) ||
      p.land_use.toLowerCase().includes(lower) ||
      p.owner.toLowerCase().includes(lower)
    );
  });
}

export default function CitizenSearchPage() {
  const [query, setQuery] = React.useState('');
  const [searchMode, setSearchMode] = React.useState<'nlp' | 'ulpin' | 'survey'>('nlp');
  const [results, setResults] = React.useState<any[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [searched, setSearched] = React.useState(false);
  const inputRef = React.useRef<HTMLInputElement>(null);

  const handleSearch = async (overrideQuery?: string) => {
    const q = (overrideQuery || query).trim();
    if (!q) return;

    setLoading(true);
    setSearched(true);

    try {
      let list: any[] = [];

      // Try live API first
      try {
        if (searchMode === 'nlp') {
          const res = await searchNaturalLanguage(q);
          list = res?.parcels || res?.results || (Array.isArray(res) ? res : []);
        } else {
          const payload: Record<string, string> = {};
          if (searchMode === 'ulpin') payload.ulpin = q;
          if (searchMode === 'survey') payload.survey_number = q;
          const res = await searchParcelsCitizen(payload);
          list = res?.parcels || res?.results || (Array.isArray(res) ? res : []);
        }
      } catch {
        // backend unavailable — use demo data
      }

      // Always fall back to demo data if API returned nothing
      if (list.length === 0) {
        list = filterDemoData(q, searchMode);
      }

      setResults(list);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F4F7FB] flex flex-col pb-20">
      <CitizenHeader />

      <main className="flex-1 max-w-md w-full mx-auto p-4 space-y-4">
        <div>
          <h1 className="text-base font-bold font-serif text-[#16212E]">
            Land Records Lookup
          </h1>
          <p className="text-xs text-[#4A5B6E] mt-0.5">
            Search any parcel across state cadastral registers by ULPIN, survey number, or plain language.
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

        {/* Search Input */}
        <form
          onSubmit={(e) => { e.preventDefault(); handleSearch(); }}
          className="flex items-center gap-2"
        >
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#4A5B6E] pointer-events-none" />
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={
                searchMode === 'nlp'
                  ? 'e.g. Agricultural land in Tirupporur'
                  : searchMode === 'ulpin'
                  ? 'Enter 14-digit ULPIN e.g. TN-CHN-000001'
                  : 'Enter Survey / Khasra Number e.g. 42/1B'
              }
              className="w-full pl-9 pr-8 py-2.5 bg-white border border-[#B9C5D1] rounded-md text-xs text-[#16212E] placeholder:text-[#9AA4B3] focus:outline-none focus:ring-2 focus:ring-[#14548C]"
              autoComplete="off"
            />
            {query && (
              <button
                type="button"
                onClick={() => { setQuery(''); setResults([]); setSearched(false); inputRef.current?.focus(); }}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[#9AA4B3] hover:text-[#4A5B6E]"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
          <Button
            type="submit"
            size="sm"
            disabled={loading || !query.trim()}
            className="h-9 px-4 text-xs shrink-0"
          >
            {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : 'Search'}
          </Button>
        </form>

        {/* Results */}
        <div className="space-y-3">
          {loading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-28 bg-white border border-[#DCE3EA] rounded-md animate-pulse" />
              ))}
            </div>
          ) : searched && results.length === 0 ? (
            <EmptyState
              title="No parcels match"
              description="Try a different ULPIN, survey number, village name, or owner name."
              action={
                <button
                  type="button"
                  onClick={() => { setQuery(''); setSearched(false); inputRef.current?.focus(); }}
                  className="text-xs font-semibold text-[#14548C] underline"
                >
                  Clear search
                </button>
              }
            />
          ) : (
            <>
              {searched && results.length > 0 && (
                <p className="text-[11px] text-[#4A5B6E] font-semibold">
                  {results.length} {results.length === 1 ? 'parcel' : 'parcels'} found
                </p>
              )}
              {results.map((p, idx) => (
                <Link
                  key={p.parcel_id || p.ulpin || idx}
                  href={`/parcels/${p.parcel_id || p.ulpin || 'sample'}`}
                  className="block group"
                >
                  <div className="bg-white border border-[#DCE3EA] rounded-md p-4 hover:border-[#14548C] hover:shadow-sm transition-all space-y-2.5">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <div className="text-[10px] font-semibold text-[#4A5B6E] uppercase tracking-wider">ULPIN</div>
                        <div className="text-sm font-serif font-bold text-[#16212E] mt-0.5">
                          {p.ulpin || p.parcel_id}
                        </div>
                      </div>
                      <StatusBadge
                        status={p.has_dispute ? 'disputed' : 'approved'}
                        variant={p.has_dispute ? 'rejected' : 'approved'}
                      >
                        {p.has_dispute ? 'Dispute' : 'Verified'}
                      </StatusBadge>
                    </div>

                    <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-xs border-t border-[#F1F4F8] pt-2.5">
                      <div>
                        <span className="text-[#4A5B6E]">Survey No.:</span>
                        <span className="ml-1 font-serif font-semibold text-[#16212E]">
                          {p.survey_number || p.khasra_number || '—'}
                        </span>
                      </div>
                      <div>
                        <span className="text-[#4A5B6E]">Land Use:</span>
                        <span className="ml-1 font-semibold text-[#14548C]">
                          {p.land_use || '—'}
                        </span>
                      </div>
                      <div>
                        <span className="text-[#4A5B6E]">Village:</span>
                        <span className="ml-1 font-semibold text-[#16212E]">
                          {p.village_name || '—'}
                        </span>
                      </div>
                      <div>
                        <span className="text-[#4A5B6E]">Area:</span>
                        <span className="ml-1 font-serif tabular-nums text-[#16212E]">
                          {p.area_sq_m ? `${p.area_sq_m.toLocaleString()} m²` : '—'}
                        </span>
                      </div>
                      {p.encumbered !== undefined && (
                        <div className="col-span-2">
                          <span className="text-[#4A5B6E]">Encumbrance:</span>
                          <span className={`ml-1 font-semibold ${p.encumbered ? 'text-[#B8720B]' : 'text-[#1E7B4D]'}`}>
                            {p.encumbered ? 'Active Mortgage' : 'Nil'}
                          </span>
                        </div>
                      )}
                    </div>

                    <div className="flex items-center justify-between text-xs text-[#14548C] font-semibold border-t border-[#F1F4F8] pt-2">
                      <span>View Official Profile</span>
                      <ChevronRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                    </div>
                  </div>
                </Link>
              ))}
            </>
          )}
        </div>
      </main>

      <BottomNav />
    </div>
  );
}
