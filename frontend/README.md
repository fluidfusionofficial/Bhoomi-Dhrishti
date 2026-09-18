# Bhoomi Dhrishti Frontend Monorepo

Complete Next.js 14 frontend for the Bhoomi Dhrishti land governance platform.

## Architecture

Turborepo monorepo with 3 Next.js apps and 3 shared packages:

```
frontend/
├── apps/
│   ├── officer/          # Map-first officer console (port 3001)
│   ├── citizen/          # Mobile-first citizen PWA (port 3002)
│   └── admin/            # State onboarding admin console (port 3003)
├── packages/
│   ├── ui/               # shadcn-based design system
│   ├── api-client/       # Typed API client with Keycloak auth
│   ├── map/              # MapLibre GL JS wrapper components
│   └── types/            # Shared TypeScript types
├── package.json          # Workspace root
└── turbo.json            # Turborepo pipeline config
```

## Tech Stack

- **Framework**: Next.js 14 App Router, React 18, TypeScript (strict mode)
- **Styling**: Tailwind CSS 3
- **Components**: shadcn/ui (Radix UI primitives)
- **Maps**: MapLibre GL JS 4.0 + PMTiles
- **Auth**: Keycloak JS adapter (OIDC PKCE)
- **i18n**: i18next (English + Tamil + Hindi)
- **PWA**: next-pwa + Workbox
- **Build**: Turborepo, pnpm workspaces

## Quick Start

### Prerequisites

- Node.js 20+
- pnpm 9+

### Installation

```bash
cd frontend
pnpm install
```

### Development

Run all apps:
```bash
pnpm dev
```

Run specific app:
```bash
pnpm dev:officer   # http://localhost:3001
pnpm dev:citizen   # http://localhost:3002
pnpm dev:admin     # http://localhost:3003
```

### Build

```bash
pnpm build        # Build all apps
pnpm type-check   # TypeScript validation
pnpm lint         # ESLint
```

## Apps

### Officer Console (`apps/officer`)

**Purpose**: Map-centric console for revenue officers to manage parcels, resolve conflicts, and review ML anomalies.

**Key Features**:
- Full-screen map (80% width) with parcel layer colored by land use
- Dashboard with conflict/review/anomaly/mutation counts
- Opening demo: 5-second conflict resolution animation
- Parcel detail sheet with 6 tabs: Overview, Rights, Transactions, Encumbrance, Conflicts, History
- Review queue for entity resolution
- ML anomaly investigation
- Timeline slider for parcel lineage

**Demo Flow**:
1. Auto-play conflict split screen on load
2. Show Revenue vs SRO data side-by-side
3. Animate unified resolved view
4. Transition to interactive map

### Citizen PWA (`apps/citizen`)

**Purpose**: Mobile-first PWA for citizens to search and access their land records.

**Key Features**:
- Mobile-optimized (max-width 480px)
- Installable PWA with offline support
- Search by ULPIN, survey number, or map tap
- Tiered disclosure: blurred ownership for unauthenticated users
- Access log: "Who accessed my land" audit trail
- i18n: English/Tamil/Hindi selector
- Download RoR, check EC, file applications

**Offline Strategy**:
- Cache MapLibre base tiles (PMTiles)
- IndexedDB for recently viewed parcels
- Workbox service worker

### Admin Console (`apps/admin`)

**Purpose**: State onboarding and system administration.

**Key Features**:
- State dashboard with onboarding status
- 4-step onboarding wizard: Upload → Preview → Validate → Ingest
- Live YAML mapping editor with DQ report
- OGC conformance checklist
- Authority matrix (field-level authoritative source)
- "Onboard a new state in 4 minutes" demo

## Shared Packages

### `packages/ui`

Design system components:

**Base Components**:
- Button, Card, Badge, Dialog, Table, Tabs, Select, Sheet

**Bhoomi-Specific**:
- `ProvenanceTag`: Displays "As per {source}, {department}, as of {date}"
- `ConfidenceBadge`: 0-100 score pill (green ≥70, amber 40-69, red <40)
- `ConflictAlert`: Dismissible conflict warning
- `TieredAccess`: Blur/lock overlay based on auth tier

**Design Tokens** (`tokens.ts`):
- Primary: `#1B4F72` (Bhoomi blue)
- Accent: `#E67E22` (orange)
- Colourblind-safe land use palette (5 colors, Paul Tol scheme)

### `packages/api-client`

Typed API client with:

**Modules**:
- `parcels.ts`: fetchParcel, searchParcels, resolveByCoordinates, getLineage, getConflicts, getParcelRights, getTransactions, getEncumbrances
- `auth.ts`: Keycloak PKCE, useAuth hook, token management
- `tiles.ts`: TileJSON fetch, PMTiles URL builder
- `client.ts`: Base apiRequest function with error handling

