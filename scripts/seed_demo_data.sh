#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# Bhoomi Dhrishti – Demo Data Seeding Script
# Seeds deterministic demo data for hackathon presentation
# ─────────────────────────────────────────────────────────────────────────────

set -e  # Exit on error

BASE_URL="${BASE_URL:-http://localhost:8000}"
SEED=42

echo "🌱 Seeding Bhoomi Dhrishti demo database..."
echo "   Base URL: $BASE_URL"
echo "   Seed: $SEED"
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# Step 1: Run data generator
# ─────────────────────────────────────────────────────────────────────────────
echo "📊 Step 1: Generating synthetic data..."
cd "$(dirname "$0")/.."

if [ -f "data/generator/generate.py" ]; then
    python data/generator/generate.py --seed $SEED --output data/raw
    echo "✓ Synthetic data generated"
else
    echo "⚠ Data generator not found, skipping..."
fi

# ─────────────────────────────────────────────────────────────────────────────
# Step 2: Ingest departmental sources (TN + CH)
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "📥 Step 2: Ingesting departmental data..."

# Tamil Nadu (TN) - Rural
if [ -f "data/raw/tn_rural/revenue_ror.jsonl" ]; then
    echo "  → Ingesting TN Revenue RoR..."
    curl -X POST "$BASE_URL/interoperability/ingest/revenue_ror" \
      -F "file=@data/raw/tn_rural/revenue_ror.jsonl" \
      -F "state_code=TN" \
      -s | jq -r '.status // "done"'
fi

if [ -f "data/raw/tn_rural/registration_deeds.jsonl" ]; then
    echo "  → Ingesting TN Registration deeds..."
    curl -X POST "$BASE_URL/interoperability/ingest/registration" \
      -F "file=@data/raw/tn_rural/registration_deeds.jsonl" \
      -F "state_code=TN" \
      -s | jq -r '.status // "done"'
fi

if [ -f "data/raw/tn_rural/survey_data.geojson" ]; then
    echo "  → Ingesting TN Survey data..."
    curl -X POST "$BASE_URL/interoperability/ingest/survey" \
      -F "file=@data/raw/tn_rural/survey_data.geojson" \
      -F "state_code=TN" \
      -s | jq -r '.status // "done"'
fi

if [ -f "data/raw/tn_rural/ulb_property_tax.jsonl" ]; then
    echo "  → Ingesting TN ULB property tax..."
    curl -X POST "$BASE_URL/interoperability/ingest/property_tax" \
      -F "file=@data/raw/tn_rural/ulb_property_tax.jsonl" \
      -F "state_code=TN" \
      -s | jq -r '.status // "done"'
fi

if [ -f "data/raw/tn_rural/planning_zones.geojson" ]; then
    echo "  → Ingesting TN Planning zones..."
    curl -X POST "$BASE_URL/interoperability/ingest/planning_zones" \
      -F "file=@data/raw/tn_rural/planning_zones.geojson" \
      -F "state_code=TN" \
      -s | jq -r '.status // "done"'
fi

# Chandigarh (CH) - Urban
if [ -f "data/raw/chandigarh/revenue_ror.jsonl" ]; then
    echo "  → Ingesting CH Revenue RoR..."
    curl -X POST "$BASE_URL/interoperability/ingest/revenue_ror" \
      -F "file=@data/raw/chandigarh/revenue_ror.jsonl" \
      -F "state_code=CH" \
      -s | jq -r '.status // "done"'
fi

if [ -f "data/raw/chandigarh/registration_deeds.jsonl" ]; then
    echo "  → Ingesting CH Registration deeds..."
    curl -X POST "$BASE_URL/interoperability/ingest/registration" \
      -F "file=@data/raw/chandigarh/registration_deeds.jsonl" \
      -F "state_code=CH" \
      -s | jq -r '.status // "done"'
fi

echo "✓ Data ingestion completed"

# ─────────────────────────────────────────────────────────────────────────────
# Step 3: Run entity resolution
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "🔗 Step 3: Running entity resolution..."
curl -X POST "$BASE_URL/parcel-identity/resolution/run" \
  -H "Content-Type: application/json" \
  -d '{"confidence_threshold": 0.75, "spatial_threshold_m": 5.0}' \
  -s | jq -r '.status // "done"'
echo "✓ Entity resolution completed"

# ─────────────────────────────────────────────────────────────────────────────
# Step 4: Detect conflicts
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "⚠️  Step 4: Detecting conflicts..."
curl -X POST "$BASE_URL/trust-engine/conflicts/detect" \
  -H "Content-Type: application/json" \
  -d '{"conflict_types": ["area_mismatch", "ownership_dispute", "boundary_overlap"]}' \
  -s | jq -r '.status // "done"'
echo "✓ Conflict detection completed"

# ─────────────────────────────────────────────────────────────────────────────
# Step 5: Run ML anomaly scoring
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "🤖 Step 5: Running ML anomaly detection..."
curl -X POST "$BASE_URL/ml-inference/anomalies/rescore" \
  -H "Content-Type: application/json" \
  -d '{"model": "isolation_forest", "contamination": 0.05}' \
  -s | jq -r '.status // "done"'
echo "✓ ML scoring completed"

