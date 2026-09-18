# ✅ Bhoomi Dhrishti - Demo Validation Checklist

**For SIH 2026 Final Presentation**  
**Date**: September 15, 2026  
**Status**: Ready for validation after Docker startup

---

## 📋 Pre-Demo Setup (15 Minutes Before)

### Infrastructure
- [ ] Docker Desktop is running
- [ ] All environment variables set in `.env`
- [ ] Network connectivity verified
- [ ] Display/projector tested
- [ ] Backup laptop ready (if available)
- [ ] Recorded demo video ready (fallback)

### System Startup
- [ ] Ran `.\start-demo.ps1` or `docker-compose up -d`
- [ ] Waited 3-4 minutes for services to initialize
- [ ] Ran `docker-compose ps` - all services show "Up"
- [ ] Ran `.\seed-demo-data.ps1` or generated data manually
- [ ] Verified 350 parcels created

### Service Health Checks
- [ ] API Gateway: http://localhost:8000/health returns `{"status": "healthy"}`
- [ ] Officer Console: http://localhost:3000/officer loads
- [ ] Citizen Portal: http://localhost:3000/citizen loads
- [ ] Admin Console: http://localhost:3000/admin loads
- [ ] API Docs: http://localhost:8000/docs displays Swagger UI

---

## 🎬 Demo Flow Validation (5-Minute Run-Through)

### 0:00-0:15 | Opening Visual (Auto-Play)
- [ ] Visit http://localhost:3000/officer
- [ ] Auto-play conflict demo appears (two panels)
- [ ] Left panel shows: Revenue data (Raman, 1.2 acres)
- [ ] Right panel shows: SRO data (Kumar, 1.4 acres)
- [ ] Bottom panel shows: Unified resolved view
- [ ] Provenance tags visible ("As per Revenue Dept...")
- [ ] Animation smooth, no glitches

**If fails**: Have screenshot ready, explain the concept verbally

### 0:15-0:45 | Problem Statement
- [ ] Can clearly articulate 3 problems:
  - Constitutional fragmentation
  - Presumptive title
  - Legacy data quality
- [ ] Reference docs/ARCHITECTURE.md for details

### 0:45-1:05 | Solution Statement
- [ ] State: "Federated interoperability layer"
- [ ] Mention: "ISO 19152 LADM - India's first"
- [ ] Highlight: "Spatial-first entity resolution"
- [ ] State metrics: "F1: 0.89 rural, 0.85 urban"

### 1:05-4:00 | Live Demo (9 Features)

#### Feature 1: Map View (15 seconds)
- [ ] Map displays with 350 parcels
- [ ] Parcels colored by land use (green=agri, yellow=residential)
- [ ] Can zoom in/out smoothly
- [ ] Click on any parcel opens detail sheet

**Test**: Click on parcel in Tirunelveli area

#### Feature 2: Parcel Detail with Provenance (15 seconds)
- [ ] Detail sheet opens on right side
- [ ] 6 tabs visible: Overview, Rights, Transactions, Encumbrance, Conflicts, History
- [ ] **Overview tab** shows:
  - ULPIN (14-char)
  - Area (native + SI units)
  - Land class
  - Title confidence dial (0-100)
- [ ] Provenance tag shows: "As per Revenue Dept. Tamil Nadu, updated [date]"

**Test**: Verify provenance tag is never bare ownership

#### Feature 3: Conflicts Tab (20 seconds)
- [ ] Click "Conflicts" tab
- [ ] Shows detected conflicts list
- [ ] Select conflict showing 35% area mismatch
- [ ] Evidence displayed:
  - Revenue: 1.2 acres
  - SRO: 1.4 acres
  - Confidence: 0.95
- [ ] Recommended action shown
- [ ] "Assign for review" button visible

**Test**: Click through at least one conflict

#### Feature 4: Review Queue (20 seconds)
- [ ] Navigate to /review-queue (or click link)
- [ ] Table shows pending entity resolution matches
- [ ] Each row has:
  - Source A details
  - Source B details
  - Evidence (IoU=0.82, name_similarity=0.89, area_ratio=0.94)
  - Approve/Reject buttons
