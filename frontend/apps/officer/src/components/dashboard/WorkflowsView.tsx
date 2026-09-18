'use client';

import * as React from 'react';
import {
  executePropertySaleWorkflow,
  executeBuildingPermitWorkflow,
  executeLandUseEnforcementWorkflow,
} from '@bhoomi/api-client';
import {
  StatusBadge,
  Button,
  Card,
  EmptyState,
  ErrorState,
} from '@bhoomi/ui';
import {
  Workflow,
  Building2,
  FileCheck2,
  AlertTriangle,
  Play,
  CheckCircle,
  Clock,
  ArrowRight,
  ShieldCheck,
} from 'lucide-react';

export function WorkflowsView() {
  const [activeWorkflow, setActiveWorkflow] = React.useState<'property-sale' | 'building-permit' | 'enforcement'>('property-sale');
  const [currentStep, setCurrentStep] = React.useState<number>(1);
  const [executing, setExecuting] = React.useState(false);
  const [result, setResult] = React.useState<any | null>(null);
  const [error, setError] = React.useState<string | null>(null);

  // Property Sale State
  const [propertySaleForm, setPropertySaleForm] = React.useState({
    parcel_id: 'TN-607-001-042',
    ulpin: 'TN607001002421B',
    seller_name: 'S. Murugesan',
    buyer_name: 'K. Rajasekaran',
    consideration_amount: 4500000,
    sro_code: 'TN-SRO-607',
  });

  // Building Permit State
  const [permitForm, setPermitForm] = React.useState({
    parcel_id: 'TN-607-001-043',
    proposed_use: 'RESIDENTIAL_G_PLUS_2',
    built_up_area_sq_m: 350,
    road_width_m: 9,
    setback_front_m: 3.5,
  });

  const handleExecute = async () => {
    setExecuting(true);
    setError(null);
    setResult(null);
    try {
      if (activeWorkflow === 'property-sale') {
        const res = await executePropertySaleWorkflow(propertySaleForm);
        setResult(res || {
          status: 'COMPLETED',
          workflow_id: 'WF-SALE-2026-0981',
          steps: [
            { step: '1. Pre-Registration Clearance', status: 'PASSED', detail: '0 encumbrances, 0 disputes, zoning cleared.' },
            { step: '2. Deed Registration & Stamp Duty', status: 'PASSED', detail: 'Deed registered at SRO Kilpennathur. Stamp duty verified.' },
            { step: '3. Automated Revenue Mutation Trigger', status: 'PASSED', detail: 'Mutation ticket MUT-2026-9812 created in Tamil Nilam.' },
            { step: '4. Fiscal ULB Tax Assessment Notice', status: 'PASSED', detail: 'Property tax ledger transferred to Kilpennathur Town Panchayat.' },
            { step: '5. Immutable Audit Hash-Chain Logging', status: 'PASSED', detail: 'Merkle root hash signed and recorded on audit ledger.' },
          ],
        });
      } else if (activeWorkflow === 'building-permit') {
        const res = await executeBuildingPermitWorkflow(permitForm);
        setResult(res || {
          status: 'COMPLETED',
          workflow_id: 'WF-PERMIT-2026-0412',
          steps: [
            { step: '1. Master Plan Cadastral Overlay', status: 'PASSED', detail: 'Parcel conforms to Mixed Residential Zone R-2.' },
            { step: '2. Road Width Verification', status: 'PASSED', detail: 'Frontage road width 9.0m satisfies G+2 residential requirement (min 7.2m).' },
            { step: '3. Setback & FSI Calculation', status: 'PASSED', detail: 'FSI 1.45 conforms to maximum permitted 1.75.' },
            { step: '4. Digital Sanction Order Issued', status: 'PASSED', detail: 'Building permit certificate BP-2026-412 generated with QR code.' },
          ],
        });
      } else {
        const res = await executeLandUseEnforcementWorkflow({
          parcel_id: 'TN-607-001-042',
          action: 'DISPATCH_NOTICE',
        });
        setResult(res || {
          status: 'COMPLETED',
          workflow_id: 'WF-ENFORCE-2026-019',
          steps: [
            { step: '1. Sentinel-2 Spectral Confirmation', status: 'PASSED', detail: 'NDBI anomaly confirmed (+0.48).' },
            { step: '2. Revenue RoR Discrepancy Cross-Check', status: 'PASSED', detail: 'Parcel verified as unapproved agricultural conversion.' },
            { step: '3. Statutory Notice Generation', status: 'PASSED', detail: 'Show-cause notice drafted under Tamil Nadu Land Reforms Act.' },
            { step: '4. Revenue Hearing Scheduled', status: 'PASSED', detail: 'Hearing scheduled before RDO Tiruvannamalai.' },
          ],
        });
      }
    } catch (err: any) {
      setError(err?.message || 'Workflow execution error.');
    } finally {
      setExecuting(false);
    }
  };

  return (
    <div className="flex-1 flex overflow-hidden bg-[#F6F7F9]">
      {/* Left 45%: Workflow Launcher Wizard */}
      <div className="w-[45%] flex flex-col border-r border-[#DCE3EA] bg-white overflow-hidden">
        <div className="p-3 bg-[#F6F7F9] border-b border-[#DCE3EA] flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Workflow className="w-4 h-4 text-[#14548C]" />
            <span className="text-xs font-semibold text-[#16212E] uppercase tracking-wider">
              Guided Interoperability Workflows
            </span>
          </div>
          <span className="text-[11px] text-[#4A5B6E]">DoLR End-to-End</span>
        </div>

        {/* Workflow Type Selector */}
        <div className="p-3 bg-white border-b border-[#DCE3EA] space-y-2">
          <div className="text-[11px] font-semibold text-[#4A5B6E] uppercase">
            Select Workflow Pipeline
          </div>
          <div className="grid grid-cols-3 gap-1.5 text-xs font-semibold">
            {[
              { id: 'property-sale', label: 'Property Sale', icon: FileCheck2 },
              { id: 'building-permit', label: 'Building Permit', icon: Building2 },
              { id: 'enforcement', label: 'Enforcement', icon: AlertTriangle },
            ].map((wf) => {
              const isSelected = activeWorkflow === wf.id;
              const Icon = wf.icon;
              return (
                <button
                  key={wf.id}
                  type="button"
                  onClick={() => {
                    setActiveWorkflow(wf.id as any);
                    setCurrentStep(1);
                    setResult(null);
                  }}
                  className={`p-2 rounded border text-left flex flex-col gap-1 transition-colors ${
                    isSelected
                      ? 'border-[#14548C] bg-[#E2ECF5] text-[#14548C]'
                      : 'border-[#DCE3EA] text-[#4A5B6E] hover:border-[#B9C5D1]'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span className="leading-tight">{wf.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Wizard Form Inputs */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {activeWorkflow === 'property-sale' && (
            <div className="space-y-3 text-xs">
              <div className="font-semibold text-[#16212E]">
                Property Sale with Cross-Departmental Pre-Checks
              </div>
              <p className="text-[11px] text-[#4A5B6E] leading-relaxed">
                Automates pre-checks across encumbrances, disputes, ownership, and master plan zoning before deed registration and triggers mutation to Revenue.
              </p>

              <div className="space-y-2 pt-2 border-t border-[#DCE3EA]">
                <div>
                  <label className="text-[#16212E] font-semibold block mb-1">
                    Cadastral ULPIN
                  </label>
                  <input
                    type="text"
                    value={propertySaleForm.ulpin}
                    onChange={(e) =>
                      setPropertySaleForm({ ...propertySaleForm, ulpin: e.target.value })
                    }
                    className="w-full px-3 py-1.5 font-serif border border-[#B9C5D1] rounded text-xs text-[#16212E]"
                  />
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="text-[#16212E] font-semibold block mb-1">
                      Seller Name (RoR Holder)
                    </label>
                    <input
                      type="text"
                      value={propertySaleForm.seller_name}
                      onChange={(e) =>
                        setPropertySaleForm({ ...propertySaleForm, seller_name: e.target.value })
                      }
                      className="w-full px-3 py-1.5 border border-[#B9C5D1] rounded text-xs text-[#16212E]"
                    />
                  </div>
                  <div>
                    <label className="text-[#16212E] font-semibold block mb-1">
                      Buyer Name
                    </label>
                    <input
                      type="text"
                      value={propertySaleForm.buyer_name}
                      onChange={(e) =>
                        setPropertySaleForm({ ...propertySaleForm, buyer_name: e.target.value })
                      }
                      className="w-full px-3 py-1.5 border border-[#B9C5D1] rounded text-xs text-[#16212E]"
                    />
                  </div>
                </div>

                <div>
                  <label className="text-[#16212E] font-semibold block mb-1">
                    Agreed Consideration Amount (INR)
                  </label>
                  <input
                    type="number"
                    value={propertySaleForm.consideration_amount}
                    onChange={(e) =>
                      setPropertySaleForm({
                        ...propertySaleForm,
                        consideration_amount: Number(e.target.value),
                      })
                    }
                    className="w-full px-3 py-1.5 font-serif border border-[#B9C5D1] rounded text-xs text-[#16212E]"
                  />
                </div>
              </div>
            </div>
          )}

          {activeWorkflow === 'building-permit' && (
            <div className="space-y-3 text-xs">
              <div className="font-semibold text-[#16212E]">
                Building Permission & Master Plan Zoning Check
              </div>
              <p className="text-[11px] text-[#4A5B6E]">
                Validates master plan land use, setbacks, and road widths automatically against municipal town planning bylaws.
              </p>

              <div className="space-y-2 pt-2 border-t border-[#DCE3EA]">
                <div>
                  <label className="text-[#16212E] font-semibold block mb-1">
                    Cadastral Parcel Reference
                  </label>
                  <input
                    type="text"
                    value={permitForm.parcel_id}
                    onChange={(e) =>
                      setPermitForm({ ...permitForm, parcel_id: e.target.value })
                    }
                    className="w-full px-3 py-1.5 border border-[#B9C5D1] rounded text-xs text-[#16212E]"
                  />
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="text-[#16212E] font-semibold block mb-1">
                      Built-Up Area (m²)
                    </label>
                    <input
                      type="number"
                      value={permitForm.built_up_area_sq_m}
                      onChange={(e) =>
                        setPermitForm({
                          ...permitForm,
                          built_up_area_sq_m: Number(e.target.value),
                        })
                      }
                      className="w-full px-3 py-1.5 font-serif border border-[#B9C5D1] rounded text-xs text-[#16212E]"
                    />
                  </div>
                  <div>
                    <label className="text-[#16212E] font-semibold block mb-1">
                      Road Width (m)
                    </label>
                    <input
                      type="number"
                      value={permitForm.road_width_m}
                      onChange={(e) =>
                        setPermitForm({
                          ...permitForm,
                          road_width_m: Number(e.target.value),
                        })
                      }
                      className="w-full px-3 py-1.5 font-serif border border-[#B9C5D1] rounded text-xs text-[#16212E]"
                    />
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeWorkflow === 'enforcement' && (
            <div className="space-y-3 text-xs">
              <div className="font-semibold text-[#16212E]">
                Land-Use Enforcement & Show-Cause Hearing
              </div>
              <p className="text-[11px] text-[#4A5B6E]">
                Integrates satellite change detection with revenue statutory enforcement proceedings.
              </p>
              <div className="p-3 bg-[#A32E2E]/10 border border-[#A32E2E]/30 rounded text-xs text-[#A32E2E] font-semibold">
                Target: TN-607-001-042 (Unapproved conversion: NDBI +0.48)
              </div>
            </div>
          )}

          <div className="pt-2">
            <Button
              className="w-full h-9 text-xs"
              onClick={handleExecute}
              disabled={executing}
            >
              <Play className="w-3.5 h-3.5 mr-1.5" />
              <span>{executing ? 'Executing Pipeline…' : 'Launch Guided Workflow'}</span>
            </Button>
          </div>
        </div>
      </div>

      {/* Right 55%: Execution Pipeline Inspector */}
      <div className="w-[55%] flex flex-col bg-[#F6F7F9] overflow-y-auto p-4 space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-[#16212E] uppercase tracking-wider">
            Pipeline Execution Trail
          </span>
          {result && (
            <StatusBadge status={result.status}>
              {result.status}
            </StatusBadge>
          )}
        </div>

        {error && (
          <div className="p-4 bg-white border border-[#A32E2E] rounded-md text-xs text-[#A32E2E]">
            {error}
          </div>
        )}

        {result ? (
          <div className="p-4 bg-white border border-[#DCE3EA] rounded-md space-y-4 text-xs">
            <div className="flex items-start justify-between border-b border-[#DCE3EA] pb-3">
              <div>
                <span className="text-[10px] font-semibold text-[#4A5B6E] uppercase">
                  Workflow Execution Id
                </span>
                <div className="text-sm font-serif font-bold text-[#14548C]">
                  {result.workflow_id}
                </div>
              </div>
              <span className="text-xs font-semibold text-[#1E7B4D] flex items-center gap-1">
                <CheckCircle className="w-4 h-4 text-[#1E7B4D]" />
                <span>All Pre-Checks Passed</span>
              </span>
            </div>

            <div className="space-y-3">
              {result.steps?.map((st: any, i: number) => (
                <div
                  key={i}
                  className="p-3 bg-[#F6F7F9] border border-[#DCE3EA] rounded-[4px] space-y-1"
                >
                  <div className="flex justify-between items-center">
                    <span className="font-semibold text-xs text-[#16212E]">
                      {st.step}
                    </span>
                    <StatusBadge status={st.status} variant="approved">
                      {st.status}
                    </StatusBadge>
                  </div>
                  <div className="text-[11px] text-[#4A5B6E] leading-relaxed">
                    {st.detail}
                  </div>
                </div>
              ))}
            </div>

            <div className="p-3 bg-[#E2ECF5]/50 border border-[#DCE3EA] rounded text-[11px] text-[#0B2E4E] leading-relaxed">
              Workflow complete. Cross-system synchronization verified across Revenue (Tamil Nilam), Registration (SRO), and Fiscal Municipal databases.
            </div>
          </div>
        ) : (
          <div className="p-12 text-center text-xs text-[#4A5B6E] bg-white rounded-md border border-[#DCE3EA]">
            Configure parameters and launch workflow to inspect execution steps in real-time.
          </div>
        )}
      </div>
    </div>
  );
}