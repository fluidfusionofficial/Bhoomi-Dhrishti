'use client';

import React, { useState, useMemo, useRef } from 'react';
import {
  CadastralMap,
  PARCEL_DATA,
  type ParcelData,
  type LayerState,
} from './CadastralMap';
import {
  AlertTriangle,
  CheckCircle2,
  AlertOctagon,
  Clock,
  Layers,
  Search,
  Filter,
  Shield,
  FileCheck2,
  FileSpreadsheet,
  Building2,
  MapPin,
  Sparkles,
  ChevronRight,
  ArrowRight,
  RefreshCw,
  SlidersHorizontal,
  Landmark,
  Scale,
  Send,
  Eye,
  Check,
  UserCheck,
  AlertCircle,
  FileText,
  Compass,
} from 'lucide-react';
import { useRole } from '@/context/RoleContext';
import { useFreshness } from '@/context/FreshnessContext';

// ── 4-Pillar Detailed Record Schema ──────────────────────────────────────────
export interface FourPillarsRecord {
  parcelId: string;
  ulpin: string;
  surveyNumber: string;
  primaryOwner: string;
  trustScore: number;
  riskBand: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  discrepancyType: 'IDENTITY' | 'TOPOLOGY' | 'AREA' | 'PLANNING' | 'ENCUMBRANCE' | 'NONE';
  title: string;
  summary: string;

  // Pillar 1: Cadastre (Survey & Settlement Dept)
  cadastre: {
    system: string;
    surveyNumber: string;
    calculatedAreaAcres: number;
    calculatedAreaSqM: number;
    fmbStatus: string;
    boundaryConflictDetails?: string;
    overlapSqM?: number;
    status: 'OK' | 'DISCREPANCY';
  };

  // Pillar 2: Registration (SRO / NGDRS)
  registration: {
    system: string;
    deedNumber: string;
    deedType: string;
    registeredOwner: string;
    deedAreaAcres: number;
    encumbranceStatus: string;
    mortgageDetails?: string;
    status: 'OK' | 'DISCREPANCY';
  };

  // Pillar 3: Revenue (Tamil Nilam / RoR)
  revenue: {
    system: string;
    pattaNumber: string;
    pattadarName: string;
    recordedAreaAcres: number;
    landClassification: string;
    taxStatus: string;
    status: 'OK' | 'DISCREPANCY';
  };

  // Pillar 4: Planning & ULB (Town Planning / Municipality)
  planning: {
    system: string;
    masterPlanZone: string;
    permittedUse: string;
    actualUse: string;
    buildingPermitNumber?: string;
    propertyTaxId?: string;
    status: 'OK' | 'DISCREPANCY';
  };

  // Discrepancy Diff items
  diffs: {
    field: string;
    deptA: { name: string; value: string };
    deptB: { name: string; value: string };
    severity: 'CRITICAL' | 'HIGH' | 'MEDIUM';
    note: string;
  }[];

  // Statutory resolution actions available
  availableActions: {
    id: string;
    label: string;
    officerRole: string;
    description: string;
    statutoryRef: string;
  }[];
}

