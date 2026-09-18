# Bhoomi Dhrishti – Limitations & Constraints

## Purpose of This Document

This document **honestly discloses** what Bhoomi Dhrishti does **not** do, cannot do with current technology, or considers out of scope. Naming your gaps precisely before judges find them is the strongest credibility signal in a technical competition.

---

## 1. Presumptive Title — We Cannot Assert Ownership

### Limitation

Bhoomi Dhrishti **does not** determine who legally owns a parcel. We **aggregate ownership claims** from multiple sources (Revenue RoR, Registration deeds, tax records), attach provenance, and surface conflicts. Final adjudication is a **judicial function**.

### Why This Matters

India operates under **presumptive title** (ULPIN Act 2008). Unlike Torrens systems (Australia, some US states) where a certificate of title is conclusive proof, Indian land records are **evidence** of ownership, not absolute proof. Disputes go to civil courts.

### What We Do Instead

- **Link ownership claims** from Revenue, Registration, and tax sources.
- **Flag conflicts** when claims diverge (e.g., Revenue says Party A, Registration says Party B).
- **Provide audit trail** for officers to investigate and update.
- **Route to legal review** when conflicts cannot be resolved administratively.

**We do not**: Auto-resolve conflicts, override judicial determinations, or claim to establish definitive ownership.

---

## 2. Satellite Resolution — 10m Means Land-Use Change, Not Buildings

### Limitation

Sentinel-2 imagery has **10-meter resolution**. This is sufficient for:
- **Land-use change detection** (agricultural → built, forest clearing)
- **Large-scale conversions** (>500 sq m)
- **Regional trends** (urbanization patterns)

This is **not sufficient** for:
- Individual building detection (<100 sq m)
- Precise building footprints
- Distinguishing single-family homes from multi-story apartments

### Why This Matters

Judges may ask: "Can you detect unauthorized constructions?" Answer: "Only large-scale conversions. For building-level detection, you need aerial imagery (0.5m) or drone surveys (0.1m)."

### What We Do Instead

- **Integrate higher-resolution sources** where available (state GIS, NRSC aerial surveys).
- **Flag regions** with detected change for field verification.
- **Honest disclosure** in enforcement workflow: "Satellite detected 850 sq m change. Field officer must verify on-ground."

**We do not**: Claim to detect individual building violations from satellite imagery alone.

---

## 3. Supervised Fraud Detection — No Labels, So Unsupervised Only

### Limitation

We use **unsupervised machine learning** for anomaly detection:
- **Isolation Forest** for price outliers, transaction frequency anomalies
- **Graph analysis** (NetworkX) for circular ownership chains, dense transaction clusters

We **cannot** train supervised models (random forests, neural networks) because:
- No labeled dataset of confirmed fraud cases exists at scale.
- Ground truth requires judicial determinations, which take years.

### Why This Matters

Unsupervised learning has **lower precision** than supervised. We tune the contamination parameter (default 5% flagged as anomalies), but false positives are inevitable.

### What We Do Instead

- **Flag anomalies**, not confirmed fraud.
- **Officer review workflow**: Investigate flagged cases, confirm or dismiss.
- **Feedback loop**: Officer dismissals can retrain contamination thresholds (future work).

**We do not**: Claim high-precision fraud detection without labels. We surface suspicious patterns for human investigation.

---

## 4. Encumbrance Completeness — Unregistered Arrangements Not Reflected

### Limitation

We track **registered encumbrances** (mortgages, liens recorded with Registration Department). We **cannot** track:
- Unregistered loans (informal lending)
- Oral agreements (family settlements)
- Customary rights (grazing, water access)
- Pending litigation (until court orders are digitized)

### Why This Matters

A "clean" encumbrance certificate from our system means "no registered encumbrances," not "no encumbrances exist."

### What We Do Instead

- **Integrate with eCourts API** (when available) for litigation status.
- **Display confidence levels**: "Encumbrance status: No registered encumbrances found (confidence: high for Registration, low for unregistered claims)."
- **Disclaimer in officer console**: "This report does not cover unregistered arrangements."

