# Bhoomi Dhrishti ML Intelligence Layer

Complete implementation of machine learning and spatial intelligence modules for land governance anomaly detection and analysis.

## Overview

The ML Intelligence Layer provides 5 core modules:

1. **Spatial Conflict Detection** - PostGIS-based geometric analysis
2. **Cross-Registry Inconsistency + Anomaly Detection** - Isolation Forest unsupervised ML
3. **Transaction Graph Analysis** - NetworkX-based pattern detection
4. **Satellite Change Detection** - Sentinel-2 NDVI/NDWI land-use monitoring
5. **Natural Language Query** - Template-based SQL generation

## Architecture

```
services/
├── ml-inference/          # Spatial conflicts & evaluation
│   ├── app/
│   │   ├── modules/
│   │   │   └── spatial_conflicts.py
│   │   └── evaluation/
│   │       └── metrics.py
│   └── requirements.txt
│
├── trust-engine/          # Anomaly detection & graph analysis
│   ├── app/
│   │   ├── modules/
│   │   │   ├── inconsistency.py
│   │   │   ├── anomaly.py
│   │   │   └── graph_analysis.py
│   │   └── routers/
│   │       ├── anomalies.py
│   │       └── graph.py
│   └── requirements.txt
│
├── satellite/             # Change detection
│   ├── app/
│   │   ├── modules/
│   │   │   └── change_detection.py
│   │   └── routers/
│   │       └── satellite.py
│   └── requirements.txt
│
└── analytics/             # NL query
    ├── app/
    │   ├── modules/
    │   │   └── nl_query.py
    │   └── routers/
    │       └── nl_query.py
    └── requirements.txt
```

---

## Module 1: Spatial Conflict Detection

**Location**: `services/ml-inference/app/modules/spatial_conflicts.py`

### Purpose
Deterministic PostGIS-based detection of geometric inconsistencies across parcel boundaries.

### Functions

#### `detect_overlapping_parcels(db, state_code, district_code, min_overlap_sq_m=1.0)`
- Uses `ST_Intersection` to find overlapping parcel geometries
- Computes Intersection over Union (IoU)
- Flags overlaps > 1 sq_m by default
- Returns `List[ConflictReport]`

#### `detect_gaps_slivers(db, state_code, district_code, min_gap_area_sq_m=5.0)`
- Computes void polygons between parcels
- Uses `ST_Difference(convex_hull, union_of_parcels)`
- Identifies unmapped land or survey gaps
- Returns `List[ConflictReport]`

#### `detect_area_geometry_divergence(db, parcel_id, threshold_percent=15.0)`
- Compares recorded area (RoR) vs computed `ST_Area`
- Flags divergence > 15% by default
- Returns `List[ConflictReport]`

#### `detect_encroachment_on_restricted_zones(db, parcel_id, state_code)`
- Checks overlap with forest/water/poramboke zones
- Uses spatial join with `geo.restricted_zones`
- Returns `List[ConflictReport]`

#### `run_all_spatial_checks(db, state_code, district_code, parcel_id)`
- Orchestrates all spatial checks
- Single parcel mode vs regional mode
- Returns consolidated `List[ConflictReport]`

### Output Model

```python
class ConflictReport(BaseModel):
    conflict_type: str          # OVERLAP | GAP | SLIVER | AREA_MISMATCH | ENCROACHMENT_*
    severity: str               # HIGH | MEDIUM | LOW
    parcel_ids: List[UUID]
    description: str            # Human-readable
    evidence: dict              # Metrics, geometries
    recommended_action: str
    detected_at: datetime
    confidence_score: float     # 1.0 for deterministic checks
```

---

## Module 2: Cross-Registry Inconsistency Detection

**Location**: `services/trust-engine/app/modules/inconsistency.py`

### Purpose
Compute consistency vectors by comparing parcel data across revenue, registration, geospatial, and planning registries.

### Functions

#### `compute_consistency_vector(db, parcel_id)`
- Extracts area, owner, status, geometry, temporal data from multiple registries
- Computes coefficient of variation for area
- Uses phonetic matching for owner names
- Returns `ConsistencyVector`

#### `compute_batch_consistency_vectors(db, state_code, district_code, limit=1000)`
- Batch processing for efficiency
- Returns `List[ConsistencyVector]`

### Output Model

```python
class ConsistencyVector(BaseModel):
    parcel_id: UUID
    bdpr: str
    area_cv: float                      # Coefficient of variation (0 = consistent)
    area_sources: int
    owner_name_agreement: float         # 0-1, fuzzy match score
    owner_sources: int
    status_agreement: float             # Categorical consistency
    geometry_iou: float                 # Intersection over Union
    temporal_alignment_days: float      # Mutation vs deed date gap
    overall_score: float                # Weighted composite (0-1)
    evidence: dict
```