- [ ] Click "Approve" on one review (test interaction)

**Test**: Verify evidence scores display

#### Feature 5: Anomalies Dashboard (20 seconds)
- [ ] Navigate to /anomalies
- [ ] List shows ML-detected anomalies ranked by severity
- [ ] Click on one anomaly
- [ ] Detail shows:
  - Parcel ID
  - Anomaly type
  - Score (0-1)
  - Reason text: "Area CV 0.45 across 3 sources..."
  - Top contributing features
- [ ] Severity color-coded (red=HIGH, amber=MEDIUM, green=LOW)

**Test**: Verify reason text is human-readable

#### Feature 6: Graph Fraud Detection (20 seconds)
- [ ] Navigate to /graph or anomalies page
- [ ] Shows circular transaction ring detected
- [ ] 4 parties in chain: A→B→C→D→A
- [ ] All transaction details visible
- [ ] Network visualization (if implemented)

**Test**: Verify circular chain of 4 parties

#### Feature 7: Parcel Lineage Timeline (15 seconds)
- [ ] Back to parcel detail, click "History" tab
- [ ] TimeSlider component visible
- [ ] Shows parcel subdivision events
- [ ] Can scrub timeline to see ULPIN changes
- [ ] Old survey numbers preserved as aliases

**Test**: Move slider, verify animation

#### Feature 8: Citizen PWA (Mobile View) (20 seconds)
- [ ] Open http://localhost:3000/citizen (or resize browser to mobile)
- [ ] Search bar prominent
- [ ] Enter ULPIN or survey number
- [ ] Results show with blurred ownership (tiered disclosure)
- [ ] Login with citizen@example.com / demo123
- [ ] "My Parcels" shows owned parcels
- [ ] Click "Who Accessed My Land"
- [ ] Shows audit log: Officer | Date | Purpose

**Test**: Verify blur overlay for unauthenticated users

#### Feature 9: Admin Console - State Onboarding (20 seconds)
- [ ] Open http://localhost:3000/admin
- [ ] Login with admin@bhoomi.gov.in / demo123
- [ ] Dashboard shows Tamil Nadu (ACTIVE), Chandigarh (ACTIVE)
- [ ] Click "Add New State" or navigate to onboarding
- [ ] 4-step wizard visible:
  1. Upload source file
  2. Preview field mappings
  3. Validate data quality
  4. Confirm ingest
- [ ] Progress bar shows steps
- [ ] Timer shows "New state onboarded in 4 minutes"

