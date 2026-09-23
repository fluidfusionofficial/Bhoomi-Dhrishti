'use client';

import * as React from 'react';
import {
  Building2,
  MapPin,
  AlertTriangle,
  CheckCircle2,
  Clock,
  FileText,
  Layers,
  ArrowRight,
  TrendingUp,
  XCircle,
  Link2,
  Search,
} from 'lucide-react';

interface ZoneRecord {
  id: string;
  parcel_id: string;
  village: string;
  current_zone: string;
  master_plan_zone: string;
  status: 'compliant' | 'violation' | 'review';
  area_ha: number;
}

interface PermitApplication {
  id: string;
  applicant: string;
  parcel_id: string;
  type: string;
  submitted: string;
  status: 'pending' | 'approved' | 'rejected';
  zone: string;
}

interface LandUseChange {
  period: string;
  agricultural: number;
  residential: number;
  commercial: number;
  industrial: number;
}

const MOCK_ZONES: ZoneRecord[] = [
  { id: 'Z-001', parcel_id: 'TN-607-001-042', village: 'Kilpennathur', current_zone: 'Agricultural', master_plan_zone: 'Agricultural', status: 'compliant', area_ha: 0.82 },
  { id: 'Z-002', parcel_id: 'TN-607-001-044', village: 'Chengalpattu', current_zone: 'Residential', master_plan_zone: 'Residential', status: 'compliant', area_ha: 0.12 },
  { id: 'Z-003', parcel_id: 'TN-607-001-051', village: 'Mamallapuram', current_zone: 'Commercial', master_plan_zone: 'Residential', status: 'violation', area_ha: 0.34 },
  { id: 'Z-004', parcel_id: 'TN-607-001-067', village: 'Uthiramerur', current_zone: 'Industrial', master_plan_zone: 'Agricultural', status: 'violation', area_ha: 1.20 },
  { id: 'Z-005', parcel_id: 'TN-607-001-089', village: 'Kanchipuram', current_zone: 'Mixed Use', master_plan_zone: 'Commercial', status: 'review', area_ha: 0.56 },
  { id: 'Z-006', parcel_id: 'TN-607-001-102', village: 'Sriperumbudur', current_zone: 'SEZ', master_plan_zone: 'SEZ', status: 'compliant', area_ha: 2.40 },
];

const MOCK_PERMITS: PermitApplication[] = [
  { id: 'BP-2026-001', applicant: 'R. Krishnamurthy', parcel_id: 'TN-607-001-044', type: 'Construction — G+2 Residential', submitted: '2026-09-10', status: 'pending', zone: 'Residential' },
  { id: 'BP-2026-002', applicant: 'Lakshmi Constructions', parcel_id: 'TN-607-001-051', type: 'Commercial Complex', submitted: '2026-09-05', status: 'pending', zone: 'Residential' },
  { id: 'BP-2026-003', applicant: 'K. Venkatesh', parcel_id: 'TN-607-001-089', type: 'Warehouse Extension', submitted: '2026-08-28', status: 'pending', zone: 'Commercial' },
  { id: 'BP-2026-004', applicant: 'S. Priya', parcel_id: 'TN-607-001-102', type: 'Factory Unit', submitted: '2026-08-15', status: 'approved', zone: 'SEZ' },
  { id: 'BP-2026-005', applicant: 'M. Selvaraj', parcel_id: 'TN-607-001-067', type: 'Godown on Ag Land', submitted: '2026-08-10', status: 'rejected', zone: 'Agricultural' },
];

const MOCK_LAND_USE: LandUseChange[] = [
  { period: 'Q1 2026', agricultural: 68.2, residential: 14.5, commercial: 6.2, industrial: 5.1 },
  { period: 'Q2 2026', agricultural: 67.1, residential: 15.2, commercial: 6.6, industrial: 5.1 },
  { period: 'Q3 2026', agricultural: 66.4, residential: 15.8, commercial: 6.9, industrial: 5.3 },
];