---

## Module 3: Anomaly Detection (Isolation Forest)

**Location**: `services/trust-engine/app/modules/anomaly.py`

### Purpose
Unsupervised anomaly detection using scikit-learn Isolation Forest over consistency vectors.

### Functions

#### `run_anomaly_detection(db, state_code, district_code, contamination=0.1, store_results=True)`
- Computes consistency vectors
- Trains Isolation Forest (contamination = expected anomaly rate)
- Computes Z-scores as secondary signal
- Generates human-readable explanations
- Stores results in `ml.conflict_scores` table
- Returns `List[AnomalyScore]` ranked by score

#### `get_anomaly_score(db, parcel_id)`
- Retrieves latest anomaly score for a parcel
- Returns `Optional[AnomalyScore]`

### Output Model

```python
class AnomalyScore(BaseModel):
    parcel_id: UUID
    anomaly_score: float            # 0-1, higher = more anomalous
    percentile_rank: float          # 0-100
    top_features: List[str]         # Contributing factors
    reason_text: str                # Human explanation
    confidence_score: float         # Based on Z-score magnitude
    model_version: str
    computed_at: datetime
```

### REST API

**`POST /anomalies/rescore`** (officer-only)
- Triggers re-scoring with updated data

**`GET /anomalies`**
- Returns ranked anomalies (min_score, limit params)
- Auto-filtered by actor's district

**`GET /anomalies/{parcel_id}`**
- Single parcel lookup

**`GET /anomalies/summary`**
- Aggregate statistics (high/medium/low risk counts)

---

## Module 4: Graph Transaction Network Analysis

**Location**: `services/trust-engine/app/modules/graph_analysis.py`

### Purpose
NetworkX-based analysis of transaction networks to detect circular chains, rapid flips, and compute party risk scores.

### Functions

#### `build_transaction_graph(db, state_code, district_code, lookback_days=730)`
- Builds directed graph: nodes = parties, edges = transactions
- Extracts from `revenue.mutations` and `registration.deeds`
- Returns `(nx.DiGraph, metadata)`

#### `detect_circular_chains(G, min_length=3, max_length=10)`
- Uses `nx.simple_cycles()` to find closed loops
- Party A → B → C → A patterns
- Returns `List[CircularChain]`

#### `detect_rapid_flips(db, state_code, days_threshold=30, min_transactions=3)`
- SQL-based detection of rapid succession sales on same parcel
- Flags potential speculative trading
- Returns `List[RapidFlip]`

#### `compute_party_risk_score(G, party_id, circular_chains, rapid_flips)`
- Degree centrality + betweenness centrality
- Involvement in circular chains and rapid flips
- Weighted risk score (0-1)
- Returns `PartyRiskScore`

#### `run_full_graph_analysis(db, state_code, district_code)`
- Orchestrates all graph analyses
- Returns `GraphAnalysisReport`

### Output Models

```python
class CircularChain(BaseModel):
    chain_id: str
    party_ids: List[UUID]
    parcel_ids: List[UUID]
    chain_length: int
    time_window_days: int
    description: str
    confidence_score: float

class RapidFlip(BaseModel):
    parcel_id: UUID
    transaction_count: int
    time_window_days: int
    parties_involved: List[UUID]
    description: str
    confidence_score: float

class PartyRiskScore(BaseModel):
    party_id: UUID
    risk_score: float               # 0-1 composite
    degree_centrality: float
    betweenness_centrality: float
    in_circular_chains: int
    rapid_flips_involved: int
    reason_text: str
```

### REST API

**`GET /graph/circular-chains`**
- State/district filter, min_length param
- Returns detected circular chains

**`GET /graph/rapid-flips`**
- Days threshold, state filter
- Returns rapid flip parcels

**`GET /graph/party/{party_id}/risk`**
- Individual party risk assessment

**`GET /graph/network?parcel_id={uuid}&hops=2`**
- Ego network for D3 visualization
- Returns nodes + edges JSON

**`GET /graph/analysis/full`** (officer-only)
- Complete report: chains, flips, high-risk parties, network stats

---

## Module 5: Satellite Change Detection

**Location**: `services/satellite/app/modules/change_detection.py`

### Purpose
Sentinel-2 (10m resolution) land-use change detection: agriculture→non-agriculture, encroachment on water/forest.

### Functions

#### `compute_ndvi(red, nir)`
- Normalized Difference Vegetation Index
- `(NIR - Red) / (NIR + Red)`
- Values: -1 to 1 (higher = more vegetation)

#### `compute_ndwi(green, nir)`
- Normalized Difference Water Index
- Detects water bodies (values > 0.3)

