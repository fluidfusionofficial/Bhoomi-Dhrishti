'use client';

import * as React from 'react';
import Link from 'next/link';
import {
  fetchMyParcels,
  MyParcelSummary,
  setToken,
  getToken,
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
  MapPin,
  FileText,
  Shield,
  Eye,
  ArrowRight,
  ExternalLink,
  ChevronRight,
  UserCheck,
  AlertCircle,
} from 'lucide-react';
import { CitizenHeader } from '@/components/CitizenHeader';
import { BottomNav } from '@/components/BottomNav';

export default function CitizenHomePage() {
  const [parcels, setParcels] = React.useState<MyParcelSummary[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [authIdentity, setAuthIdentity] = React.useState<string>('CITIZEN:a1b2c3d4');

  const loadParcels = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // Set citizen bearer token for demonstration & integration
      setToken(authIdentity);
      const res = await fetchMyParcels();
      if (res && Array.isArray(res.parcels)) {
        setParcels(res.parcels);
      } else {
        setParcels([]);
      }
    } catch (err: any) {
      // Handle network or backend empty case
      setError(
        err?.message ||
          'Could not retrieve registered parcels. Check your network or identity authentication.'
      );
    } finally {
      setLoading(false);
    }
  }, [authIdentity]);

  React.useEffect(() => {
    loadParcels();
  }, [loadParcels]);

  return (
    <div className="min-h-screen bg-[#F4F7FB] flex flex-col pb-20">
      <CitizenHeader />

      <main className="flex-1 max-w-md w-full mx-auto p-4 space-y-5">
        {/* Verification / Citizen ID Strip */}
        <div className="bg-white border border-[#DCE3EA] rounded-md p-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-full bg-[#E2ECF5] text-[#14548C] flex items-center justify-center">
              <UserCheck className="w-4 h-4" />
            </div>
            <div>
              <div className="text-xs font-semibold text-[#16212E]">
                Aadhaar e-KYC Verified
              </div>
              <div className="text-[10px] text-[#4A5B6E] font-serif tabular-nums">
                Citizen ID: •••• •••• 8912
              </div>
            </div>
          </div>
          <span className="text-[11px] font-semibold text-[#1E7B4D] bg-[#E2ECF5]/60 px-2 py-0.5 rounded-[4px]">
            ACTIVE
          </span>
        </div>

        {/* Quick Search Card */}
        <div className="bg-white border border-[#DCE3EA] rounded-md p-4 space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-[#16212E]">
              Search Land Records
            </h2>
            <span className="text-[10px] text-[#4A5B6E] uppercase tracking-wider">
              Public Ledger
            </span>
          </div>
          <p className="text-xs text-[#4A5B6E]">
            Verify cadastral ownership, ULPIN, survey number, or plot boundaries.
          </p>
          <Link href="/search" className="block">
            <Button className="w-full justify-between" size="default">
              <span className="flex items-center gap-2">
                <Search className="w-4 h-4" />
                <span>Search by ULPIN or Survey No.</span>
              </span>
              <ChevronRight className="w-4 h-4 opacity-75" />
            </Button>
          </Link>
        </div>

        {/* Privacy Inversion Highlight: Who Accessed My Land */}
        <Link href="/access-log" className="block">
          <div className="bg-white border border-[#14548C]/30 hover:border-[#14548C] rounded-md p-3.5 flex items-center justify-between transition-colors">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-[4px] bg-[#E2ECF5] text-[#14548C] flex items-center justify-center">
                <Eye className="w-4 h-4" />
              </div>
              <div>
                <div className="text-xs font-semibold text-[#14548C]">
                  Who Accessed My Land
                </div>
                <div className="text-[11px] text-[#4A5B6E]">
                  Transparent audit of all officer and bank record inquiries
                </div>
              </div>
            </div>
            <ChevronRight className="w-4 h-4 text-[#14548C]" />
          </div>
        </Link>

        {/* My Land Parcels Section */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-[#16212E]">
              My Registered Parcels
            </h2>
            <span className="text-xs text-[#4A5B6E] tabular-nums font-serif font-semibold">
              {parcels.length} {parcels.length === 1 ? 'Parcel' : 'Parcels'}
            </span>
          </div>

          {loading ? (
            <div className="space-y-3">
              {[1, 2].map((i) => (
                <div
                  key={i}
                  className="h-32 bg-white border border-[#DCE3EA] rounded-md animate-pulse p-4"
                />
              ))}
            </div>
          ) : error ? (
            <ErrorState
              title="Unable to load parcels"
              description={error}
              onRetry={loadParcels}
            />
          ) : parcels.length === 0 ? (
            <EmptyState
              title="No parcels linked to your ID"
              description="If you recently purchased land, ensure the mutation has been entered in the revenue registry, or search by ULPIN to view public profile."
              action={
                <Link href="/search">
                  <Button variant="outline" size="sm">
                    Search Public Land Registry
                  </Button>
                </Link>
              }
            />
          ) : (
            <div className="space-y-3">
              {parcels.map((p) => (
                <Link
                  key={p.parcel_id || p.ulpin}
                  href={`/parcels/${p.parcel_id || p.ulpin}`}
                  className="block group"
                >
                  <Card className="hover:border-[#14548C] transition-colors overflow-hidden">
                    <div className="p-4 space-y-3">
                      <div className="flex items-start justify-between">
                        <div>
                          <span className="text-[10px] text-[#4A5B6E] uppercase tracking-wider font-semibold">
                            ULPIN
                          </span>
                          <div className="text-base font-serif font-bold text-[#16212E] tracking-tight">
                            {p.ulpin}
                          </div>
                        </div>
                        <StatusBadge
                          status={p.has_dispute ? 'disputed' : 'approved'}
                          variant={p.has_dispute ? 'rejected' : 'approved'}
                        >
                          {p.has_dispute ? 'Dispute Open' : 'Clear Title'}
                        </StatusBadge>
                      </div>

                      <div className="grid grid-cols-2 gap-2 text-xs pt-1 border-t border-[#DCE3EA]">
                        <div>
                          <span className="text-[#4A5B6E]">Survey Number:</span>
                          <span className="ml-1 font-serif font-semibold text-[#16212E]">
                            {p.survey_number || '42/1B'}
                          </span>
                        </div>
                        <div>
                          <span className="text-[#4A5B6E]">Area:</span>
                          <span className="ml-1 font-serif font-semibold tabular-nums text-[#16212E]">
                            {p.area_sq_m
                              ? `${p.area_sq_m.toLocaleString()} m²`
                              : '1.42 Ha'}
                          </span>
                        </div>
                        <div>
                          <span className="text-[#4A5B6E]">Classification:</span>
                          <span className="ml-1 font-semibold text-[#14548C]">
                            {p.land_use || 'Agricultural'}
                          </span>
                        </div>
                        <div>
                          <span className="text-[#4A5B6E]">Encumbrance:</span>
                          <span
                            className={`ml-1 font-semibold ${
                              p.encumbered ? 'text-[#B8720B]' : 'text-[#1E7B4D]'
                            }`}
                          >
                            {p.encumbered ? 'Active Mortgage' : 'Nil'}
                          </span>
                        </div>
                      </div>

                      <div className="flex items-center justify-between text-xs text-[#14548C] pt-2 border-t border-[#DCE3EA]/60 font-medium">
                        <span>View complete deed & RoR profile</span>
                        <ChevronRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
                      </div>
                    </div>
                  </Card>
                </Link>
              ))}
            </div>
          )}
        </div>

        {/* Quick Services Grid */}
        <div className="space-y-2 pt-2">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-semibold text-[#4A5B6E] uppercase tracking-wider">
              Citizen Services
            </h2>
            <Link
              href="/applications/new"
              className="text-xs text-[#14548C] font-semibold hover:underline"
            >
              View Catalog
            </Link>
          </div>

          <div className="grid grid-cols-2 gap-2.5">
            <Link href="/applications/new?service=MUTATION">
              <div className="bg-white border border-[#DCE3EA] hover:border-[#14548C] rounded-md p-3 transition-colors">
                <FileText className="w-5 h-5 text-[#14548C] mb-1.5" />
                <div className="text-xs font-semibold text-[#16212E]">
                  Apply for Mutation
                </div>
                <div className="text-[10px] text-[#4A5B6E] mt-0.5">
                  Transfer of title & RoR update
                </div>
              </div>
            </Link>

            <Link href="/applications/new?service=EC">
              <div className="bg-white border border-[#DCE3EA] hover:border-[#14548C] rounded-md p-3 transition-colors">
                <Shield className="w-5 h-5 text-[#14548C] mb-1.5" />
                <div className="text-xs font-semibold text-[#16212E]">
                  Encumbrance Certificate
                </div>
                <div className="text-[10px] text-[#4A5B6E] mt-0.5">
                  Download digital certificate (EC)
                </div>
              </div>
            </Link>
          </div>
        </div>
      </main>

      <BottomNav />
    </div>
  );
}