// ── Master Discrepancy Data Store ────────────────────────────────────────────
export const FOUR_PILLARS_DATA: FourPillarsRecord[] = [
  {
    parcelId: 'P003',
    ulpin: 'TN-CHN-000003',
    surveyNumber: '42/3B',
    primaryOwner: 'Arun Kumar / Rajasekharan',
    trustScore: 38,
    riskBand: 'CRITICAL',
    discrepancyType: 'IDENTITY',
    title: 'Owner Identity Mismatch & 42 m² Cadastral Boundary Overlap',
    summary: 'Phonetic name discrepancy between RoR & SRO Deed, combined with 14.5% area discrepancy and physical boundary overlap with Parcel P008.',
    cadastre: {
      system: 'Survey & Settlement (FMB)',
      surveyNumber: '42/3B',
      calculatedAreaAcres: 2.40,
      calculatedAreaSqM: 9712,
      fmbStatus: 'FMB Triangulation Overlap Detected',
      boundaryConflictDetails: 'Overlaps Survey 45/2A (P008) along southern bund by 42.18 m²',
      overlapSqM: 42.18,
      status: 'DISCREPANCY',
    },
    registration: {
      system: 'NGDRS / SRO Tirupporur',
      deedNumber: 'Deed-2019-1042',
      deedType: 'SALE_DEED',
      registeredOwner: 'Rajasekharan Kandasamy',
      deedAreaAcres: 2.75,
      encumbranceStatus: 'Clear EC (Issued 2024)',
      status: 'DISCREPANCY',
    },
    revenue: {
      system: 'Tamil Nilam (Revenue Dept)',
      pattaNumber: 'Patta #4210',
      pattadarName: 'K. Rajasekaran',
      recordedAreaAcres: 2.40,
      landClassification: 'Ryotwari Nanjai (Wet)',
      taxStatus: 'FY 2024-25 Paid (₹1,420)',
      status: 'DISCREPANCY',
    },
    planning: {
      system: 'Tirupporur Master Plan 2041',
      masterPlanZone: 'Agricultural Conservation (A-1)',
      permittedUse: 'Crops / Allied Agriculture',
      actualUse: 'Residential Construction (Unapproved)',
      status: 'DISCREPANCY',
    },
    diffs: [
      {
        field: 'Party Identity',
        deptA: { name: 'Revenue (Tamil Nilam)', value: 'K. Rajasekaran' },
        deptB: { name: 'Registration (SRO Deed)', value: 'Rajasekharan Kandasamy' },
        severity: 'HIGH',
        note: 'Jaro-Winkler phonetic similarity: 88%. Levenshtein distance: 3. Aadhaar hash match verified.',
      },
      {
        field: 'Registered Area',
        deptA: { name: 'Revenue & Cadastre', value: '2.40 acres (9,712 m²)' },
        deptB: { name: 'SRO Sale Deed', value: '2.75 acres (11,128 m²)' },
        severity: 'CRITICAL',
        note: 'Deed area is +14.5% higher than ground cadastral geometry (+0.35 acres). Potential fictitious area sale.',
      },
      {
        field: 'Spatial Boundary',
        deptA: { name: 'Cadastre Survey 42/3B', value: 'Calculated Polygon' },
        deptB: { name: 'Cadastre Survey 45/2A (P008)', value: 'Adjacent Polygon' },
        severity: 'CRITICAL',
        note: '42.18 m² physical overlap zone detected in official digital cadastral vector.',
      },
      {
        field: 'Land Use Compliance',
        deptA: { name: 'Revenue & Planning', value: 'Agricultural A-1' },
        deptB: { name: 'Ground Survey & Satellite', value: 'Residential Layout' },
        severity: 'HIGH',
        note: 'Structure constructed without Town & Country Planning Directorate NOC.',
      },
    ],
    availableActions: [
      {
        id: 'ACTION_ALIAS_MUTATION',
        label: 'Sanction Mutation with Certified Alias',
        officerRole: 'Tehsildar',
        description: 'Record "K. Rajasekaran @ Rajasekharan Kandasamy" as official composite pattadar in Tamil Nilam with Aadhaar hash link.',
        statutoryRef: 'TN Land Revenue Act Sec. 31',
      },
      {
        id: 'ACTION_SNAP_CADASTRE',
        label: 'Order Boundary Realignment (Snap to Survey Stone)',
        officerRole: 'Surveyor / Tehsildar',
        description: 'Trim overlapping 42.18 m² polygon to adhere to 1968 baseline survey triangulation.',
        statutoryRef: 'Tamil Nadu Survey and Boundaries Act 1923 Sec. 10',
      },
      {
        id: 'ACTION_SRO_AREA_RECT',
        label: 'Issue Statutory Notice for Deed Area Rectification',
        officerRole: 'Sub-Registrar',
        description: 'Serve 15-day notice to deed parties to execute supplementary rectification deed reducing area from 2.75 to 2.40 acres.',
        statutoryRef: 'Registration Act 1908 Sec. 34A',
      },
      {
        id: 'ACTION_DISPATCH_DGPS',
        label: 'Dispatch Field Surveyor Rover (DGPS)',
        officerRole: 'Surveyor',
        description: 'Schedule automated field task for joint peg-marking and differential GPS measurement.',
        statutoryRef: 'DILRMP Technical Guidelines 2024',
      },
      {
        id: 'ACTION_REFER_SDM',
        label: 'Refer to Sub-Divisional Magistrate (SDM) Court',
        officerRole: 'Collector / SDM',
        description: 'Impose provisional status freeze and open summary inquiry into overlapping possession claims.',
        statutoryRef: 'CrPC Sec. 145 / Land Revenue Code',
      },
    ],
  },

  {
    parcelId: 'P006',
    ulpin: 'TN-CHN-000006',
    surveyNumber: '43/2A',
    primaryOwner: 'Karthik Selvam',
    trustScore: 42,
    riskBand: 'CRITICAL',
    discrepancyType: 'PLANNING',
    title: 'Unauthorized Commercial Conversion in Agricultural Green Belt',
    summary: 'Sentinel-2 satellite change detection identified active warehouse construction (+0.48 NDBI). Property tax assessed by ULB despite zero Planning NOC.',
    cadastre: {
      system: 'Survey & Settlement (FMB)',
      surveyNumber: '43/2A',
      calculatedAreaAcres: 2.75,
      calculatedAreaSqM: 11128,
      fmbStatus: 'Clear Cadastral Boundary',
      status: 'OK',
    },
    registration: {
      system: 'NGDRS / SRO Tirupporur',
      deedNumber: 'Deed-2023-0482',
      deedType: 'SALE_DEED',
      registeredOwner: 'Karthik Selvam',
      deedAreaAcres: 2.75,
      encumbranceStatus: 'Clear',
      status: 'OK',
    },
    revenue: {
      system: 'Tamil Nilam (Revenue Dept)',
      pattaNumber: 'Patta #4312',
      pattadarName: 'Karthik Selvam',
      recordedAreaAcres: 2.75,
      landClassification: 'Agricultural Nanjai (Wet)',
      taxStatus: 'Tax Paid',
      status: 'DISCREPANCY',
    },
    planning: {
      system: 'Tirupporur Master Plan 2041 / Town Planning',
      masterPlanZone: 'Agricultural Green Buffer Zone',
      permittedUse: 'Strict Agricultural / Afforestation',
      actualUse: 'Commercial Logistics Godown (Active)',
      propertyTaxId: 'ULB-TP-2024-8841',
      status: 'DISCREPANCY',
    },
    diffs: [
      {
        field: 'Land Use Classification',
        deptA: { name: 'Revenue (Tamil Nilam)', value: 'Agricultural Nanjai' },
        deptB: { name: 'Municipal Tax Roll', value: 'Commercial Warehouse (PID: 8841)' },
        severity: 'CRITICAL',
        note: 'ULB collects commercial tax, but Revenue RoR has no conversion order under Section 47A.',
      },
      {
        field: 'Master Plan Compliance',
        deptA: { name: 'Master Plan 2041', value: 'Green Buffer Zone' },
        deptB: { name: 'Satellite Imagery', value: 'NDBI +0.48 (Built-up Area 4,200 m²)' },
        severity: 'CRITICAL',
        note: 'Built structure violates mandatory 50-metre lake catchment buffer restriction.',
      },
    ],
    availableActions: [
      {
        id: 'ACTION_HOLD_MUNICIPAL_TAX',
        label: 'Hold Municipal Commercial Tax Assessment',
        officerRole: 'Town Planner',
        description: 'Suspend commercial tax status until valid Land Use Conversion Order is submitted.',
        statutoryRef: 'Tamil Nadu District Municipalities Act 1920',
      },
      {
        id: 'ACTION_NOTICE_CONVERSION',
        label: 'Issue Show-Cause Notice for Illegal Conversion',
        officerRole: 'Tehsildar',
        description: 'Initiate revenue proceedings under Tamil Nadu Land Conversion Rules for unapproved diversion.',
        statutoryRef: 'Tamil Nadu Change of Land Use Rules 2017',
      },
      {
        id: 'ACTION_ORDER_INSPECTION',
        label: 'Order Joint Revenue-Planning Site Inspection',
        officerRole: 'District Collector',
        description: 'Depute squad comprising Deputy Tahsildar and Town Planning Officer for physical verification.',
        statutoryRef: 'Disaster & Town Planning Enforcement Protocol',
      },
    ],
  },

  {
    parcelId: 'P004',
    ulpin: 'TN-CHN-000004',
    surveyNumber: '42/4A',
    primaryOwner: 'Suresh Babu',
    trustScore: 52,
    riskBand: 'MEDIUM',
    discrepancyType: 'ENCUMBRANCE',
    title: 'Unrecorded Commercial Bank Mortgage Lien (₹45,00,000)',
    summary: 'Active mortgage deed registered at SRO with State Bank of India. Revenue Patta Passbook (Column 12) omits mortgage remark, creating high double-pledge risk.',
    cadastre: {
      system: 'Survey & Settlement (FMB)',
      surveyNumber: '42/4A',
      calculatedAreaAcres: 4.20,
      calculatedAreaSqM: 16997,
      fmbStatus: 'Clear',
      status: 'OK',
    },
    registration: {
      system: 'NGDRS / SRO Tirupporur',
      deedNumber: 'Mortgage Deed #0891/2021',
      deedType: 'SIMPLE_MORTGAGE',
      registeredOwner: 'Suresh Babu',
      deedAreaAcres: 4.20,
      encumbranceStatus: 'ENCUMBERED — State Bank of India (₹45,00,000)',
      mortgageDetails: 'Registered 24-Aug-2021 · Loan A/c: 382910481 · Mortgagee: SBI Chengalpattu Branch',
      status: 'DISCREPANCY',
    },
    revenue: {
      system: 'Tamil Nilam (Revenue Dept)',
      pattaNumber: 'Patta #4218',
      pattadarName: 'Suresh Babu',
      recordedAreaAcres: 4.20,
      landClassification: 'Dry (Punjai)',
      taxStatus: 'Current',
      status: 'DISCREPANCY',
    },
    planning: {
      system: 'Tirupporur Master Plan 2041',
      masterPlanZone: 'Agricultural Primary',
      permittedUse: 'Agriculture',
      actualUse: 'Cultivated Farm',
      status: 'OK',
    },
    diffs: [
      {
        field: 'Encumbrance / Lien Sync',
        deptA: { name: 'Registration (SRO Deed Register)', value: 'Active SBI Mortgage (₹45L)' },
        deptB: { name: 'Revenue (Patta Passbook Col 12)', value: 'Blank / Clean Title' },
        severity: 'HIGH',
        note: 'SRO registered mortgage 3 years ago but automated XML push to Tamil Nilam failed. Risk of seller mortgaging to cooperative bank.',
      },
    ],
    availableActions: [
      {
        id: 'ACTION_TRANSMIT_LIEN',
        label: 'Synchronize SRO Mortgage Lien into Revenue RoR',
        officerRole: 'Sub-Registrar / Tehsildar',
        description: 'Auto-populate Col 12 of Patta Passbook with SBI charge and block alienation without Bank NOC.',
        statutoryRef: 'Tamil Nadu Patta Pass Book Act 1983 Sec. 10(2)',
      },
      {
        id: 'ACTION_FREEZE_MUTATION',
        label: 'Impose Provisional Transfer Lock',
        officerRole: 'Tehsildar',
        description: 'Flag parcel with automated lock preventing mutation until SBI discharge deed is registered.',
        statutoryRef: 'Registration Rules Rule 55A',
      },
    ],
  },

  {
    parcelId: 'P009',
    ulpin: 'TN-CHN-000009',
    surveyNumber: '45/3B',
    primaryOwner: 'Ganesh Moorthy',
    trustScore: 61,
    riskBand: 'MEDIUM',
    discrepancyType: 'AREA',
    title: 'Cadastral Vector Area Discrepancy (-7.1% vs Revenue RoR)',
    summary: 'GIS geometry polygon measures 1.95 acres while Revenue RoR and Deed state 2.10 acres. 2.1 m² sliver along southern cart track bund.',
    cadastre: {
      system: 'Survey & Settlement (FMB)',
      surveyNumber: '45/3B',
      calculatedAreaAcres: 1.95,
      calculatedAreaSqM: 7891,
      fmbStatus: 'Sliver conflict on southern boundary',
      boundaryConflictDetails: 'Sliver of 2.1 m² with cart-track right-of-way',
      status: 'DISCREPANCY',
    },
    registration: {
      system: 'NGDRS / SRO Tirupporur',
      deedNumber: 'Deed-2022-1102',
      deedType: 'SALE_DEED',
      registeredOwner: 'Ganesh Moorthy',
      deedAreaAcres: 2.10,
      encumbranceStatus: 'Clear',
      status: 'OK',
    },
    revenue: {
      system: 'Tamil Nilam (Revenue Dept)',
      pattaNumber: 'Patta #4503',
      pattadarName: 'Ganesh Moorthy',
      recordedAreaAcres: 2.10,
      landClassification: 'Residential',
      taxStatus: 'Paid',
      status: 'DISCREPANCY',
    },
    planning: {
      system: 'Tirupporur Master Plan 2041',
      masterPlanZone: 'Residential Mixed',
      permittedUse: 'Residential',
      actualUse: 'Residential House',
      status: 'OK',
    },
    diffs: [
      {
        field: 'Physical vs Legal Area',
        deptA: { name: 'Cadastral GIS Vector', value: '1.95 acres (7,891 m²)' },
        deptB: { name: 'Revenue RoR & SRO Deed', value: '2.10 acres (8,498 m²)' },
        severity: 'MEDIUM',
        note: 'Deficit of 0.15 acres (-7.1%). Potential road widening encroachment into cart-track RoW.',
      },
    ],
    availableActions: [
      {
        id: 'ACTION_ORDER_DEMARCATION',
        label: 'Order Field Demarcation & Boundary Settlement',
        officerRole: 'Surveyor',
        description: 'Dispatch survey team to re-verify boundary stones against village FMB baseline.',
        statutoryRef: 'Tamil Nadu Survey and Boundaries Act Sec. 9',
      },
      {
        id: 'ACTION_RECTIFY_ROR_AREA',
        label: 'Update RoR Area to Verified Cadastral Ground Truth',
        officerRole: 'Tehsildar',
        description: 'Adjust patta record to 1.95 acres following surveyor certification.',
        statutoryRef: 'Tamil Nadu Revenue Standing Order 31',
      },
    ],
  },

  {
    parcelId: 'P012',
    ulpin: 'TN-CHN-000012',
    surveyNumber: '47/1B',
    primaryOwner: 'Nithya Sundaram',
    trustScore: 31,
    riskBand: 'CRITICAL',
    discrepancyType: 'TOPOLOGY',
    title: 'Rapid-Flip Transaction Chain (3 Sales in 14 Months) & Water Body Encroachment',
    summary: 'Trust engine flagged circular ownership network. Northern 31.6 m² boundary encroaches into Village Common Eri (Water Body Poramboke).',
    cadastre: {
      system: 'Survey & Settlement (FMB)',
      surveyNumber: '47/1B',
      calculatedAreaAcres: 0.80,
      calculatedAreaSqM: 3237,
      fmbStatus: 'Critical Water Body Overlap',
      boundaryConflictDetails: 'Encroachment of 31.6 m² into Survey 48/2B (Eri Poramboke / Public Lake)',
      overlapSqM: 31.6,
      status: 'DISCREPANCY',
    },
    registration: {
      system: 'NGDRS / SRO Tirupporur',
      deedNumber: 'Deed-2024-0319',
      deedType: 'SALE_DEED',
      registeredOwner: 'Nithya Sundaram',
      deedAreaAcres: 0.80,
      encumbranceStatus: 'Suspicious Velocity Flagged',
      status: 'DISCREPANCY',
    },
    revenue: {
      system: 'Tamil Nilam (Revenue Dept)',
      pattaNumber: 'Patta #4711 (Pending)',
      pattadarName: 'S. Ramanathan (Previous Owner)',
      recordedAreaAcres: 0.80,
      landClassification: 'Commercial / Industrial',
      taxStatus: 'Arrears (₹18,400)',
      status: 'DISCREPANCY',
    },
    planning: {
      system: 'Tirupporur Master Plan 2041',
      masterPlanZone: 'Ecological Water Buffer Zone',
      permittedUse: 'Strict Zero Development',
      actualUse: 'Small Scale Workshop',
      status: 'DISCREPANCY',
    },
    diffs: [
      {
        field: 'Public Land Encroachment',
        deptA: { name: 'Cadastre Survey 47/1B', value: 'Private Claim' },
        deptB: { name: 'Survey 48/2B (Eri Poramboke)', value: 'Protected Water Body' },
        severity: 'CRITICAL',
        note: '31.6 m² overlaps Supreme Court protected water body buffer. Section 131 action required.',
      },
      {
        field: 'Transaction Velocity Anomaly',
        deptA: { name: 'Trust Engine Graph', value: '3 Transfers / 14 Months' },
        deptB: { name: 'District Median', value: '1 Transfer / 8.5 Years' },
        severity: 'HIGH',
        note: 'Consideration surged from ₹12L to ₹48L in 14 months without development.',
      },
    ],
    availableActions: [
      {
        id: 'ACTION_WATER_BODY_EVICTION',
        label: 'Issue Encroachment Removal Notice (Water Body)',
        officerRole: 'Tehsildar / District Collector',
        description: 'Initiate eviction under Tamil Nadu Protection of Tanks and Eviction of Encroachment Act 2007.',
        statutoryRef: 'TN Tanks Protection Act 2007 Sec. 7',
      },
      {
        id: 'ACTION_FREEZE_TRANSFER_BENAMI',
        label: 'Freeze Registry Transfer for Benami Scrutiny',
        officerRole: 'Sub-Registrar',
        description: 'Refuse deed registration pending inquiry into beneficial ownership chain.',
        statutoryRef: 'Prohibition of Benami Property Transactions Act 1988',
      },
    ],
  },

  {
    parcelId: 'P001',
    ulpin: 'TN-CHN-000001',
    surveyNumber: '41/1A',
    primaryOwner: 'Lakshmi Narayanan',
    trustScore: 94,
    riskBand: 'LOW',
    discrepancyType: 'NONE',
    title: 'Verified Parcel — Full 4-Pillar Cross-System Harmony',
    summary: 'Full consensus across Cadastral FMB, SRO Sale Deed, Tamil Nilam RoR, and Master Plan 2041. Zero disputes, taxes current.',
    cadastre: {
      system: 'Survey & Settlement (FMB)',
      surveyNumber: '41/1A',
      calculatedAreaAcres: 3.10,
      calculatedAreaSqM: 12545,
      fmbStatus: 'Settled & Georeferenced (Class A)',
      status: 'OK',
    },
    registration: {
      system: 'NGDRS / SRO Tirupporur',
      deedNumber: 'Deed-2019-1042',
      deedType: 'SALE_DEED',
      registeredOwner: 'Lakshmi Narayanan',
      deedAreaAcres: 3.10,
      encumbranceStatus: 'Clear Nil Encumbrance Certificate',
      status: 'OK',
    },
    revenue: {
      system: 'Tamil Nilam (Revenue Dept)',
      pattaNumber: 'Patta #4101',
      pattadarName: 'Lakshmi Narayanan',
      recordedAreaAcres: 3.10,
      landClassification: 'Wet Agriculture (Nanjai)',
      taxStatus: 'Paid (FY 2024-25)',
      status: 'OK',
    },
    planning: {
      system: 'Tirupporur Master Plan 2041',
      masterPlanZone: 'Agricultural Primary (A-1)',
      permittedUse: 'Agriculture',
      actualUse: 'Paddy Cultivation',
      status: 'OK',
    },
    diffs: [],
    availableActions: [
      {
        id: 'ACTION_DOWNLOAD_PASSPORT',
        label: 'Generate Unified Digital Land Certificate (Bhu-Aadhaar)',
        officerRole: 'All Roles',
        description: 'Issue tamper-evident QR verified land passbook with 4-way provenance stamps.',
        statutoryRef: 'DILRMP Bhu-Aadhaar Framework 2024',
      },
    ],
  },
];

