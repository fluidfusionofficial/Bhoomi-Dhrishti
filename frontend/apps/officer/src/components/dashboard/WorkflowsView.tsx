'use client';

import * as React from 'react';
import {
  GitBranch, Scissors, Lock, ShieldAlert,
  Play, CheckCircle2, XCircle, Loader2,
  ArrowRight, Database, FileText, Building2,
  Landmark, AlertTriangle, Leaf, BarChart3,
  Zap, Globe, Clock, Hash,
} from 'lucide-react';

// ── Types ──────────────────────────────────────────────────────────────────────

type WorkflowId = 'mutation' | 'partition' | 'encumbrance' | 'violation';
type StepStatus = 'pending' | 'running' | 'done' | 'failed';

interface Step {
  id: string;
  dept: string;
  deptColor: string;
  deptBg: string;
  icon: React.ElementType;
  label: string;
  detail: string;
  status: StepStatus;
  artifact?: { label: string; value: string };
  durationMs: number;
}

interface EventLog {
  ts: string;
  dept: string;
  deptColor: string;
  msg: string;
}

// ── Workflow definitions ───────────────────────────────────────────────────────

function buildMutationSteps(form: { ulpin: string; seller: string; buyer: string; deed: string; amount: number }): Step[] {
  const mutId = `MUT-2026-${Math.floor(9000 + Math.random() * 999)}`;
  const hash = `3f${Math.random().toString(16).slice(2, 10)}...`;
  return [
    { id: 's1', dept: 'Registration Dept (SRO)', deptColor: '#7C3AED', deptBg: '#EDE9FE', icon: Landmark,
      label: 'Deed Execution Received at SRO', durationMs: 900,
      detail: `Deed ${form.deed} registered at SRO Kilpennathur. Consideration: ₹${form.amount.toLocaleString()}.`,
      status: 'pending' },
    { id: 's2', dept: 'Bhoomi Dhrishti', deptColor: '#14548C', deptBg: '#E2ECF5', icon: Database,
      label: 'ULPIN Cross-Reference — RoR Pattadar Match', durationMs: 700,
      detail: `ULPIN ${form.ulpin} → Revenue RoR pattadar = "${form.seller}" → MATCH with deed seller.`,
      status: 'pending' },
    { id: 's3', dept: 'Bhoomi Dhrishti', deptColor: '#14548C', deptBg: '#E2ECF5', icon: ShieldAlert,
      label: 'Pre-Registration Clearance Check', durationMs: 1100,
      detail: `Encumbrances: 0 · Court stays: 0 · Zoning compliance: PASS → Title is clear.`,
      status: 'pending' },
    { id: 's4', dept: 'Bhoomi Dhrishti → Revenue Dept', deptColor: '#1E7B4D', deptBg: '#E7F6EC', icon: GitBranch,
      label: 'Auto-Mutation Trigger Dispatched', durationMs: 800,
      detail: `Cross-system event fired: deed execution in Registration → mutation pending notice in Revenue.`,
      status: 'pending',
      artifact: { label: 'Mutation Ticket', value: mutId } },
    { id: 's5', dept: 'Revenue Dept (Tamil Nilam)', deptColor: '#14548C', deptBg: '#E2ECF5', icon: FileText,
      label: `Mutation ${mutId} Created in Revenue Queue`, durationMs: 900,
      detail: `Pattadar transfer: "${form.seller}" → "${form.buyer}". Assigned to Tehsildar, Kilpennathur.`,
      status: 'pending' },
    { id: 's6', dept: 'Fiscal / ULB', deptColor: '#B45309', deptBg: '#FEF3C7', icon: BarChart3,
      label: 'Property Tax Ledger Transfer Queued', durationMs: 600,
      detail: `Annual property tax ledger entry to be transferred to Kilpennathur Town Panchayat on mutation sanction.`,
      status: 'pending' },
    { id: 's7', dept: 'Audit Hash-Chain', deptColor: '#4A5B6E', deptBg: '#F1F4F8', icon: Hash,
      label: 'Immutable Event Recorded to Audit Ledger', durationMs: 500,
      detail: `Cross-system event hash: ${hash} · Block sealed on audit chain.`,
      status: 'pending' },
  ];
}

