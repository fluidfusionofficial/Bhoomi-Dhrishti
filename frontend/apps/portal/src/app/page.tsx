'use client';

import * as React from 'react';
import {
  Users,
  ShieldCheck,
  Scale,
  Map,
  BarChart3,
  Globe,
  ArrowRight,
  Landmark,
  Database,
  Eye,
  Layers,
  GitBranch,
  Shield,
  Search,
  FileSpreadsheet,
  FileCheck2,
  Building2,
  Satellite,
  MapPin,
  Settings,
} from 'lucide-react';

interface RoleOption {
  id: string;
  title: string;
  subtitle: string;
  description: string;
  icon: React.ElementType;
  color: string;
  bgColor: string;
  href: string;
  tags: string[];
  toolCount: number;
  features: string[];
}

const roles: RoleOption[] = [
  {
    id: 'citizen',
    title: 'Citizen',
    subtitle: 'Land Owner / Public User',
    description: 'Search land records, verify ownership, download RoR extracts, track mutation applications, and view who accessed your parcel data.',
    icon: Users,
    color: '#0F766E',
    bgColor: '#E6F6F4',
    href: 'http://localhost:3002',
    tags: ['Parcel Lookup', 'RoR Download', 'Access Audit'],
    toolCount: 5,
    features: ['ULPIN / Survey search', 'My Registered Parcels', 'Who Accessed My Land', 'Mutation Application', 'EC Download'],
  },
  {
    id: 'tehsildar',
    title: 'Tehsildar',
    subtitle: 'Revenue Officer',
    description: 'View mutation casework, RoR records, inspect spatial overlaps, and monitor trust scores — all from cross-verified state department data.',
    icon: Scale,
    color: '#14548C',
    bgColor: '#E2ECF5',
    href: 'http://localhost:3000?role=tehsildar',
    tags: ['Mutations', 'Revenue Records', 'Trust & Fraud'],
    toolCount: 10,
    features: ['Revenue Casework Register', 'Mutation Queue', 'Cadastral GIS Map', 'Entity Resolution', 'Trust Score Engine'],
  },
  {
    id: 'sub-registrar',
    title: 'Sub-Registrar',
    subtitle: 'Registration & Deeds Officer',
    description: 'View registered deeds, encumbrance certificates, stamp duty calculations, and flag suspicious transfers across the NGDRS registry.',
    icon: ShieldCheck,
    color: '#7C3AED',
    bgColor: '#EDE9FE',
    href: 'http://localhost:3000?role=sub-registrar',
    tags: ['Deeds & EC', 'Stamp Duty Calculator', 'Fraud Flags'],
    toolCount: 7,
    features: ['Deed Register (SRO)', 'Encumbrance Certificate', 'Stamp Duty Calculator', 'Duplicate Deed Check', 'Suspicious Transfer Alerts'],
  },
  {
    id: 'town-planner',
    title: 'Town Planner',
    subtitle: 'Planning & Zoning Officer',
    description: 'Inspect zoning compliance, review building permits, manage restriction zones, and map municipal Property IDs to ULPINs.',
    icon: Map,
    color: '#B45309',
    bgColor: '#FEF3C7',
    href: 'http://localhost:3000?role=town-planner',
    tags: ['Zoning', 'Building Permits', 'Tax Linkage'],
    toolCount: 8,
    features: ['Zoning Compliance Register', 'Building Permit Review', 'Land Use Trends', 'Restriction Zones', 'Property Tax Linkage (ID→ULPIN)'],
  },
  {
    id: 'surveyor',
    title: 'Surveyor',
    subtitle: 'Cadastral Survey Officer',
    description: 'Resolve topology conflicts, validate parcel boundaries, detect encroachments via satellite imagery, and manage field demarcation.',
    icon: Globe,
    color: '#0369A1',
    bgColor: '#E0F2FE',
    href: 'http://localhost:3000?role=surveyor',
    tags: ['Topology', 'Demarcation', 'Satellite Watch'],
    toolCount: 7,
    features: ['Topology Conflict Resolver', 'Cadastral GIS Map', 'Sentinel-2 Watch', 'Dynamic Partitioning', 'DGPS Measurement'],
  },
  {
    id: 'collector',
    title: 'District Collector',
    subtitle: 'Executive & Policy Analytics',
    description: 'District-wide GIS heatmaps, KPIs, cross-department conflict summaries, scheme coverage, land conversion trends, and department performance.',
    icon: BarChart3,
    color: '#0B2E4E',
    bgColor: '#E2ECF5',
    href: 'http://localhost:3000?role=collector',
    tags: ['Analytics', 'Heatmaps', 'All Departments'],
    toolCount: 14,
    features: ['Executive Analytics Dashboard', 'District Heatmap', 'All Officer Tools (inherited)', 'Cross-Dept Conflicts', 'Scheme Coverage'],
  },
  {
    id: 'admin',
    title: 'Platform Admin',
    subtitle: 'State Admin / System Admin',
    description: 'State onboarding, schema field mappings, service health monitoring, natural language query console, and audit hash-chain integrity verification.',
    icon: Settings,
    color: '#4A5B6E',
    bgColor: '#F1F4F8',
    href: 'http://localhost:3003',
    tags: ['State Onboarding', 'Schema Mappings', 'Service Health'],
    toolCount: 5,
    features: ['National Overview & Trends', 'State Onboarding Console', 'Schema Mapping Editor', 'NL Query Explorer', 'Microservices Health Mesh'],
  },
];