**Features**:
- Bearer token injection
- Typed errors (ApiClientError)
- localStorage token persistence
- Auto-refresh tokens (60s interval)

### `packages/map`

MapLibre wrapper components (all SSR-safe with dynamic imports):

**Components**:
- `Map`: Base map with context provider
- `ParcelLayer`: Vector tile layer with land use colors
- `ConflictLayer`: Circle markers for conflicts (color by severity)
- `ZoneLayer`: Planning zones with colourblind palette
- `ParcelPopup`: Click handler with ULPIN, area, conflict count
- `ThreeDBuildings`: Fill-extrusion for apartment blocks (BAUnit demo)
- `TimeSlider`: Scrub parcel lineage timeline

**Hooks**:
- `useMap()`: Access map instance from children

## Environment Variables

Create `.env.local` in each app:

```bash
# API
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_TILE_URL=http://localhost:8000/api/v1/tiles

# Keycloak
NEXT_PUBLIC_KEYCLOAK_URL=http://localhost:8080
NEXT_PUBLIC_KEYCLOAK_REALM=bhoomi
NEXT_PUBLIC_KEYCLOAK_CLIENT_ID=bhoomi-officer

# MapLibre
NEXT_PUBLIC_MAPTILER_KEY=your_key_here
NEXT_PUBLIC_PMTILES_URL=http://localhost:8000/tiles/cadastral.pmtiles

# Feature flags
NEXT_PUBLIC_ENABLE_ML_SCORES=true
NEXT_PUBLIC_DEMO_MODE=true
```

## Code Quality Standards

✅ **TypeScript**: Strict mode, no `any`  
✅ **Styling**: Tailwind only, no inline styles  
✅ **SSR**: MapLibre in `dynamic(() => import(...), {ssr: false})`  
✅ **API**: All calls via `@bhoomi/api-client`, no raw fetch  
✅ **Components**: Reuse from `@bhoomi/ui` package  

## i18n

Namespaces: `common`, `parcel`, `officer`, `citizen`

Tamil font: `Noto Sans Tamil`

Example usage:
```tsx
import { useTranslation } from 'react-i18next';

const { t } = useTranslation('parcel');
<p>{t('ulpin')}</p>
```

## Key Demo Moments

1. **Officer Console Opening**: Auto-play conflict resolution (Revenue vs SRO → Unified)
2. **Citizen Tiered Disclosure**: Blurred ownership → Login to reveal
3. **Admin 4-Minute Onboarding**: Upload → Preview → Validate → Ingest progress bar
4. **3D Buildings**: Apartment block BAUnit demonstration
5. **Timeline Scrubber**: Parcel lineage over time

## File Structure

```
apps/officer/src/
├── app/
│   ├── page.tsx                    # Dashboard with demo
│   ├── parcels/[id]/page.tsx       # Parcel detail sheet
│   ├── review-queue/page.tsx       # Entity resolution
│   ├── anomalies/page.tsx          # ML alerts
│   └── mutations/page.tsx          # Pending mutations
└── components/
    ├── MapView.tsx                 # Main map component
    └── DemoConflictSplit.tsx       # Opening demo

apps/citizen/src/
├── app/
│   ├── page.tsx                    # Home with search
│   ├── search/page.tsx             # Search interface
│   └── parcels/[id]/page.tsx       # Tiered parcel view
└── public/
    └── manifest.json               # PWA manifest

apps/admin/src/
└── app/
    ├── page.tsx                    # State dashboard
    └── states/[stateId]/
        ├── onboard/page.tsx        # 4-step wizard
        └── mapping/page.tsx        # YAML editor
```

## Performance

- **Code splitting**: Dynamic imports for MapLibre
- **Caching**: Turborepo remote cache, Next.js ISR
- **Bundle size**: Tree-shaking, no unused Radix components
- **Offline**: Service worker with Workbox strategies

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 15+
- Edge 90+

PWA requires HTTPS in production.

## Deployment

```bash
# Build all apps
pnpm build

# Deploy to Vercel/Netlify (recommended)
# Or use Docker:
docker build -t bhoomi-officer ./apps/officer
docker build -t bhoomi-citizen ./apps/citizen
docker build -t bhoomi-admin ./apps/admin
```

## Troubleshooting

**MapLibre not rendering**:
- Ensure `dynamic` import with `ssr: false`
- Check `NEXT_PUBLIC_MAPTILER_KEY` is set
- Verify tile URL is accessible

**Keycloak auth fails**:
- Check realm and client ID match backend
- Ensure `silent-check-sso.html` exists in `/public`
- Verify CORS settings in Keycloak

**PWA not installing**:
- Must be served over HTTPS (use ngrok for local testing)
- Check `manifest.json` is valid
- Service worker must register successfully

## License

Part of Smart India Hackathon 2026 PS-26014 submission.