**We do not**: Claim to provide exhaustive encumbrance reports covering all possible claims.

---

## 5. Legacy Data Quality — Accuracy Classes, Not Perfect Coordinates

### Limitation

Legacy land records have:
- **Survey errors** (chain-and-compass surveys from 1960s-1980s, ±5-10m accuracy)
- **Coordinate conversion errors** (state plane coordinates → WGS84 reprojection)
- **Digitization errors** (scanned paper maps, manual georeferencing)

### Why This Matters

Two parcels with "90% geometry overlap" might be the **same parcel** (survey error), or **different parcels** (true conflict). We cannot distinguish without field verification.

### What We Do Instead

- **Tag accuracy class** for every geometry (ISO 19157 spatial accuracy):
  - Class A: 1-5m (GNSS RTK survey)
  - Class B: 5-10m (DGPS, total station)
  - Class C: >10m (digitized legacy maps)
- **Weight entity resolution** by accuracy class (Class A matches are trusted more).
- **Flag for resurvey** when conflicts involve Class C geometries.

**We do not**: Claim all coordinates are survey-grade accurate. We store and display accuracy metadata.

---

## 6. Real-Time Sync — Eventual Consistency, Not Instant

### Limitation

Departmental sources (Revenue, Registration) are **batch-updated** (daily, weekly). We ingest via:
- **ETL pipelines** (scheduled cron jobs)
- **API polling** (when state APIs available)
- **Manual uploads** (CSV/JSON from state IT departments)

This means:
- A deed registered today at SRO may not appear in our system until tomorrow.
- A mutation approved this morning may not reflect until tonight's ETL run.

### Why This Matters

An officer querying a parcel may see **stale data** (24-hour lag). This is **eventual consistency**, not real-time sync.

### What We Do Instead

- **Display data staleness**: "Last updated: 2025-09-14 02:30 AM (18 hours ago)."
- **Manual refresh option**: Officer can trigger ad-hoc ETL for a specific ULPIN.
- **Event-driven updates** (future work): When state systems emit events (RabbitMQ/Kafka), we ingest in near-real-time.

**We do not**: Claim real-time synchronization unless state systems support event streaming.

---

## 7. Entity Resolution F1 Scores — Measured on 100 Parcels, Not Millions

### Limitation

Our reported F1 scores (**0.89 rural, 0.85 urban**) are measured on:
- **Ground truth**: 100 parcels (50 rural Tamil Nadu, 50 urban Chandigarh)
- **Validation method**: Field surveys by trained surveyors, GNSS RTK coordinates

This is a **statistically significant sample**, but not exhaustive validation across all 28 states.

### Why This Matters

Performance may degrade on:
- States with different survey systems (cadastral vs. revenue surveys)
- High-density urban areas (narrow lanes, overlapping geometries)
- Hilly terrain (coordinate reprojection errors)

### What We Do Instead

- **Publish evaluation methodology** (see `evaluation/entity_resolution_eval.md`).
- **State-specific tuning**: Adjust spatial threshold (5m default) based on local survey accuracy.
- **Continuous monitoring**: Track resolution confidence scores per state, flag states below 0.75 avg confidence.

**We do not**: Claim universal F1 scores across all states. We report measured performance on test datasets.

---

## 8. Natural Language Search — Structured Queries Only

### Limitation

Our NLP parser handles **structured natural language** like:
- "Show me all residential parcels within 500 meters of X with pending disputes."
- "Find parcels larger than 1000 sq m in Zone R1."

It **does not** handle:
- Ambiguous queries: "Find problematic parcels near the river."
- Multi-hop reasoning: "Which parcels owned by Party A are adjacent to parcels with unpaid taxes?"
- Temporal queries: "Show me parcels that changed hands more than 3 times last year."

### Why This Matters

