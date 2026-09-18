'use client';

import { useState } from 'react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow, Button, Badge } from '@bhoomi/ui';

interface ReviewItem {
  id: string;
  sourceA: string;
  valueA: string;
  sourceB: string;
  valueB: string;
  areaSimilarity: number;
  nameSimilarity: number;
  iou: number;
}

export default function ReviewQueuePage() {
  const [items] = useState<ReviewItem[]>([
    {
      id: '1',
      sourceA: 'Revenue: Rajesh Kumar, 1.2 acres',
      valueA: 'TN-33-0001-12345',
      sourceB: 'SRO: R. Kumar, 1.4 acres',
      valueB: 'SRO-2024-05678',
      areaSimilarity: 86,
      nameSimilarity: 92,
      iou: 78,
    },
  ]);

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">Entity Resolution Review Queue</h1>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Source A</TableHead>
            <TableHead>Source B</TableHead>
            <TableHead>Evidence</TableHead>
            <TableHead>Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {items.map((item) => (
            <TableRow key={item.id}>
              <TableCell>
                <div>
                  <p className="font-semibold">{item.sourceA}</p>
                  <p className="text-xs text-neutral-500">{item.valueA}</p>
                </div>
              </TableCell>
              <TableCell>
                <div>
                  <p className="font-semibold">{item.sourceB}</p>
                  <p className="text-xs text-neutral-500">{item.valueB}</p>
                </div>
              </TableCell>
              <TableCell>
                <div className="space-y-1">
                  <Badge variant="success">Name: {item.nameSimilarity}%</Badge>
                  <Badge variant="success">Area: {item.areaSimilarity}%</Badge>
                  <Badge variant="warning">IoU: {item.iou}%</Badge>
                </div>
              </TableCell>
              <TableCell>
                <div className="flex gap-2">
                  <Button size="sm" variant="default">Approve</Button>
                  <Button size="sm" variant="destructive">Reject</Button>
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
