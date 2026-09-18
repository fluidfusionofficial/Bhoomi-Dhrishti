'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, Button, Badge } from '@bhoomi/ui';
import { Check, Upload, Eye, Database, CheckCircle } from 'lucide-react';

export default function StateOnboardingPage() {
  const [step, setStep] = useState(1);

  const steps = [
    { id: 1, name: 'Upload', icon: Upload, status: step > 1 ? 'complete' : step === 1 ? 'current' : 'upcoming' },
    { id: 2, name: 'Preview', icon: Eye, status: step > 2 ? 'complete' : step === 2 ? 'current' : 'upcoming' },
    { id: 3, name: 'Validate', icon: CheckCircle, status: step > 3 ? 'complete' : step === 3 ? 'current' : 'upcoming' },
    { id: 4, name: 'Ingest', icon: Database, status: step === 4 ? 'current' : 'upcoming' },
  ];

  return (
    <div className="min-h-screen bg-neutral-50 p-6">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-2xl font-bold mb-6">Onboard New State - Karnataka</h1>

        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            {steps.map((s, idx) => (
              <div key={s.id} className="flex items-center">
                <div
                  className={`flex items-center justify-center w-10 h-10 rounded-full ${
                    s.status === 'complete'
                      ? 'bg-green-600 text-white'
                      : s.status === 'current'
                      ? 'bg-primary-600 text-white'
                      : 'bg-neutral-300 text-neutral-600'
                  }`}
                >
                  {s.status === 'complete' ? <Check className="h-5 w-5" /> : <s.icon className="h-5 w-5" />}
                </div>
                <span className="ml-2 text-sm font-medium">{s.name}</span>
                {idx < steps.length - 1 && (
                  <div
                    className={`w-20 h-1 mx-4 ${
                      s.status === 'complete' ? 'bg-green-600' : 'bg-neutral-300'
                    }`}
                  />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Step Content */}
        {step === 1 && (
          <Card>
            <CardHeader>
              <CardTitle>Step 1: Upload Source Data</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="border-2 border-dashed border-neutral-300 rounded-lg p-8 text-center">
                <Upload className="h-12 w-12 mx-auto text-neutral-400 mb-3" />
                <p className="font-semibold mb-2">Upload State Land Records</p>
                <p className="text-sm text-neutral-600 mb-4">
                  Supported formats: Shapefile (ZIP), GeoJSON, CSV with geometry
                </p>
                <Button>Choose Files</Button>
              </div>

              <div className="space-y-2">
                <p className="text-sm font-semibold">Required Files:</p>
                <ul className="text-sm text-neutral-600 space-y-1 ml-4">
                  <li>✓ Parcel boundaries (vector data)</li>
                  <li>✓ Revenue records (CSV/Excel)</li>
                  <li>✓ Registration records (CSV/Excel)</li>
                  <li>✓ Mapping configuration (YAML)</li>
                </ul>
              </div>

              <Button className="w-full" onClick={() => setStep(2)}>
                Continue to Preview
              </Button>
            </CardContent>
          </Card>
        )}

        {step === 2 && (
          <Card>
            <CardHeader>
              <CardTitle>Step 2: Preview Data</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="bg-neutral-50 p-4 rounded space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm font-semibold">Files Uploaded:</span>
                  <Badge variant="success">4 files</Badge>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm font-semibold">Parcels Detected:</span>
                  <span className="font-semibold">1,234,567</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm font-semibold">Format:</span>
                  <span>Shapefile + CSV</span>
                </div>
              </div>

              <div className="flex gap-2">
                <Button variant="outline" onClick={() => setStep(1)}>
                  Back
                </Button>
                <Button className="flex-1" onClick={() => setStep(3)}>
                  Validate Data
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {step === 3 && (
          <Card>
            <CardHeader>
              <CardTitle>Step 3: Validation Report</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 bg-green-50 rounded">
                  <span className="text-sm font-semibold">Schema Validation</span>
                  <Badge variant="success">PASS</Badge>
                </div>
                <div className="flex items-center justify-between p-3 bg-green-50 rounded">
                  <span className="text-sm font-semibold">Geometry Check</span>
                  <Badge variant="success">PASS</Badge>
                </div>
                <div className="flex items-center justify-between p-3 bg-yellow-50 rounded">
                  <span className="text-sm font-semibold">Data Quality</span>
                  <Badge variant="warning">WARNING (3 issues)</Badge>
                </div>
                <div className="flex items-center justify-between p-3 bg-green-50 rounded">
                  <span className="text-sm font-semibold">OGC Conformance</span>
                  <Badge variant="success">PASS</Badge>
                </div>
              </div>

              <div className="flex gap-2">
                <Button variant="outline" onClick={() => setStep(2)}>
                  Back
                </Button>
                <Button className="flex-1" onClick={() => setStep(4)}>
                  Proceed to Ingest
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {step === 4 && (
          <Card>
            <CardHeader>
              <CardTitle>Step 4: Data Ingestion</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="bg-blue-50 p-4 rounded">
                <p className="text-sm font-semibold text-blue-800 mb-2">
                  Ingestion in Progress
                </p>
                <div className="w-full bg-blue-200 rounded-full h-2">
                  <div className="bg-blue-600 h-2 rounded-full" style={{ width: '75%' }}></div>
                </div>
                <p className="text-xs text-blue-700 mt-2">Processing: 925,000 / 1,234,567 parcels</p>
              </div>

              <div className="space-y-2 text-sm">
                <p>✓ Creating spatial index</p>
                <p>✓ Linking cross-references</p>
                <p className="animate-pulse">→ Running entity resolution...</p>
                <p className="text-neutral-400">Generating trust scores</p>
              </div>

              <p className="text-xs text-neutral-600 text-center">
                Estimated time remaining: ~2 minutes
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