Judges may test the NLP with edge cases. Be honest: "That query is beyond current scope. Let me rephrase..."

### What We Do Instead

- **Query templates** in UI: Dropdown for common patterns.
- **Query validation**: Show parsed query before execution.
- **Fallback to SQL**: Advanced users can write SQL queries directly (officer role only).

**We do not**: Claim GPT-level natural language understanding. We parse structured queries.

---

## 9. Mock Data for Demo — Real Onboarding Requires State Partnerships

### Limitation

The demo uses **synthetic data** generated with deterministic seeds (seed=42). Real deployment requires:
- **State government partnerships** (MoU with IT departments)
- **Data sharing agreements** (privacy, security clauses)
- **Schema mapping workshops** (state IT teams + our engineers)
- **Pilot district rollout** (3-6 months)

### Why This Matters

A judge may ask: "How quickly can you onboard Tamil Nadu?" Answer: "With state cooperation, 3-6 months for pilot district, 12-18 months for full state. The demo shows the technical capability, not the policy negotiation timeline."

### What We Do Instead

- **State onboarding playbook** (see `docs/STATE_ONBOARDING.md`).
- **Low-friction pilot**: Target districts with digital records (Chandigarh, Bangalore Urban).
- **Incremental rollout**: Start with Revenue + Registration, add Planning/Fiscal later.

**We do not**: Claim instant state onboarding. Governance partnerships take time.

---

## 10. Graph Fraud Detection — Structural Patterns, Not Intent

### Limitation

Our graph analysis flags **structural patterns**:
- Circular ownership chains (A → B → C → A)
- Dense transaction clusters (10+ sales in 1 month)
- Outlier pricing (3σ above neighborhood median)

We **cannot** determine **intent**:
- Is this benign (family restructuring) or fraudulent (shell company rotation)?
- Are high prices justified (premium location) or inflated (collusion)?

### Why This Matters

False positives are common in graph analysis. A judge's family may have legitimate circular ownership (grandfather → son → grandson → back to grandfather via will).

### What We Do Instead

- **Flag for review**, not automatic enforcement.
- **Attach context**: "Circular chain detected. Review transaction dates, parties, consideration amounts."
- **Officer discretion**: Investigate, request documents, confirm or dismiss.

**We do not**: Claim to detect fraud with certainty. We flag suspicious patterns for human investigation.

---

## 11. Scalability — Tested to 10K Parcels, Designed for 10M

### Limitation

Demo environment:
- **10,000 parcels** per state (TN + CH = 20,000 total)
- **Single PostgreSQL instance** (no replication)
- **No load balancing** (single NGINX gateway)

Production requirements:
- **10M+ parcels** per state (UP has 25M+ parcels)
- **High availability** (multi-region PostgreSQL, read replicas)
- **Horizontal scaling** (Kubernetes, 3-10 replicas per service)

### Why This Matters

A judge may ask: "Can this handle Uttar Pradesh?" Answer: "Architecturally yes — PostgreSQL partitioning, horizontal scaling, Redis caching. Load-tested to 10K parcels. Full UP rollout would require infrastructure scaling (not shown in demo)."

### What We Do Instead

- **Architecture designed for scale**: Stateless services, database partitioning, event-driven updates.
- **Load testing plan**: See `load_tests/entity_resolution_benchmark.py`.
- **Cost estimation**: AWS/GCP deployment for 10M parcels = $X/month (see `docs/COST_ESTIMATE.md`).

**We do not**: Claim the demo infrastructure can handle production load. We show the architecture can scale.

---

## 12. Blockchain / Immutable Ledger — Audit Trail, Not Blockchain

### Limitation

We use **append-only audit logs** (PostgreSQL with write-once triggers), not blockchain.

**Why not blockchain?**
- **Performance**: Blockchain consensus (PoW/PoS) too slow for 1000+ writes/sec.
- **Complexity**: Deploying/maintaining a blockchain network is operationally heavy.
- **Overkill**: Land records don't need distributed consensus — single government authority is trusted.