const RESTRICTION_ZONES = [
  { name: 'Mahabalipuram Heritage Buffer (500m)', type: 'ASI Heritage', parcels_affected: 42, status: 'active' },
  { name: 'Palar River Flood Plain', type: 'CRZ / Flood Zone', parcels_affected: 18, status: 'active' },
  { name: 'Sriperumbudur Industrial SEZ', type: 'SEZ Notified', parcels_affected: 124, status: 'active' },
  { name: 'Kanchipuram Temple Zone', type: 'Religious / Heritage', parcels_affected: 31, status: 'active' },
];

const MOCK_TAX_LINKAGE = [
  { property_id: 'CGL-MUN-2024-00412', ulpin: 'TN607001002421B', owner: 'K. Rajasekaran', ward: 'Ward 12, Chengalpattu', tax_status: 'PAID', annual_tax: 4200, type: 'Urban' },
  { property_id: 'CGL-MUN-2024-00891', ulpin: 'TN607001002422C', owner: 'S. Murugesan', ward: 'Ward 8, Chengalpattu', tax_status: 'ARREAR', annual_tax: 3800, type: 'Urban' },
  { property_id: 'TVL-GP-2024-01204', ulpin: 'TN607001002423D', owner: 'R. Anbarasan', ward: 'Kilpennathur GP', tax_status: 'PAID', annual_tax: 1200, type: 'Rural' },
  { property_id: 'KPM-MUN-2024-00567', ulpin: 'TN607001002489X', owner: 'L. Constructions Pvt Ltd', ward: 'Ward 3, Kanchipuram', tax_status: 'PAID', annual_tax: 18500, type: 'Urban' },
  { property_id: 'SRP-MUN-2024-02100', ulpin: 'TN607001002501Z', owner: 'Industrial Estate Auth.', ward: 'Sriperumbudur SEZ', tax_status: 'EXEMPT', annual_tax: 0, type: 'SEZ' },
];

