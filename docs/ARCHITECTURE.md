# BHOOMI DHRISHTI (भूमि दृष्टि) — Master System Architecture Flow
## Federated GIS-based Digital Public Infrastructure (DPI) for Unified Indian Land Governance
### Smart India Hackathon (SIH 2026) · Problem Statement ID: 26014
### Ministry of Rural Development / Department of Land Resources (DoLR)

---

## 💡 Core Architectural Metaphor
> **“साफ पाइप से शुद्ध पानी” (*Clean Water Through a Clean Pipe*)**  
> Fragmented, unverified land records from 28 States enter our **X-Road + Modular Factory Pattern (MFP) Interoperability Pipe**, pass through **ISO 19152 Standardization & Spatial-Graph Analytics**, and emerge as **Cryptographically Verified Canonical Land Data** delivering **Spatial Layers, Base Layers, and a Unique Parcel Identity (ULPIN)**.

---

## 🗺️ Master Architecture Flow Diagram

> **High-Resolution Slide Image:** [Bhoomi_Dhrishti_Whiteboard_Architecture.jpg](file:///d:/Bhoomi%20Dhrishti/Bhoomi_Dhrishti_Whiteboard_Architecture.jpg)  
> *(Also saved at [Bhoomi_Dhrishti_Architecture_Flow.jpg](file:///d:/Bhoomi%20Dhrishti/Bhoomi_Dhrishti_Architecture_Flow.jpg))*

```
ARCHITECTURE FLOW:

  ┌──────────────────┐      ┌─────────────────────────────────────────────────────┐      ┌───────────────────────────────────────────────────┐
  │       USER       │      │   Multiple State  ──►  Data Search  ──►  Land Class.│      │           Interoperability Layer (X-Road)         │
  │ (Central, State, │ ───► │  [28 States APIs]    [Federated Query]  [RoR, SRO]  │ ───► │   X-Road Transport  ──►  Modular Factory Pattern  │
  │  Citizen) / RBAC │      │                     STATE LEVEL                     │      │   [mTLS 1.3 / P2P]       [Dynamic State Adapters] │
  │   [Keycloak 24]  │      └─────────────────────────────────────────────────────┘      │              DATA LEVEL (Transport)               │
  └──────────────────┘                                                                   └─────────────────────────┬─────────────────────────┘
                                                                                                                   │
  ┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────┴─────────────────────────┐
  │                                                         ANALYTICS LAYER                                                                  │
  │                                                                                                                                          │
  │  Versioning &  ◄──  Cross-Record    ◄──  Meta-Data &   ◄──(High)──  Confidence  ◄──  Rule & Spatial  ◄──   Data           ◄──  Schema    │
  │  Meta-Data          Reconciliation       Provenance                   Score          Validation            Standardization     Mapping   │
  │                     [GraphRAG/Neo4j]     [(ISO 19152)]                (0–100)        [PostGIS/GEOS]        [ISO 19152/LGD]     [Laya +   │
  │      │                                                                  │                                                       Cython]  │
  └──────┼──────────────────────────────────────────────────────────────────┼───────────────────────────────────────────────────────────▲────┘
         │                                                                  │ (Low)                                                     │
         │                                                                  ▼                                                           │
         │                                                       ┌─────────────────────┐             Feedback Learning 🔄               │
         │                                                       │  Human-In-The-Loop  │ ───────────────────────────────────────────────┘
         │                                                       └─────────────────────┘
         ▼
  ┌───────────────────────────────────────────────────────────────┐      ┌───────────────────────────────────────────────────────────────────┐
  │ Audit Event & Secure Repository                               │      │                                             ┌─► 1. Spatial Layers │
  │                                                               │      │                                             │   [OpenLayers /     │
  │  Data Hashing  ──►     Database      ──►  Integration Layer   │ ───► │   Cloud   ──►  Interactive Layer ───────────┤    GeoServer]       │
  │   [SHA 256]        [PostgreSQL +         [DILRMP, NGDRS, GIS] │      │   [NIC]        [MapLibre / Next.js]         ├─► 2. Base Layers    │
  │                     PostGIS]                                  │      │                                             │   [Cadastral + RoR] │
  │                        CANONICAL DATA                         │      │                                             └─► 3. Unique Parcel  │
  └───────────────────────────────────────────────────────────────┘      │                   OUTCOME                       [ULPIN Bhu-Aadhaar│
                                                                         └───────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Complete Node-by-Node Tech Stack Breakdown

### 1. Entry Point: `USER (RBAC)`
| Component | Role in Flow | Tech Stack (Red Label) |
|---|---|---|
| **Role-Based Access Control (RBAC)** | Authenticates Central Officials, State Revenue Officers (Tehsildars/SROs), Banks, and Citizens with purpose-bound permissions. | `Keycloak 24` · `OAuth 2.0 / OIDC` · `DEPA Consent` |

---

### 2. Block 1: `STATE LEVEL` (Multi-State Discovery & Classification)
| Sub-Component | Role in Flow | Tech Stack (Red Label) |
|---|---|---|
| **Multiple State** | Connects to sovereign state portals without moving or centralizing their master databases. | `28 States APIs` · `FastAPI Async` |
| **Data Search** | Executes parallel, non-blocking queries across departmental silos for the requested parcel. | `Federated Query` · `GraphQL / REST` |
| **Land Classification** | Identifies record categories across Revenue, Registration, Cadastral Survey, and Municipal rolls. | `RoR, SRO, Survey` · `JSONSchema` |

---

### 3. Block 2: `DATA LEVEL (Transport)` — `Interoperability Layer (X-Road)`
| Sub-Component | Role in Flow | Tech Stack (Red Label) |
|---|---|---|
| **X-Road Transport** | Establishes encrypted, peer-to-peer tunnels between State Security Servers with dual digital signatures. | `mTLS 1.3 / P2P` · `X.509 PKI` |
| **Modular Factory Pattern (MFP)** | Dynamically instantiates the exact State Adapter class (`StateAdapterFactory.create("TN")`, `create("UP")`) at runtime—enabling zero-code plug-and-play onboarding of new states. | `Dynamic State Adapters` · `Python Factory Pattern` |

---

### 4. Block 3 & 4: `DATA STANDARDIZATION` & `ANALYTICS LAYER` (Middle Serpentine Row)
| Sub-Component | Role in Flow | Tech Stack (Red Label) |
|---|---|---|
| **Schema Mapping (Two-Phase)** | **Phase 1 (Onboard):** AI maps local vernacular fields (*Patta, 7/12, Khatauni*) with officer approval.<br/>**Phase 2 (Runtime):** Compiles into frozen Cython code executing in $<80\,\mu\text{s}$ with **0% AI hallucination**. | `Laya / Bhashini + Cython` · `Pydantic V2` |
| **Data Standardization** | Translates state-specific legal terms into the **ISO 19152 LADM India Profile** and converts regional units (*Bigha, Guntha, Cent*) into standard square meters ($\text{m}^2$). | `ISO 19152 LADM / LGD` |
| **Rule & Spatial Validation** | Validates polygon geometry closure (`ST_IsValid`), detects boundary overlaps, and catches the **35% textual vs. spatial area mismatch** (`ST_Area` vs. RoR area). | `PostGIS / GEOS` · `Shapely` |
| **Confidence Score (0–100)** | Deterministic 6-axis `ConsistencyVector` scoring ownership continuity, area match, bank liens, and court stays.<br/>• **Low Score ($<75$):** Routes to **Human-In-The-Loop** (*Tehsildar Console*) with **Feedback Learning 🔄**.<br/>• **High Score ($\ge 75$):** Advances to Provenance & Cross-Record Reconciliation. | `6-Axis ConsistencyVector` |
| **Meta-Data & Provenance** | Wraps every attribute with its issuing department, timestamp, and cryptographic signature (preserving *Presumptive Title* honesty). | `(ISO 19152)` · `Sec 65B IEA` |
| **Cross-Record Reconciliation** | Links 4–6 disparate departmental IDs (*Khasra No., Deed No., Tax PID, Plot No.*) into a single unified parcel graph. | `GraphRAG / Neo4j` · `NetworkX` |
| **Versioning & Meta-Data** | Maintains bitemporal history of mutations, sub-divisions, and ownership transfers. | `Temporal Event Sourcing` |

---

### 5. Block 5: `CANONICAL DATA` (Audit Event & Secure Repository)
| Sub-Component | Role in Flow | Tech Stack (Red Label) |
|---|---|---|
| **Data Hashing** | Generates tamper-evident cryptographic hash chains for every reconciled state snapshot and audit event. | `SHA 256` · `Merkle DAG` |
| **Database** | Stores the materialized ISO 19152 canonical classes (`LA_Party`, `LA_RRR`, `LA_BAUnit`, `LA_SpatialUnit`) and spatial geometries. | `PostgreSQL 16 + PostGIS 3.4` · `Redis 7` |
| **Integration Layer** | Bi-directional API bridge linking national land and governance ecosystems. | `DILRMP, NGDRS, GIS` · `BhuNaksha` |

---

### 6. Block 6: `OUTCOME` (Sovereign Cloud & 3-Layer Delivery)
| Sub-Component | Role in Flow | Tech Stack (Red Label) |
|---|---|---|
| **Cloud** | Deployed on sovereign Government of India cloud infrastructure. | `NIC / MeghRaj` · `Docker / K8s` |
| **Interactive Layer** | Role-based consoles (Citizen Land Health Card PWA, Officer Split-Pane Discrepancy Inspector, Bank Loan Gateway). | `MapLibre / Next.js` · `Tailwind CSS` |
| **Output 1: Spatial Layers** | High-speed 60 FPS vector cadastral overlays, satellite NDVI/NDBI change layers, and zoning boundaries. | `OpenLayers / GeoServer` · `PostGIS MVT` |
| **Output 2: Base Layers** | Unified Cadastral + Record of Rights (RoR) + Registration Deeds + Encumbrance & Municipal Tax layers. | `Cadastral + RoR` · `ISO 19152 JSON` |
| **Output 3: Unique Parcel** | Every reconciled parcel is anchored to its 14-digit geocoordinate-derived national identifier. | `ULPIN (Bhu-Aadhaar)` |
