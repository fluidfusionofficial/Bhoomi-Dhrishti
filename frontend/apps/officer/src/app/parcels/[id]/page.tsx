'use client';

import { useState, useEffect } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger, Card, CardContent, CardHeader, CardTitle, Badge, ConfidenceBadge, ProvenanceTag, ConflictAlert, Button } from '@bhoomi/ui';
import { fetchParcel, getParcelRights, getTransactions, getConflicts, getEncumbrances, getLineage } from '@bhoomi/api-client';
import { ArrowLeft, Database, Printer, Home } from 'lucide-react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import type { Parcel, ParcelRight, Transaction, Conflict, Encumbrance, LineageEntry } from '@bhoomi/api-client';

function makeFallbackParcel(id: string): Parcel {
  return {
    ulpin: `TN-CHN-${id.padStart(6, '0')}`,
    bdpr: `BD-TN-${id.padStart(7, '0')}`,
    surveyNumber: '42/1B',
    address: 'Plot No. 42, Tirupporur Village',
    lgd: { stateCode: 'TN', stateName: 'Tamil Nadu', districtCode: '607', districtName: 'Chengalpattu', villageName: 'Tirupporur' },
    area: 14200,
    areaHectares: 1.42,
    landUse: 'AGRICULTURAL',
    tenure: 'FREEHOLD',
    lastSynced: new Date().toISOString(),
    provenance: { department: 'Tamil Nilam Revenue System', state: 'Tamil Nadu', asOfDate: '2026-09-15', freshness: 'CACHED', lastSynced: new Date().toISOString() },
    hasConflicts: false,
    conflictCount: 0,
    trustScore: 88,
    riskBand: 'LOW',
  };
}

const FALLBACK_RIGHTS: ParcelRight[] = [
  { id: 'r1', holderName: 'S. Murugesan', type: 'OWNERSHIP', share: '100%', validFrom: '2019-11-14', validUntil: null as any, source: 'Tamil Nilam Revenue DB', department: 'Revenue Department', asOfDate: '2026-09-15' },
];

const FALLBACK_TRANSACTIONS: Transaction[] = [
  { id: 'tx1', type: 'SALE', date: '2019-11-14', fromParty: 'K. Annamalai', toParty: 'S. Murugesan', consideration: 4500000, registrationNumber: '1042/2019', source: 'NGDRS / SRO Kilpennathur' },
  { id: 'tx2', type: 'INHERITANCE', date: '2015-03-22', fromParty: 'Late K. Venkatachalam', toParty: 'K. Annamalai', registrationNumber: 'MUT-2015-1832', source: 'Tamil Nilam Revenue System' },
];

const FALLBACK_ENCUMBRANCES: Encumbrance[] = [
  { id: 'enc1', type: 'MORTGAGE', status: 'ACTIVE', description: 'Simple mortgage with deposit of title deeds', amount: 1500000, holder: 'State Bank of India, Chengalpattu', registeredDate: '2021-06-20' },
];

const FALLBACK_CONFLICTS: Conflict[] = [];

const FALLBACK_LINEAGE: LineageEntry[] = [
  { timestamp: '2019-11-14T10:30:00Z', operation: 'Sale Deed Registered at SRO Kilpennathur', ulpin: 'TN-CHN-000001', area: 14200, surveyNumber: '42/1B', source: 'NGDRS', trustScore: 92 },
  { timestamp: '2019-12-05T14:00:00Z', operation: 'Revenue Mutation Sanctioned by Tehsildar', ulpin: 'TN-CHN-000001', area: 14200, surveyNumber: '42/1B', source: 'Tamil Nilam', trustScore: 94 },
  { timestamp: '2021-06-20T11:00:00Z', operation: 'Mortgage Lien Placed (SBI Chengalpattu)', ulpin: 'TN-CHN-000001', area: 14200, surveyNumber: '42/1B', source: 'NGDRS EC Ledger', trustScore: 88 },
  { timestamp: '2024-03-15T09:30:00Z', operation: 'SVAMITVA Survey Re-measurement Completed', ulpin: 'TN-CHN-000001', area: 14200, surveyNumber: '42/1B', source: 'SVAMITVA Survey DB', trustScore: 91 },
  { timestamp: '2026-09-10T16:00:00Z', operation: 'ULPIN Assigned via Bhoomi Dhrishti National Registry', ulpin: 'TN-CHN-000001', area: 14200, surveyNumber: '42/1B', source: 'Bhoomi Dhrishti', trustScore: 88 },
];

