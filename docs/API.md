# Bhoomi Dhrishti – API Reference

## Overview

All services expose **FastAPI** REST endpoints with automatic OpenAPI documentation. Base URL: `http://localhost:8000` (API Gateway).

## Authentication

### OAuth2 / OIDC via Keycloak

**Token Endpoint**: `POST http://localhost:8080/realms/bhoomi-dhrishti/protocol/openid-connect/token`

#### Password Grant (Demo Only)
```bash
curl -X POST http://localhost:8080/realms/bhoomi-dhrishti/protocol/openid-connect/token \
  -d grant_type=password \
  -d client_id=bhoomi-web \
  -d username=citizen@example.com \
  -d password=demo123
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### Authorization Code + PKCE (Production)
For web/mobile apps, use PKCE flow:
1. Generate `code_verifier` (random 43-128 chars)
2. SHA-256 hash → `code_challenge`
3. Redirect to `/auth?code_challenge=...&code_challenge_method=S256`
4. Exchange code for token: `POST /token` with `code_verifier`

### Common Headers

All authenticated requests require:
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

## Service Endpoints

### 1. Parcel Identity (`/parcel-identity`)

**Port**: 8001  
**OpenAPI**: http://localhost:8001/docs

#### Get Parcel by ULPIN
```http
GET /parcels/{ulpin}
```

**Example**:
```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/parcel-identity/parcels/09-01-015-123-456
```

**Response**:
```json
{
  "ulpin": "09-01-015-123-456",
  "area_sqm": {
    "value": 250.5,
    "provenance": {
      "source_department": "revenue",
      "source_system": "TN-iFMIS",
      "confidence": 0.95
    }
  },
  "geometry": {
    "type": "Polygon",
    "coordinates": [[[77.123, 11.456], ...]]
  },
  "land_use": "residential",
  "owners": [
    {
      "name": "[ENCRYPTED - requires citizen role or jurisdiction access]",
      "share": "1/1"
    }
  ]
}
```

#### Search Parcels (Spatial)
```http
POST /parcels/search
Content-Type: application/json
```

**Request Body**:
```json
{
  "bbox": [77.0, 11.0, 77.5, 11.5],
  "filters": {
    "land_use": ["residential", "commercial"],
    "min_area_sqm": 100.0,
    "max_area_sqm": 1000.0
  },
  "limit": 100
}
```

#### Run Entity Resolution
```http
POST /resolution/run
```

**Request**:
```json
{
  "confidence_threshold": 0.75,
  "spatial_threshold_m": 5.0
}
```

**Response**:
```json
{
  "status": "completed",
  "resolved_count": 8543,
  "unresolved_count": 157,
  "avg_confidence": 0.89,
  "execution_time_ms": 12456
}
```

#### Parcel Lineage
```http
GET /lineage/{ulpin}
```

**Response**:
```json
{
  "ulpin": "09-01-015-123-456",
  "lineage": [
    {
      "event_type": "subdivision",
      "parent_ulpin": "09-01-015-123",
      "event_date": "2024-03-15T00:00:00Z",
      "document_ref": "SUB-2024-001"
    }
  ],
  "children": [],
  "parents": ["09-01-015-123"]
}
```

---

### 2. Geospatial (`/geospatial`)

**Port**: 8002  
**OpenAPI**: http://localhost:8002/docs

#### Spatial Intersection
```http
POST /spatial/intersects
```

**Request**:
```json
{
  "geometry": {
    "type": "Point",
    "coordinates": [77.123, 11.456]
  },
  "buffer_m": 500.0
}
```

**Response**:
```json
{
  "parcels": [
    {"ulpin": "09-01-015-123-456", "distance_m": 23.5},
    {"ulpin": "09-01-015-123-457", "distance_m": 120.8}
  ],
  "count": 2
}
```

#### Topology Validation
```http
POST /spatial/validate
```

Checks for:
- Self-intersections
- Gaps
- Overlaps
- Slivers

---

### 3. Revenue Records (`/revenue-records`)

**Port**: 8003  
**OpenAPI**: http://localhost:8003/docs

#### Get Record of Rights (RoR)
```http
GET /parcels/{ulpin}/ror
```

**Response**:
```json
{
  "ulpin": "09-01-015-123-456",
  "survey_number": "123/1A",
  "khata_number": "456",
  "owners": [
    {
      "name": "Rajesh Kumar",
      "aadhaar_hash": "e3b0c44...",
      "share": "1/2"
    }
  ],
  "land_use": "agricultural",
  "pattadar": "owner",
  "mutations": [
    {
      "mutation_id": "MUT-2024-001",
      "mutation_type": "sale",
      "approval_date": "2024-06-20",
      "deed_id": "DEED-2024-456"
    }
  ]
}
```

#### Request Mutation
```http
POST /mutations
```

**Request**:
```json
{
  "ulpin": "09-01-015-123-456",
  "deed_id": "DEED-2024-456",
  "new_owner_aadhaar": "123456789012",
  "mutation_type": "sale"
}
```

---

### 4. Registration (`/registration`)

**Port**: 8004  
**OpenAPI**: http://localhost:8004/docs

#### Get Deed History
```http
GET /parcels/{ulpin}/deeds
```

**Response**:
```json
{
  "deeds": [
    {
      "deed_id": "DEED-2024-456",
      "registration_date": "2024-06-15",
      "transaction_type": "sale",
      "sale_price": 5000000.0,
      "seller": "[ENCRYPTED]",
      "buyer": "[ENCRYPTED]",
      "sro_code": "TN-TVL-01",
      "document_url": "https://tnrms.gov.in/deeds/2024/456"
    }
  ]
}
```

#### Register Deed
```http
POST /deeds
```

**Request**:
```json
{
  "ulpin": "09-01-015-123-456",
  "seller_aadhaar": "123456789012",
  "buyer_aadhaar": "987654321098",
  "sale_price": 5000000.0,
  "transaction_type": "sale",
  "sro_code": "TN-TVL-01"
}
```

---

### 5. Planning & Zoning (`/planning-zoning`)

**Port**: 8005  
**OpenAPI**: http://localhost:8005/docs

#### Get Zoning Information
```http
GET /parcels/{ulpin}/zone
```

**Response**:
```json
{
  "ulpin": "09-01-015-123-456",
  "zone_type": "residential",
  "permitted_uses": ["residential", "mixed"],
  "regulations": {
    "fsi_residential": 2.0,
    "setback_front_min": 3.0,
    "setback_rear_min": 3.0,
    "max_height_m": 15.0
  },
  "restrictions": {
    "sale_restricted": false
  }
}
```

#### Building Permit Application
```http
POST /applications
```

**Request**:
```json
{
  "ulpin": "09-01-015-123-456",
  "applicant_aadhaar": "123456789012",
  "building_type": "residential",
  "proposed_area_sqm": 400.0,
  "proposed_floors": 3
}
```

---

### 6. Fiscal (`/fiscal`)

**Port**: 8006  
**OpenAPI**: http://localhost:8006/docs

#### Property Tax Dues
```http
GET /property-tax/{ulpin}/dues
```

**Response**:
```json
{
  "ulpin": "09-01-015-123-456",
  "pending_amount": 12500.0,
  "pending_years": [2024, 2025],
  "last_payment_date": "2023-03-31",
  "tax_assessment_value": 8500000.0
}
```

#### Encumbrances
```http
GET /encumbrances/{ulpin}
```

**Response**:
```json
{
  "ulpin": "09-01-015-123-456",
  "encumbrances": [
    {
      "type": "mortgage",
      "creditor": "State Bank of India",
      "amount": 4000000.0,
      "registration_date": "2022-05-10",
      "status": "active"
    }
  ]
}
```

---

### 7. Trust Engine (`/trust-engine`)

**Port**: 8008  
**OpenAPI**: http://localhost:8008/docs

#### Conflict Detection
```http
GET /conflicts/{ulpin}
```

**Response**:
```json
{
  "ulpin": "09-01-015-123-456",
  "conflicts": [
    {
      "conflict_type": "area_mismatch",
      "severity": "high",
      "sources": [
        {"department": "revenue", "value": 250.5},
        {"department": "registration", "value": 175.3}
      ],
      "variance_pct": 35.2
    }
  ]
}
```

#### Create Enforcement Case
```http
POST /enforcement-cases
```

**Request**:
```json
{
  "ulpin": "09-01-015-123-456",
  "case_type": "unauthorized_construction",
  "priority": "high",
  "detection_details": {
    "change_area_sqm": 850.0,
    "detected_date": "2025-09-01"
  }
}
```

---

### 8. ML Inference (`/ml-inference`)

**Port**: 8009  
**OpenAPI**: http://localhost:8009/docs

#### Anomaly Scoring
```http
GET /anomalies/{ulpin}
```

**Response**:
```json
{
  "ulpin": "09-01-015-123-456",
  "anomaly_score": 0.82,
  "anomaly_type": "price_outlier",
  "features": {
    "sale_price_per_sqm": 45000.0,
    "neighborhood_median": 18000.0,
    "z_score": 3.8
  },
  "flagged": true
}
```

#### Graph Fraud Detection
```http
POST /graph/analyze
```

**Response**:
```json
{
  "circular_chains": [
    {
      "chain": [
        "09-01-015-123-456",
        "09-01-015-234-567",
        "09-01-015-345-678",
        "09-01-015-123-456"
      ],
      "chain_length": 4,
      "total_value": 25000000.0
    }
  ],
  "suspicious_communities": []
}
```

---

### 9. Satellite (`/satellite`)

**Port**: 8016  
**OpenAPI**: http://localhost:8016/docs

#### Change Detection
```http
POST /change-detection
```

**Request**:
```json
{
  "region_code": "TN-TVL",
  "since_date": "2025-06-01",
  "min_change_area_sqm": 500.0,
  "detection_types": ["agricultural_to_built"]
}
```

**Response**:
```json
{
  "detections": [
    {
      "ulpin": "09-01-015-123-456",
      "conversion_type": "agricultural_to_built",
      "change_area_sqm": 850.0,
      "confidence_score": 0.89,
      "detected_date": "2025-09-01"
    }
  ],
  "count": 1
}
```

---

### 10. Workflows (`/workflows`)

**Port**: 8000 (via Gateway)  
**OpenAPI**: http://localhost:8000/workflows/docs

#### Property Sale Workflow
```http
POST /workflows/property-sale
```

**Request**:
```json
{
  "ulpin": "09-01-015-123-456",
  "seller_aadhaar": "123456789012",
  "buyer_aadhaar": "987654321098",
  "sale_price": 5000000.0,
  "sale_area_sqm": 250.5,
  "sro_code": "TN-TVL-01"
}
```

**Response**:
```json
{
  "workflow_id": "PS-20260915123045-09-01-015",
  "status": "APPROVED",
  "prechecks": [
    {"check_name": "encumbrances", "status": "PASS"},
    {"check_name": "ownership", "status": "PASS"}
  ],
  "timeline": [...]
}
```

#### Building Permit Workflow
```http
POST /workflows/building-permit
```

#### Land-Use Enforcement Workflow
```http
POST /workflows/land-use-enforcement
```

**Request**:
```json
{
  "region_code": "TN-TVL",
  "lookback_days": 90
}
```

---

## Rate Limiting

| Role     | Rate Limit            |
|----------|-----------------------|
| Citizen  | 100 req/min          |
| Officer  | 500 req/min          |
| Admin    | 1000 req/min         |
| System   | Unlimited (internal) |

Rate limit headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1632150000
```