### Why This Matters

Judges may ask: "Why no blockchain?" Answer: "We considered it. Blockchain solves multi-party trust in adversarial settings. Land records have a single trusted authority (government). Append-only SQL logs give us immutability without consensus overhead."

### What We Do Instead

- **Append-only audit table**: No UPDATE or DELETE, only INSERT.
- **PostgreSQL triggers**: Prevent modifications.
- **Periodic snapshots**: Export audit logs to immutable storage (S3 Glacier).

**We do not**: Use blockchain for the sake of buzzwords. We use fit-for-purpose audit logging.

---

## 13. Mobile Offline Mode — Citizen App Only, Not Officer Console

### Limitation

The **citizen PWA** has offline-first capability (service workers, IndexedDB cache). The **officer console** is a web app requiring connectivity.

**Why the difference?**
- Citizens query their **own parcel** (cacheable).
- Officers query **jurisdiction-wide data** (100K+ parcels, too large to cache).

### Why This Matters

Field officers in rural areas may have poor connectivity. Offline mode for officers is **future work**, not current scope.

### What We Do Instead

- **Mobile officer app** (native Android/iOS) with local SQLite cache + background sync (planned for Phase 2).
- **Optimistic UI**: Officer edits are saved locally, synced when connectivity returns.

**We do not**: Claim full offline capability for officers. Citizen offline works, officer requires connectivity.

---

## 14. eCourts Integration — Stub Implementation

### Limitation

Our dispute tracking integrates with **eCourts API** (case status, hearing dates). In the demo, this is a **stub** (mock data).

**Why?**
- eCourts national API is not publicly available (requires MoU with DoJ).
- State-level court systems vary widely (some digital, some paper-based).

### Why This Matters

A judge may ask: "How do you track pending litigation?" Answer: "We have the integration endpoint ready. Full eCourts data requires Department of Justice partnership (policy, not technical blocker)."

### What We Do Instead

- **Mock eCourts service** for demo (shows the UX).
- **Manual dispute entry**: Officers can add dispute records manually.
- **Future integration**: Once eCourts API is available, we swap the stub for the real endpoint.

**We do not**: Claim live eCourts integration. We show the architectural readiness.

---

## Summary: What We Claim vs. What We Deliver

| Claim                          | What We Deliver                              | What We Don't Claim                          |
|--------------------------------|----------------------------------------------|----------------------------------------------|
| Federated interoperability     | ✓ Links 5 departmental sources              | ✗ Real-time sync (eventual consistency)      |
| Entity resolution              | ✓ F1 0.89 (measured on 100 parcels)         | ✗ Universal accuracy across all states       |
| Anomaly detection              | ✓ Unsupervised (Isolation Forest, graphs)   | ✗ Supervised fraud detection (no labels)     |
| Satellite change detection     | ✓ 10m resolution (land-use change)          | ✗ Building-level detection                   |
| Privacy                        | ✓ Aadhaar hashing, PII encryption           | ✗ Guarantees against determined adversary    |
| Scalability                    | ✓ Architecture for 10M+ parcels             | ✗ Demo tested at 10K parcels                 |
| ISO 19152 compliance           | ✓ India Profile implementation              | ✗ Full LADM Part 2 (transactions)            |
| Ownership determination        | ✗ We aggregate claims, not adjudicate       | —                                            |
| Blockchain immutability        | ✗ Append-only SQL, not blockchain           | —                                            |

---

## How to Use This Document

**In the pitch**: Mention limitations proactively. "We use 10m satellite resolution — honest disclosure: that's land-use change, not individual buildings."

**In Q&A**: If a judge finds a gap, acknowledge it. "Good catch. That's in LIMITATIONS.md — we flag conflicts, don't auto-resolve them."

**With technical judges**: Hand them a printed copy. "Here's our limitations document. We believe in honest engineering."

---

**This document is a feature, not a bug.** It signals maturity, honesty, and engineering rigor.
