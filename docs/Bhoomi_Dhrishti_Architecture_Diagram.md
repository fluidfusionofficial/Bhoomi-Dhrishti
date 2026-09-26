# BHOOMI DHRISHTI — Unified Architecture Diagram

### Federated GIS-based DPI for Land Governance
### SIH 2026 · PS-26014 · Ministry of Rural Development / DoLR

---

```
╔═══════════════════════════════════════════════════════════════════════╗
║                      BHOOMI DHRISHTI                                 ║
║       Federated GIS-based DPI for Land Governance                    ║
║              SIH 2026 · PS-26014 · DoLR                              ║
╚═══════════════════════════════════════════════════════════════════════╝


  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐
  │  CITIZEN   │  │  REVENUE   │  │   BANK /   │  │   STATE    │
  │   PWA      │  │  OFFICER   │  │   NBFC     │  │   ADMIN    │
  │            │  │  CONSOLE   │  │            │  │  CONSOLE   │
  │ Land Health│  │ Discrepancy│  │ Collateral │  │ Onboarding │
  │ Card, NL   │  │ Inspector, │  │ Verify,    │  │ Schema     │
  │ Query, Map │  │ Map, Queue │  │ KCC Loan   │  │ Mapper     │
  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘
        └───────────┬────┴───────────────┴────┬──────────┘
                    ▼                         ▼
 ┌─────────────────────────────────────────────────────────────────┐
 │   API GATEWAY · AUTH · CONSENT                                  │
 │   Keycloak 24 │ DEPA Purpose-Bound Tokens │ RBAC │ PII Masking │
 └────────────────────────────┬────────────────────────────────────┘
                              │
 ┌────────────────────────────┼────────────────────────────────────┐
 │                    APPLICATION CORE                              │
 │                                                                  │
 │  ┌─ SERVE ──────────┐  ┌─ SCORE ──────────┐  ┌─ RESOLVE ────┐ │
 │  │                   │  │                   │  │               │ │
 │  │ • Query/Search    │  │ • Trust Engine    │  │ • Entity      │ │
 │  │ • Geospatial/MVT  │  │   (5-axis score)  │  │   Resolution  │ │
 │  │ • Notifications   │  │ • Audit Trail     │  │   (5-stage    │ │
 │  │ • GraphRAG NL     │  │   (Merkle hash    │  │   cascade)    │ │
 │  │                   │  │   chain)           │  │               │ │
 │  └───────────────────┘  └───────────────────┘  └───────────────┘ │
 │                                                                  │
 │  ┌─ INTELLIGENCE & GOVERNANCE ──────────────────────────────┐   │
 │  │  Onboarding: System 1 AI (Laya / Jev / Bhashini Schema)  │   │
 │  │  Runtime: 100% Deterministic Rules & PostGIS (Zero Hallu)│   │
 │  │  Analytical: GraphRAG NL Query & Sentinel-2 Satellite    │   │
 │  └──────────────────────────────────────────────────────────┘   │
 └────────────────────────────┬────────────────────────────────────┘
                              │
 ╔════════════════════════════╧════════════════════════════════════╗
 ║   CANONICAL DATA STORE  (System of Engagement — NOT of Record) ║
 ║                                                                 ║
 ║   PostgreSQL 16         Neo4j / Neptune       Redis 7           ║
 ║   + PostGIS 3.4         Knowledge Graph       Cache             ║
 ║                                                                 ║
 ║   LADM India Profile:   Parcel─Owner─Dept     MVT tiles,       ║
 ║   Party → RRR →         edges with temporal    query results,   ║
 ║   BAUnit → SpatialUnit  event sourcing         OCSP responses   ║
 ║                                                                 ║
 ║   Every record wrapped in: source_dept │ signature │ timestamp  ║
 ╚════════════════════════════╤════════════════════════════════════╝
                              │
 ┌────────────────────────────┴────────────────────────────────────┐
 │             INTEROPERABILITY ENGINE                              │
 │                                                                  │
 │  ┌─ LAYER 3: SEMANTIC ─────────────────────────────────────┐   │
 │  │  LRES (Land Record Exchange Standard)                    │   │
 │  │  CodeSystems · ConceptMaps · State Profiles              │   │
 │  │  Patta=Khata=RoR=Jamabandi → TENURE-FREEHOLD-001        │   │
 │  │  Nanjai=Tari=Sona → LU_AGR_IRRIGATED                    │   │
 │  │  Taluk=Tehsil=Mandal=Block → SUB_DISTRICT               │   │
 │  │  Bigha(Bihar)≠Bigha(WB) → jurisdiction-aware sqm        │   │
 │  └──────────────────────────────────────────────────────────┘   │
 │  ┌─ LAYER 2: SYNTACTIC (TWO-PHASE COMPILER PATTERN) ──────┐   │
 │  │  [PHASE 1: ONBOARDING] (AI Human-in-the-Loop)            │   │
 │  │  State Schema ──► AI (Laya/Jev/Bhashini) ──► Approvals   │   │
 │  │                    │ Compiles into Immutable             │   │
 │  │                    ▼                                     │   │
 │  │  [PHASE 2: RUNTIME] (Pure Compiled Code)                 │   │
 │  │  Query ──► Frozen mapping.yaml / Cython ──► Clean LADM   │   │
 │  └──────────────────────────────────────────────────────────┘   │
 └────────────────────────────┬────────────────────────────────────┘
                              │
 ╔════════════════════════════╧════════════════════════════════════╗
 ║          LAND EXCHANGE MESH (LEM)                               ║
 ║          X-Road Architecture · Layer 1: Transport               ║
 ║                                                                 ║
 ║  ┌───────────────────────────────────────────────────────────┐  ║
 ║  │              BD CENTRAL  (config only, no data)           │  ║
 ║  │     Member Registry │ Trusted CAs │ TSAs │ LRES Distro   │  ║
 ║  └───────────────────────────┬───────────────────────────────┘  ║
 ║                              │                                  ║
 ║  ┌───────┐ ┌───────┐ ┌──────┴┐ ┌───────┐ ┌───────┐ ┌───────┐ ║
 ║  │FCN-TN │◄►│FCN-KA │◄►│FCN-MH│◄►│FCN-AP │◄►│FCN-WB │◄►│ ×36 │ ║
 ║  └───┬───┘ └───┬───┘ └───┬───┘ └───┬───┘ └───┬───┘ └───┬───┘ ║
 ║      │ ◄──── peer-to-peer · mutual TLS · dual-signed ────► │   ║
 ║      │         │         │         │         │         │        ║
 ║  Each FCN: Auth Cert + Signing Cert + Adapter + Message Log    ║
 ║  Conformance: 🥉 Bronze (read) → 🥈 Silver (events) → 🥇 Gold ║
 ╚════════╤═══════╤═════════╤═════════╤═════════╤═════════╤═══════╝
          │       │         │         │         │         │
          ▼       ▼         ▼         ▼         ▼         ▼
 ┌─────────────────────────────────────────────────────────────────┐
 │        STATE SYSTEMS  (Sovereign Systems of Record)             │
 │   Constitutional authority: 7th Schedule, List II, Entry 18/45  │
 │                                                                  │
 │   TNREGINET  Bhoomi/   MahaBhu-  MeeBhoomi  Banglar-  Bhulekh  │
 │   (TCS)      Kaveri    lekh/     /DHARANI   bhumi     Odisha   │
 │              (NIC)     iSarita   (AP)       (WB)      (NIC)    │
 │                        (NIC)                                     │
 │                                                                  │
 │          Data stays here. Always. Bhoomi Dhrishti queries,      │
 │          caches temporarily, NEVER asserts conclusive title.     │
 └─────────────────────────────────────────────────────────────────┘
```