#### `compute_ndbi(swir, nir)`
- Normalized Difference Built-up Index
- Positive values indicate built-up areas

#### `classify_land_use(ndvi, ndwi, ndbi)`
- Rule-based classification:
  - Water: NDWI > 0.3
  - Vegetation: NDVI > 0.5
  - Built-up: NDVI < 0.3, NDBI > 0
  - Barren: NDVI < 0.2

#### `detect_change(classification_t1, classification_t2)`
- Change matrix: vegetation→built-up, water→built-up, etc.
- Returns change map + statistics

#### `vectorize_change_polygons(change_map, transform, min_area_sq_m=500)`
- Converts raster to vector polygons
- Filters small polygons (<500 sq_m)
- Returns `List[ChangePolygon]`

#### `run_change_detection_pipeline(db, village_code, data_dir)`
- Full pipeline: load imagery → compute indices → classify → detect change → vectorize
- Cross-references with parcel boundaries
- Returns `ChangeDetectionResult`

### Output Model

```python
class ChangeDetectionResult(BaseModel):
    village_code: str
    change_type: str                # AGRI_TO_NON_AGRI | ENCROACHMENT_WATER | etc.
    confidence_score: float
    change_area_sq_m: float
    affected_parcels: List[UUID]
    detected_from_date: date
    detected_to_date: date
    ndvi_change: float
    description: str
    resolution_note: str            # "10m resolution. Field-level, not buildings."
```

### REST API

**`GET /satellite/change-detection/{village_code}`**
- Runs change detection for village
- Returns ChangeDetectionResult

**`GET /satellite/change-layers/{village_code}`**
- Returns GeoJSON FeatureCollection for mapping
- Polygons with change type, area, confidence

**`GET /satellite/affected-parcels/{village_code}`**
- List of parcels intersecting change polygons
- Filterable by change_type, min_area

**`GET /satellite/resolution-note`**
- Documentation on 10m resolution capabilities and limitations

---

## Module 6: Natural Language Query

**Location**: `services/analytics/app/modules/nl_query.py`

### Purpose
Template-based (no LLM API) natural language to SQL conversion for common spatial and administrative queries.

### Supported Patterns

1. **Spatial proximity**: "Show all agricultural parcels within 500 metres of forest"
2. **Dispute count**: "How many parcels in Bangalore have open disputes?"
3. **Area mismatch**: "Find parcels with area mismatch greater than 20%"
4. **Owner search**: "Show owner Ramesh Kumar all parcels" (phonetic fuzzy match)
5. **Stale building permissions**: "Parcels with building permissions but no RoR update in last 3 years"
6. **Encumbered parcels**: "List all encumbered parcels in 560001 village"
7. **Anomaly scores**: "Show parcels with high anomaly scores in Mysore"
8. **Land class count**: "How many agricultural parcels in Hassan"

### Functions

#### `NLQueryParser.parse_and_build_sql(query_text, actor_roles, state_code, district_code)`
- Regex pattern matching
- SQL template substitution
- Tiered access control (officer → district, citizen → public only)
- Returns `(sql, interpreted_as, pattern_name)`

#### `execute_nl_query(db, query_text, actor_roles, state_code, district_code)`
- Parses query
- Executes SQL
- Returns `NLQueryResult` with results, execution time, explanation

#### `get_example_queries()`
- Returns 10 example queries with descriptions

### Output Model

```python
class NLQueryResult(BaseModel):
    query_text: str
    interpreted_as: str             # Human explanation
    sql_query: str                  # Generated SQL
    results: List[dict]             # Query results
    result_count: int
    execution_time_ms: float
    pattern_matched: str            # Pattern name
```

### REST API

**`POST /query/natural-language`**
- Body: `{"text": "your query"}`
- Returns NLQueryResult

**`GET /query/examples`**
- Returns 10 example queries

**`GET /query/capabilities`**
- Documentation on supported patterns, limitations, access control

**`GET /query/help`**
- Query construction tips and best practices

---

## Module 7: Evaluation Metrics

**Location**: `services/ml-inference/app/evaluation/metrics.py`

### Purpose
Compute evaluation metrics for all ML modules to track quality and performance.

### Functions

#### `compute_spatial_conflict_recall(db)`
- Precision = confirmed / detected
- Recall = detected / (detected + manual_reported)
- F1 score
- Returns dict with metrics

#### `compute_anomaly_precision_at_k(db, k=50)`
- Precision@K for top anomalies
- Checks confirmation via officer review or network flags
- Returns precision + avg score

#### `compute_graph_circular_chain_recall(db)`
- Detected vs confirmed circular chains
- Precision = confirmed / detected
- Returns metrics dict

#### `compute_all_metrics(db, model_version="v1.0")`
- Orchestrates all evaluation metrics
- Returns `MetricsReport`