export function PlanningView() {
  const [activeSection, setActiveSection] = React.useState<'zoning' | 'permits' | 'landuse' | 'restrictions' | 'taxlinkage'>('zoning');
  const [taxSearchQuery, setTaxSearchQuery] = React.useState('');

  const violationCount = MOCK_ZONES.filter((z) => z.status === 'violation').length;
  const pendingPermitCount = MOCK_PERMITS.filter((p) => p.status === 'pending').length;

  return (
    <div className="flex-1 overflow-y-auto p-5 space-y-5">
      {/* Section Tabs */}
      <div className="bg-white border border-[#DCE3EA] rounded-[4px] px-3 flex gap-1 overflow-x-auto text-xs font-semibold">
        {[
          { id: 'zoning', label: `Zoning Compliance (${violationCount} violations)`, icon: Building2 },
          { id: 'permits', label: `Building Permits (${pendingPermitCount} pending)`, icon: FileText },
          { id: 'landuse', label: 'Land Use Trends', icon: TrendingUp },
          { id: 'restrictions', label: `Restriction Zones (${RESTRICTION_ZONES.length})`, icon: Layers },
          { id: 'taxlinkage', label: `Property Tax Linkage (${MOCK_TAX_LINKAGE.length})`, icon: Link2 },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeSection === tab.id;
          return (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveSection(tab.id as typeof activeSection)}
              className={`py-3 px-3.5 border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap ${
                isActive ? 'border-[#B45309] text-[#B45309]' : 'border-transparent text-[#4A5B6E] hover:text-[#16212E]'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Zoning Compliance */}
      {activeSection === 'zoning' && (
        <div className="space-y-4">
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-white border border-[#DCE3EA] rounded-md p-4">
              <div className="text-2xl font-serif font-bold text-[#16212E]">{MOCK_ZONES.filter((z) => z.status === 'compliant').length}</div>
              <div className="text-xs text-[#4A5B6E] mt-1 flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-[#1E7B4D]" />
                Compliant with Master Plan
              </div>
            </div>
            <div className="bg-white border border-[#DCE3EA] rounded-md p-4">
              <div className="text-2xl font-serif font-bold text-[#A32E2E]">{violationCount}</div>
              <div className="text-xs text-[#4A5B6E] mt-1 flex items-center gap-1.5">
                <AlertTriangle className="w-3.5 h-3.5 text-[#A32E2E]" />
                Zone Violations Detected
              </div>
            </div>
            <div className="bg-white border border-[#DCE3EA] rounded-md p-4">
              <div className="text-2xl font-serif font-bold text-[#B8720B]">{MOCK_ZONES.filter((z) => z.status === 'review').length}</div>
              <div className="text-xs text-[#4A5B6E] mt-1 flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-[#B8720B]" />
                Under Review
              </div>
            </div>
          </div>

          <div className="bg-white border border-[#DCE3EA] rounded-md overflow-hidden">
            <div className="px-4 py-3 border-b border-[#DCE3EA] flex items-center justify-between">
              <h3 className="text-sm font-bold text-[#16212E]">Zoning Compliance Register</h3>
              <span className="text-[10px] text-[#4A5B6E] uppercase tracking-wider">Master Plan 2026 Overlay</span>
            </div>
            <table className="w-full text-xs">
              <thead>
                <tr className="bg-[#F7F9FC] text-[#4A5B6E] text-left">
                  <th className="px-4 py-2.5 font-semibold">Parcel ID</th>
                  <th className="px-4 py-2.5 font-semibold">Village</th>
                  <th className="px-4 py-2.5 font-semibold">Current Use</th>
                  <th className="px-4 py-2.5 font-semibold">Master Plan Zone</th>
                  <th className="px-4 py-2.5 font-semibold">Area (Ha)</th>
                  <th className="px-4 py-2.5 font-semibold">Status</th>
                </tr>
              </thead>
              <tbody>
                {MOCK_ZONES.map((z) => (
                  <tr key={z.id} className="border-t border-[#F1F4F8] hover:bg-[#F7F9FC]">
                    <td className="px-4 py-2.5 font-mono font-semibold text-[#14548C]">{z.parcel_id}</td>
                    <td className="px-4 py-2.5 text-[#16212E]">{z.village}</td>
                    <td className="px-4 py-2.5 text-[#16212E]">{z.current_zone}</td>
                    <td className="px-4 py-2.5 text-[#16212E]">{z.master_plan_zone}</td>
                    <td className="px-4 py-2.5 font-serif font-semibold tabular-nums">{z.area_ha}</td>
                    <td className="px-4 py-2.5">
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                          z.status === 'compliant'
                            ? 'bg-[#E7F6EC] text-[#1E7B4D]'
                            : z.status === 'violation'
                            ? 'bg-[#FDEAEA] text-[#A32E2E]'
                            : 'bg-[#FDF1E0] text-[#B8720B]'
                        }`}
                      >
                        {z.status === 'compliant' ? 'COMPLIANT' : z.status === 'violation' ? 'VIOLATION' : 'REVIEW'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Building Permits */}
      {activeSection === 'permits' && (
        <div className="bg-white border border-[#DCE3EA] rounded-md overflow-hidden">
          <div className="px-4 py-3 border-b border-[#DCE3EA] flex items-center justify-between">
            <h3 className="text-sm font-bold text-[#16212E]">Building Permit Applications</h3>
            <span className="text-xs text-[#B45309] font-semibold">{pendingPermitCount} Pending Review</span>
          </div>
          <div className="divide-y divide-[#F1F4F8]">
            {MOCK_PERMITS.map((p) => (
              <div key={p.id} className="px-4 py-3.5 flex items-center justify-between hover:bg-[#F7F9FC]">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-mono font-bold text-[#14548C]">{p.id}</span>
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                        p.status === 'pending'
                          ? 'bg-[#FDF1E0] text-[#B8720B]'
                          : p.status === 'approved'
                          ? 'bg-[#E7F6EC] text-[#1E7B4D]'
                          : 'bg-[#FDEAEA] text-[#A32E2E]'
                      }`}
                    >
                      {p.status.toUpperCase()}
                    </span>
                  </div>
                  <div className="text-xs text-[#16212E] font-semibold">{p.type}</div>
                  <div className="text-[11px] text-[#4A5B6E] mt-0.5">
                    {p.applicant} · {p.parcel_id} · Zone: {p.zone} · Submitted {p.submitted}
                  </div>
                </div>
                <div className="ml-4 text-right flex-shrink-0">
                  <div className="text-[10px] text-[#4A5B6E]">
                    {p.status === 'pending' ? 'Pending at ULB Planning Dept.' :
                     p.status === 'approved' ? 'Sanctioned via DTCP' :
                     'Rejected by DTCP'}
                  </div>
                  <div className="text-[9px] text-[#4A5B6E] mt-0.5">
                    Source: State Town Planning Portal
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Land Use Trends */}
      {activeSection === 'landuse' && (
        <div className="space-y-4">
          <div className="bg-white border border-[#DCE3EA] rounded-md overflow-hidden">
            <div className="px-4 py-3 border-b border-[#DCE3EA]">
              <h3 className="text-sm font-bold text-[#16212E]">Land Use Distribution — Quarterly Trend</h3>
              <p className="text-[11px] text-[#4A5B6E] mt-0.5">Percentage of total area by classification</p>
            </div>
            <table className="w-full text-xs">
              <thead>
                <tr className="bg-[#F7F9FC] text-[#4A5B6E] text-left">
                  <th className="px-4 py-2.5 font-semibold">Period</th>
                  <th className="px-4 py-2.5 font-semibold">Agricultural %</th>
                  <th className="px-4 py-2.5 font-semibold">Residential %</th>
                  <th className="px-4 py-2.5 font-semibold">Commercial %</th>
                  <th className="px-4 py-2.5 font-semibold">Industrial %</th>
                </tr>
              </thead>
              <tbody>
                {MOCK_LAND_USE.map((row) => (
                  <tr key={row.period} className="border-t border-[#F1F4F8]">
                    <td className="px-4 py-2.5 font-semibold text-[#16212E]">{row.period}</td>
                    <td className="px-4 py-2.5 font-serif tabular-nums">{row.agricultural}%</td>
                    <td className="px-4 py-2.5 font-serif tabular-nums">{row.residential}%</td>
                    <td className="px-4 py-2.5 font-serif tabular-nums">{row.commercial}%</td>
                    <td className="px-4 py-2.5 font-serif tabular-nums">{row.industrial}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="bg-[#FEF3C7] border border-[#FCD34D] rounded-md p-4 flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-[#B45309] flex-shrink-0 mt-0.5" />
            <div>
              <div className="text-xs font-bold text-[#B45309]">Agricultural Land Conversion Alert</div>
              <div className="text-[11px] text-[#92400E] mt-1">
                1.8% net decrease in agricultural land observed over 3 quarters. Primary conversion corridors: Chengalpattu–Sriperumbudur industrial belt and Mamallapuram coastal tourism zone.
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Restriction Zones */}
      {activeSection === 'restrictions' && (
        <div className="bg-white border border-[#DCE3EA] rounded-md overflow-hidden">
          <div className="px-4 py-3 border-b border-[#DCE3EA]">
            <h3 className="text-sm font-bold text-[#16212E]">Active Restriction Zones</h3>
            <p className="text-[11px] text-[#4A5B6E] mt-0.5">Heritage buffers, flood plains, CRZ, and SEZ notified areas</p>
          </div>
          <div className="divide-y divide-[#F1F4F8]">
            {RESTRICTION_ZONES.map((rz) => (
              <div key={rz.name} className="px-4 py-3.5 flex items-center justify-between hover:bg-[#F7F9FC]">
                <div>
                  <div className="text-xs font-semibold text-[#16212E]">{rz.name}</div>
                  <div className="text-[11px] text-[#4A5B6E] mt-0.5">
                    Type: {rz.type} · {rz.parcels_affected} parcels affected
                  </div>
                </div>
                <span className="text-[10px] font-bold bg-[#FDEAEA] text-[#A32E2E] px-2.5 py-1 rounded-full">
                  RESTRICTED
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Property Tax Linkage */}
      {activeSection === 'taxlinkage' && (
        <div className="space-y-4">
          <div className="bg-white border border-[#DCE3EA] rounded-md overflow-hidden">
            <div className="px-4 py-3 border-b border-[#DCE3EA]">
              <h3 className="text-sm font-bold text-[#16212E]">Property Tax Linkage — Municipal Property ID to ULPIN</h3>
              <p className="text-[11px] text-[#4A5B6E] mt-0.5">Maps municipal/panchayat Property IDs to canonical Bhoomi Dhrishti ULPINs for tax reconciliation</p>
            </div>

            <div className="px-4 py-3 border-b border-[#DCE3EA] bg-[#F7F9FC] flex gap-2">
              <input
                type="text"
                value={taxSearchQuery}
                onChange={(e) => setTaxSearchQuery(e.target.value)}
                placeholder="Search by Property ID, ULPIN, owner name, or ward…"
                className="flex-1 px-3 py-1.5 text-xs bg-white border border-[#B9C5D1] rounded-[4px] focus:outline-none focus:ring-2 focus:ring-[#B45309]"
              />
              <button className="h-7 px-3 text-xs font-semibold bg-[#B45309] text-white rounded-[4px] hover:bg-[#92400E] flex items-center gap-1.5">
                <Search className="w-3.5 h-3.5" /> Search
              </button>
            </div>

            <table className="w-full text-xs">
              <thead>
                <tr className="bg-[#F7F9FC] text-[#4A5B6E] text-left">
                  <th className="px-4 py-2.5 font-semibold">Municipal Property ID</th>
                  <th className="px-4 py-2.5 font-semibold">ULPIN (Bhoomi Dhrishti)</th>
                  <th className="px-4 py-2.5 font-semibold">Owner</th>
                  <th className="px-4 py-2.5 font-semibold">Ward / GP</th>
                  <th className="px-4 py-2.5 font-semibold">Type</th>
                  <th className="px-4 py-2.5 font-semibold text-right">Annual Tax</th>
                  <th className="px-4 py-2.5 font-semibold">Status</th>
                </tr>
              </thead>
              <tbody>
                {MOCK_TAX_LINKAGE
                  .filter((row) => {
                    if (!taxSearchQuery.trim()) return true;
                    const q = taxSearchQuery.toLowerCase();
                    return (
                      row.property_id.toLowerCase().includes(q) ||
                      row.ulpin.toLowerCase().includes(q) ||
                      row.owner.toLowerCase().includes(q) ||
                      row.ward.toLowerCase().includes(q)
                    );
                  })
                  .map((row) => (
                  <tr key={row.property_id} className="border-t border-[#F1F4F8] hover:bg-[#F7F9FC]">
                    <td className="px-4 py-2.5 font-mono font-semibold text-[#B45309]">{row.property_id}</td>
                    <td className="px-4 py-2.5">
                      <div className="flex items-center gap-1.5">
                        <Link2 className="w-3 h-3 text-[#14548C]" />
                        <span className="font-mono font-semibold text-[#14548C]">{row.ulpin}</span>
                      </div>
                    </td>
                    <td className="px-4 py-2.5 text-[#16212E] font-semibold">{row.owner}</td>
                    <td className="px-4 py-2.5 text-[#4A5B6E]">{row.ward}</td>
                    <td className="px-4 py-2.5">
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                        row.type === 'Urban' ? 'bg-[#E2ECF5] text-[#14548C]' :
                        row.type === 'Rural' ? 'bg-[#E7F6EC] text-[#1E7B4D]' :
                        'bg-[#FEF3C7] text-[#B45309]'
                      }`}>
                        {row.type}
                      </span>
                    </td>
                    <td className="px-4 py-2.5 text-right font-serif tabular-nums font-semibold">
                      {row.annual_tax > 0 ? `₹${row.annual_tax.toLocaleString()}` : '—'}
                    </td>
                    <td className="px-4 py-2.5">
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                        row.tax_status === 'PAID' ? 'bg-[#E7F6EC] text-[#1E7B4D]' :
                        row.tax_status === 'ARREAR' ? 'bg-[#FDEAEA] text-[#A32E2E]' :
                        'bg-[#F1F4F8] text-[#4A5B6E]'
                      }`}>
                        {row.tax_status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="bg-[#FEF3C7] border border-[#FCD34D] rounded-md p-4 flex items-start gap-3">
            <Link2 className="w-5 h-5 text-[#B45309] flex-shrink-0 mt-0.5" />
            <div>
              <div className="text-xs font-bold text-[#B45309]">Cross-System Linkage Status</div>
              <div className="text-[11px] text-[#92400E] mt-1">
                {MOCK_TAX_LINKAGE.length} municipal/panchayat Property IDs linked to ULPINs. 1 arrear flagged for revenue department follow-up. ULPIN linkage enables unified property tax assessment across rural and urban jurisdictions.
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