function buildPartitionSteps(form: { ulpin: string; area: number; splitA: number }): Step[] {
  const splitB = 100 - form.splitA;
  const areaA = ((form.area * form.splitA) / 100).toFixed(2);
  const areaB = ((form.area * splitB) / 100).toFixed(2);
  const childA = `${form.ulpin}-A`;
  const childB = `${form.ulpin}-B`;
  return [
    { id: 's1', dept: 'Survey Dept', deptColor: '#0369A1', deptBg: '#E0F2FE', icon: Globe,
      label: 'Parent Parcel Validated by Surveyor', durationMs: 800,
      detail: `ULPIN ${form.ulpin} · Area: ${form.area} m² · FMB survey settled · No active disputes.`,
      status: 'pending' },
    { id: 's2', dept: 'Bhoomi Dhrishti (GIS Engine)', deptColor: '#14548C', deptBg: '#E2ECF5', icon: Scissors,
      label: 'Geometry Split Algorithm Applied', durationMs: 1200,
      detail: `Split ratio ${form.splitA}:${splitB} applied. Child polygon coordinates computed from cadastral boundary vertices.`,
      status: 'pending' },
    { id: 's3', dept: 'Bhoomi Dhrishti', deptColor: '#14548C', deptBg: '#E2ECF5', icon: Database,
      label: 'Child ULPINs Allocated from National Registry', durationMs: 700,
      detail: `Child A: ${childA} (${areaA} m²)  ·  Child B: ${childB} (${areaB} m²)`,
      status: 'pending',
      artifact: { label: 'Child ULPINs', value: `${childA} · ${childB}` } },
    { id: 's4', dept: 'Revenue Dept (Tamil Nilam)', deptColor: '#1E7B4D', deptBg: '#E7F6EC', icon: FileText,
      label: 'New RoR Entries Drafted for Each Child', durationMs: 900,
      detail: `RoR sub-entries created under parent survey number. Awaiting Tehsildar sanction in source system.`,
      status: 'pending' },
    { id: 's5', dept: 'Survey Dept', deptColor: '#0369A1', deptBg: '#E0F2FE', icon: FileText,
      label: 'Subdivision Mutation Notice Generated', durationMs: 700,
      detail: `Mutation for partition filed. FMB sub-division sketch to be updated by Village Surveyor.`,
      status: 'pending' },
    { id: 's6', dept: 'Audit Hash-Chain', deptColor: '#4A5B6E', deptBg: '#F1F4F8', icon: Hash,
      label: 'Parent–Child Lineage Recorded', durationMs: 500,
      detail: `Parent ${form.ulpin} marked PARTITIONED. Lineage chain: ${form.ulpin} → ${childA}, ${childB}.`,
      status: 'pending' },
  ];
}