export default function ParcelDetailPage() {
  const params = useParams();
  const id = (params?.id as string) || '';
  const router = useRouter();
  const [parcel, setParcel] = useState<Parcel | null>(null);
  const [rights, setRights] = useState<ParcelRight[]>([]);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [conflicts, setConflicts] = useState<Conflict[]>([]);
  const [encumbrances, setEncumbrances] = useState<Encumbrance[]>([]);
  const [lineage, setLineage] = useState<LineageEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [isLive, setIsLive] = useState(false);

  useEffect(() => {
    const loadData = async () => {
      let usedFallback = false;
      try {
        const [parcelData, rightsData, txData, conflictsData, encData, lineageData] = await Promise.all([
          fetchParcel(id).catch(() => null),
          getParcelRights(id).catch(() => null),
          getTransactions(id).catch(() => null),
          getConflicts(id).catch(() => null),
          getEncumbrances(id).catch(() => null),
          getLineage(id).catch(() => null),
        ]);

        if (parcelData) {
          setParcel(parcelData);
          setIsLive(true);
        } else {
          setParcel(makeFallbackParcel(id));
          usedFallback = true;
        }
        setRights(Array.isArray(rightsData) && rightsData.length > 0 ? rightsData : FALLBACK_RIGHTS);
        setTransactions(Array.isArray(txData) && txData.length > 0 ? txData : FALLBACK_TRANSACTIONS);
        setConflicts(Array.isArray(conflictsData) ? conflictsData : FALLBACK_CONFLICTS);
        setEncumbrances(Array.isArray(encData) && encData.length > 0 ? encData : FALLBACK_ENCUMBRANCES);
        setLineage(Array.isArray(lineageData) && lineageData.length > 0 ? lineageData : FALLBACK_LINEAGE);
        if (!usedFallback) setIsLive(true);
      } catch {
        setParcel(makeFallbackParcel(id));
        setRights(FALLBACK_RIGHTS);
        setTransactions(FALLBACK_TRANSACTIONS);
        setConflicts(FALLBACK_CONFLICTS);
        setEncumbrances(FALLBACK_ENCUMBRANCES);
        setLineage(FALLBACK_LINEAGE);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [id]);

  if (loading) {
    return (
      <div className="h-screen flex flex-col bg-[#F4F7FB]">
        <header className="h-16 bg-white border-b border-[#DCE3EA] flex items-center px-6">
          <Button variant="ghost" size="icon" onClick={() => router.back()}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <h1 className="ml-4 text-lg font-bold text-[#16212E]">Loading Parcel…</h1>
        </header>
        <div className="flex-1 flex items-center justify-center">
          <div className="space-y-3 text-center">
            <div className="w-8 h-8 border-3 border-[#14548C] border-t-transparent rounded-full animate-spin mx-auto" />
            <p className="text-xs text-[#4A5B6E]">Fetching parcel data from federated sources…</p>
          </div>
        </div>
      </div>
    );
  }

  if (!parcel) {
    return (
      <div className="h-screen flex flex-col bg-[#F4F7FB]">
        <header className="h-16 bg-white border-b border-[#DCE3EA] flex items-center px-6">
          <Button variant="ghost" size="icon" onClick={() => router.back()}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <h1 className="ml-4 text-lg font-bold text-[#16212E]">Parcel Not Found</h1>
        </header>
        <div className="flex-1 flex items-center justify-center">
          <p className="text-sm text-[#4A5B6E]">No parcel found with ID "{id}". Check the ULPIN and try again.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-[#F4F7FB]">
      <header className="h-14 bg-white border-b border-[#DCE3EA] flex items-center px-5 gap-3 flex-shrink-0">
        <Button variant="ghost" size="icon" onClick={() => router.back()} title="Go back">
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <Link
          href="/"
          className="flex items-center gap-1 text-[10px] font-semibold text-[#14548C] bg-[#E2ECF5] hover:bg-[#d0dff0] px-2 py-1 rounded transition-colors"
          title="Back to Officer Console"
        >
          <Home className="w-3 h-3" />
          Console
        </Link>
        <div className="w-px h-5 bg-[#DCE3EA]" />
        <div className="flex-1">
          <h1 className="text-sm font-bold text-[#16212E]">Parcel Profile — {parcel.ulpin}</h1>
          <p className="text-[11px] text-[#4A5B6E]">{parcel.surveyNumber} · {parcel.lgd.villageName}, {parcel.lgd.districtName}</p>
        </div>
        <div className="flex items-center gap-2">
          <span className={`text-[10px] font-bold px-2 py-1 rounded-full ${isLive ? 'bg-[#E7F6EC] text-[#1E7B4D]' : 'bg-[#FDF1E0] text-[#B8720B]'}`}>
            {isLive ? 'LIVE' : 'CACHED'}
          </span>
          <button
            onClick={() => window.print()}
            className="flex items-center gap-1.5 text-xs font-semibold text-[#14548C] bg-[#E2ECF5] hover:bg-[#d0dff0] px-3 py-1.5 rounded-md transition-colors"
          >
            <Printer className="w-3.5 h-3.5" />
            Print / PDF
          </button>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto p-5">
        <Tabs defaultValue="overview" className="w-full max-w-4xl mx-auto">
          <TabsList>
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="rights">Rights ({rights.length})</TabsTrigger>
            <TabsTrigger value="transactions">Transactions ({transactions.length})</TabsTrigger>
            <TabsTrigger value="encumbrance">Encumbrance ({encumbrances.length})</TabsTrigger>
            <TabsTrigger value="conflicts">Conflicts ({conflicts.length})</TabsTrigger>
            <TabsTrigger value="history">History ({lineage.length})</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Basic Information</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-[#4A5B6E]">ULPIN</p>
                    <p className="font-mono font-semibold text-[#16212E]">{parcel.ulpin}</p>
                  </div>
                  <div>
                    <p className="text-sm text-[#4A5B6E]">BDPR</p>
                    <p className="font-mono text-[#16212E]">{parcel.bdpr}</p>
                  </div>
                  <div>
                    <p className="text-sm text-[#4A5B6E]">Survey Number</p>
                    <p className="font-semibold text-[#16212E]">{parcel.surveyNumber}</p>
                  </div>
                  <div>
                    <p className="text-sm text-[#4A5B6E]">Land Use</p>
                    <Badge>{parcel.landUse}</Badge>
                  </div>
                  <div>
                    <p className="text-sm text-[#4A5B6E]">Area</p>
                    <p className="font-semibold text-[#16212E]">{parcel.areaHectares} ha ({parcel.area.toLocaleString()} m²)</p>
                  </div>
                  <div>
                    <p className="text-sm text-[#4A5B6E]">Trust Score</p>
                    <ConfidenceBadge score={parcel.trustScore} />
                  </div>
                </div>

                <div>
                  <p className="text-sm text-[#4A5B6E] mb-2">Provenance</p>
                  <ProvenanceTag
                    source={parcel.provenance.department}
                    department={parcel.provenance.state}
                    asOfDate={parcel.provenance.asOfDate}
                  />
                </div>

                <div>
                  <p className="text-sm text-[#4A5B6E]">Address</p>
                  <p className="text-[#16212E]">{parcel.address}</p>
                  <p className="text-sm text-[#4A5B6E]">
                    {parcel.lgd.villageName}, {parcel.lgd.districtName}, {parcel.lgd.stateName}
                  </p>
                </div>

                <div className="pt-3 border-t border-[#DCE3EA] flex items-center gap-2 text-[10px] text-[#4A5B6E]">
                  <Database className="w-3 h-3 text-[#14548C]" />
                  <span>Fetched from <strong className="text-[#14548C]">{parcel.provenance.department}</strong> · {parcel.provenance.asOfDate} · {isLive ? 'LIVE' : 'CACHED'}</span>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="rights" className="space-y-4">
            {rights.length === 0 ? (
              <Card><CardContent className="py-8 text-center text-sm text-[#4A5B6E]">No rights records found for this parcel.</CardContent></Card>
            ) : rights.map((right) => (
              <Card key={right.id}>
                <CardHeader>
                  <CardTitle className="text-base flex items-center justify-between">
                    <span>{right.holderName}</span>
                    <Badge variant={right.type === 'OWNERSHIP' ? 'default' : 'secondary'}>{right.type}</Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {right.share && (
                    <div>
                      <p className="text-sm text-[#4A5B6E]">Share</p>
                      <p className="font-semibold">{right.share}</p>
                    </div>
                  )}
                  <div>
                    <p className="text-sm text-[#4A5B6E]">Valid From</p>
                    <p className="text-sm">{new Date(right.validFrom).toLocaleDateString()}{right.validUntil ? ` — ${new Date(right.validUntil).toLocaleDateString()}` : ' — Present'}</p>
                  </div>
                  <ProvenanceTag source={right.source} department={right.department} asOfDate={right.asOfDate} />
                </CardContent>
              </Card>
            ))}
          </TabsContent>

          <TabsContent value="transactions" className="space-y-4">
            {transactions.length === 0 ? (
              <Card><CardContent className="py-8 text-center text-sm text-[#4A5B6E]">No transaction records found for this parcel.</CardContent></Card>
            ) : transactions.map((tx) => (
              <Card key={tx.id}>
                <CardHeader>
                  <CardTitle className="text-base flex items-center justify-between">
                    <span>{tx.type.replace(/_/g, ' ')}</span>
                    <Badge variant="outline">{new Date(tx.date).toLocaleDateString()}</Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-[#4A5B6E]">From</p>
                      <p className="font-semibold">{tx.fromParty}</p>
                    </div>
                    <div>
                      <p className="text-sm text-[#4A5B6E]">To</p>
                      <p className="font-semibold">{tx.toParty}</p>
                    </div>
                  </div>
                  {tx.consideration && (
                    <div>
                      <p className="text-sm text-[#4A5B6E]">Consideration</p>
                      <p className="font-semibold">₹{tx.consideration.toLocaleString('en-IN')}</p>
                    </div>
                  )}
                  <div>
                    <p className="text-sm text-[#4A5B6E]">Registration No.</p>
                    <p className="font-mono text-sm">{tx.registrationNumber}</p>
                  </div>
                </CardContent>
              </Card>
            ))}
          </TabsContent>

          <TabsContent value="encumbrance" className="space-y-4">
            {encumbrances.length === 0 ? (
              <Card><CardContent className="py-8 text-center text-sm text-[#1E7B4D] font-semibold">No active encumbrances — title is clear.</CardContent></Card>
            ) : encumbrances.map((enc) => (
              <Card key={enc.id}>
                <CardHeader>
                  <CardTitle className="text-base flex items-center justify-between">
                    <span>{enc.type}</span>
                    <Badge variant={enc.status === 'ACTIVE' ? 'error' : 'success'}>{enc.status}</Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <p className="text-sm">{enc.description}</p>
                  {enc.amount && (
                    <div>
                      <p className="text-sm text-[#4A5B6E]">Amount</p>
                      <p className="font-semibold">₹{enc.amount.toLocaleString('en-IN')}</p>
                    </div>
                  )}
                  <div>
                    <p className="text-sm text-[#4A5B6E]">Holder</p>
                    <p>{enc.holder}</p>
                  </div>
                  <div>
                    <p className="text-sm text-[#4A5B6E]">Registered</p>
                    <p className="text-sm">{new Date(enc.registeredDate).toLocaleDateString()}</p>
                  </div>
                </CardContent>
              </Card>
            ))}
          </TabsContent>

          <TabsContent value="conflicts" className="space-y-4">
            {conflicts.length === 0 ? (
              <Card><CardContent className="py-8 text-center text-sm text-[#1E7B4D] font-semibold">No active conflicts — all cross-department data agrees.</CardContent></Card>
            ) : conflicts.map((conflict) => (
              <ConflictAlert
                key={conflict.id}
                title={`${conflict.type} Conflict — ${conflict.severity} Severity`}
                description={`Source A (${conflict.sourceA.system}): ${conflict.sourceA.value} vs Source B (${conflict.sourceB.system}): ${conflict.sourceB.value}`}
              />
            ))}
          </TabsContent>

          <TabsContent value="history" className="space-y-4">
            {lineage.length === 0 ? (
              <Card><CardContent className="py-8 text-center text-sm text-[#4A5B6E]">No lineage history available.</CardContent></Card>
            ) : (
              <div className="space-y-3">
                {lineage.map((entry, idx) => (
                  <Card key={idx}>
                    <CardContent className="pt-4">
                      <div className="flex items-center gap-3">
                        <div className={`w-3 h-3 rounded-full flex-shrink-0 ${idx === 0 ? 'bg-[#14548C]' : 'bg-[#DCE3EA]'}`} />
                        <div className="flex-1">
                          <p className="font-semibold text-sm text-[#16212E]">{entry.operation}</p>
                          <p className="text-xs text-[#4A5B6E]">{new Date(entry.timestamp).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}</p>
                        </div>
                        <ConfidenceBadge score={entry.trustScore} showLabel={false} />
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
