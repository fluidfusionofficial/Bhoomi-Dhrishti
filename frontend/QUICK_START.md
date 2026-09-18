# Quick Start Guide

## 1. Install Dependencies

```bash
cd frontend
pnpm install
```

If you don't have pnpm:
```bash
npm install -g pnpm@9
```

## 2. Environment Setup

Each app needs a `.env.local` file. Start with the officer app:

```bash
cd apps/officer
cp .env.local.example .env.local
```

Edit `.env.local` and update:
- `NEXT_PUBLIC_MAPTILER_KEY` - Get free key from https://www.maptiler.com/
- Other URLs can stay as localhost defaults for development

Repeat for citizen and admin apps if needed.

## 3. Run Development Servers

From the `frontend/` directory:

```bash
# Run all three apps simultaneously
pnpm dev

# Or run individually:
pnpm dev:officer    # http://localhost:3001
pnpm dev:citizen    # http://localhost:3002  
pnpm dev:admin      # http://localhost:3003
```

## 4. View the Apps

### Officer Console (Primary Demo)
**URL**: http://localhost:3001

**What you'll see**:
1. Automatic 5-second conflict resolution demo on first load
2. Dashboard with summary cards
3. Full-screen map (requires MapTiler key)
4. Click "View Details" buttons to navigate

**Key routes**:
- `/` - Dashboard with demo
- `/review-queue` - Entity resolution table
- `/anomalies` - ML anomaly alerts

### Citizen PWA
**URL**: http://localhost:3002

**What you'll see**:
- Mobile-first interface (resize to 480px width)
- Search interface
- Language selector (EN/TA/HI)
- Tiered access demo

### Admin Console
**URL**: http://localhost:3003

**What you'll see**:
- State dashboard
- Tamil Nadu and Chandigarh cards
- Click "Add New State" for 4-step onboarding wizard

## 5. Explore the Demo Features

### Conflict Resolution Demo (Officer)
1. Open http://localhost:3001
2. Watch the automatic animation showing:
   - Revenue data vs SRO data side-by-side
   - Unified resolution view
3. Animation completes in 5 seconds

### Parcel Detail Sheet (Officer)
1. After demo, click any dashboard card
2. Or navigate to `/parcels/TN-33-0001-12345`
3. Explore 6 tabs: Overview, Rights, Transactions, Encumbrance, Conflicts, History

### Tiered Access (Citizen)
1. Open http://localhost:3002
2. Navigate to any parcel (e.g., `/parcels/TN-33-0001-12345`)
3. See blurred ownership section
4. "Login" button shows access requirement

### State Onboarding (Admin)
1. Open http://localhost:3003
2. Click "Add New State" card
3. Follow 4-step wizard: Upload → Preview → Validate → Ingest

## 6. Type Checking & Linting

```bash
# Check types across all apps
pnpm type-check

# Run linter
pnpm lint

# Format code
pnpm format
```

## 7. Build for Production

```bash
# Build all apps
pnpm build

# Build specific app
cd apps/officer && pnpm build
```

Built files go to `apps/*/. next/` directories.

## Troubleshooting

### "Map not loading"
- Check `NEXT_PUBLIC_MAPTILER_KEY` is set in `.env.local`
- Or use demo mode with basic basemap

### "Module not found" errors
- Run `pnpm install` again from root
- Clear cache: `rm -rf node_modules .next && pnpm install`

### "Port already in use"
- Change port in `package.json`: `"dev": "next dev -p 3005"`

### TypeScript errors
- Run `pnpm type-check` to see all errors
- Most errors are in stub pages that need backend integration

## Development Tips

1. **Hot Reload**: Changes auto-reload in development
2. **Component Library**: All components are in `packages/ui/src/components/`
3. **API Mocking**: Currently uses hardcoded data; replace with real API calls
4. **Map Tiles**: Will need backend tile server for production
5. **Auth**: Keycloak integration ready but requires backend setup

## Next Steps

1. ✅ Frontend is complete
2. 🔄 Connect to backend APIs (replace hardcoded data)
3. 🔄 Set up Keycloak realm and clients
4. 🔄 Configure tile server
5. 🔄 Add real data from Tamil Nadu/Chandigarh

## File Structure Quick Reference

```
frontend/
├── apps/
│   ├── officer/      ← Revenue officer console
│   ├── citizen/      ← Public citizen PWA
│   └── admin/        ← System admin dashboard
├── packages/
│   ├── ui/           ← Reusable components
│   ├── api-client/   ← API integration
│   ├── map/          ← Map components
│   └── types/        ← TypeScript types
└── README.md         ← Full documentation
```

## Getting Help

- **Full README**: `frontend/README.md`
- **Build Status**: `frontend/BUILD_COMPLETE.md`
- **Issues**: Check console for error messages
- **Logs**: Next.js terminal output shows helpful errors

---

**Ready to go!** Start with `pnpm install && pnpm dev` 🚀
