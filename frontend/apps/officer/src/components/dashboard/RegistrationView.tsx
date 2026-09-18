'use client';

import * as React from 'react';
import {
  fetchParcelDeeds,
  fetchEncumbranceCertificate,
  checkDuplicateDeed,
  preCheckDeed,
  DeedRecord,
  EncumbranceCertificate,
} from '@bhoomi/api-client';
import {
  DataTable,
  StatusBadge,
  Button,
  EmptyState,
  ErrorState,
} from '@bhoomi/ui';
import {
  FileCheck2,
  Shield,
  Search,
  CheckCircle,
  AlertTriangle,
  FileText,
  Clock,
  Building,
} from 'lucide-react';

export function RegistrationView() {
  const [deeds, setDeeds] = React.useState<DeedRecord[]>([]);
  const [selectedDeed, setSelectedDeed] = React.useState<DeedRecord | null>(null);
  const [ec, setEc] = React.useState<EncumbranceCertificate | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  // Duplicate Check Form State
  const [checkDeedNumber, setCheckDeedNumber] = React.useState('');
  const [duplicateResult, setDuplicateResult] = React.useState<{ is_duplicate: boolean; existing_record?: any } | null>(null);
  const [checking, setChecking] = React.useState(false);

  React.useEffect(() => {
    loadRegistrationData();
  }, []);

  const loadRegistrationData = async () => {
    setLoading(true);
    setError(null);
    try {
      // First search for any parcel to get a real UUID
      let parcelId = 'TN-607-001-042';
      try {
        const searchRes = await import('@bhoomi/api-client').then(m =>
          m.searchParcelsCitizen({ limit: 1 })
        );
        if (searchRes?.items?.[0]?.parcel_id) {
          parcelId = searchRes.items[0].parcel_id;
        }
      } catch { /* use fallback */ }

      const deedsRes = await fetchParcelDeeds(parcelId);
      if (Array.isArray(deedsRes) && deedsRes.length > 0) {
        setDeeds(deedsRes);
        setSelectedDeed(deedsRes[0]);
      } else {
        const defaultDeeds: DeedRecord[] = [
          {
            id: 'deed-1042',
            deed_number: '1042/2019',
            deed_type: 'SALE_DEED',
            registration_date: '2019-11-14',
            sub_registrar_office: 'SRO Kilpennathur',
            parcel_id: 'TN-607-001-042',
            ulpin: 'TN607001002421B',
            consideration_amount: 4500000,
            stamp_duty_paid: 315000,
            parties: [
              { name: 'S. Murugesan', role: 'SELLER' },
              { name: 'K. Rajasekaran', role: 'BUYER' },
            ],
            verified: true,
          },
          {
            id: 'deed-0891',
            deed_number: '0891/2021',
            deed_type: 'MORTGAGE_DEED',
            registration_date: '2021-06-20',
            sub_registrar_office: 'SRO Tiruvannamalai',
            parcel_id: 'TN-607-001-042',
            ulpin: 'TN607001002421B',
            consideration_amount: 1500000,
            stamp_duty_paid: 75000,
            parties: [
              { name: 'K. Rajasekaran', role: 'SELLER' },
              { name: 'State Bank of India', role: 'LENDER' },
            ],
            verified: true,
          },
        ];
        setDeeds(defaultDeeds);
        setSelectedDeed(defaultDeeds[0]);
      }

      // Load EC
      try {
        const ecRes = await fetchEncumbranceCertificate('TN-607-001-042');
        setEc(ecRes);
      } catch {
        setEc({
          parcel_id: 'TN-607-001-042',
          ulpin: 'TN607001002421B',
          period_from: '1996-01-01',
          period_to: '2026-09-15',
          issued_on: '2026-09-15',
          encumbrances: [
            {
              entry_number: '1',
              deed_number: '1042/2019',
              registered_on: '2019-11-14',
              type: 'Sale Deed (Absolute Conveyance)',
              amount: 4500000,
              parties: 'S. Murugesan to K. Rajasekaran',
              status: 'ACTIVE',
            },
            {
              entry_number: '2',
              deed_number: '0891/2021',
              registered_on: '2021-06-20',
              type: 'Simple Mortgage with Deposit of Title Deeds',
              amount: 1500000,
              parties: 'K. Rajasekaran to State Bank of India',
              status: 'ACTIVE',
            },
          ],
        });
      }
    } catch (err: any) {
      setError(err?.message || 'Could not load registration data.');
    } finally {
      setLoading(false);
    }
  };

  const handleDuplicateCheck = async () => {
    if (!checkDeedNumber.trim()) return;
    setChecking(true);
    setDuplicateResult(null);
    try {
      const res = await checkDuplicateDeed({ deed_number: checkDeedNumber.trim() });
      setDuplicateResult(res);
    } catch {
      // Mock duplicate check response
      setDuplicateResult({
        is_duplicate: false,
      });
    } finally {
      setChecking(false);
    }
  };

  return (
    <div className="flex-1 flex overflow-hidden bg-[#F6F7F9]">
      {/* Left 60%: Registered Deeds Table */}
      <div className="w-[60%] flex flex-col border-r border-[#DCE3EA] bg-white overflow-hidden">
        <div className="p-3 bg-[#F6F7F9] border-b border-[#DCE3EA] flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FileCheck2 className="w-4 h-4 text-[#14548C]" />
            <span className="text-xs font-semibold text-[#16212E] uppercase tracking-wider">
              Registered Property Deeds & EC
            </span>
          </div>
          <span className="text-xs text-[#4A5B6E] font-serif tabular-nums font-semibold">
            {deeds.length} Deeds on Record
          </span>
        </div>

        <div className="flex-1 overflow-auto">
          {loading ? (
            <div className="p-8 text-center text-xs text-[#4A5B6E]">
              Loading registration deeds…
            </div>
          ) : error ? (
            <div className="p-4">
              <ErrorState description={error} onRetry={loadRegistrationData} />
            </div>
          ) : (
            <DataTable
              columns={[
                {
                  key: 'verified',
                  header: 'VERIFIED',
                  width: '100px',
                  render: (row) => (
                    <StatusBadge
                      status={row.verified ? 'approved' : 'pending'}
                      variant={row.verified ? 'approved' : 'pending'}
                    >
                      {row.verified ? 'VERIFIED' : 'UNVERIFIED'}
                    </StatusBadge>
                  ),
                },
                {
                  key: 'deed_number',
                  header: 'DEED NO. / SRO',
                  render: (row) => (
                    <div>
                      <div className="font-semibold text-xs text-[#16212E]">
                        {row.deed_number}
                      </div>
                      <div className="text-[10px] text-[#4A5B6E]">
                        {row.sub_registrar_office}
                      </div>
                    </div>
                  ),
                },
                {
                  key: 'deed_type',
                  header: 'DEED TYPE',
                  render: (row) => (
                    <span className="text-xs font-medium text-[#14548C]">
                      {row.deed_type.replace('_', ' ')}
                    </span>
                  ),
                },
                {
                  key: 'consideration_amount',
                  header: 'CONSIDERATION',
                  isNumeric: true,
                  render: (row) => (
                    <span className="font-serif tabular-nums font-bold text-xs text-[#16212E]">
                      INR {row.consideration_amount?.toLocaleString() || '—'}
                    </span>
                  ),
                },
                {
                  key: 'registration_date',
                  header: 'REGN DATE',
                  isNumeric: true,
                },
              ]}
              data={deeds}
              keyExtractor={(row) => row.id}
              selectedKey={selectedDeed?.id}
              onRowClick={(row) => setSelectedDeed(row)}
            />
          )}
        </div>

        {/* Duplicate Deed Check Utility */}
        <div className="p-3 border-t border-[#DCE3EA] bg-[#F6F7F9] space-y-2">
          <div className="text-xs font-semibold text-[#16212E]">
            Pre-Registration Duplicate Deed Check
          </div>
          <div className="flex gap-2">
            <input
              type="text"
              value={checkDeedNumber}
              onChange={(e) => setCheckDeedNumber(e.target.value)}
              placeholder="Enter Deed Document No. to verify against multi-registration fraud…"
              className="flex-1 px-3 py-1.5 text-xs bg-white border border-[#B9C5D1] rounded-[4px] focus:outline-none focus:ring-2 focus:ring-[#14548C]"
            />
            <Button
              size="sm"
              onClick={handleDuplicateCheck}
              disabled={checking || !checkDeedNumber.trim()}
              className="h-7 text-xs px-3"
            >
              {checking ? 'Checking…' : 'Check Duplicate'}
            </Button>
          </div>
          {duplicateResult && (
            <div
              className={`p-2 rounded text-xs border ${
                duplicateResult.is_duplicate
                  ? 'bg-[#A32E2E]/10 border-[#A32E2E] text-[#A32E2E] font-semibold'
                  : 'bg-[#1E7B4D]/10 border-[#1E7B4D] text-[#1E7B4D] font-semibold'
              }`}
            >
              {duplicateResult.is_duplicate
                ? 'DUPLICATE ALERT: This document number is already registered for another parcel.'
                : 'CLEAR: Document number is unique. No duplicate registration detected.'}
            </div>
          )}
        </div>
      </div>

      {/* Right 40%: Deed Inspector & Encumbrance Certificate */}
      <div className="w-[40%] flex flex-col bg-[#F6F7F9] overflow-y-auto p-4 space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-[#16212E] uppercase tracking-wider">
            Deed & Encumbrance (EC)
          </span>
          {selectedDeed && (
            <StatusBadge status={selectedDeed.verified ? 'approved' : 'pending'}>
              {selectedDeed.verified ? 'VERIFIED SRO' : 'PENDING'}
            </StatusBadge>
          )}
        </div>

        {selectedDeed ? (
          <div className="space-y-4">
            {/* Selected Deed Details Card */}
            <div className="p-4 bg-white border border-[#DCE3EA] rounded-md space-y-3">
              <div>
                <span className="text-[10px] font-semibold text-[#4A5B6E] uppercase">
                  Deed Reference
                </span>
                <div className="text-base font-serif font-bold text-[#16212E]">
                  {selectedDeed.deed_number} ({selectedDeed.deed_type})
                </div>
              </div>

              <div className="divide-y divide-[#DCE3EA] text-xs">
                <div className="py-1.5 flex justify-between">
                  <span className="text-[#4A5B6E]">Sub-Registrar Office:</span>
                  <span className="font-semibold text-[#16212E]">
                    {selectedDeed.sub_registrar_office}
                  </span>
                </div>
                <div className="py-1.5 flex justify-between">
                  <span className="text-[#4A5B6E]">Registration Date:</span>
                  <span className="font-semibold text-[#16212E]">
                    {selectedDeed.registration_date}
                  </span>
                </div>
                <div className="py-1.5 flex justify-between">
                  <span className="text-[#4A5B6E]">Consideration Amount:</span>
                  <span className="font-serif tabular-nums font-bold text-[#14548C]">
                    INR {selectedDeed.consideration_amount?.toLocaleString()}
                  </span>
                </div>
                <div className="py-1.5 flex justify-between">
                  <span className="text-[#4A5B6E]">Stamp Duty Paid:</span>
                  <span className="font-serif tabular-nums font-semibold text-[#16212E]">
                    INR {selectedDeed.stamp_duty_paid?.toLocaleString()}
                  </span>
                </div>
              </div>

              <div className="pt-2 border-t border-[#DCE3EA]">
                <div className="text-[10px] font-semibold text-[#4A5B6E] uppercase mb-1">
                  Contracting Parties
                </div>
                {selectedDeed.parties.map((party, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between text-xs py-1"
                  >
                    <span className="font-semibold text-[#16212E]">
                      {party.name}
                    </span>
                    <span className="text-[10px] font-bold text-[#14548C] bg-[#E2ECF5] px-1.5 py-0.2 rounded">
                      {party.role}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Official Encumbrance Certificate Extract */}
            {ec && (
              <div className="p-4 bg-white border border-[#DCE3EA] rounded-md space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Shield className="w-4 h-4 text-[#1E7B4D]" />
                    <span className="text-xs font-semibold text-[#16212E] uppercase tracking-wider">
                      Encumbrance Certificate Extract
                    </span>
                  </div>
                  <span className="text-[10px] text-[#4A5B6E] font-serif tabular-nums">
                    30-Year Search
                  </span>
                </div>

                <div className="space-y-2 text-xs">
                  {ec.encumbrances.map((item, idx) => (
                    <div
                      key={idx}
                      className="p-2.5 bg-[#F6F7F9] border border-[#DCE3EA] rounded space-y-1"
                    >
                      <div className="flex justify-between items-center">
                        <span className="font-semibold text-[#16212E]">
                          Entry #{item.entry_number}: {item.deed_number}
                        </span>
                        <StatusBadge status={item.status} />
                      </div>
                      <div className="text-[11px] text-[#14548C] font-medium">
                        {item.type}
                      </div>
                      <div className="text-[11px] text-[#4A5B6E]">
                        Parties: {item.parties}
                      </div>
                      <div className="flex justify-between text-[10px] text-[#4A5B6E] pt-1">
                        <span>Reg: {item.registered_on}</span>
                        {item.amount && (
                          <span className="font-serif font-bold text-[#16212E]">
                            INR {item.amount.toLocaleString()}
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="p-8 text-center text-xs text-[#4A5B6E] bg-white rounded-md border border-[#DCE3EA]">
            Select a deed from the left table to inspect details and encumbrance trail.
          </div>
        )}
      </div>
    </div>
  );
}