function buildEncumbranceSteps(form: { ulpin: string; lender: string; amount: number; years: number }): Step[] {
  const ecNo = `EC-TN-2026-${Math.floor(10000 + Math.random() * 9000)}`;
  const lienId = `LIEN-${Math.floor(100000 + Math.random() * 900000)}`;
  return [
    { id: 's1', dept: 'Bank / Financial Institution', deptColor: '#B45309', deptBg: '#FEF3C7', icon: Building2,
      label: 'Lien Registration Request Received', durationMs: 700,
      detail: `${form.lender} filed lien placement request for ULPIN ${form.ulpin}. Loan: ₹${form.amount.toLocaleString()} · ${form.years}-year mortgage.`,
      status: 'pending' },
    { id: 's2', dept: 'Bhoomi Dhrishti', deptColor: '#14548C', deptBg: '#E2ECF5', icon: ShieldAlert,
      label: 'Title Status — Unencumbered Check', durationMs: 900,
      detail: `Current EC search: 0 active mortgages · 0 charges · 0 court stays → Title CLEAR. Lien can proceed.`,
      status: 'pending' },
    { id: 's3', dept: 'Bhoomi Dhrishti', deptColor: '#14548C', deptBg: '#E2ECF5', icon: Database,
      label: 'RoR Pattadar Verified as Mortgage Executor', durationMs: 700,
      detail: `ULPIN cross-reference confirms registered pattadar matches loan applicant identity.`,
      status: 'pending' },
    { id: 's4', dept: 'Registration Dept (EC Ledger)', deptColor: '#7C3AED', deptBg: '#EDE9FE', icon: Lock,
      label: 'Encumbrance Entry Written to EC Database', durationMs: 1000,
      detail: `EC No. ${ecNo} · Lien ID: ${lienId} · Mortgagee: ${form.lender} · Amount: ₹${form.amount.toLocaleString()}`,
      status: 'pending',
      artifact: { label: 'EC / Lien Reference', value: `${ecNo} · ${lienId}` } },
    { id: 's5', dept: 'Bhoomi Dhrishti', deptColor: '#A32E2E', deptBg: '#FDEAEA', icon: Lock,
      label: 'Title Certificate Status → ENCUMBERED', durationMs: 600,
      detail: `Parcel ${form.ulpin} title status instantly updated. Mortgage badge visible on all portal views.`,
      status: 'pending' },
    { id: 's6', dept: 'Notifications', deptColor: '#0369A1', deptBg: '#E0F2FE', icon: Zap,
      label: 'Pattadar Notified via Aadhaar-Linked Mobile', durationMs: 600,
      detail: `SMS + DigiLocker document dispatch. Consent event logged under Data Principal rights.`,
      status: 'pending' },
    { id: 's7', dept: 'Audit Hash-Chain', deptColor: '#4A5B6E', deptBg: '#F1F4F8', icon: Hash,
      label: 'Lien Hash Recorded to Immutable Ledger', durationMs: 500,
      detail: `Lien ${lienId} committed to audit hash-chain. Tamper-proof. Effective from today.`,
      status: 'pending' },
  ];
}

function buildViolationSteps(form: { ulpin: string; parcelArea: number }): Step[] {
  const noticeNo = `SCN-${Math.floor(100 + Math.random() * 900)}/2026`;
  return [
    { id: 's1', dept: 'Bhoomi Dhrishti (GIS Engine)', deptColor: '#14548C', deptBg: '#E2ECF5', icon: Globe,
      label: 'Parcel Geometry Extracted from Cadastral DB', durationMs: 600,
      detail: `ULPIN ${form.ulpin} · Area: ${form.parcelArea} m² · Coordinates loaded for spatial intersection analysis.`,
      status: 'pending' },
    { id: 's2', dept: 'GIS — Eco-Sensitive Zone Check', deptColor: '#1E7B4D', deptBg: '#E7F6EC', icon: Leaf,
      label: 'Eco-Sensitive Zone Buffer Intersection', durationMs: 1100,
      detail: `Overlay against MoEFCC ESZ notifications. Result: NO intersection. Distance to nearest ESZ: 2.4 km.`,
      status: 'pending' },
    { id: 's3', dept: 'GIS — CRZ / River Catchment', deptColor: '#0891b2', deptBg: '#E0F2FE', icon: Globe,
      label: 'River Catchment & CRZ 100m Buffer Check', durationMs: 1000,
      detail: `Parcel intersects Palar River 100m CRZ-III buffer zone by 42 m². VIOLATION DETECTED.`,
      status: 'pending',
      artifact: { label: 'Violation', value: 'CRZ-III Buffer — 42 m² Encroachment' } },
    { id: 's4', dept: 'GIS — Reserved Corridor', deptColor: '#B45309', deptBg: '#FEF3C7', icon: AlertTriangle,
      label: 'Reserved Government Corridor Check', durationMs: 800,
      detail: `SH-114 RoW corridor check: parcel boundary is 8m from RoW edge. Minimum clearance 5m → PASS.`,
      status: 'pending' },
    { id: 's5', dept: 'GIS — Master Plan Zoning', deptColor: '#7C3AED', deptBg: '#EDE9FE', icon: Building2,
      label: 'Master Plan Zone Compliance', durationMs: 700,
      detail: `Parcel designated Agricultural. Current use detected as Mixed (NDBI anomaly via Sentinel-2). MISMATCH.`,
      status: 'pending',
      artifact: { label: 'Violation', value: 'Agricultural → Mixed Use (Unauthorised Conversion)' } },
    { id: 's6', dept: 'Revenue / Planning Dept', deptColor: '#A32E2E', deptBg: '#FDEAEA', icon: FileText,
      label: `Show-Cause Notice ${noticeNo} Drafted`, durationMs: 900,
      detail: `Under Tamil Nadu Land Reforms Act s.12(4) and CRZ Notification 2019. Forwarded to RDO queue.`,
      status: 'pending',
      artifact: { label: 'Notice', value: noticeNo } },
    { id: 's7', dept: 'Audit Hash-Chain', deptColor: '#4A5B6E', deptBg: '#F1F4F8', icon: Hash,
      label: 'Spatial Violation Event Recorded', durationMs: 500,
      detail: `Violation audit trail sealed. 2 violations flagged, 1 show-cause notice issued, 1 monitoring flag set.`,
      status: 'pending' },
  ];
}

