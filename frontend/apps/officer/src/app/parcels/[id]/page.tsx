'use client';

import { use, useState, useEffect } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger, Card, CardContent, CardHeader, CardTitle, Badge, ConfidenceBadge, ProvenanceTag, ConflictAlert, Button } from '@bhoomi/ui';
import { fetchParcel, getParcelRights, getTransactions, getConflicts, getEncumbrances, getLineage } from '@bhoomi/api-client';
import { TimeSlider } from '@bhoomi/map';
import { ArrowLeft } from 'lucide-react';
import { useRouter } from 'next/navigation';
import type { Parcel, ParcelRight, Transaction, Conflict, Encumbrance, LineageEntry } from '@bhoomi/api-client';

export default function ParcelDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const router = useRouter();
  const [parcel, setParcel] = useState<Parcel | null>(null);
  const [rights, setRights] = useState<ParcelRight[]>([]);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [conflicts, setConflicts] = useState<Conflict[]>([]);
  const [encumbrances, setEncumbrances] = useState<Encumbrance[]>([]);
  const [lineage, setLineage] = useState<LineageEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [parcelData, rightsData, txData, conflictsData, encData, lineageData] = await Promise.all([
          fetchParcel(id),
          getParcelRights(id),
          getTransactions(id),
          getConflicts(id),
          getEncumbrances(id),
          getLineage(id),
        ]);

        setParcel(parcelData);
        setRights(rightsData);
        setTransactions(txData);
        setConflicts(conflictsData);
        setEncumbrances(encData);
        setLineage(lineageData);
      } catch (error) {
        console.error('Failed to load parcel data', error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [id]);

  if (loading) {
    return <div className="p-6">Loading...</div>;
  }

  if (!parcel) {
    return <div className="p-6">Parcel not found</div>;
  }

  return (
    <div className="h-screen flex flex-col bg-neutral-50">
      <header className="h-16 bg-white border-b border-neutral-200 flex items-center px-6">
        <Button variant="ghost" size="icon" onClick={() => router.back()}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <h1 className="ml-4 text-xl font-bold">Parcel Details</h1>
      </header>

      <div className="flex-1 overflow-y-auto p-6">
        <Tabs defaultValue="overview" className="w-full">
          <TabsList>
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="rights">Rights (RRR)</TabsTrigger>
            <TabsTrigger value="transactions">Transactions</TabsTrigger>
            <TabsTrigger value="encumbrance">Encumbrance</TabsTrigger>
            <TabsTrigger value="conflicts">Conflicts</TabsTrigger>
            <TabsTrigger value="history">History</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Basic Information</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-neutral-600">ULPIN</p>
                    <p className="font-mono font-semibold">{parcel.ulpin}</p>
                  </div>
                  <div>
                    <p className="text-sm text-neutral-600">BDPR</p>
                    <p className="font-mono">{parcel.bdpr}</p>
                  </div>
                  <div>
                    <p className="text-sm text-neutral-600">Survey Number</p>
                    <p className="font-semibold">{parcel.surveyNumber}</p>
                  </div>
                  <div>
                    <p className="text-sm text-neutral-600">Land Use</p>
                    <Badge>{parcel.landUse}</Badge>
                  </div>
                  <div>
                    <p className="text-sm text-neutral-600">Area</p>
                    <p className="font-semibold">{parcel.areaHectares} ha ({parcel.area} m²)</p>
                  </div>
                  <div>
                    <p className="text-sm text-neutral-600">Trust Score</p>
                    <ConfidenceBadge score={parcel.trustScore} />
                  </div>
                </div>

                <div>
                  <p className="text-sm text-neutral-600 mb-2">Provenance</p>
                  <ProvenanceTag
                    source={parcel.provenance.department}
                    department={parcel.provenance.state}
                    asOfDate={parcel.provenance.asOfDate}
                  />
                </div>

                <div>
                  <p className="text-sm text-neutral-600">Address</p>
                  <p>{parcel.address}</p>
                  <p className="text-sm text-neutral-500">
                    {parcel.lgd.villageName}, {parcel.lgd.districtName}, {parcel.lgd.stateName}
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="rights" className="space-y-4">
            {rights.map((right) => (
              <Card key={right.id}>
                <CardHeader>
                  <CardTitle className="text-base flex items-center justify-between">
                    <span>{right.holderName}</span>
                    <Badge variant={right.type === 'OWNERSHIP' ? 'default' : 'secondary'}>
                      {right.type}
                    </Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {right.share && (
                    <div>
                      <p className="text-sm text-neutral-600">Share</p>
                      <p className="font-semibold">{right.share}</p>
                    </div>
                  )}
                  <div>
                    <p className="text-sm text-neutral-600">Valid Period</p>
                    <p className="text-sm">
                      {new Date(right.validFrom).toLocaleDateString()}
                      {right.validUntil && ` - ${new Date(right.validUntil).toLocaleDateString()}`}
                    </p>
                  </div>
                  <ProvenanceTag
                    source={right.source}
                    department={right.department}
                    asOfDate={right.asOfDate}
                  />
                </CardContent>
              </Card>
            ))}
          </TabsContent>

          <TabsContent value="transactions" className="space-y-4">
            {transactions.map((tx) => (
              <Card key={tx.id}>
                <CardHeader>
                  <CardTitle className="text-base flex items-center justify-between">
                    <span>{tx.type}</span>
                    <Badge variant="outline">{new Date(tx.date).toLocaleDateString()}</Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-neutral-600">From</p>
                      <p className="font-semibold">{tx.fromParty}</p>
                    </div>
                    <div>
                      <p className="text-sm text-neutral-600">To</p>
                      <p className="font-semibold">{tx.toParty}</p>
                    </div>
                  </div>
                  {tx.consideration && (
                    <div>
                      <p className="text-sm text-neutral-600">Consideration</p>
                      <p className="font-semibold">₹{tx.consideration.toLocaleString('en-IN')}</p>
                    </div>
                  )}
                  <div>
                    <p className="text-sm text-neutral-600">Registration No.</p>
                    <p className="font-mono text-sm">{tx.registrationNumber}</p>
                  </div>
                </CardContent>
              </Card>
            ))}
          </TabsContent>

          <TabsContent value="encumbrance" className="space-y-4">
            {encumbrances.map((enc) => (
              <Card key={enc.id}>
                <CardHeader>
                  <CardTitle className="text-base flex items-center justify-between">
                    <span>{enc.type}</span>
                    <Badge variant={enc.status === 'ACTIVE' ? 'error' : 'success'}>
                      {enc.status}
                    </Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <p className="text-sm">{enc.description}</p>
                  {enc.amount && (
                    <div>
                      <p className="text-sm text-neutral-600">Amount</p>
                      <p className="font-semibold">₹{enc.amount.toLocaleString('en-IN')}</p>
                    </div>
                  )}
                  <div>
                    <p className="text-sm text-neutral-600">Holder</p>
                    <p>{enc.holder}</p>
                  </div>
                  <div>
                    <p className="text-sm text-neutral-600">Registered</p>
                    <p className="text-sm">{new Date(enc.registeredDate).toLocaleDateString()}</p>
                  </div>
                </CardContent>
              </Card>
            ))}
          </TabsContent>

          <TabsContent value="conflicts" className="space-y-4">
            {conflicts.map((conflict) => (
              <ConflictAlert
                key={conflict.id}
                title={`${conflict.type} Conflict - ${conflict.severity} Severity`}
                description={`Source A (${conflict.sourceA.system}): ${conflict.sourceA.value} vs Source B (${conflict.sourceB.system}): ${conflict.sourceB.value}`}
              />
            ))}
            {conflicts.length > 0 && (
              <Button className="w-full">Assign for Review</Button>
            )}
          </TabsContent>

          <TabsContent value="history" className="space-y-4">
            <TimeSlider
              events={lineage.map((entry) => ({
                timestamp: entry.timestamp,
                label: entry.operation,
                data: entry,
              }))}
            />
            <div className="space-y-3">
              {lineage.map((entry, idx) => (
                <Card key={idx}>
                  <CardContent className="pt-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-semibold">{entry.operation}</p>
                        <p className="text-sm text-neutral-600">
                          {new Date(entry.timestamp).toLocaleDateString()}
                        </p>
                      </div>
                      <ConfidenceBadge score={entry.trustScore} showLabel={false} />
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