# ─────────────────────────────────────────────────────────────────────────────
# Step 6: Run graph analysis
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "🕸️  Step 6: Running graph analysis..."
curl -X POST "$BASE_URL/trust-engine/graph/analyze" \
  -H "Content-Type: application/json" \
  -d '{"algorithms": ["circular_ownership", "community_detection"]}' \
  -s | jq -r '.status // "done"'
echo "✓ Graph analysis completed"

# ─────────────────────────────────────────────────────────────────────────────
# Step 7: Seed lineage events
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "📜 Step 7: Seeding parcel lineage events..."

# Event 1: Subdivision
curl -X POST "$BASE_URL/parcel-identity/lineage/events" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "subdivision",
    "parent_ulpin": "09-01-015-123-456",
    "child_ulpins": ["09-01-015-123-456-01", "09-01-015-123-456-02"],
    "event_date": "2024-03-15T00:00:00Z",
    "document_ref": "SUB-2024-001",
    "authority": "TN-TVL Tehsildar"
  }' \
  -s | jq -r '.event_id // "created"'

# Event 2: Amalgamation
curl -X POST "$BASE_URL/parcel-identity/lineage/events" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "amalgamation",
    "parent_ulpins": ["09-01-015-234-567", "09-01-015-234-568"],
    "child_ulpin": "09-01-015-234-569",
    "event_date": "2024-06-20T00:00:00Z",
    "document_ref": "AMAL-2024-042",
    "authority": "TN-TVL Tehsildar"
  }' \
  -s | jq -r '.event_id // "created"'

# Event 3: Renumbering
curl -X POST "$BASE_URL/parcel-identity/lineage/events" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "renumbering",
    "old_ulpin": "09-01-015-345-678",
    "new_ulpin": "09-01-015-999-001",
    "event_date": "2025-01-10T00:00:00Z",
    "document_ref": "RENUM-2025-003",
    "authority": "TN-TVL Survey Department",
    "reason": "Survey resurvey 2025"
  }' \
  -s | jq -r '.event_id // "created"'

echo "✓ Lineage events seeded"

# ─────────────────────────────────────────────────────────────────────────────
# Step 8: Create demo Keycloak users
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "👥 Step 8: Creating demo users in Keycloak..."

KEYCLOAK_URL="${KEYCLOAK_URL:-http://localhost:8080}"
REALM="bhoomi-dhrishti"

# Get admin token
ADMIN_TOKEN=$(curl -X POST "$KEYCLOAK_URL/realms/master/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=${KEYCLOAK_ADMIN_USER:-admin}" \
  -d "password=${KEYCLOAK_ADMIN_PASSWORD:-admin}" \
  -d "grant_type=password" \
  -d "client_id=admin-cli" \
  -s | jq -r '.access_token // empty')

if [ -n "$ADMIN_TOKEN" ]; then
    # Create citizen user
    echo "  → Creating citizen@example.com..."
    curl -X POST "$KEYCLOAK_URL/admin/realms/$REALM/users" \
      -H "Authorization: Bearer $ADMIN_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "username": "citizen@example.com",
        "email": "citizen@example.com",
        "enabled": true,
        "emailVerified": true,
        "credentials": [{"type": "password", "value": "demo123", "temporary": false}],
        "realmRoles": ["citizen"],
        "attributes": {
          "aadhaar_hash": ["e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"]
        }
      }' \
      -s > /dev/null

    # Create officer user
    echo "  → Creating officer@tn.gov.in..."
    curl -X POST "$KEYCLOAK_URL/admin/realms/$REALM/users" \
      -H "Authorization: Bearer $ADMIN_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "username": "officer@tn.gov.in",
        "email": "officer@tn.gov.in",
        "enabled": true,
        "emailVerified": true,
        "credentials": [{"type": "password", "value": "demo123", "temporary": false}],
        "realmRoles": ["officer", "revenue_officer"],
        "attributes": {
          "department": ["revenue"],
          "jurisdiction": ["TN-TVL"]
        }
      }' \
      -s > /dev/null

    # Create admin user
    echo "  → Creating admin@bhoomi.gov.in..."
    curl -X POST "$KEYCLOAK_URL/admin/realms/$REALM/users" \
      -H "Authorization: Bearer $ADMIN_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "username": "admin@bhoomi.gov.in",
        "email": "admin@bhoomi.gov.in",
        "enabled": true,
        "emailVerified": true,
        "credentials": [{"type": "password", "value": "demo123", "temporary": false}],
        "realmRoles": ["admin", "system_admin"],
        "attributes": {
          "full_access": ["true"]
        }
      }' \
      -s > /dev/null

    echo "✓ Demo users created"
else
    echo "⚠ Could not get Keycloak admin token, skipping user creation"
    echo "  You can create users manually via Keycloak console: $KEYCLOAK_URL"
fi

# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "══════════════════════════════════════════════════════════════════════════"
echo "✓ Demo data seeding completed successfully!"
echo "══════════════════════════════════════════════════════════════════════════"
echo ""
echo "Demo credentials:"
echo "  Citizen:  citizen@example.com   / demo123"
echo "  Officer:  officer@tn.gov.in     / demo123"
echo "  Admin:    admin@bhoomi.gov.in   / demo123"
echo ""
echo "Ready for presentation. Access the platform at:"
echo "  Frontend:     http://localhost:3000"
echo "  API Gateway:  http://localhost:8000"
echo "  Keycloak:     http://localhost:8080"
echo ""