// ── Workflow metadata ──────────────────────────────────────────────────────────

const WORKFLOWS = [
  { id: 'mutation' as const, label: 'Auto-Triggered Mutation', icon: GitBranch,
    color: '#1E7B4D', bg: '#E7F6EC',
    tagline: 'Sale deed → Revenue mutation with zero manual delay' },
  { id: 'partition' as const, label: 'Dynamic Partitioning', icon: Scissors,
    color: '#0369A1', bg: '#E0F2FE',
    tagline: 'Boundary split → new child ULPINs generated' },
  { id: 'encumbrance' as const, label: 'Encumbrance Locking', icon: Lock,
    color: '#7C3AED', bg: '#EDE9FE',
    tagline: 'Bank lien → instant title ENCUMBERED status' },
  { id: 'violation' as const, label: 'Violation Detection', icon: ShieldAlert,
    color: '#A32E2E', bg: '#FDEAEA',
    tagline: 'Spatial auto-flag for CRZ, ESZ, RoW, zoning' },
];

// ── Main component ─────────────────────────────────────────────────────────────

export function WorkflowsView() {
  const [activeWf, setActiveWf] = React.useState<WorkflowId>('mutation');
  const [steps, setSteps] = React.useState<Step[]>([]);
  const [eventLog, setEventLog] = React.useState<EventLog[]>([]);
  const [running, setRunning] = React.useState(false);
  const [done, setDone] = React.useState(false);

  // Form state per workflow
  const [mutForm, setMutForm] = React.useState({ ulpin: 'TN-CHN-000001', seller: 'Lakshmi Narayanan', buyer: 'Karthik Selvam', deed: '1042/2026', amount: 4500000 });
  const [partForm, setPartForm] = React.useState({ ulpin: 'TN-CHN-000004', area: 4200, splitA: 60 });
  const [encForm, setEncForm] = React.useState({ ulpin: 'TN-CHN-000002', lender: 'State Bank of India, Chengalpattu', amount: 1800000, years: 15 });
  const [violForm, setViolForm] = React.useState({ ulpin: 'TN-CHN-000006', parcelArea: 2750 });

  const logRef = React.useRef<HTMLDivElement>(null);

  function resetWorkflow() {
    setSteps([]);
    setEventLog([]);
    setDone(false);
  }

  function buildSteps(): Step[] {
    if (activeWf === 'mutation') return buildMutationSteps(mutForm);
    if (activeWf === 'partition') return buildPartitionSteps(partForm);
    if (activeWf === 'encumbrance') return buildEncumbranceSteps(encForm);
    return buildViolationSteps(violForm);
  }

  async function launch() {
    resetWorkflow();
    setRunning(true);
    const initial = buildSteps();
    setSteps(initial);

    for (let i = 0; i < initial.length; i++) {
      // Mark step as running
      setSteps((prev) => prev.map((s, idx) => idx === i ? { ...s, status: 'running' } : s));
      const ts = new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      setEventLog((prev) => [...prev, { ts, dept: initial[i].dept, deptColor: initial[i].deptColor, msg: initial[i].label }]);
      setTimeout(() => { logRef.current?.scrollTo({ top: logRef.current.scrollHeight, behavior: 'smooth' }); }, 50);

      await new Promise((r) => setTimeout(r, initial[i].durationMs));

      setSteps((prev) => prev.map((s, idx) => idx === i ? { ...s, status: 'done' } : s));
    }

    setRunning(false);
    setDone(true);
  }

  const wfMeta = WORKFLOWS.find((w) => w.id === activeWf)!;
  const artifacts = steps.filter((s) => s.artifact && s.status === 'done').map((s) => s.artifact!);
  const violations = steps.filter((s) => s.id !== 's7' && s.artifact && s.status === 'done' && activeWf === 'violation').map((s) => s.artifact!);

  return (
    <div className="flex-1 flex overflow-hidden bg-[#F6F7F9]">

      {/* ── LEFT: Selector + Form ───────────────────────────────────────────── */}
      <div className="w-[380px] flex-shrink-0 flex flex-col border-r border-[#DCE3EA] bg-white overflow-hidden">

        {/* Header */}
        <div className="p-3 bg-[#F6F7F9] border-b border-[#DCE3EA] flex items-center gap-2">
          <GitBranch className="w-4 h-4 text-[#14548C]" />
          <span className="text-xs font-semibold text-[#16212E] uppercase tracking-wider">
            Cross-Departmental Workflows
          </span>
        </div>

        {/* Workflow selector */}
        <div className="p-3 border-b border-[#DCE3EA] space-y-1.5">
          {WORKFLOWS.map((wf) => {
            const Icon = wf.icon;
            const isActive = activeWf === wf.id;
            return (
              <button
                key={wf.id}
                type="button"
                onClick={() => { setActiveWf(wf.id); resetWorkflow(); }}
                className={`w-full flex items-center gap-3 p-2.5 rounded-md border-2 text-left transition-all ${
                  isActive ? 'border-current' : 'border-[#DCE3EA] hover:border-[#B9C5D1]'
                }`}
                style={isActive ? { borderColor: wf.color, backgroundColor: wf.bg } : {}}
              >
                <div className="w-8 h-8 rounded-md flex items-center justify-center flex-shrink-0" style={{ backgroundColor: isActive ? wf.color : '#F1F4F8', color: isActive ? '#fff' : wf.color }}>
                  <Icon className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-xs font-bold" style={{ color: isActive ? wf.color : '#16212E' }}>{wf.label}</div>
                  <div className="text-[10px] text-[#4A5B6E]">{wf.tagline}</div>
                </div>
              </button>
            );
          })}
        </div>

        {/* Form inputs */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3 text-xs">
          <div className="font-bold text-[#16212E]">Simulation Parameters</div>

          {/* Mutation form */}
          {activeWf === 'mutation' && (
            <div className="space-y-2">
              {[
                { label: 'ULPIN', key: 'ulpin', value: mutForm.ulpin },
                { label: 'Seller (RoR Pattadar)', key: 'seller', value: mutForm.seller },
                { label: 'Buyer', key: 'buyer', value: mutForm.buyer },
                { label: 'Deed Number', key: 'deed', value: mutForm.deed },
              ].map(({ label, key, value }) => (
                <div key={key}>
                  <label className="text-[10px] font-bold text-[#4A5B6E] uppercase block mb-1">{label}</label>
                  <input type="text" value={value} onChange={(e) => setMutForm({ ...mutForm, [key]: e.target.value })}
                    className="w-full px-2.5 py-1.5 text-xs border border-[#B9C5D1] rounded focus:outline-none focus:ring-2 focus:ring-[#14548C]" />
                </div>
              ))}
              <div>
                <label className="text-[10px] font-bold text-[#4A5B6E] uppercase block mb-1">Consideration Amount (INR)</label>
                <input type="number" value={mutForm.amount} onChange={(e) => setMutForm({ ...mutForm, amount: Number(e.target.value) })}
                  className="w-full px-2.5 py-1.5 text-xs font-serif border border-[#B9C5D1] rounded focus:outline-none focus:ring-2 focus:ring-[#14548C]" />
              </div>
            </div>
          )}

          {/* Partition form */}
          {activeWf === 'partition' && (
            <div className="space-y-2">
              <div>
                <label className="text-[10px] font-bold text-[#4A5B6E] uppercase block mb-1">Parent ULPIN</label>
                <input type="text" value={partForm.ulpin} onChange={(e) => setPartForm({ ...partForm, ulpin: e.target.value })}
                  className="w-full px-2.5 py-1.5 text-xs border border-[#B9C5D1] rounded focus:outline-none focus:ring-2 focus:ring-[#0369A1]" />
              </div>
              <div>
                <label className="text-[10px] font-bold text-[#4A5B6E] uppercase block mb-1">Total Area (sq.m)</label>
                <input type="number" value={partForm.area} onChange={(e) => setPartForm({ ...partForm, area: Number(e.target.value) })}
                  className="w-full px-2.5 py-1.5 text-xs font-serif border border-[#B9C5D1] rounded focus:outline-none focus:ring-2 focus:ring-[#0369A1]" />
              </div>
              <div>
                <label className="text-[10px] font-bold text-[#4A5B6E] uppercase block mb-1">Split Ratio — Part A: {partForm.splitA}% · Part B: {100 - partForm.splitA}%</label>
                <input type="range" min={10} max={90} value={partForm.splitA} onChange={(e) => setPartForm({ ...partForm, splitA: Number(e.target.value) })}
                  className="w-full accent-[#0369A1]" />
                <div className="flex justify-between text-[10px] text-[#4A5B6E] mt-1">
                  <span>Part A: {((partForm.area * partForm.splitA) / 100).toFixed(0)} m²</span>
                  <span>Part B: {((partForm.area * (100 - partForm.splitA)) / 100).toFixed(0)} m²</span>
                </div>
              </div>
              {/* Visual split diagram */}
              <div className="mt-2 h-8 flex rounded overflow-hidden border border-[#B9C5D1]">
                <div className="flex items-center justify-center text-[10px] font-bold text-white" style={{ width: `${partForm.splitA}%`, background: '#0369A1' }}>A</div>
                <div className="flex items-center justify-center text-[10px] font-bold text-white flex-1" style={{ background: '#0891b2' }}>B</div>
              </div>
            </div>
          )}

          {/* Encumbrance form */}
          {activeWf === 'encumbrance' && (
            <div className="space-y-2">
              {[
                { label: 'ULPIN', key: 'ulpin', value: encForm.ulpin },
                { label: 'Lending Institution', key: 'lender', value: encForm.lender },
              ].map(({ label, key, value }) => (
                <div key={key}>
                  <label className="text-[10px] font-bold text-[#4A5B6E] uppercase block mb-1">{label}</label>
                  <input type="text" value={value} onChange={(e) => setEncForm({ ...encForm, [key]: e.target.value })}
                    className="w-full px-2.5 py-1.5 text-xs border border-[#B9C5D1] rounded focus:outline-none focus:ring-2 focus:ring-[#7C3AED]" />
                </div>
              ))}
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-[10px] font-bold text-[#4A5B6E] uppercase block mb-1">Loan Amount (INR)</label>
                  <input type="number" value={encForm.amount} onChange={(e) => setEncForm({ ...encForm, amount: Number(e.target.value) })}
                    className="w-full px-2.5 py-1.5 text-xs font-serif border border-[#B9C5D1] rounded focus:outline-none focus:ring-2 focus:ring-[#7C3AED]" />
                </div>
                <div>
                  <label className="text-[10px] font-bold text-[#4A5B6E] uppercase block mb-1">Mortgage (years)</label>
                  <input type="number" value={encForm.years} onChange={(e) => setEncForm({ ...encForm, years: Number(e.target.value) })}
                    className="w-full px-2.5 py-1.5 text-xs font-serif border border-[#B9C5D1] rounded focus:outline-none focus:ring-2 focus:ring-[#7C3AED]" />
                </div>
              </div>
            </div>
          )}

          {/* Violation form */}
          {activeWf === 'violation' && (
            <div className="space-y-2">
              <div>
                <label className="text-[10px] font-bold text-[#4A5B6E] uppercase block mb-1">ULPIN to Inspect</label>
                <input type="text" value={violForm.ulpin} onChange={(e) => setViolForm({ ...violForm, ulpin: e.target.value })}
                  className="w-full px-2.5 py-1.5 text-xs border border-[#B9C5D1] rounded focus:outline-none focus:ring-2 focus:ring-[#A32E2E]" />
              </div>
              <div>
                <label className="text-[10px] font-bold text-[#4A5B6E] uppercase block mb-1">Parcel Area (sq.m)</label>
                <input type="number" value={violForm.parcelArea} onChange={(e) => setViolForm({ ...violForm, parcelArea: Number(e.target.value) })}
                  className="w-full px-2.5 py-1.5 text-xs font-serif border border-[#B9C5D1] rounded focus:outline-none focus:ring-2 focus:ring-[#A32E2E]" />
              </div>
              <div className="p-2.5 bg-[#FDEAEA] border border-[#F8C8C8] rounded text-[11px] text-[#A32E2E] font-semibold flex items-start gap-2">
                <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
                Checks: CRZ buffer · ESZ overlay · RoW corridor · Master Plan zoning · Satellite change detection
              </div>
            </div>
          )}

          {/* Launch button */}
          <div className="pt-2">
            <button
              onClick={launch}
              disabled={running}
              className="w-full h-10 flex items-center justify-center gap-2 rounded-md text-sm font-bold text-white transition-all disabled:opacity-60"
              style={{ backgroundColor: wfMeta.color }}
            >
              {running ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Executing Pipeline…
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" />
                  Launch Workflow
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* ── RIGHT: Pipeline + Event Log ─────────────────────────────────────── */}
      <div className="flex-1 flex flex-col overflow-hidden">

        {/* Top: Step pipeline */}
        <div className="flex-1 overflow-y-auto p-4 space-y-2">

          {steps.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full gap-4 text-[#4A5B6E]">
              <div className="w-16 h-16 rounded-full bg-[#F1F4F8] flex items-center justify-center">
                <GitBranch className="w-8 h-8 text-[#B9C5D1]" />
              </div>
              <div className="text-sm font-semibold">Configure parameters and launch a workflow</div>
              <div className="text-xs text-[#4A5B6E]">Watch cross-departmental events execute in real-time</div>
            </div>
          ) : (
            <>
              {/* Workflow title */}
              <div className="flex items-center justify-between pb-2 border-b border-[#DCE3EA]">
                <div className="flex items-center gap-2">
                  <div className="w-6 h-6 rounded flex items-center justify-center" style={{ backgroundColor: wfMeta.color }}>
                    <wfMeta.icon className="w-3.5 h-3.5 text-white" />
                  </div>
                  <span className="text-xs font-bold text-[#16212E]">{wfMeta.label}</span>
                </div>
                {done && (
                  <span className="text-[10px] font-bold bg-[#E7F6EC] text-[#1E7B4D] px-2.5 py-1 rounded-full flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3" /> PIPELINE COMPLETE
                  </span>
                )}
              </div>

              {/* Steps */}
              {steps.map((step, i) => {
                const Icon = step.icon;
                const isRunning = step.status === 'running';
                const isDone = step.status === 'done';
                const isPending = step.status === 'pending';
                return (
                  <div key={step.id} className={`bg-white rounded-md border p-3 flex gap-3 transition-all duration-300 ${
                    isDone ? 'border-[#DCE3EA] opacity-100' :
                    isRunning ? 'border-[#14548C] shadow-md opacity-100' :
                    'border-[#F1F4F8] opacity-40'
                  }`}>
                    {/* Step number / status icon */}
                    <div className="flex flex-col items-center gap-1 flex-shrink-0">
                      <div className={`w-7 h-7 rounded-full flex items-center justify-center text-[11px] font-bold border-2 ${
                        isDone ? 'bg-[#E7F6EC] border-[#1E7B4D] text-[#1E7B4D]' :
                        isRunning ? 'bg-[#E2ECF5] border-[#14548C] text-[#14548C]' :
                        'bg-[#F1F4F8] border-[#DCE3EA] text-[#9AA4B3]'
                      }`}>
                        {isDone ? <CheckCircle2 className="w-4 h-4" /> :
                         isRunning ? <Loader2 className="w-4 h-4 animate-spin" /> :
                         i + 1}
                      </div>
                      {i < steps.length - 1 && (
                        <div className={`w-0.5 h-3 rounded ${isDone ? 'bg-[#A3CFBB]' : 'bg-[#E3E8EF]'}`} />
                      )}
                    </div>

                    {/* Step content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start gap-2 flex-wrap">
                        <span className="text-[9px] font-bold px-1.5 py-0.5 rounded-full flex-shrink-0" style={{ backgroundColor: step.deptBg, color: step.deptColor }}>
                          {step.dept}
                        </span>
                        <span className="text-xs font-bold text-[#16212E]">{step.label}</span>
                      </div>
                      {(isDone || isRunning) && (
                        <p className="text-[11px] text-[#4A5B6E] mt-1 leading-relaxed">{step.detail}</p>
                      )}
                      {isDone && step.artifact && (
                        <div className="mt-1.5 inline-flex items-center gap-1.5 text-[10px] font-bold px-2 py-1 rounded-md" style={{ backgroundColor: wfMeta.bg, color: wfMeta.color }}>
                          <Hash className="w-3 h-3" />
                          {step.artifact.label}: {step.artifact.value}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}

              {/* Artifacts summary */}
              {done && artifacts.length > 0 && (
                <div className="bg-white rounded-md border border-[#DCE3EA] p-3 space-y-2">
                  <div className="text-[10px] font-bold text-[#4A5B6E] uppercase tracking-wider">Generated Artifacts</div>
                  {artifacts.map((a, i) => (
                    <div key={i} className="flex items-center gap-2 text-xs">
                      <Hash className="w-3 h-3 flex-shrink-0" style={{ color: wfMeta.color }} />
                      <span className="text-[#4A5B6E] font-semibold">{a.label}:</span>
                      <span className="font-mono font-bold" style={{ color: wfMeta.color }}>{a.value}</span>
                    </div>
                  ))}
                  <div className="pt-2 border-t border-[#F1F4F8] flex items-center gap-1.5 text-[10px] text-[#4A5B6E]">
                    <Database className="w-3 h-3" />
                    Cross-system sync verified · Audit hash-chain sealed · All events CACHED with provenance
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Bottom: Event log */}
        <div className="h-[160px] border-t border-[#DCE3EA] bg-[#0B2447] flex flex-col flex-shrink-0">
          <div className="px-3 py-1.5 border-b border-white/10 flex items-center gap-2">
            <div className="w-1.5 h-1.5 rounded-full bg-[#14a89a] animate-pulse" />
            <span className="text-[10px] font-bold text-[#7fe9db] uppercase tracking-wider">Live Cross-System Event Log</span>
          </div>
          <div ref={logRef} className="flex-1 overflow-y-auto px-3 py-2 space-y-1 font-mono text-[10.5px]">
            {eventLog.length === 0 ? (
              <div className="text-[#4a6a8c]">Waiting for workflow execution…</div>
            ) : (
              eventLog.map((ev, i) => (
                <div key={i} className="flex items-start gap-2">
                  <span className="text-[#4a6a8c] flex-shrink-0">{ev.ts}</span>
                  <span className="font-bold flex-shrink-0 px-1.5 rounded-[3px]" style={{ backgroundColor: ev.deptColor + '33', color: ev.deptColor === '#4A5B6E' ? '#aac4e8' : ev.deptColor }}>
                    [{ev.dept}]
                  </span>
                  <span className="text-[#c7d8f0]">{ev.msg}</span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