### Output Model

```python
class MetricsReport(BaseModel):
    report_timestamp: datetime
    model_version: str
    spatial_conflict_metrics: Dict[str, float]
    anomaly_detection_metrics: Dict[str, float]
    graph_analysis_metrics: Dict[str, float]
    overall_summary: Dict[str, any]
```

---

## Dependencies

All services require:

```
fastapi>=0.111.0
uvicorn[standard]>=0.29.0
pydantic>=2.7.0
sqlalchemy[asyncio]>=2.0.30
asyncpg>=0.29.0
```

### ML-specific:
```
scikit-learn>=1.4.0
networkx>=3.2
numpy>=1.26.0
pandas>=2.2.0
```

### Satellite-specific:
```
rasterio>=1.3.9
scipy>=1.12.0
shapely>=2.0.0
```

---

## Database Schema Usage

### Tables Read

- `identity.parcels` - Parcel master registry
- `geo.parcel_geometries` - PostGIS geometries
- `geo.topology_conflicts` - Stored conflicts
- `geo.restricted_zones` - Forest/water/poramboke boundaries
- `revenue.records_of_rights` - Land records
- `revenue.rights` - Ownership rights
- `revenue.mutations` - Transactions
- `revenue.parties` - Party registry
- `registration.deeds` - Registered documents
- `registration.encumbrances` - Mortgages
- `planning.building_permissions` - Building approvals

### Tables Written

- `ml.conflict_scores` - Anomaly scores
- `ml.transaction_network_flags` - Graph analysis flags
- `ml.land_use_changes` - Satellite change detection results

---

## Authentication & Authorization

All endpoints use `bhoomi_common.auth`:

- **`get_current_actor()`** - JWT verification, extracts Actor
- **`require_roles(["revenue_officer"])`** - Role-based access control

### Tiered Access

- **Citizen**: Public records, limited query types
- **Revenue Officer**: District-scoped, read/write anomalies
- **District Collector**: District-scoped, full access
- **System Admin**: State-wide, rescore permissions

---

## Ethics & Transparency

### Never Claim "Fraud Detected"

All outputs use language:
- "Anomaly surfaced for review"
- "Pattern detected requiring officer verification"
- "Inconsistency flagged for investigation"

### Confidence Scores & Explanations

Every ML output includes:
- `confidence_score` (0-1)
- `reason_text` (human-readable)
- `model_version` (for audit trails)
- `computed_at` (timestamp)

### Officer-in-the-Loop

- All high-risk flags require officer review before action
- `POST /anomalies/rescore` restricted to officers
- Manual review updates `reviewed_status` field

---

## Performance Characteristics

| Module | Typical Response Time | Scale |
|--------|----------------------|-------|
| Spatial conflicts | <5s | 1000 parcels |
| Anomaly detection | 10-30s | 5000 parcels |
| Graph analysis | 20-60s | 10,000 transactions |
| Satellite change | 5-15s | 1 village (1 sq km) |
| NL query | <1s | Most queries |

---

## Deployment

### Docker Compose

Services run as separate containers:
```yaml
services:
  ml-inference:
    image: bhoomi/ml-inference:latest
    environment:
      - DATABASE_URL=postgresql://...
  trust-engine:
    image: bhoomi/trust-engine:latest
  satellite:
    image: bhoomi/satellite:latest
  analytics:
    image: bhoomi/analytics:latest
```

### Health Checks

All services expose:
- `GET /health` - Basic health check
- `GET /metrics` - Prometheus metrics

---

## Testing

### Unit Tests
```bash
cd services/trust-engine
pytest app/tests/
```

### Integration Tests
```bash
# Requires running Postgres with PostGIS
docker-compose up -d postgres
pytest --integration
```

### Evaluation Metrics
```bash
# Compute metrics for production deployment
curl -X POST http://localhost:8004/evaluation/compute
```

---

## Future Enhancements

1. **Deep Learning**: Replace Isolation Forest with Graph Neural Networks for anomaly detection
2. **Cartosat-3 Integration**: 0.25m resolution for building detection
3. **LLM Integration**: Replace template matching with fine-tuned LLM for NL query
4. **Real-time Scoring**: Stream processing with Kafka for instant anomaly alerts
5. **Explainable AI**: SHAP values for model interpretability
6. **Active Learning**: Officer feedback loop to improve models

---

## Contact & Support

- **Architecture**: See `CLAUDE.md` for system overview
- **Database Schema**: `infrastructure/postgres/init/02_tables.sql`
- **API Docs**: Visit `/docs` on each service (FastAPI Swagger UI)

---

**Version**: 1.0.0  
**Last Updated**: 2026-09-15  
**License**: Government of India (restricted)