## Error Responses

### Standard Error Format
```json
{
  "error": {
    "code": "PARCEL_NOT_FOUND",
    "message": "Parcel with ULPIN 09-01-015-999-999 not found",
    "details": {
      "ulpin": "09-01-015-999-999"
    },
    "timestamp": "2025-09-15T12:34:56Z",
    "request_id": "req-abc123"
  }
}
```

### HTTP Status Codes

| Code | Meaning                          |
|------|----------------------------------|
| 200  | Success                          |
| 201  | Created                          |
| 400  | Bad Request (validation failed)  |
| 401  | Unauthorized (missing token)     |
| 403  | Forbidden (insufficient access)  |
| 404  | Not Found                        |
| 409  | Conflict (duplicate resource)    |
| 422  | Unprocessable Entity             |
| 429  | Rate Limit Exceeded              |
| 500  | Internal Server Error            |

## Interactive Documentation

Each service exposes **Swagger UI** at `/docs`:

- **Parcel Identity**: http://localhost:8001/docs
- **Geospatial**: http://localhost:8002/docs
- **Revenue Records**: http://localhost:8003/docs
- **Registration**: http://localhost:8004/docs
- **Planning & Zoning**: http://localhost:8005/docs
- **Fiscal**: http://localhost:8006/docs
- **Trust Engine**: http://localhost:8008/docs
- **ML Inference**: http://localhost:8009/docs
- **Satellite**: http://localhost:8016/docs

## Client Libraries

### Python
```python
from bhoomiclient import BhoomiAPI

client = BhoomiAPI(
    base_url="http://localhost:8000",
    token="eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
)

parcel = await client.parcels.get("09-01-015-123-456")
print(parcel.area_sqm.value)  # 250.5
```

### cURL
```bash
TOKEN="eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/parcel-identity/parcels/09-01-015-123-456
```

---

**Next**: See `DEMO_NARRATIVE.md` for the 5-minute pitch script and `LIMITATIONS.md` for honest technical constraints.
