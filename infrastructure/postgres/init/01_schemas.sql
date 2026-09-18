-- ─────────────────────────────────────────────────────────────────────────────
-- Bhoomi Dhrishti – 01_schemas.sql
-- Create schema namespaces and roles
-- ─────────────────────────────────────────────────────────────────────────────

-- ── Schema namespaces ────────────────────────────────────────────────────────

-- Core parcel identity management
CREATE SCHEMA IF NOT EXISTS identity;
COMMENT ON SCHEMA identity IS 'Canonical parcel identifiers (BDPR/ULPIN), lineage, and cross-system aliases';

-- Geospatial / GIS data
CREATE SCHEMA IF NOT EXISTS geo;
COMMENT ON SCHEMA geo IS 'Parcel geometries (PostGIS), administrative boundaries, restriction zones, topology conflicts';

-- Revenue (land records / Bhoomi / Dharani / etc.)
CREATE SCHEMA IF NOT EXISTS revenue;
COMMENT ON SCHEMA revenue IS 'Records of Rights, ownership rights, mutations, party registry';

-- Property registration (SRO / NGDRS)
CREATE SCHEMA IF NOT EXISTS registration;
COMMENT ON SCHEMA registration IS 'Registered deeds, encumbrances, stamp duty records';

-- Urban planning and zoning
CREATE SCHEMA IF NOT EXISTS planning;
COMMENT ON SCHEMA planning IS 'Zoning regulations, building permissions, dispute linkages';

-- Fiscal / property tax
CREATE SCHEMA IF NOT EXISTS fiscal;
COMMENT ON SCHEMA fiscal IS 'Property tax assessments, valuations, payment status';

-- Append-only audit ledger
CREATE SCHEMA IF NOT EXISTS audit;
COMMENT ON SCHEMA audit IS 'Append-only partitioned event log; no UPDATE or DELETE ever executed here';

-- ML / AI scoring and entity resolution
CREATE SCHEMA IF NOT EXISTS ml;
COMMENT ON SCHEMA ml IS 'ML conflict scores, entity resolution links, network anomaly flags, satellite change detection';

-- Reference / lookup data
CREATE SCHEMA IF NOT EXISTS reference;
COMMENT ON SCHEMA reference IS 'LGD hierarchy, unit conversions, code list mappings';

-- Keycloak uses its own schema (created by Keycloak itself; we only pre-declare it)
CREATE SCHEMA IF NOT EXISTS keycloak;
COMMENT ON SCHEMA keycloak IS 'Keycloak IAM internal tables — managed by Keycloak, not by this codebase';

-- ── Application roles ────────────────────────────────────────────────────────

-- Service account (used by all FastAPI services)
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'bhoomi_app') THEN
    CREATE ROLE bhoomi_app LOGIN PASSWORD 'change_me_app_role_password';
  END IF;
END
$$;

-- Read-only analytics role
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'bhoomi_readonly') THEN
    CREATE ROLE bhoomi_readonly LOGIN PASSWORD 'change_me_readonly_password';
  END IF;
END
$$;

-- Grant schema usage
GRANT USAGE ON SCHEMA identity, geo, revenue, registration, planning, fiscal, audit, ml, reference
  TO bhoomi_app;
GRANT USAGE ON SCHEMA identity, geo, revenue, registration, planning, fiscal, ml, reference
  TO bhoomi_readonly;

-- Default privileges for future tables created by superuser
ALTER DEFAULT PRIVILEGES IN SCHEMA identity, geo, revenue, registration, planning, fiscal, ml, reference
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO bhoomi_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA audit
  GRANT SELECT, INSERT ON TABLES TO bhoomi_app;   -- No UPDATE/DELETE on audit
ALTER DEFAULT PRIVILEGES IN SCHEMA identity, geo, revenue, registration, planning, fiscal, ml, reference
  GRANT SELECT ON TABLES TO bhoomi_readonly;

-- Sequences
ALTER DEFAULT PRIVILEGES IN SCHEMA identity, geo, revenue, registration, planning, fiscal, ml, reference
  GRANT USAGE, SELECT ON SEQUENCES TO bhoomi_app;