---

## Layer Reference

| Layer | Technology Source | Role in Bhoomi Dhrishti |
|---|---|---|
| **Layer 3: SEMANTIC** | FHIR (HL7) pattern | LRES — translates *meaning* across 28 state vocabularies |
| **Layer 2: SYNTACTIC** | Two-Phase Compiler (Alt 4) | Phase 1: AI Onboarding (Laya/Jev/Bhashini) ──► Phase 2: Frozen YAML/Cython Runtime |
| **Layer 1: TRANSPORT** | X-Road (Estonia) | Secure *connectivity* — mutual TLS, dual signatures, P2P |

## 4-Stage Lifecycle Mapping

| Stage | What Happens | Where in Diagram |
|---|---|---|
| **INGEST** | FCN fetches raw data, Layer 1-2-3 transforms it | LEM + Interoperability Engine |
| **RESOLVE** | 5-stage cascade matches cross-dept records into unified parcels | Application Core (Resolve + Intelligence) |
| **SCORE** | ConsistencyVector computed, risk bands assigned, hash-chained | Application Core (Score) |
| **SERVE** | MVT tiles, search results, alerts delivered to consumers | Application Core (Serve) + Consumer Interfaces |

## PPT Reproduction Guide

| Section | Suggested Color | Shape |
|---|---|---|
| Consumer Interfaces (top) | Light blue `#DBEAFE` | 4 rounded rectangles |
| API Gateway / Auth | Dark navy `#1E3A5F` | Thin horizontal bar |
| Application Core | White with blue border `#3B82F6` | Grouped rectangles |
| Canonical Data Store | Light purple `#EDE9FE` | Rounded rectangle, double border |
| Interoperability Engine | Orange/amber `#FEF3C7` / `#F59E0B` | Two stacked rectangles (make this pop — it's the differentiator) |
| Land Exchange Mesh | Dark green `#065F46` | Rectangle with FCN nodes as small circles connected by lines |
| State Systems (bottom) | Grey `#F3F4F6` | Flat rectangle |
| Arrows between tiers | Dark grey `#4B5563` | Simple downward arrows |

## Callout Labels (right side of slide)

```
 ─── Layer 3: SEMANTIC (LRES)     ← "FHIR for Land Records"
 ─── Layer 2: SYNTACTIC (Two-Phase)← AI Onboarding ──► Frozen Runtime
 ─── Layer 1: TRANSPORT (X-Road)  ← Trust & connectivity
```

## Layer 2 Deep Dive: The Two-Phase Compiler Pattern (Alternative 4)

Bhoomi Dhrishti implements the **Two-Phase Architecture** to achieve zero-hallucination, sub-microsecond runtime execution while minimizing human developer effort during state onboarding.

```
PHASE 1: STATE ONBOARDING (ONE-TIME / HUMAN-IN-THE-LOOP)
[Messy State Schema] ──► [AI (Laya / Jev / Bhashini)] ──► Suggests Mappings ──► Officer Approves (Admin Console: 3003)
                                                                                  │
                                                          Compiles into Immutable │
                                                                                  ▼
PHASE 2: LIVE RUNTIME PIPELINE (PURE COMPILED CODE)
[Incoming Query] ──► [Frozen mapping.yaml / Cython / Pydantic] ──► Clean LADM (Microseconds!)
```

### Phase 1: State Onboarding (One-Time / Human-in-the-Loop)
1. **Schema Discovery**: When onboarding a new state or municipal department, the raw schema (CSV headers, database DDL, or API payload) is ingested into the State Admin Console (Port 3003).
2. **System 1 AI Inference (Laya / Jev / Bhashini)**:
   - Ultra-fast non-autoregressive decision models evaluate ambiguous vernacular column names (`kandaya_darara_hesaru` -> `party.name`).
   - Project Bhashini APIs map script transliteration rules (Tamil/Devanagari -> ISO 15919 Latin).
   - Generates a draft `mapping.yaml` in <2 seconds.
3. **Nodal Officer Review & Cryptographic Sign-Off**:
   - The State Nodal Officer reviews the AI-suggested mappings on the visual Schema Mapper UI.
   - The officer verifies metric conversion factors, approves edge cases, and clicks **"Verify & Approve"**.
4. **Compilation into Immutable Artifacts**:
   - The approved mapping is compiled into an immutable, frozen `mapping.yaml` and pre-compiled Pydantic / Cython parsers.
   - The compiled configuration is cryptographically signed with the state's administrative key and published to the local node.

### Phase 2: Live Runtime Pipeline (Pure Compiled Code)
1. **Zero Runtime AI Invocation**: Live queries from citizens, banks, or SROs **NEVER touch an AI model**.
2. **Deterministic Execution**:
   - Incoming payload is parsed directly through the frozen `mapping.yaml` and compiled Pydantic models.
   - Mathematical unit conversions (e.g. Bigha to square meters) execute via district-scoped LGD formulas with exact precision.
   - Date formats are coerced via deterministic strptime parsers (`DD/MM/YYYY -> ISO 8601`).
3. **Sub-Microsecond Latency**: The parsing overhead is <0.5 milliseconds per record, ensuring high-concurrency throughput without expensive GPU infrastructure.
4. **100% Legal Non-Repudiation**: Because runtime transformations are 100% deterministic and derived from a human-approved contract, every normalized output is legally admissible in revenue and civil courts.

## Tagline

> *"India digitized its land records. Nobody built the bridge between them. That bridge is Bhoomi Dhrishti."*