**Test**: Click through wizard steps (don't submit)

### 4:00-5:00 | Technical Depth & Differentiators

#### Key Metrics to State
- [ ] "Entity resolution F1: 0.89 rural, 0.85 urban"
- [ ] "Measured against known ground truth"
- [ ] "350 parcels, 7 departmental sources"
- [ ] "47 conflicts detected, 12 anomalies scored"
- [ ] "1 circular transaction ring found"

#### Differentiators to Emphasize
- [ ] **ISO 19152 LADM**: "India's first implementation with country profile"
- [ ] **Provenance Everywhere**: "Every field carries source, department, as-of date"
- [ ] **Spatial-First Matching**: "Geometry IoU as strongest signal"
- [ ] **Unsupervised ML**: "Isolation Forest, NetworkX - no labels needed"
- [ ] **Honest Limitations**: "LIMITATIONS.md states constraints upfront"
- [ ] **One-Command Demo**: "`make demo` = ready in 3 minutes"

---

## 🎤 Judge Q&A Validation (10 Questions)

### Question 1: "How is this different from DILRMP?"
- [ ] Answer ready: "DILRMP digitizes and links. We add standards layer (ISO 19152) + analytics on disagreements between linked records"
- [ ] Reference: docs/DEMO_NARRATIVE.md

### Question 2: "Why would states adopt this?"
- [ ] Answer ready: "Federated - states keep data and authority. Get value back: revenue leakage detection, conflict queues, planning analytics"

### Question 3: "Where does the data come from?"
- [ ] Answer ready: "For demo: synthetic data (no real PII). For production: reference adapters + conformance suite that states implement"

### Question 4: "How accurate is fraud detection?"
- [ ] Answer ready: "We don't claim fraud detection. Unsupervised anomaly surfacing only. Labels don't exist publicly. Report F1 for entity resolution: 0.89"

### Question 5: "Can you detect unauthorized construction?"
- [ ] Answer ready: "Land-use change, not individual buildings. Sentinel-2 is 10m resolution = 100 sq_m per pixel. Good for agri→non-agri conversion, not house detection"

### Question 6: "What about apartments?"
- [ ] Answer ready: "ISO 19152 BAUnit model. One spatial unit, many Basic Administrative Units. Demo: 40-unit apartment with 3D extrusion"

### Question 7: "Cadastral maps don't line up with imagery?"
- [ ] Answer ready: "Correct. Legacy maps not geodetically accurate. We store accuracy classes, flag offsets >20m for resurvey, never claim precision source can't support"

### Question 8: "Can this scale to all of India?"
- [ ] Answer ready: "Federated topology scales horizontally. Per-state partition. Central index holds identity only, not records. Capacity projection in docs/ARCHITECTURE.md"

### Question 9: "Why not blockchain?"
- [ ] Answer ready: "Append-only audit log sufficient. Blockchain adds complexity. Land records must be correctable (surveys get revised, errors rectified by court order)"

### Question 10: "What doesn't work yet?"
- [ ] Answer ready: "See LIMITATIONS.md - presumptive title means no title guarantees, 10m satellite resolution, unsupervised ML only, no labeled fraud data, encumbrance completeness caveats"
- [ ] Emphasize: "Naming limitations upfront is strongest credibility signal"

---

## 📊 Metrics Verification

### Entity Resolution
- [ ] Run: `curl http://localhost:8000/resolution/metrics | jq`
- [ ] Verify output shows:
  ```json
  {
    "overall_f1": 0.89,
    "rural_f1": 0.89,
    "urban_f1": 0.85,
    "precision": 0.92,
    "recall": 0.86
  }
  ```

### Anomaly Detection
- [ ] Run: `curl http://localhost:8000/anomalies/summary | jq`
- [ ] Verify shows: 12 anomalies total
- [ ] By severity: HIGH=3, MEDIUM=6, LOW=3

### Graph Fraud
- [ ] Run: `curl http://localhost:8000/graph/circular-chains?state=TN | jq`
- [ ] Verify shows: 1 circular chain with 4 parties

### Spatial Conflicts
- [ ] Run: `curl http://localhost:8000/ml-inference/spatial-conflicts?state=TN | jq`
- [ ] Verify shows: Overlapping parcels, area mismatches detected

---

## 🎥 Backup Plan (If Live Demo Fails)

### Option A: Screenshots
- [ ] Pre-captured screenshots of all 9 features in `/demo-screenshots/`
- [ ] Can show on slides while narrating

### Option B: Recorded Video
- [ ] 5-minute video of full demo flow
- [ ] Stored at: `/demo-video/bhoomi-dhrishti-demo.mp4`
- [ ] Test video playback before presentation

### Option C: Code Walkthrough
- [ ] Show key files:
  - `services/parcel-identity/app/resolution/cascade.py` (entity resolution)
  - `services/trust-engine/app/modules/anomaly.py` (ML)
  - `frontend/apps/officer/app/page.tsx` (auto-play demo)
- [ ] Explain architecture from docs/ARCHITECTURE.md
- [ ] Show F1 evaluation code in `services/parcel-identity/app/evaluation/`

---

## 🔍 Final Pre-Demo Checks (5 Minutes Before)

### System Status
```powershell
# All commands should succeed
docker-compose ps                                    # All "Up"
curl http://localhost:8000/health                   # {"status": "healthy"}
curl http://localhost:3000/officer                  # HTML returned
curl http://localhost:8000/resolution/metrics       # F1 scores
curl http://localhost:8000/anomalies/summary        # 12 anomalies
curl http://localhost:8000/graph/circular-chains    # 1 chain
```

### Browser Tabs Open
- [ ] Tab 1: http://localhost:3000/officer (main demo)
- [ ] Tab 2: http://localhost:3000/citizen (citizen flow)
- [ ] Tab 3: http://localhost:3000/admin (admin onboarding)
- [ ] Tab 4: http://localhost:8000/docs (API reference)
- [ ] Tab 5: docs/DEMO_NARRATIVE.md (Q&A cheat sheet)

### Materials Ready
- [ ] Laptop fully charged
- [ ] Projector tested and working
- [ ] Audio working (if using video)
- [ ] Backup USB with code + docs
- [ ] Printed QUICK_START.md (judges' reference)
- [ ] Business cards / contact info

---

## 📝 Post-Demo Debrief

### What Worked Well
- [ ] Which demo features got positive reactions?
- [ ] Which metrics impressed judges?
- [ ] Which differentiators resonated?

### What to Improve
- [ ] Questions we couldn't answer?
- [ ] Features that didn't work smoothly?
- [ ] Explanations that were unclear?

### Judge Feedback
- [ ] Technical depth assessment?
- [ ] Scalability concerns?
- [ ] Suggestions for improvement?

---

## 🏆 Success Criteria

### Minimum (Pass)
- [ ] All 9 demo features shown (live or video)
- [ ] F1 scores stated (0.89/0.85)
- [ ] ISO 19152 mentioned
- [ ] All 10 questions answered

### Target (Good)
- [ ] Live demo worked smoothly
- [ ] Technical depth impressed judges
- [ ] No major questions unanswered
- [ ] Limitations acknowledged proactively

### Excellent (Outstanding)
- [ ] Judges asked to see code
- [ ] Requested architecture details
- [ ] Asked about production deployment
- [ ] Expressed interest in collaboration

---

## 📞 Emergency Contacts (During Demo)

**If system crashes:**
1. Switch to backup laptop (if available)
2. Switch to recorded video
3. Switch to screenshot walkthrough
4. Explain architecture verbally with docs

**If questions stump you:**
1. Acknowledge: "Great question"
2. Reference: "Detailed in our ARCHITECTURE.md"
3. Offer: "Happy to discuss after presentation"
4. Never: Fake an answer or overstate capabilities

---

## ✅ Final Go/No-Go Checklist

### GO Criteria (All Must Be True)
- [ ] Docker Desktop running
- [ ] All 16 services "Up" in `docker-compose ps`
- [ ] Officer console loads and shows map
- [ ] At least 1 parcel clickable with detail
- [ ] API health checks pass
- [ ] Demo script rehearsed at least once

### NO-GO Criteria (Any Triggers Backup Plan)
- [ ] Services won't start after 5 minutes
- [ ] Database connection fails
- [ ] Frontend shows errors
- [ ] Map won't render
- [ ] Less than 50% of features working

**If NO-GO**: Switch to recorded video + code walkthrough immediately

---

## 🎓 Remember

1. **Be honest about limitations** - It's your strongest credibility signal
2. **Show, don't tell** - Live demo > slides
3. **State metrics** - F1 0.89 is measurable, verifiable
4. **Reference standards** - ISO 19152 is external validation
5. **Acknowledge judges' expertise** - They know the domain
6. **Stay calm if demo fails** - Backup plans exist for a reason

---

## 🚀 You're Ready!

**All documentation complete:**
- ✅ 297 files of production code
- ✅ 30,000+ words of documentation
- ✅ 5-minute demo script
- ✅ 10 judge Q&A prepared
- ✅ Backup plans in place

**Go present with confidence!** 🇮🇳

---

**Last Updated**: September 15, 2026  
**Next Review**: 15 minutes before presentation  
**Status**: READY ✅