export interface ReconciliationCockpitProps {
  onNavigateTab?: (tab: any) => void;
}

export function ReconciliationCockpit({ onNavigateTab }: ReconciliationCockpitProps) {
  const { role, config } = useRole();
  const freshness = useFreshness();

  // State
  const [selectedParcelId, setSelectedParcelId] = useState<string>('P003');
  const [filterSeverity, setFilterSeverity] = useState<'ALL' | 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'>('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [officerRemarks, setOfficerRemarks] = useState('');
  const [actionSuccessMsg, setActionSuccessMsg] = useState<string | null>(null);
  const [actionInProgress, setActionInProgress] = useState(false);

  // Map state
  const mapInstanceRef = useRef<any>(null);
  const [mapLayers, setMapLayers] = useState<LayerState>({
    parcels: true,
    ulpin: true,
    villageBoundary: false,
    roads: false,
    railway: false,
    governmentLand: false,
    ownership: true,
    landUse: true,
    zoning: true,
    registration: true,
    encumbrance: true,
    litigation: true,
    topologyConflicts: true,
    propertyTax: false,
    utilityLines: false,
    infrastructureRoW: false,
    envBuffers: true,
  });

  const activeRecord = useMemo(() => {
    return FOUR_PILLARS_DATA.find((p) => p.parcelId === selectedParcelId) || FOUR_PILLARS_DATA[0];
  }, [selectedParcelId]);

  const filteredQueue = useMemo(() => {
    return FOUR_PILLARS_DATA.filter((p) => {
      if (filterSeverity !== 'ALL' && p.riskBand !== filterSeverity) return false;
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        return (
          p.parcelId.toLowerCase().includes(q) ||
          p.ulpin.toLowerCase().includes(q) ||
          p.surveyNumber.toLowerCase().includes(q) ||
          p.primaryOwner.toLowerCase().includes(q) ||
          p.title.toLowerCase().includes(q)
        );
      }
      return true;
    });
  }, [filterSeverity, searchQuery]);

  const handleSelectParcel = (parcelId: string) => {
    setSelectedParcelId(parcelId);
    setActionSuccessMsg(null);
    setOfficerRemarks('');

    // Smooth pan/zoom to parcel in MapLibre
    const map = mapInstanceRef.current;
    if (map) {
      // Find parcel centroid coordinate from PARCEL_DATA
      const target = PARCEL_DATA.find((p) => p.parcel_id === parcelId);
      if (target) {
        // Center of Tirupporur parcels cluster
        map.flyTo({
          center: [80.1873, 12.7290],
          zoom: 15,
          duration: 1500,
          essential: true,
        });
      }
    }
  };

  const handleExecuteAction = (actionLabel: string, statutoryRef: string) => {
    if (!officerRemarks.trim()) {
      alert('Statutory Compliance Rule: Officer adjudication remarks are mandatory before executing resolution.');
      return;
    }
    setActionInProgress(true);
    setTimeout(() => {
      setActionInProgress(false);
      setActionSuccessMsg(`✓ Successfully executed: "${actionLabel}" under ${statutoryRef}. BNDR Audit Hash: 0x9f4a...e281.`);
    }, 800);
  };

  return (
    <div className="flex-1 flex flex-col min-h-0 bg-[#0B1528] text-[#E2ECF5] overflow-hidden">

      {/* ── SUB-HEADER: Triage Banner & 4-Pillars Mission Strip ──────────────── */}
      <div className="bg-[#0e1d38] border-b border-[#1A3158] px-4 py-2 flex flex-wrap items-center justify-between gap-3 flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-md bg-gradient-to-br from-[#14a89a] to-[#0f766e] flex items-center justify-center text-white shadow-sm">
            <Compass className="w-4.5 h-4.5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-white">
                4-Pillar Reconciliation Cockpit
              </span>
              <span className="text-[10px] font-bold px-1.5 py-0.2 rounded bg-[#dc2626]/20 text-[#f87171] border border-[#dc2626]/40">
                ACTIVE TRIAGE
              </span>
              <span className="text-[10px] font-mono text-[#7EA3CC]">
                PS-26014 Inter-Silo Truth Engine
              </span>
            </div>
            <p className="text-[11px] text-[#8EAECF] mt-0.5">
              Reconciling <strong className="text-white">Cadastre</strong>, <strong className="text-white">SRO Deeds</strong>, <strong className="text-white">Revenue RoR</strong>, and <strong className="text-white">Town Planning</strong> in real time.
            </p>
          </div>
        </div>

        {/* 4 Pillars Status Indicators */}
        <div className="hidden lg:flex items-center gap-2 bg-[#091326] px-3 py-1.5 rounded-lg border border-[#1b345c]">
          <span className="text-[10px] text-[#7EA3CC] uppercase font-bold tracking-wider mr-1">
            Pillars Checked:
          </span>
          <div className="flex items-center gap-1.5 text-[10px] font-semibold">
            <span className="w-2 h-2 rounded-full bg-[#10b981]" />
            <span className="text-[#a7f3d0]">1. Cadastre</span>
          </div>
          <span className="text-[#3b5980]">|</span>
          <div className="flex items-center gap-1.5 text-[10px] font-semibold">
            <span className="w-2 h-2 rounded-full bg-[#38bdf8]" />
            <span className="text-[#bae6fd]">2. SRO Deed</span>
          </div>
          <span className="text-[#3b5980]">|</span>
          <div className="flex items-center gap-1.5 text-[10px] font-semibold">
            <span className="w-2 h-2 rounded-full bg-[#f59e0b]" />
            <span className="text-[#fde68a]">3. RoR Patta</span>
          </div>
          <span className="text-[#3b5980]">|</span>
          <div className="flex items-center gap-1.5 text-[10px] font-semibold">
            <span className="w-2 h-2 rounded-full bg-[#a855f7]" />
            <span className="text-[#e9d5ff]">4. Master Plan</span>
          </div>
        </div>

        <div className="flex items-center gap-3 text-xs">
          <div className="text-[11px] text-[#8EAECF]">
            Role: <span className="font-bold text-white uppercase">{config.title}</span>
          </div>
          <div className="h-3.5 w-[1px] bg-[#1A3158]" />
          <div className="text-[11px] text-[#8EAECF]">
            Jurisdiction: <span className="font-semibold text-emerald-400">Chengalpattu (Tirupporur)</span>
          </div>
        </div>
      </div>

      {/* ── 3-PANE WORKSPACE ─────────────────────────────────────────────────── */}
      <div className="flex-1 flex min-h-0 overflow-hidden">

        {/* ═════════════════════════════════════════════════════════════════════
            PANE 1: CONTESTED DISCREPANCY QUEUE (25% Width)
            ═════════════════════════════════════════════════════════════════════ */}
        <aside className="w-[340px] flex-shrink-0 flex flex-col border-r border-[#162B4D] bg-[#0c182e] overflow-hidden">
          {/* Queue Filter Bar */}
          <div className="p-3 border-b border-[#162B4D] space-y-2.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-white flex items-center gap-1.5">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                Discrepancy Queue ({filteredQueue.length})
              </span>
              <span className="text-[10px] text-[#7EA3CC] font-mono">
                Ranked by Risk
              </span>
            </div>

            {/* Quick search input */}
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-[#5D80A6]" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search ULPIN, survey, owner..."
                className="w-full bg-[#071020] text-xs text-white pl-8 pr-3 py-1.5 rounded border border-[#1d375e] placeholder-[#5D80A6] focus:outline-none focus:border-[#14a89a]"
              />
            </div>

            {/* Severity Pill Filter */}
            <div className="flex items-center gap-1 overflow-x-auto pb-0.5">
              {(['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'] as const).map((sev) => (
                <button
                  key={sev}
                  type="button"
                  onClick={() => setFilterSeverity(sev)}
                  className={`text-[10px] font-bold px-2 py-1 rounded transition-colors whitespace-nowrap ${
                    filterSeverity === sev
                      ? 'bg-[#14548C] text-white'
                      : 'bg-[#081224] text-[#7EA3CC] hover:text-white hover:bg-[#122646]'
                  }`}
                >
                  {sev}
                </button>
              ))}
            </div>
          </div>

          {/* Queue Items List */}
          <div className="flex-1 overflow-y-auto divide-y divide-[#142644]">
            {filteredQueue.map((item) => {
              const isSelected = item.parcelId === selectedParcelId;
              const isCrit = item.riskBand === 'CRITICAL';
              const isHigh = item.riskBand === 'HIGH';
              const isMed = item.riskBand === 'MEDIUM';

              return (
                <div
                  key={item.parcelId}
                  onClick={() => handleSelectParcel(item.parcelId)}
                  className={`p-3.5 cursor-pointer transition-all ${
                    isSelected
                      ? 'bg-[#122a50] border-l-4 border-[#14a89a]'
                      : 'hover:bg-[#0f203d] border-l-4 border-transparent'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <div className="flex items-center gap-1.5">
                        <span className="text-xs font-bold text-white tracking-tight">
                          {item.ulpin}
                        </span>
                        <span className="text-[10px] font-mono text-[#8EAECF]">
                          ({item.surveyNumber})
                        </span>
                      </div>
                      <div className="text-[11px] text-[#A6C5E8] mt-0.5 truncate max-w-[200px]">
                        {item.primaryOwner}
                      </div>
                    </div>

                    {/* Trust Score Pill */}
                    <div
                      className={`text-right px-2 py-0.5 rounded text-[11px] font-bold font-mono ${
                        isCrit
                          ? 'bg-red-950/80 text-red-400 border border-red-700/50'
                          : isHigh
                          ? 'bg-amber-950/80 text-amber-400 border border-amber-700/50'
                          : isMed
                          ? 'bg-yellow-950/80 text-yellow-400 border border-yellow-700/50'
                          : 'bg-emerald-950/80 text-emerald-400 border border-emerald-700/50'
                      }`}
                    >
                      {item.trustScore}/100
                    </div>
                  </div>

                  <div className="text-xs font-semibold text-white/90 mt-1.5 leading-snug line-clamp-2">
                    {item.title}
                  </div>

                  {/* 4 Pillars Mini-Pill Consensus Indicator */}
                  <div className="flex items-center justify-between mt-2 pt-2 border-t border-[#182d4f] text-[10px]">
                    <div className="flex items-center gap-1">
                      <span
                        title="Cadastre"
                        className={`px-1 py-0.2 rounded font-bold ${
                          item.cadastre.status === 'DISCREPANCY' ? 'bg-red-900/60 text-red-300' : 'bg-emerald-900/60 text-emerald-300'
                        }`}
                      >
                        CAD
                      </span>
                      <span
                        title="SRO Deed"
                        className={`px-1 py-0.2 rounded font-bold ${
                          item.registration.status === 'DISCREPANCY' ? 'bg-red-900/60 text-red-300' : 'bg-emerald-900/60 text-emerald-300'
                        }`}
                      >
                        SRO
                      </span>
                      <span
                        title="Revenue RoR"
                        className={`px-1 py-0.2 rounded font-bold ${
                          item.revenue.status === 'DISCREPANCY' ? 'bg-red-900/60 text-red-300' : 'bg-emerald-900/60 text-emerald-300'
                        }`}
                      >
                        ROR
                      </span>
                      <span
                        title="Town Planning / ULB"
                        className={`px-1 py-0.2 rounded font-bold ${
                          item.planning.status === 'DISCREPANCY' ? 'bg-red-900/60 text-red-300' : 'bg-emerald-900/60 text-emerald-300'
                        }`}
                      >
                        PLN
                      </span>
                    </div>

                    <span className="text-[10px] font-bold text-[#8EAECF] uppercase">
                      {item.discrepancyType}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </aside>

        {/* ═════════════════════════════════════════════════════════════════════
            PANE 2: GROUND-TRUTH GIS MAPLIBRE CANVAS (Center 42%)
            ═════════════════════════════════════════════════════════════════════ */}
        <section className="flex-1 relative bg-[#060c18] flex flex-col min-w-0 overflow-hidden">
          {/* Map floating header banner */}
          <div className="absolute top-3 left-3 z-30 bg-[#09152b]/90 backdrop-blur-md px-3.5 py-2 rounded-lg border border-[#1b345c] shadow-lg flex items-center gap-3">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-xs font-bold text-white">
                Cadastral Ground Truth Engine
              </span>
            </div>
            <div className="h-3 w-[1px] bg-[#1b345c]" />
            <span className="text-[11px] text-[#8EAECF] font-mono">
              Active: {activeRecord.parcelId} · Survey {activeRecord.surveyNumber}
            </span>
          </div>

          {/* Map Layer Quick Toggles */}
          <div className="absolute top-3 right-3 z-30 bg-[#09152b]/90 backdrop-blur-md px-3 py-1.5 rounded-lg border border-[#1b345c] shadow-lg flex items-center gap-2 text-xs">
            <button
              type="button"
              onClick={() => setMapLayers((prev) => ({ ...prev, topologyConflicts: !prev.topologyConflicts }))}
              className={`px-2 py-1 rounded text-[10px] font-bold transition-colors ${
                mapLayers.topologyConflicts ? 'bg-red-600/80 text-white' : 'bg-[#112340] text-[#7EA3CC]'
              }`}
            >
              Overlaps (Red)
            </button>
            <button
              type="button"
              onClick={() => setMapLayers((prev) => ({ ...prev, registration: !prev.registration }))}
              className={`px-2 py-1 rounded text-[10px] font-bold transition-colors ${
                mapLayers.registration ? 'bg-purple-600/80 text-white' : 'bg-[#112340] text-[#7EA3CC]'
              }`}
            >
              SRO Deeds
            </button>
            <button
              type="button"
              onClick={() => setMapLayers((prev) => ({ ...prev, zoning: !prev.zoning }))}
              className={`px-2 py-1 rounded text-[10px] font-bold transition-colors ${
                mapLayers.zoning ? 'bg-amber-600/80 text-white' : 'bg-[#112340] text-[#7EA3CC]'
              }`}
            >
              Master Plan
            </button>
          </div>

          {/* Embedded MapLibre Component */}
          <div className="flex-1 w-full h-full relative">
            <CadastralMap
              onMapReady={(map) => {
                mapInstanceRef.current = map;
              }}
              layers={mapLayers}
              statusFilter="all"
              riskFilter="all"
              selectedParcelId={selectedParcelId}
              onParcelSelect={(p) => handleSelectParcel(p.parcel_id)}
            />
          </div>

          {/* Map bottom overlay: Spatial metrics bar */}
          <div className="absolute bottom-3 left-3 right-3 z-30 bg-[#09152b]/95 backdrop-blur-md px-4 py-2 rounded-lg border border-[#1b345c] shadow-lg flex items-center justify-between text-xs">
            <div className="flex items-center gap-4">
              <div>
                <span className="text-[10px] text-[#7EA3CC] uppercase font-bold">Calculated FMB Area:</span>
                <span className="ml-1.5 font-bold font-mono text-white">
                  {activeRecord.cadastre.calculatedAreaAcres.toFixed(2)} acres ({activeRecord.cadastre.calculatedAreaSqM.toLocaleString()} m²)
                </span>
              </div>
              {activeRecord.cadastre.overlapSqM && (
                <div className="text-red-400 font-bold flex items-center gap-1">
                  <AlertOctagon className="w-3.5 h-3.5" />
                  <span>Overlap Area: {activeRecord.cadastre.overlapSqM} m²</span>
                </div>
              )}
            </div>

            <div className="text-[11px] text-[#7EA3CC] font-mono">
              Projection: EPSG:4326 · WGS84
            </div>
          </div>
        </section>

        {/* ═════════════════════════════════════════════════════════════════════
            PANE 3: 4-PILLAR RECONCILIATION & ADJUDICATION PANEL (Right 33%)
            ═════════════════════════════════════════════════════════════════════ */}
        <aside className="w-[440px] flex-shrink-0 flex flex-col border-l border-[#162B4D] bg-[#0c182e] overflow-hidden">
          {/* Panel Header */}
          <div className="p-4 border-b border-[#162B4D] bg-[#0f203d]">
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="text-[10px] font-bold text-[#7EA3CC] uppercase tracking-wider">
                  Active Adjudication File
                </div>
                <h2 className="text-base font-bold text-white font-serif tracking-tight mt-0.5">
                  {activeRecord.ulpin}
                </h2>
                <div className="text-xs text-[#A6C5E8]">
                  Survey No: <strong className="text-white">{activeRecord.surveyNumber}</strong> · Village: Tirupporur
                </div>
              </div>

              {/* Trust Score Badge */}
              <div className="text-right">
                <div
                  className={`text-lg font-black font-mono px-3 py-1 rounded-lg border ${
                    activeRecord.trustScore < 50
                      ? 'bg-red-950/80 text-red-400 border-red-700/60'
                      : activeRecord.trustScore < 75
                      ? 'bg-amber-950/80 text-amber-400 border-amber-700/60'
                      : 'bg-emerald-950/80 text-emerald-400 border-emerald-700/60'
                  }`}
                >
                  {activeRecord.trustScore}
                  <span className="text-[10px] font-normal text-white/60">/100</span>
                </div>
                <div className="text-[9px] font-bold uppercase tracking-wider text-[#7EA3CC] mt-0.5">
                  Trust Score ({activeRecord.riskBand})
                </div>
              </div>
            </div>
          </div>

          {/* Panel Scrollable Content: 4 Pillars Matrix & Action Center */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">

            {/* ── 4-PILLARS FEDERATED COMPARISON GRID ─────────────────────── */}
            <div className="space-y-2.5">
              <div className="text-[11px] font-bold uppercase tracking-wider text-[#7EA3CC] flex items-center justify-between">
                <span>The Four Pillars of Land Truth</span>
                <span className="text-[10px] text-emerald-400 font-mono">Live Federated Sync</span>
              </div>

              {/* Pillar 1: Cadastre */}
              <div className={`p-3 rounded-lg border text-xs transition-colors ${
                activeRecord.cadastre.status === 'DISCREPANCY'
                  ? 'bg-red-950/30 border-red-800/60'
                  : 'bg-[#081326] border-[#1b345c]'
              }`}>
                <div className="flex items-center justify-between text-[11px] font-bold">
                  <span className="text-emerald-400 flex items-center gap-1.5">
                    <MapPin className="w-3.5 h-3.5" />
                    1. CADASTRE (Survey Dept)
                  </span>
                  <span className={`text-[10px] px-1.5 rounded font-bold ${
                    activeRecord.cadastre.status === 'DISCREPANCY' ? 'bg-red-900 text-red-200' : 'bg-emerald-900 text-emerald-200'
                  }`}>
                    {activeRecord.cadastre.status}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-2 mt-2 text-[#9bb7d4]">
                  <div>Area: <strong className="text-white">{activeRecord.cadastre.calculatedAreaAcres} ac</strong></div>
                  <div>Survey No: <strong className="text-white">{activeRecord.cadastre.surveyNumber}</strong></div>
                  <div className="col-span-2 text-[11px] text-[#A6C5E8]">
                    Status: {activeRecord.cadastre.fmbStatus}
                  </div>
                  {activeRecord.cadastre.boundaryConflictDetails && (
                    <div className="col-span-2 text-[11px] font-bold text-red-400">
                      ⚠️ {activeRecord.cadastre.boundaryConflictDetails}
                    </div>
                  )}
                </div>
              </div>

              {/* Pillar 2: Registration (SRO) */}
              <div className={`p-3 rounded-lg border text-xs transition-colors ${
                activeRecord.registration.status === 'DISCREPANCY'
                  ? 'bg-red-950/30 border-red-800/60'
                  : 'bg-[#081326] border-[#1b345c]'
              }`}>
                <div className="flex items-center justify-between text-[11px] font-bold">
                  <span className="text-sky-400 flex items-center gap-1.5">
                    <FileCheck2 className="w-3.5 h-3.5" />
                    2. REGISTRATION (SRO / NGDRS)
                  </span>
                  <span className={`text-[10px] px-1.5 rounded font-bold ${
                    activeRecord.registration.status === 'DISCREPANCY' ? 'bg-red-900 text-red-200' : 'bg-emerald-900 text-emerald-200'
                  }`}>
                    {activeRecord.registration.status}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-2 mt-2 text-[#9bb7d4]">
                  <div className="col-span-2">
                    Deed Holder: <strong className="text-white">{activeRecord.registration.registeredOwner}</strong>
                  </div>
                  <div>Doc: <strong className="text-white">{activeRecord.registration.deedNumber}</strong></div>
                  <div>Deed Area: <strong className="text-white">{activeRecord.registration.deedAreaAcres} ac</strong></div>
                  <div className="col-span-2 text-[11px] text-[#A6C5E8]">
                    EC: <span className={activeRecord.registration.encumbranceStatus.includes('ENCUMBERED') ? 'text-amber-400 font-bold' : 'text-emerald-400'}>{activeRecord.registration.encumbranceStatus}</span>
                  </div>
                  {activeRecord.registration.mortgageDetails && (
                    <div className="col-span-2 text-[11px] font-bold text-amber-400">
                      ⚠️ {activeRecord.registration.mortgageDetails}
                    </div>
                  )}
                </div>
              </div>

              {/* Pillar 3: Revenue (Tamil Nilam RoR) */}
              <div className={`p-3 rounded-lg border text-xs transition-colors ${
                activeRecord.revenue.status === 'DISCREPANCY'
                  ? 'bg-red-950/30 border-red-800/60'
                  : 'bg-[#081326] border-[#1b345c]'
              }`}>
                <div className="flex items-center justify-between text-[11px] font-bold">
                  <span className="text-amber-400 flex items-center gap-1.5">
                    <FileSpreadsheet className="w-3.5 h-3.5" />
                    3. REVENUE (Tamil Nilam RoR)
                  </span>
                  <span className={`text-[10px] px-1.5 rounded font-bold ${
                    activeRecord.revenue.status === 'DISCREPANCY' ? 'bg-red-900 text-red-200' : 'bg-emerald-900 text-emerald-200'
                  }`}>
                    {activeRecord.revenue.status}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-2 mt-2 text-[#9bb7d4]">
                  <div className="col-span-2">
                    Pattadar: <strong className="text-white">{activeRecord.revenue.pattadarName}</strong>
                  </div>
                  <div>Patta: <strong className="text-white">{activeRecord.revenue.pattaNumber}</strong></div>
                  <div>RoR Area: <strong className="text-white">{activeRecord.revenue.recordedAreaAcres} ac</strong></div>
                  <div className="col-span-2 text-[11px] text-[#A6C5E8]">
                    Classification: {activeRecord.revenue.landClassification} · {activeRecord.revenue.taxStatus}
                  </div>
                </div>
              </div>

              {/* Pillar 4: Planning & ULB */}
              <div className={`p-3 rounded-lg border text-xs transition-colors ${
                activeRecord.planning.status === 'DISCREPANCY'
                  ? 'bg-red-950/30 border-red-800/60'
                  : 'bg-[#081326] border-[#1b345c]'
              }`}>
                <div className="flex items-center justify-between text-[11px] font-bold">
                  <span className="text-purple-400 flex items-center gap-1.5">
                    <Building2 className="w-3.5 h-3.5" />
                    4. PLANNING & ULB (Master Plan)
                  </span>
                  <span className={`text-[10px] px-1.5 rounded font-bold ${
                    activeRecord.planning.status === 'DISCREPANCY' ? 'bg-red-900 text-red-200' : 'bg-emerald-900 text-emerald-200'
                  }`}>
                    {activeRecord.planning.status}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-2 mt-2 text-[#9bb7d4]">
                  <div className="col-span-2">
                    Zone: <strong className="text-white">{activeRecord.planning.masterPlanZone}</strong>
                  </div>
                  <div>Permitted: <strong className="text-white">{activeRecord.planning.permittedUse}</strong></div>
                  <div>Actual Use: <strong className="text-white">{activeRecord.planning.actualUse}</strong></div>
                  {activeRecord.planning.propertyTaxId && (
                    <div className="col-span-2 text-[11px] text-[#A6C5E8]">
                      ULB Property Tax ID: {activeRecord.planning.propertyTaxId}
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* ── DISCREPANCY DIFF SUMMARY ─────────────────────────────────── */}
            {activeRecord.diffs.length > 0 && (
              <div className="bg-[#121c2e] p-3.5 rounded-lg border border-[#233d6b] space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                    Inter-Silo Discrepancy Diff ({activeRecord.diffs.length})
                  </span>
                  <span className="text-[10px] text-amber-400 font-bold bg-amber-950/60 px-2 py-0.5 rounded">
                    Action Required
                  </span>
                </div>

                <div className="space-y-2 pt-1">
                  {activeRecord.diffs.map((diff, idx) => (
                    <div key={idx} className="bg-[#091220] p-2.5 rounded border border-[#1a3052] text-xs">
                      <div className="flex items-center justify-between text-[11px] font-bold text-white">
                        <span>{diff.field}</span>
                        <span className={`text-[9px] px-1.5 py-0.2 rounded font-mono ${
                          diff.severity === 'CRITICAL' ? 'bg-red-900 text-red-300' : 'bg-amber-900 text-amber-300'
                        }`}>
                          {diff.severity}
                        </span>
                      </div>

                      <div className="grid grid-cols-2 gap-2 mt-1.5 text-[11px]">
                        <div className="bg-[#0f1d33] p-1.5 rounded">
                          <span className="text-[9px] text-[#7EA3CC] block">{diff.deptA.name}</span>
                          <strong className="text-white">{diff.deptA.value}</strong>
                        </div>
                        <div className="bg-[#0f1d33] p-1.5 rounded">
                          <span className="text-[9px] text-[#7EA3CC] block">{diff.deptB.name}</span>
                          <strong className="text-amber-300">{diff.deptB.value}</strong>
                        </div>
                      </div>

                      <div className="text-[10px] text-[#8EAECF] mt-1.5 leading-relaxed">
                        {diff.note}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* ── STATUTORY ADJUDICATION ACTION PALETTE ─────────────────────── */}
            <div className="bg-[#0f203d] p-3.5 rounded-lg border border-[#1e3c6a] space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                  <Scale className="w-3.5 h-3.5 text-[#14a89a]" />
                  Statutory Adjudication Console
                </span>
                <span className="text-[10px] text-[#8EAECF] font-mono">
                  BNDR Legal Framework
                </span>
              </div>

              {actionSuccessMsg && (
                <div className="bg-emerald-950/80 border border-emerald-600/80 p-2.5 rounded-md text-xs text-emerald-200 flex items-start gap-2">
                  <Check className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <div className="font-bold">Adjudication Order Executed</div>
                    <div className="text-[11px] text-emerald-300 mt-0.5">{actionSuccessMsg}</div>
                  </div>
                </div>
              )}

              {/* Mandatory remarks field */}
              <div className="space-y-1">
                <label className="text-[11px] font-bold text-[#A6C5E8]">
                  Officer Order Remarks & Finding <span className="text-red-400">*</span>
                </label>
                <textarea
                  rows={2}
                  value={officerRemarks}
                  onChange={(e) => setOfficerRemarks(e.target.value)}
                  placeholder="Enter statutory reasons for reconciliation (e.g. Identity verified via Aadhaar; Cadastral area confirmed by FMB stone)..."
                  className="w-full bg-[#081224] text-xs text-white p-2 rounded border border-[#1e3c6a] placeholder-[#5D80A6] focus:outline-none focus:border-[#14a89a]"
                />
              </div>

              {/* Action buttons list */}
              <div className="space-y-2 pt-1">
                <div className="text-[10px] font-bold uppercase tracking-wider text-[#7EA3CC]">
                  Select Statutory Resolution Action:
                </div>
                {activeRecord.availableActions.map((action) => (
                  <button
                    key={action.id}
                    type="button"
                    disabled={actionInProgress}
                    onClick={() => handleExecuteAction(action.label, action.statutoryRef)}
                    className="w-full text-left bg-[#14284b] hover:bg-[#1a3563] p-2.5 rounded border border-[#214376] hover:border-[#14a89a] transition-all group"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-white group-hover:text-[#14a89a] transition-colors flex items-center gap-1.5">
                        <Send className="w-3 h-3 text-[#14a89a]" />
                        {action.label}
                      </span>
                      <span className="text-[9px] font-mono text-[#8EAECF] bg-[#0b172d] px-1.5 py-0.5 rounded">
                        {action.officerRole}
                      </span>
                    </div>
                    <div className="text-[10.5px] text-[#A6C5E8] mt-1 leading-snug">
                      {action.description}
                    </div>
                    <div className="text-[9.5px] text-[#7EA3CC] mt-1 font-mono">
                      Ref: {action.statutoryRef}
                    </div>
                  </button>
                ))}
              </div>

              {/* Provenance note */}
              <div className="text-[10px] text-[#5D80A6] pt-1 border-t border-[#1a3563] flex items-center justify-between">
                <span>Presumptive Title Standard · Non-Conclusive</span>
                <span>Audit Chain: SHA-256</span>
              </div>
            </div>

          </div>
        </aside>

      </div>
    </div>
  );
}
