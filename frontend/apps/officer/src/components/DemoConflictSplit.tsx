'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@bhoomi/ui';

interface DemoConflictSplitProps {
  onComplete: () => void;
}

export function DemoConflictSplit({ onComplete }: DemoConflictSplitProps) {
  const [step, setStep] = useState(0);

  useEffect(() => {
    if (step === 0) {
      const timer = setTimeout(() => setStep(1), 1000);
      return () => clearTimeout(timer);
    } else if (step === 1) {
      const timer = setTimeout(() => setStep(2), 2000);
      return () => clearTimeout(timer);
    } else if (step === 2) {
      const timer = setTimeout(() => onComplete(), 2000);
      return () => clearTimeout(timer);
    }
  }, [step, onComplete]);

  return (
    <div className="absolute inset-0 bg-white z-50 flex items-center justify-center p-8">
      <div className="max-w-6xl w-full">
        <h2 className="text-2xl font-bold text-center mb-8 text-primary-600">
          Conflict Detection Demo
        </h2>

        {step >= 1 && (
          <div className="grid grid-cols-2 gap-6 mb-8">
            {/* Revenue Source */}
            <Card className="border-2 border-blue-300 animate-in fade-in slide-in-from-left duration-500">
              <CardHeader>
                <CardTitle className="text-lg">Revenue Department</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <p className="text-sm text-neutral-600">ULPIN</p>
                  <p className="font-mono font-semibold">TN-33-0001-12345</p>
                </div>
                <div>
                  <p className="text-sm text-neutral-600">Owner</p>
                  <p className="font-semibold text-blue-600">Rajesh Kumar</p>
                </div>
                <div>
                  <p className="text-sm text-neutral-600">Area</p>
                  <p className="font-semibold text-blue-600">1.2 acres</p>
                </div>
                <div>
                  <p className="text-sm text-neutral-600">Survey No.</p>
                  <p className="font-mono">123/4A</p>
                </div>
              </CardContent>
            </Card>

            {/* SRO Source */}
            <Card className="border-2 border-amber-300 animate-in fade-in slide-in-from-right duration-500">
              <CardHeader>
                <CardTitle className="text-lg">Sub-Registrar Office</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <p className="text-sm text-neutral-600">Document ID</p>
                  <p className="font-mono font-semibold">SRO-2024-05678</p>
                </div>
                <div>
                  <p className="text-sm text-neutral-600">Owner</p>
                  <p className="font-semibold text-amber-600">R. Kumar</p>
                </div>
                <div>
                  <p className="text-sm text-neutral-600">Area</p>
                  <p className="font-semibold text-amber-600">1.4 acres</p>
                </div>
                <div>
                  <p className="text-sm text-neutral-600">Survey No.</p>
                  <p className="font-mono">123/4-A</p>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {step >= 2 && (
          <Card className="border-2 border-green-400 animate-in fade-in zoom-in duration-500">
            <CardHeader className="bg-green-50">
              <CardTitle className="text-lg text-green-700 flex items-center gap-2">
                ✓ Unified View - Conflict Resolved
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 pt-6">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-neutral-600">ULPIN</p>
                  <p className="font-mono font-semibold">TN-33-0001-12345</p>
                </div>
                <div>
                  <p className="text-sm text-neutral-600">Resolved Owner</p>
                  <p className="font-semibold">Rajesh Kumar</p>
                  <p className="text-xs text-green-600">95% confidence match</p>
                </div>
                <div>
                  <p className="text-sm text-neutral-600">Reconciled Area</p>
                  <p className="font-semibold">1.3 acres</p>
                  <p className="text-xs text-neutral-500">Average of sources</p>
                </div>
                <div>
                  <p className="text-sm text-neutral-600">Trust Score</p>
                  <p className="font-semibold text-green-600">82%</p>
                </div>
              </div>
              <div className="bg-neutral-50 p-3 rounded text-xs space-y-1">
                <p className="font-semibold">Resolution Log:</p>
                <p>• Name variation detected (Rajesh Kumar ≈ R. Kumar)</p>
                <p>• Area discrepancy within 20% threshold</p>
                <p>• Survey number format normalized</p>
                <p>• Entity linked across systems</p>
              </div>
            </CardContent>
          </Card>
        )}

        <div className="flex justify-center gap-2 mt-6">
          <div className={`h-2 w-2 rounded-full ${step >= 0 ? 'bg-primary-500' : 'bg-neutral-300'}`} />
          <div className={`h-2 w-2 rounded-full ${step >= 1 ? 'bg-primary-500' : 'bg-neutral-300'}`} />
          <div className={`h-2 w-2 rounded-full ${step >= 2 ? 'bg-primary-500' : 'bg-neutral-300'}`} />
        </div>
      </div>
    </div>
  );
}