const HOW_IT_WORKS = [
  { icon: Database, label: 'Federated Data', desc: 'State departments keep their records. This platform fetches and cross-verifies.' },
  { icon: MapPin, label: 'Single ULPIN', desc: 'Every parcel has a 14-digit identifier linking all departmental records.' },
  { icon: Layers, label: 'Three-Tier GIS', desc: 'Base spatial + governance overlays + utility layers on one map.' },
  { icon: Eye, label: 'Read-Only View', desc: 'No action taken here — a unified visibility layer with full provenance.' },
];

export default function RoleSelectionPage() {
  const [hoveredRole, setHoveredRole] = React.useState<string | null>(null);

  return (
    <div className="min-h-screen flex flex-col bg-[#F4F7FB]">
      {/* Header */}
      <header className="bg-[#0B2E4E] text-white">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[#14a89a] to-[#0f766e] flex items-center justify-center">
              <Landmark className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold tracking-tight leading-tight">
                Bhoomi Dhrishti
              </h1>
              <p className="text-[11px] text-white/60 leading-tight">
                Department of Land Resources (DoLR) &bull; Ministry of Rural Development
              </p>
            </div>
          </div>
          <div className="hidden sm:flex items-center gap-4 text-xs text-white/50">
            <span className="font-mono">SIH 2026 &bull; PS-26014</span>
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>All Services Operational</span>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="bg-gradient-to-b from-[#0B2E4E] to-[#14548C] text-white py-10 px-6">
        <div className="max-w-4xl mx-auto text-center space-y-4">
          <p className="text-xs uppercase tracking-[0.2em] text-white/50 font-semibold">
            Integrated GIS-Based Digital Public Infrastructure
          </p>
          <h2 className="text-3xl sm:text-4xl font-serif font-bold tracking-tight leading-tight">
            Select Your Role
          </h2>
          <p className="text-sm text-white/70 max-w-2xl mx-auto leading-relaxed">
            Each role provides a tailored view of the same underlying land records.
            Choose your designation to see the tools, dashboards, and data relevant to your responsibilities.
          </p>
        </div>
      </section>

      {/* How it works strip */}
      <div className="bg-white border-b border-[#DCE3EA]">
        <div className="max-w-6xl mx-auto px-6 py-4 grid grid-cols-2 lg:grid-cols-4 gap-4">
          {HOW_IT_WORKS.map((item) => {
            const Icon = item.icon;
            return (
              <div key={item.label} className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-lg bg-[#E2ECF5] flex items-center justify-center flex-shrink-0">
                  <Icon className="w-4 h-4 text-[#14548C]" />
                </div>
                <div>
                  <div className="text-xs font-bold text-[#16212E]">{item.label}</div>
                  <div className="text-[11px] text-[#4A5B6E] leading-relaxed">{item.desc}</div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Role Cards */}
      <main className="flex-1 px-6 py-8">
        <div className="max-w-6xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {roles.map((role, index) => {
              const Icon = role.icon;
              const isHovered = hoveredRole === role.id;
              return (
                <a
                  key={role.id}
                  href={role.href}
                  onMouseEnter={() => setHoveredRole(role.id)}
                  onMouseLeave={() => setHoveredRole(null)}
                  className="animate-fade-in-up group focus:outline-none focus:ring-2 focus:ring-offset-2 rounded-lg"
                  style={{ animationDelay: `${index * 80}ms`, '--tw-ring-color': role.color } as React.CSSProperties}
                >
                  <div
                    className="bg-white rounded-lg border-2 h-full flex flex-col transition-all duration-200 hover:shadow-lg hover:-translate-y-1 overflow-hidden"
                    style={{ borderColor: isHovered ? role.color : '#DCE3EA' }}
                  >
                    {/* Card header */}
                    <div className="p-5 pb-0 flex items-start gap-4">
                      <div
                        className="w-12 h-12 rounded-lg flex items-center justify-center flex-shrink-0 transition-transform duration-200 group-hover:scale-110"
                        style={{ backgroundColor: role.bgColor }}
                      >
                        <Icon className="w-6 h-6" style={{ color: role.color }} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <h3 className="text-base font-bold text-[#16212E] leading-tight">{role.title}</h3>
                          <span className="text-[9px] font-bold px-1.5 py-0.5 rounded-full" style={{ backgroundColor: role.bgColor, color: role.color }}>
                            {role.toolCount} tools
                          </span>
                        </div>
                        <p className="text-xs font-semibold mt-0.5" style={{ color: role.color }}>{role.subtitle}</p>
                      </div>
                    </div>

                    {/* Description */}
                    <p className="text-xs text-[#4A5B6E] leading-relaxed px-5 pt-3 flex-1">{role.description}</p>

                    {/* What you'll see */}
                    <div className="px-5 pt-3 pb-1">
                      <div className="text-[10px] font-bold text-[#9AA4B3] uppercase tracking-wider mb-1.5">What you&apos;ll see</div>
                      <div className="space-y-1">
                        {role.features.slice(0, 4).map((f) => (
                          <div key={f} className="flex items-center gap-1.5 text-[11px] text-[#4A5B6E]">
                            <div className="w-1 h-1 rounded-full flex-shrink-0" style={{ backgroundColor: role.color }} />
                            {f}
                          </div>
                        ))}
                        {role.features.length > 4 && (
                          <div className="text-[10px] font-semibold" style={{ color: role.color }}>
                            +{role.features.length - 4} more
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Tags */}
                    <div className="flex flex-wrap gap-1.5 px-5 pt-3">
                      {role.tags.map((tag) => (
                        <span
                          key={tag}
                          className="text-[10px] font-semibold px-2 py-0.5 rounded-full"
                          style={{ backgroundColor: role.bgColor, color: role.color }}
                        >
                          {tag}
                        </span>
                      ))}
                    </div>

                    {/* CTA */}
                    <div
                      className="mx-5 mt-4 mb-5 py-2.5 rounded-md flex items-center justify-center gap-2 text-xs font-bold text-white transition-all group-hover:shadow-md"
                      style={{ backgroundColor: role.color }}
                    >
                      <span>Enter {role.title} Portal</span>
                      <ArrowRight className="w-3.5 h-3.5 transition-transform group-hover:translate-x-1" />
                    </div>
                  </div>
                </a>
              );
            })}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-[#DCE3EA] bg-white py-5 px-6">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-[#4A5B6E]">
          <div className="flex items-center gap-2">
            <Landmark className="w-3.5 h-3.5" />
            <span>Bhoomi Dhrishti &bull; Department of Land Resources (DoLR), Ministry of Rural Development</span>
          </div>
          <div className="flex items-center gap-4 text-[11px]">
            <span className="font-mono">SIH 2026 &bull; PS-26014</span>
            <span>&bull;</span>
            <span>Keycloak OIDC Protected</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
