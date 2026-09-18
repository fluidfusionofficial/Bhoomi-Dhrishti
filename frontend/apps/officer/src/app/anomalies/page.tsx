'use client';

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow, Button, Badge } from '@bhoomi/ui';
import Link from 'next/link';

export default function AnomaliesPage() {
  const anomalies = [
    {
      parcelId: 'TN-33-0001-12345',
      type: 'SUSPICIOUS_TRANSACTION',
      score: 0.89,
      reason: 'Transaction value 5x below market rate',
    },
    {
      parcelId: 'TN-33-0001-12346',
      type: 'AREA_DISCREPANCY',
      score: 0.76,
      reason: 'Area mismatch >30% between revenue and survey records',
    },
  ];

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">ML Anomaly Alerts</h1>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Parcel ID</TableHead>
            <TableHead>Anomaly Type</TableHead>
            <TableHead>Score</TableHead>
            <TableHead>Reason</TableHead>
            <TableHead>Action</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {anomalies.map((anomaly) => (
            <TableRow key={anomaly.parcelId}>
              <TableCell className="font-mono">{anomaly.parcelId}</TableCell>
              <TableCell>
                <Badge variant="warning">{anomaly.type}</Badge>
              </TableCell>
              <TableCell>{Math.round(anomaly.score * 100)}%</TableCell>
              <TableCell>{anomaly.reason}</TableCell>
              <TableCell>
                <Link href={`/parcels/${anomaly.parcelId}`}>
                  <Button size="sm">Investigate</Button>
                </Link>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
