'use client';

import * as React from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import {
  fetchServiceCatalog,
  submitApplication,
  CatalogServiceItem,
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
  ArrowLeft,
  CheckCircle,
  Clock,
  FileText,
  Shield,
  UploadCloud,
  ChevronRight,
  AlertCircle,
  HelpCircle,
  Send,
} from 'lucide-react';
import { CitizenHeader } from '@/components/CitizenHeader';
import { BottomNav } from '@/components/BottomNav';

export default function NewApplicationPage() {
  return (
    <React.Suspense fallback={<div className="p-8 text-center text-xs text-[#4A5B6E]">Loading service application...</div>}>
      <NewApplicationContent />
    </React.Suspense>
  );
}

function NewApplicationContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialParcelId = searchParams?.get('parcel_id') || '';
  const initialUlpin = searchParams?.get('ulpin') || '';

  const [catalog, setCatalog] = React.useState<CatalogServiceItem[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  // Wizard state
  const [currentStep, setCurrentStep] = React.useState<1 | 2 | 3 | 4>(1);
  const [selectedService, setSelectedService] = React.useState<CatalogServiceItem | null>(null);
  const [formData, setFormData] = React.useState({
    parcel_id: initialParcelId || 'a1b2c3d4-0000-0000-0000-000000000001',
    ulpin: initialUlpin || 'TN607001002421B',
    applicant_name: 'K. Rajasekaran',
    applicant_phone: '+91 98765 43210',
    applicant_email: 'rajasekaran@bhoomi.gov.in',
    notes: '',
  });

  const [submitting, setSubmitting] = React.useState(false);
  const [submitResult, setSubmitResult] = React.useState<{
    application_id: string;
    tracking_number: string;
    status: string;
  } | null>(null);

  React.useEffect(() => {
    loadCatalog();
  }, []);

  const loadCatalog = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchServiceCatalog();
      if (Array.isArray(res) && res.length > 0) {
        setCatalog(res);
        setSelectedService(res[0]);
      } else {
        // Fallback standard DoLR service catalog items
        const defaultCatalog: CatalogServiceItem[] = [
          {
            id: 'svc-1',
            code: 'MUTATION_SALE',
            title: 'Revenue Title Mutation (Sale / Transfer)',
            description: 'Update Record of Rights (Pattadar / RoR) following registered sale deed.',
            department: 'Revenue & Disaster Management',
            estimated_days: 15,
            fee_inr: 250,
            required_documents: ['Registered Sale Deed', 'Aadhaar / Voter ID', 'Prior Patta Copy'],
          },
          {
            id: 'svc-2',
            code: 'ENCUMBRANCE_CERT',
            title: 'Encumbrance Certificate (EC)',
            description: 'Official Nil-encumbrance or liability extract for banks and property sales.',
            department: 'Registration Department',
            estimated_days: 3,
            fee_inr: 100,
            required_documents: ['Survey Number Details', 'Applicant ID Proof'],
          },
          {
            id: 'svc-3',
            code: 'LAND_USE_CONVERSION',
            title: 'Land-Use Change NOC (Agricultural to Residential)',
            description: 'Apply for statutory conversion permission under District Collectorate authority.',
            department: 'Town & Country Planning',
            estimated_days: 30,
            fee_inr: 1500,
            required_documents: ['RoR Extract', 'Master Plan Site Plan', 'Challan Receipt'],
          },
        ];
        setCatalog(defaultCatalog);
        setSelectedService(defaultCatalog[0]);
      }
    } catch (err: any) {
      setError(err?.message || 'Could not load service catalog.');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!selectedService) return;
    setSubmitting(true);
    setError(null);
    try {
      const res = await submitApplication({
        service_code: selectedService.code,
        parcel_id: formData.parcel_id,
        applicant_name: formData.applicant_name,
        applicant_phone: formData.applicant_phone,
        applicant_email: formData.applicant_email,
        details: {
          ulpin: formData.ulpin,
          notes: formData.notes,
          fee_inr: selectedService.fee_inr,
        },
      });
      setSubmitResult(res);
    } catch (err: any) {
      setError(
        err?.message ||
          'Failed to submit application. Check the input details and try again.'
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F4F7FB] flex flex-col pb-20">
      <CitizenHeader />

      <main className="flex-1 max-w-md w-full mx-auto p-4 space-y-4">
        {/* Top Header */}
        <div className="flex items-center justify-between">
          <button
            type="button"
            onClick={() => router.back()}
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#14548C]"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back</span>
          </button>
          <span className="text-[10px] font-semibold text-[#4A5B6E] uppercase tracking-wider">
            Step {currentStep} of 4
          </span>
        </div>

        <div>
          <h1 className="text-base font-bold font-serif text-[#16212E]">
            Apply for Land Record Services
          </h1>
          <p className="text-xs text-[#4A5B6E] mt-0.5">
            MoRD citizen service gateway for mutations, certificates, and title updates.
          </p>
        </div>

        {/* Step Progress Bar */}
        <div className="grid grid-cols-4 gap-1.5 py-1">
          {[1, 2, 3, 4].map((s) => (
            <div
              key={s}
              className={`h-1.5 rounded-full transition-colors ${
                currentStep >= s ? 'bg-[#14548C]' : 'bg-[#DCE3EA]'
              }`}
            />
          ))}
        </div>

        {submitResult ? (
          /* Confirmation State */
          <Card className="p-6 text-center space-y-4">
            <div className="w-12 h-12 rounded-full bg-[#1E7B4D]/10 text-[#1E7B4D] mx-auto flex items-center justify-center">
              <CheckCircle className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-base font-bold font-serif text-[#16212E]">
                Application Submitted
              </h2>
              <p className="text-xs text-[#4A5B6E] mt-1">
                Your request has entered the official revenue review queue.
              </p>
            </div>

            <div className="p-3 bg-[#F6F7F9] border border-[#DCE3EA] rounded-md text-left space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-[#4A5B6E]">Tracking Number:</span>
                <span className="font-serif font-bold text-[#14548C] tabular-nums">
                  {submitResult.tracking_number || 'BD-APP-2026-9140'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#4A5B6E]">Service:</span>
                <span className="font-semibold text-[#16212E]">
                  {selectedService?.title}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#4A5B6E]">Initial Status:</span>
                <StatusBadge status="submitted" variant="pending">
                  SUBMITTED
                </StatusBadge>
              </div>
            </div>

            <div className="pt-2 flex flex-col gap-2">
              <Link href="/applications">
                <Button className="w-full" size="default">
                  Track in My Applications
                </Button>
              </Link>
              <Link href="/">
                <Button variant="outline" className="w-full" size="sm">
                  Return to Home
                </Button>
              </Link>
            </div>
          </Card>
        ) : (
          /* Guided Form Steps */
          <div className="space-y-4">
            {error && (
              <div className="p-3 bg-white border border-[#A32E2E] rounded-md text-xs text-[#A32E2E]">
                {error}
              </div>
            )}

            {/* STEP 1: Select Service */}
            {currentStep === 1 && (
              <div className="space-y-3">
                <h3 className="text-xs font-semibold text-[#16212E] uppercase tracking-wider">
                  1. Choose Service from Catalog
                </h3>

                {loading ? (
                  <div className="h-40 bg-white rounded-md animate-pulse border border-[#DCE3EA]" />
                ) : (
                  catalog.map((svc) => {
                    const isSelected = selectedService?.id === svc.id;
                    return (
                      <div
                        key={svc.id}
                        onClick={() => setSelectedService(svc)}
                        className={`p-3.5 bg-white border rounded-md cursor-pointer transition-colors space-y-2 ${
                          isSelected
                            ? 'border-[#14548C] ring-1 ring-[#14548C]'
                            : 'border-[#DCE3EA] hover:border-[#B9C5D1]'
                        }`}
                      >
                        <div className="flex items-start justify-between">
                          <div className="text-xs font-semibold text-[#16212E]">
                            {svc.title}
                          </div>
                          <span className="font-serif tabular-nums font-bold text-xs text-[#14548C]">
                            INR {svc.fee_inr}
                          </span>
                        </div>
                        <p className="text-[11px] text-[#4A5B6E] leading-relaxed">
                          {svc.description}
                        </p>
                        <div className="flex items-center gap-3 text-[10px] text-[#4A5B6E] pt-1 border-t border-[#DCE3EA]">
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3 text-[#14548C]" />
                            <span>SLA: ~{svc.estimated_days} working days</span>
                          </span>
                          <span>Dept: {svc.department}</span>
                        </div>
                      </div>
                    );
                  })
                )}

                <Button
                  className="w-full mt-3"
                  onClick={() => setCurrentStep(2)}
                  disabled={!selectedService}
                >
                  Continue to Land Details
                </Button>
              </div>
            )}

            {/* STEP 2: Land Identifiers */}
            {currentStep === 2 && (
              <Card className="p-4 space-y-3">
                <h3 className="text-xs font-semibold text-[#16212E] uppercase tracking-wider">
                  2. Land Identifiers
                </h3>

                <div>
                  <label className="text-xs font-semibold text-[#16212E] block mb-1">
                    ULPIN (14 Digits)
                  </label>
                  <input
                    type="text"
                    value={formData.ulpin}
                    onChange={(e) =>
                      setFormData({ ...formData, ulpin: e.target.value })
                    }
                    className="w-full px-3 py-2 bg-white border border-[#B9C5D1] rounded-md text-xs font-serif text-[#16212E] focus:outline-none focus:ring-2 focus:ring-[#14548C]"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-[#16212E] block mb-1">
                    Parcel System ID (UUID)
                  </label>
                  <input
                    type="text"
                    value={formData.parcel_id}
                    onChange={(e) =>
                      setFormData({ ...formData, parcel_id: e.target.value })
                    }
                    className="w-full px-3 py-2 bg-white border border-[#B9C5D1] rounded-md text-xs text-[#16212E] focus:outline-none focus:ring-2 focus:ring-[#14548C]"
                  />
                </div>

                <div className="flex gap-2 pt-2">
                  <Button
                    variant="outline"
                    className="flex-1"
                    onClick={() => setCurrentStep(1)}
                  >
                    Back
                  </Button>
                  <Button
                    className="flex-1"
                    onClick={() => setCurrentStep(3)}
                    disabled={!formData.ulpin.trim()}
                  >
                    Applicant Details
                  </Button>
                </div>
              </Card>
            )}

            {/* STEP 3: Applicant Details */}
            {currentStep === 3 && (
              <Card className="p-4 space-y-3">
                <h3 className="text-xs font-semibold text-[#16212E] uppercase tracking-wider">
                  3. Applicant Details
                </h3>

                <div>
                  <label className="text-xs font-semibold text-[#16212E] block mb-1">
                    Full Legal Name
                  </label>
                  <input
                    type="text"
                    value={formData.applicant_name}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        applicant_name: e.target.value,
                      })
                    }
                    className="w-full px-3 py-2 bg-white border border-[#B9C5D1] rounded-md text-xs text-[#16212E] focus:outline-none focus:ring-2 focus:ring-[#14548C]"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-[#16212E] block mb-1">
                    Mobile Phone (for SMS notifications)
                  </label>
                  <input
                    type="text"
                    value={formData.applicant_phone}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        applicant_phone: e.target.value,
                      })
                    }
                    className="w-full px-3 py-2 bg-white border border-[#B9C5D1] rounded-md text-xs text-[#16212E] focus:outline-none focus:ring-2 focus:ring-[#14548C]"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-[#16212E] block mb-1">
                    Application Remarks / Additional Notes
                  </label>
                  <textarea
                    rows={2}
                    value={formData.notes}
                    onChange={(e) =>
                      setFormData({ ...formData, notes: e.target.value })
                    }
                    placeholder="Provide deed registration number or mutation grounds"
                    className="w-full px-3 py-2 bg-white border border-[#B9C5D1] rounded-md text-xs text-[#16212E] focus:outline-none focus:ring-2 focus:ring-[#14548C]"
                  />
                </div>

                <div className="flex gap-2 pt-2">
                  <Button
                    variant="outline"
                    className="flex-1"
                    onClick={() => setCurrentStep(2)}
                  >
                    Back
                  </Button>
                  <Button
                    className="flex-1"
                    onClick={() => setCurrentStep(4)}
                    disabled={!formData.applicant_name.trim()}
                  >
                    Review & Fee
                  </Button>
                </div>
              </Card>
            )}

            {/* STEP 4: Review & Submit */}
            {currentStep === 4 && (
              <Card className="p-4 space-y-4">
                <h3 className="text-xs font-semibold text-[#16212E] uppercase tracking-wider">
                  4. Review & Confirm Application
                </h3>

                <div className="divide-y divide-[#DCE3EA] text-xs">
                  <div className="py-2 flex justify-between">
                    <span className="text-[#4A5B6E]">Service:</span>
                    <span className="font-semibold text-[#16212E]">
                      {selectedService?.title}
                    </span>
                  </div>
                  <div className="py-2 flex justify-between">
                    <span className="text-[#4A5B6E]">ULPIN:</span>
                    <span className="font-serif font-semibold text-[#16212E]">
                      {formData.ulpin}
                    </span>
                  </div>
                  <div className="py-2 flex justify-between">
                    <span className="text-[#4A5B6E]">Applicant:</span>
                    <span className="font-semibold text-[#16212E]">
                      {formData.applicant_name}
                    </span>
                  </div>
                  <div className="py-2 flex justify-between">
                    <span className="text-[#4A5B6E]">Statutory Fee:</span>
                    <span className="font-serif font-bold text-[#14548C] tabular-nums">
                      INR {selectedService?.fee_inr}
                    </span>
                  </div>
                  <div className="py-2 flex justify-between">
                    <span className="text-[#4A5B6E]">Expected Completion:</span>
                    <span className="font-semibold text-[#16212E]">
                      {selectedService?.estimated_days} working days
                    </span>
                  </div>
                </div>

                <div className="p-3 bg-[#E2ECF5]/50 border border-[#DCE3EA] rounded-md text-[11px] text-[#0B2E4E] leading-relaxed">
                  I hereby declare that the particulars furnished above are true and the registered deeds submitted correspond to lawful cadastral title.
                </div>

                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    className="flex-1"
                    onClick={() => setCurrentStep(3)}
                    disabled={submitting}
                  >
                    Back
                  </Button>
                  <Button
                    className="flex-1"
                    onClick={handleSubmit}
                    disabled={submitting}
                  >
                    {submitting ? 'Submitting…' : 'Confirm & Submit'}
                  </Button>
                </div>
              </Card>
            )}
          </div>
        )}
      </main>

      <BottomNav />
    </div>
  );
}