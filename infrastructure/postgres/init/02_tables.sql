-- ─────────────────────────────────────────────────────────────────────────────
-- Bhoomi Dhrishti – 02_tables.sql
-- Complete table definitions across all schemas
-- Production-quality: constraints, comments, check constraints, defaults
-- ─────────────────────────────────────────────────────────────────────────────

-- ═════════════════════════════════════════════════════════════════════════════
-- SCHEMA: reference
-- ═════════════════════════════════════════════════════════════════════════════

-- LGD (Local Government Directory) Hierarchy
CREATE TABLE reference.lgd_hierarchy (
  lgd_code        VARCHAR(20) PRIMARY KEY,
  entity_type     VARCHAR(20) NOT NULL
                    CHECK (entity_type IN ('STATE', 'DISTRICT', 'SUBDISTRICT', 'VILLAGE', 'WARD', 'BLOCK', 'URBAN_LOCAL_BODY')),
  name_en         VARCHAR(200) NOT NULL,
  name_local      VARCHAR(200),
  script_local    VARCHAR(50),   -- DEVANAGARI | TAMIL | TELUGU | etc.
  parent_lgd_code VARCHAR(20) REFERENCES reference.lgd_hierarchy(lgd_code),
  hierarchy_type  VARCHAR(20) NOT NULL
                    CHECK (hierarchy_type IN ('REVENUE', 'LOCAL_BODY')),
  state_code      VARCHAR(10),
  is_active       BOOLEAN DEFAULT true,
  census_code     VARCHAR(20),   -- Census 2011/2021 code for cross-reference
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  updated_at      TIMESTAMPTZ DEFAULT NOW()
);
COMMENT ON TABLE reference.lgd_hierarchy IS 'LGD administrative hierarchy. Two parallel trees: REVENUE (state→district→subdistrict→village) and LOCAL_BODY (state→district→ULB→ward).';

-- Unit Conversion Registry (district-scoped; handles bigha, gunta, cent, etc.)
CREATE TABLE reference.unit_conversions (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  state_lgd_code        VARCHAR(20) REFERENCES reference.lgd_hierarchy(lgd_code),
  district_lgd_code     VARCHAR(20) REFERENCES reference.lgd_hierarchy(lgd_code),
  unit_name             VARCHAR(50) NOT NULL,
  unit_local_name       VARCHAR(100),
  unit_script           VARCHAR(50),
  sq_metres_per_unit    NUMERIC(20, 8) NOT NULL CHECK (sq_metres_per_unit > 0),
  is_official           BOOLEAN DEFAULT false,  -- Gazette-notified vs. traditional
  notes                 TEXT,   -- e.g. "Pucca bigha, Rajasthan"
  source                VARCHAR(200),
  created_at            TIMESTAMPTZ DEFAULT NOW()
);
COMMENT ON TABLE reference.unit_conversions IS 'Maps local area units (bigha, gunta, cent, kanal, marla, etc.) to sq_metres. Scoped by district when conversion varies sub-nationally.';

-- Code List / Value Mapping Registry
CREATE TABLE reference.code_lists (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  list_name         VARCHAR(100) NOT NULL,  -- e.g. LAND_CLASSIFICATION, MUTATION_TYPE
  list_version      VARCHAR(20) NOT NULL DEFAULT '1.0',
  source_system     VARCHAR(100),
  state_lgd_code    VARCHAR(20),            -- NULL = national/canonical
  code_value        VARCHAR(100) NOT NULL,  -- State-specific value
  canonical_value   VARCHAR(100) NOT NULL,  -- Bhoomi Dhrishti canonical value
  description_en    VARCHAR(500),
  description_local VARCHAR(500),
  is_active         BOOLEAN DEFAULT true,
  created_at        TIMESTAMPTZ DEFAULT NOW()
);
COMMENT ON TABLE reference.code_lists IS 'Maps state-specific code values to canonical Bhoomi Dhrishti equivalents. Enables cross-state normalisation of land classification, mutation type, etc.';

-- ═════════════════════════════════════════════════════════════════════════════
-- SCHEMA: identity
-- ═════════════════════════════════════════════════════════════════════════════

-- Core Parcel Identity
CREATE TABLE identity.parcels (
  id                        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  bdpr                      VARCHAR(20) UNIQUE NOT NULL,             -- Bhoomi Dhrishti Parcel Reference (internal stable ID)
  ulpin                     VARCHAR(20),                             -- Authoritative ULPIN from DILRMP (nullable until assigned)
  ulpin_source              VARCHAR(100),                            -- DILRMP | STATE_ASSIGN | INFERRED
  ulpin_assigned_at         TIMESTAMPTZ,
  state_code                VARCHAR(10) NOT NULL REFERENCES reference.lgd_hierarchy(lgd_code),
  district_code             VARCHAR(10) NOT NULL REFERENCES reference.lgd_hierarchy(lgd_code),
  subdistrict_code          VARCHAR(10) REFERENCES reference.lgd_hierarchy(lgd_code),
  village_code              VARCHAR(10) REFERENCES reference.lgd_hierarchy(lgd_code),
  urban_ward_code           VARCHAR(10) REFERENCES reference.lgd_hierarchy(lgd_code),
  is_urban                  BOOLEAN NOT NULL DEFAULT false,
  created_at                TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at                TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  is_active                 BOOLEAN NOT NULL DEFAULT true,
  system_of_record_flag     VARCHAR(20) NOT NULL DEFAULT 'DERIVED'
                              CHECK (system_of_record_flag IN ('AUTHORITATIVE', 'DERIVED', 'CACHE')),
  -- Validate: must have either village_code (rural) or urban_ward_code (urban)
  CONSTRAINT parcel_location_check CHECK (
    (is_urban = false AND village_code IS NOT NULL) OR
    (is_urban = true  AND urban_ward_code IS NOT NULL) OR
    (ulpin IS NOT NULL)  -- ULPIN-only records may lack granular hierarchy before entity resolution
  ),
  CONSTRAINT ulpin_format CHECK (ulpin IS NULL OR ulpin ~ '^[0-9]{2}[0-9]{2}[0-9]{4}[A-Z0-9]{8}$')
);
COMMENT ON TABLE identity.parcels IS 'Master parcel registry. One row per unique real-world land parcel as known to Bhoomi Dhrishti. BDPR is our stable internal ID; ULPIN is the national identifier issued by DILRMP.';
COMMENT ON COLUMN identity.parcels.bdpr IS 'Bhoomi Dhrishti Parcel Reference: format BD-<STATE>-<SEQUENCE>, e.g. BD-TN-000001';
COMMENT ON COLUMN identity.parcels.ulpin IS '20-digit ULPIN: 2-digit state + 2-digit district + 4-digit village/ward + 8-char unique suffix. Nullable until DILRMP confirms assignment.';

-- Parcel Lineage (subdivision, amalgamation, boundary correction, resurvey)
CREATE TABLE identity.parcel_lineage (
  id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  event_type              VARCHAR(30) NOT NULL
                            CHECK (event_type IN ('SUBDIVISION', 'AMALGAMATION', 'BOUNDARY_CORRECTION', 'RESURVEY_RENUMBER', 'SPLIT', 'MERGE')),
  parent_parcel_id        UUID REFERENCES identity.parcels(id),
  child_parcel_id         UUID REFERENCES identity.parcels(id),
  event_date              DATE NOT NULL,
  authorising_document    VARCHAR(200),   -- GO/Order number
  authorising_authority   VARCHAR(200),
  notes                   TEXT,
  created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT lineage_different_parcels CHECK (parent_parcel_id <> child_parcel_id),
  CONSTRAINT lineage_at_least_one_parcel CHECK (parent_parcel_id IS NOT NULL OR child_parcel_id IS NOT NULL)
);
COMMENT ON TABLE identity.parcel_lineage IS 'Tracks how parcels split, merge, or get renumbered over time. Each event links parent → child with the authorising instrument.';

-- Cross-System Parcel Aliases
CREATE TABLE identity.parcel_aliases (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  parcel_id       UUID NOT NULL REFERENCES identity.parcels(id) ON DELETE CASCADE,
  alias_type      VARCHAR(50) NOT NULL
                    CHECK (alias_type IN ('SURVEY_NUMBER', 'MUNICIPAL_PID', 'TAX_ASSESSMENT', 'KHASRA', 'KHATA', 'PLOT_NUMBER', 'RS_SURVEY', 'FMB_NUMBER', 'SRO_PID', 'SVAMITVA_PID', 'OTHER')),
  alias_value     VARCHAR(200) NOT NULL,
  source_system   VARCHAR(100),
  state_lgd_code  VARCHAR(10),
  valid_from      DATE,
  valid_to        DATE,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT alias_validity CHECK (valid_from IS NULL OR valid_to IS NULL OR valid_from <= valid_to),
  UNIQUE (alias_type, alias_value, source_system)  -- Same alias from same system = same parcel
);
COMMENT ON TABLE identity.parcel_aliases IS 'Maps alternative identifiers from external systems (survey numbers, PID, khasra, etc.) to the canonical BDPR.';

-- ═════════════════════════════════════════════════════════════════════════════
-- SCHEMA: geo
-- ═════════════════════════════════════════════════════════════════════════════

-- Parcel Geometries (versioned)
CREATE TABLE geo.parcel_geometries (
  id                        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  parcel_id                 UUID NOT NULL REFERENCES identity.parcels(id) ON DELETE CASCADE,
  geometry                  GEOMETRY(MULTIPOLYGON, 4326) NOT NULL,
  accuracy_class            VARCHAR(20) NOT NULL
                              CHECK (accuracy_class IN ('A', 'B', 'C', 'D', 'UNKNOWN')),
  -- A = sub-metre GPS/CORS, B = 1-5m DGPS, C = 5-20m GPS, D = >20m or digitised from unrectified maps
  crs_native                VARCHAR(50),   -- Original CRS before reprojection, e.g. EPSG:32643
  source_survey_date        DATE,
  digitisation_method       VARCHAR(100),  -- ETS | CORS_GNSS | DRONE_LiDAR | CADASTRAL_DIGITISE | MANUAL_TRACE
  georeferencing_method     VARCHAR(100),  -- GCP_BASED | CONTROL_NETWORK | NOT_GEOREFERENCED
  area_sq_m                 NUMERIC(20, 4) GENERATED ALWAYS AS
                              (ST_Area(geometry::geography)) STORED,
  area_native               NUMERIC(20, 6),
  area_unit_native          VARCHAR(50),
  area_conversion_source    VARCHAR(200),  -- Reference to reference.unit_conversions
  created_at                TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  is_active                 BOOLEAN NOT NULL DEFAULT true,
  version_number            INTEGER NOT NULL DEFAULT 1,
  replaced_by_id            UUID REFERENCES geo.parcel_geometries(id),
  reason_for_update         TEXT
);
COMMENT ON TABLE geo.parcel_geometries IS 'PostGIS polygon store for parcels. Versioned: when geometry is corrected, old row is deactivated and replaced_by_id links to the new row. area_sq_m is auto-computed.';

-- Administrative Boundaries (LGD-aligned)
CREATE TABLE geo.administrative_boundaries (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  level            VARCHAR(20) NOT NULL
                     CHECK (level IN ('STATE', 'DISTRICT', 'SUBDISTRICT', 'VILLAGE', 'WARD', 'BLOCK', 'URBAN_LOCAL_BODY')),
  lgd_code         VARCHAR(20) UNIQUE NOT NULL REFERENCES reference.lgd_hierarchy(lgd_code),
  name_en          VARCHAR(200) NOT NULL,
  name_local       VARCHAR(200),
  script_local     VARCHAR(50),
  parent_lgd_code  VARCHAR(20) REFERENCES reference.lgd_hierarchy(lgd_code),
  geometry         GEOMETRY(MULTIPOLYGON, 4326),
  area_sq_km       NUMERIC(15, 4),
  hierarchy_type   VARCHAR(20) NOT NULL DEFAULT 'REVENUE'
                     CHECK (hierarchy_type IN ('REVENUE', 'LOCAL_BODY')),
  source_dataset   VARCHAR(200),  -- e.g. OSGIS_2023, CENSUS_2011
  created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE geo.administrative_boundaries IS 'Vector boundaries of all LGD administrative units. Used for spatial joins to assign parcel hierarchy and for map display.';

-- Restriction Zones (forest, coastal regulation, defence, heritage)
CREATE TABLE geo.restriction_zones (
  id                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  zone_type                VARCHAR(50) NOT NULL
                             CHECK (zone_type IN ('FOREST', 'WATER_BODY', 'COASTAL_REG', 'HERITAGE_PROTECTED', 'DEFENCE', 'AIRPORT', 'METRO_ALIGNMENT', 'FLOOD_PLAIN', 'ECO_SENSITIVE', 'TRIBAL_AREA')),
  name                     VARCHAR(200),
  geometry                 GEOMETRY(GEOMETRY, 4326) NOT NULL,  -- GEOMETRY allows both polygon and multipolygon inputs
  legal_basis              VARCHAR(200),   -- Forest Conservation Act 1980, etc.
  authority                VARCHAR(200),   -- MoEFCC, ASI, MoD, etc.
  restriction_description  TEXT,
  buffer_metres            NUMERIC(10, 2) NOT NULL DEFAULT 0,  -- Statutory buffer distance
  state_lgd_code           VARCHAR(10) REFERENCES reference.lgd_hierarchy(lgd_code),
  source_dataset           VARCHAR(200),
  is_active                BOOLEAN NOT NULL DEFAULT true,
  created_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at               TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE geo.restriction_zones IS 'Statutory exclusion and restriction areas overlaid on parcels. Parcels intersecting a zone trigger an alert in the trust-engine.';

-- Topology Conflicts (auto-detected overlaps, gaps, slivers)
CREATE TABLE geo.topology_conflicts (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  conflict_type         VARCHAR(50) NOT NULL
                          CHECK (conflict_type IN ('OVERLAP', 'GAP', 'SLIVER', 'AREA_MISMATCH', 'BOUNDARY_MISMATCH', 'DUPLICATE_PARCEL')),
  parcel_id_1           UUID REFERENCES identity.parcels(id),
  parcel_id_2           UUID REFERENCES identity.parcels(id),
  geometry              GEOMETRY(GEOMETRY, 4326),  -- The conflicting geometry (intersection polygon, gap, etc.)
  overlap_area_sq_m     NUMERIC(20, 4),
  area_mismatch_sq_m    NUMERIC(20, 4),  -- Difference between stated area and computed area
  detected_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  detection_method      VARCHAR(50) DEFAULT 'AUTO',  -- AUTO | MANUAL | EXTERNAL_REPORT
  resolution_status     VARCHAR(20) NOT NULL DEFAULT 'OPEN'
                          CHECK (resolution_status IN ('OPEN', 'UNDER_REVIEW', 'RESOLVED', 'ACCEPTED_AS_IS', 'INVALID')),
  resolved_at           TIMESTAMPTZ,
  resolver_id           VARCHAR(100),
  resolution_notes      TEXT,
  CONSTRAINT conflict_different_parcels CHECK (parcel_id_1 IS NULL OR parcel_id_2 IS NULL OR parcel_id_1 <> parcel_id_2)
);
COMMENT ON TABLE geo.topology_conflicts IS 'Records of detected topological inconsistencies. OPEN conflicts are shown as flags on the parcel detail view and trigger ML scoring uplift.';

-- ═════════════════════════════════════════════════════════════════════════════
-- SCHEMA: revenue
-- ═════════════════════════════════════════════════════════════════════════════

-- Party Registry (individuals, companies, government bodies)
-- Must be created before rights/mutations which reference it
CREATE TABLE revenue.parties (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  party_type          VARCHAR(20) NOT NULL
                        CHECK (party_type IN ('INDIVIDUAL', 'COMPANY', 'GOVERNMENT', 'TRUST', 'JOINT', 'COOPERATIVE', 'WAQF', 'BHOODAN')),
  name_en             VARCHAR(300),
  name_local          VARCHAR(300),
  name_phonetic_key   VARCHAR(300),  -- Metaphone/Soundex key for fuzzy matching
  name_trigram        TSVECTOR,      -- Updated by trigger for full-text search
  id_type             VARCHAR(50),   -- AADHAAR_HASH | PAN | VOTER_ID | CIN | TAN | GST | PASSPORT | RATION
  id_hash             VARCHAR(200),  -- Salted SHA-256 of the actual ID — never plaintext
  date_of_birth       DATE,          -- For disambiguation; stored only if needed
  guardian_name_en    VARCHAR(200),  -- Father/Mother/Husband name (as appearing on records)
  guardian_type       VARCHAR(20),   -- FATHER | MOTHER | HUSBAND | GUARDIAN
  address_lgd_code    VARCHAR(20) REFERENCES reference.lgd_hierarchy(lgd_code),
  address_text        VARCHAR(500),
  created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  is_active           BOOLEAN NOT NULL DEFAULT true
);
COMMENT ON TABLE revenue.parties IS 'De-duplicated party (person/entity) registry. IDs are stored as salted hashes only. name_phonetic_key enables transliteration-aware matching across states.';

-- Records of Rights (RoR / Pahani / Khata)
CREATE TABLE revenue.records_of_rights (
  id                        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  parcel_id                 UUID NOT NULL REFERENCES identity.parcels(id),
  ror_id                    VARCHAR(100),           -- State-specific RoR identifier (Pahani number, Khata number, etc.)
  record_date               DATE,
  survey_number             VARCHAR(100),
  sub_survey_number         VARCHAR(50),
  hissa_number              VARCHAR(50),            -- Sub-division within survey number
  land_classification       VARCHAR(100),           -- Mapped through reference.code_lists
  land_use                  VARCHAR(100),
  irrigated                 BOOLEAN,
  water_source              VARCHAR(100),           -- CANAL | WELL | BOREWELL | RAINWATER | NONE
  soil_type                 VARCHAR(100),
  area_sq_m                 NUMERIC(20, 4),
  area_native               NUMERIC(20, 6),
  area_unit_native          VARCHAR(50),
  area_conversion_source    VARCHAR(200),
  -- Provenance (mandatory on every record)
  source_department         VARCHAR(100) NOT NULL,
  source_system             VARCHAR(100) NOT NULL,
  source_as_of_date         DATE NOT NULL,
  data_freshness_status     VARCHAR(20) NOT NULL DEFAULT 'CACHED'
                              CHECK (data_freshness_status IN ('LIVE', 'CACHED', 'SYNTHETIC')),
  last_synced_at            TIMESTAMPTZ,
  sync_failure_reason       TEXT,
  created_at                TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  is_active                 BOOLEAN NOT NULL DEFAULT true
);
COMMENT ON TABLE revenue.records_of_rights IS 'The canonical revenue record for a parcel (Pahani/Khata/RoR). Provenance columns are mandatory; data_freshness_status indicates how current this snapshot is.';

-- Rights (ownership, tenancy, etc. within a RoR)
CREATE TABLE revenue.rights (
  id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  parcel_id               UUID NOT NULL REFERENCES identity.parcels(id),
  ror_id                  UUID REFERENCES revenue.records_of_rights(id),
  right_type              VARCHAR(50) NOT NULL
                            CHECK (right_type IN ('OWNERSHIP', 'TENANCY', 'SHARECROP', 'OCCUPANCY', 'BHOODAN', 'INAM', 'PORAMBOKE', 'GOVERNMENT', 'LEASE', 'MORTGAGE_POSSESSION', 'ENCROACHMENT')),
  party_id                UUID REFERENCES revenue.parties(id),
  share_numerator         INTEGER NOT NULL DEFAULT 1 CHECK (share_numerator > 0),
  share_denominator       INTEGER NOT NULL DEFAULT 1 CHECK (share_denominator > 0),
  valid_from              DATE,
  valid_to                DATE,
  -- Provenance
  source_department       VARCHAR(100) NOT NULL,
  source_as_of_date       DATE NOT NULL,
  data_freshness_status   VARCHAR(20) NOT NULL DEFAULT 'CACHED'
                            CHECK (data_freshness_status IN ('LIVE', 'CACHED', 'SYNTHETIC')),
  created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT rights_valid_share CHECK (share_numerator <= share_denominator),
  CONSTRAINT rights_validity_range CHECK (valid_from IS NULL OR valid_to IS NULL OR valid_from <= valid_to)
);
COMMENT ON TABLE revenue.rights IS 'Individual rights entries within a RoR. Multiple rows per parcel cover joint ownership (different share fractions), tenancy and government poramboke.';

-- Mutations (transfers and changes of land rights)
CREATE TABLE revenue.mutations (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  parcel_id         UUID NOT NULL REFERENCES identity.parcels(id),
  mutation_number   VARCHAR(100),
  mutation_type     VARCHAR(50) NOT NULL
                      CHECK (mutation_type IN ('SALE', 'INHERITANCE', 'PARTITION', 'GIFT', 'COURT_ORDER', 'GOVERNMENT_ACQUISITION', 'LAND_REFORM', 'BHOODAN_TRANSFER', 'EXCHANGE', 'LEASE', 'MORTGAGE')),
  from_party_id     UUID REFERENCES revenue.parties(id),
  to_party_id       UUID REFERENCES revenue.parties(id),
  mutation_date     DATE,
  document_ref      VARCHAR(200),         -- Registration deed / court order reference
  area_transferred_sq_m NUMERIC(20, 4),
  consideration_amount NUMERIC(20, 2),    -- NULL for non-sale mutations
  status            VARCHAR(20) NOT NULL DEFAULT 'PENDING'
                      CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED', 'UNDER_DISPUTE', 'CANCELLED')),
  officer_id        VARCHAR(100),
  approved_at       TIMESTAMPTZ,
  notes             TEXT,
  -- Provenance
  source_department VARCHAR(100) NOT NULL,
  source_as_of_date DATE NOT NULL,
  data_freshness_status VARCHAR(20) NOT NULL DEFAULT 'CACHED'
                          CHECK (data_freshness_status IN ('LIVE', 'CACHED', 'SYNTHETIC')),
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE revenue.mutations IS 'Records all changes of ownership/rights on a parcel. Status-tracked through approval workflow. Links to registration.deeds where a deed was executed.';

-- ═════════════════════════════════════════════════════════════════════════════
-- SCHEMA: registration
-- ═════════════════════════════════════════════════════════════════════════════

-- Registered Deeds
CREATE TABLE registration.deeds (
  id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  parcel_id               UUID NOT NULL REFERENCES identity.parcels(id),
  deed_number             VARCHAR(100) NOT NULL,
  deed_type               VARCHAR(50) NOT NULL
                            CHECK (deed_type IN ('SALE', 'GIFT', 'MORTGAGE', 'RELEASE', 'PARTITION', 'LEASE', 'WILL', 'POWER_OF_ATTORNEY', 'SETTLEMENT', 'EXCHANGE', 'RECTIFICATION')),
  sro_code                VARCHAR(50) NOT NULL,   -- Sub-Registrar Office code
  registration_date       DATE NOT NULL,
  execution_date          DATE,
  seller_party_id         UUID REFERENCES revenue.parties(id),
  buyer_party_id          UUID REFERENCES revenue.parties(id),
  consideration_amount    NUMERIC(20, 2),
  consideration_currency  VARCHAR(10) NOT NULL DEFAULT 'INR',
  market_value            NUMERIC(20, 2),         -- As assessed for stamp duty
  stamp_duty_paid         NUMERIC(20, 2),
  registration_fee_paid   NUMERIC(20, 2),
  document_url            VARCHAR(500),           -- Encrypted S3/NIC reference
  is_registered           BOOLEAN NOT NULL DEFAULT true,
  -- Provenance
  source_department       VARCHAR(100) NOT NULL,
  source_as_of_date       DATE NOT NULL,
  data_freshness_status   VARCHAR(20) NOT NULL DEFAULT 'CACHED'
                            CHECK (data_freshness_status IN ('LIVE', 'CACHED', 'SYNTHETIC')),
  created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT deed_date_order CHECK (execution_date IS NULL OR execution_date <= registration_date),
  UNIQUE (sro_code, deed_number, registration_date)
);
COMMENT ON TABLE registration.deeds IS 'Registered instruments from SRO / NGDRS. Linked to parcels and parties. document_url holds an encrypted reference to the scanned document.';

-- Encumbrances
CREATE TABLE registration.encumbrances (
  id                        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  parcel_id                 UUID NOT NULL REFERENCES identity.parcels(id),
  encumbrance_type          VARCHAR(50) NOT NULL
                              CHECK (encumbrance_type IN ('MORTGAGE', 'LIEN', 'COURT_ATTACHMENT', 'LEASE', 'EASEMENT', 'INALIENABILITY', 'GOVT_CLAIM', 'IT_ATTACHMENT')),
  in_favour_of_party_id     UUID REFERENCES revenue.parties(id),
  created_date              DATE,
  expiry_date               DATE,
  amount                    NUMERIC(20, 2),
  is_active                 BOOLEAN NOT NULL DEFAULT true,
  release_deed_id           UUID REFERENCES registration.deeds(id),
  release_date              DATE,
  -- Provenance
  source_department         VARCHAR(100) NOT NULL,
  source_as_of_date         DATE NOT NULL,
  data_freshness_status     VARCHAR(20) NOT NULL DEFAULT 'CACHED'
                              CHECK (data_freshness_status IN ('LIVE', 'CACHED', 'SYNTHETIC')),
  created_at                TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT encumbrance_dates CHECK (created_date IS NULL OR expiry_date IS NULL OR created_date <= expiry_date)
);
COMMENT ON TABLE registration.encumbrances IS 'Active and historical encumbrances on parcels (mortgages, court attachments, IT liens, etc.). is_active=false when released.';

-- ═════════════════════════════════════════════════════════════════════════════
-- SCHEMA: planning
-- ═════════════════════════════════════════════════════════════════════════════

CREATE TABLE planning.zones (
  id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  parcel_id               UUID NOT NULL REFERENCES identity.parcels(id),
  zone_code               VARCHAR(50),
  zone_type               VARCHAR(100)
                            CHECK (zone_type IN ('RESIDENTIAL', 'COMMERCIAL', 'INDUSTRIAL', 'AGRICULTURAL', 'GREEN', 'MIXED_USE', 'PUBLIC_SEMI_PUBLIC', 'TRANSPORT', 'SPECIAL_PURPOSE', 'NO_DEVELOPMENT', 'WATER_BODY')),
  fsi_allowed             NUMERIC(5, 2),   -- Floor Space Index
  ground_coverage_pct     NUMERIC(5, 2) CHECK (ground_coverage_pct BETWEEN 0 AND 100),
  max_height_m            NUMERIC(8, 2),
  setback_front_m         NUMERIC(6, 2),
  setback_rear_m          NUMERIC(6, 2),
  setback_side_m          NUMERIC(6, 2),
  master_plan_year        INTEGER,
  master_plan_authority   VARCHAR(200),
  -- Provenance
  source_department       VARCHAR(100) NOT NULL,
  source_as_of_date       DATE NOT NULL,
  data_freshness_status   VARCHAR(20) NOT NULL DEFAULT 'CACHED'
                            CHECK (data_freshness_status IN ('LIVE', 'CACHED', 'SYNTHETIC')),
  created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE planning.zones IS 'Master plan zoning parameters for urban parcels. FSI, coverage, height limits sourced from municipality / development authority.';

CREATE TABLE planning.building_permissions (
  id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  parcel_id               UUID NOT NULL REFERENCES identity.parcels(id),
  permission_number       VARCHAR(100),
  permission_type         VARCHAR(50)
                            CHECK (permission_type IN ('NEW_CONSTRUCTION', 'EXTENSION', 'ALTERATION', 'CHANGE_OF_USE', 'DEMOLITION', 'RENOVATION', 'LAYOUT_PLAN')),
  status                  VARCHAR(30) NOT NULL DEFAULT 'APPLIED'
                            CHECK (status IN ('APPLIED', 'UNDER_SCRUTINY', 'APPROVED', 'APPROVED_WITH_CONDITIONS', 'REJECTED', 'REVOKED', 'COMPLETED', 'LAPSED')),
  applied_date            DATE,
  approved_date           DATE,
  validity_upto           DATE,
  completed_date          DATE,
  applicant_party_id      UUID REFERENCES revenue.parties(id),
  floor_count             INTEGER,
  approved_area_sq_m      NUMERIC(20, 4),
  built_up_area_sq_m      NUMERIC(20, 4),
  -- Provenance
  source_department       VARCHAR(100) NOT NULL,
  source_as_of_date       DATE NOT NULL,
  data_freshness_status   VARCHAR(20) NOT NULL DEFAULT 'CACHED'
                            CHECK (data_freshness_status IN ('LIVE', 'CACHED', 'SYNTHETIC')),
  created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE planning.building_permissions IS 'Building permission records from municipal bodies / development authorities. Linked to parcels for encumbrance and compliance checking.';

CREATE TABLE planning.disputes (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  parcel_id           UUID NOT NULL REFERENCES identity.parcels(id),
  case_number         VARCHAR(100),
  court               VARCHAR(200),
  case_type           VARCHAR(100),   -- TITLE_DISPUTE | BOUNDARY | PARTITION | EVICTION | ACQUISITION
  status              VARCHAR(30),    -- PENDING | DECREE_PASSED | APPEAL | SETTLED | WITHDRAWN
  filed_date          DATE,
  last_heard_date     DATE,
  parties_description TEXT,
  decree_in_favour    VARCHAR(100),
  -- Confidence (IMPORTANT: never assert a court case is certain without explicit confirmation)
  confidence          VARCHAR(20) NOT NULL DEFAULT 'POSSIBLE'
                        CHECK (confidence IN ('POSSIBLE', 'CONFIRMED', 'RULED_OUT')),
  linkage_method      VARCHAR(50)
                        CHECK (linkage_method IN ('PARTY_MATCH', 'NLP_EXTRACT', 'MANUAL', 'DIRECT_IMPORT')),
  linked_by           VARCHAR(100),
  linked_at           TIMESTAMPTZ,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE planning.disputes IS 'Court and quasi-judicial dispute records linked to parcels. confidence=POSSIBLE when linked via NLP/party-match; confidence=CONFIRMED only after manual verification.';

-- ═════════════════════════════════════════════════════════════════════════════
-- SCHEMA: fiscal
-- ═════════════════════════════════════════════════════════════════════════════

CREATE TABLE fiscal.property_tax (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  parcel_id             UUID NOT NULL REFERENCES identity.parcels(id),
  assessment_year       INTEGER NOT NULL CHECK (assessment_year BETWEEN 1950 AND 2100),
  annual_value          NUMERIC(20, 2),
  tax_amount            NUMERIC(20, 2) CHECK (tax_amount >= 0),
  rebate_amount         NUMERIC(20, 2) DEFAULT 0,
  penalty_amount        NUMERIC(20, 2) DEFAULT 0,
  arrears               NUMERIC(20, 2) NOT NULL DEFAULT 0 CHECK (arrears >= 0),
  total_due             NUMERIC(20, 2) GENERATED ALWAYS AS
                          (COALESCE(tax_amount,0) - COALESCE(rebate_amount,0) + COALESCE(penalty_amount,0) + COALESCE(arrears,0)) STORED,
  payment_status        VARCHAR(20) NOT NULL DEFAULT 'DUE'
                          CHECK (payment_status IN ('PAID', 'PARTIAL', 'DUE', 'OVERDUE', 'EXEMPTED', 'DISPUTED')),
  last_payment_date     DATE,
  last_payment_amount   NUMERIC(20, 2),
  ulb_code              VARCHAR(50),   -- Urban Local Body code
  ward_code             VARCHAR(50),
  -- Provenance
  source_department     VARCHAR(100) NOT NULL,
  source_as_of_date     DATE NOT NULL,
  data_freshness_status VARCHAR(20) NOT NULL DEFAULT 'CACHED'
                          CHECK (data_freshness_status IN ('LIVE', 'CACHED', 'SYNTHETIC')),
  created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (parcel_id, assessment_year, ulb_code)
);
COMMENT ON TABLE fiscal.property_tax IS 'Annual property tax records from ULBs. total_due is auto-computed. Multiple rows per parcel if it falls across ULB jurisdictions.';

-- ═════════════════════════════════════════════════════════════════════════════
-- SCHEMA: audit
-- ═════════════════════════════════════════════════════════════════════════════

-- Append-only audit event log (partitioned by month)
CREATE TABLE audit.events (
  id             UUID NOT NULL DEFAULT gen_random_uuid(),
  event_time     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  event_type     VARCHAR(100) NOT NULL,
  -- PARCEL_VIEWED | PARCEL_SEARCHED | RECORD_UPDATED | RECORD_CREATED |
  -- ACCESS_GRANTED | ACCESS_REVOKED | LOGIN | LOGOUT | BULK_EXPORT |
  -- CONSENT_GIVEN | CONSENT_WITHDRAWN | MUTATION_APPROVED | MUTATION_REJECTED
  actor_id       VARCHAR(200) NOT NULL,  -- Keycloak subject (UUID or system account)
  actor_role     VARCHAR(100),
  actor_org      VARCHAR(200),
  resource_type  VARCHAR(100),           -- PARCEL | DEED | MUTATION | RIGHTS | etc.
  resource_id    UUID,
  parcel_id      UUID,                   -- Denormalized for fast "who accessed parcel X" queries
  purpose        VARCHAR(200),           -- Purpose-bound access: e.g. "LOAN_VERIFICATION", "LAND_ACQUISITION"
  ip_address     INET,
  session_id     VARCHAR(200),
  user_agent     VARCHAR(500),
  payload        JSONB,                  -- Additional event-specific data
  -- Append-only safety check
  CONSTRAINT no_future_events CHECK (event_time <= NOW() + INTERVAL '1 minute'),
  PRIMARY KEY (id, event_time)           -- Composite PK needed for partitioned tables
) PARTITION BY RANGE (event_time);

COMMENT ON TABLE audit.events IS 'Append-only audit ledger. Never UPDATE or DELETE. Partitioned monthly. actor_id is always the Keycloak subject. parcel_id is denormalized for O(1) "who accessed my land" queries.';

-- Create initial monthly partitions (Sep 2026 onwards)
CREATE TABLE audit.events_2026_09 PARTITION OF audit.events
  FOR VALUES FROM ('2026-09-01') TO ('2026-10-01');

CREATE TABLE audit.events_2026_10 PARTITION OF audit.events
  FOR VALUES FROM ('2026-10-01') TO ('2026-11-01');

CREATE TABLE audit.events_2026_11 PARTITION OF audit.events
  FOR VALUES FROM ('2026-11-01') TO ('2026-12-01');

CREATE TABLE audit.events_2026_12 PARTITION OF audit.events
  FOR VALUES FROM ('2026-12-01') TO ('2027-01-01');

CREATE TABLE audit.events_2027_01 PARTITION OF audit.events
  FOR VALUES FROM ('2027-01-01') TO ('2027-02-01');

CREATE TABLE audit.events_2027_02 PARTITION OF audit.events
  FOR VALUES FROM ('2027-02-01') TO ('2027-03-01');

CREATE TABLE audit.events_2027_03 PARTITION OF audit.events
  FOR VALUES FROM ('2027-03-01') TO ('2027-04-01');

-- Default catch-all partition for unexpected dates
CREATE TABLE audit.events_default PARTITION OF audit.events DEFAULT;

-- ═════════════════════════════════════════════════════════════════════════════
-- SCHEMA: ml
-- ═════════════════════════════════════════════════════════════════════════════

-- ML Conflict Scores
CREATE TABLE ml.conflict_scores (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  parcel_id             UUID NOT NULL REFERENCES identity.parcels(id),
  score_type            VARCHAR(50) NOT NULL
                          CHECK (score_type IN ('CROSS_REGISTRY', 'SPATIAL', 'ANOMALY', 'GRAPH_NETWORK', 'COMPOSITE')),
  score_value           NUMERIC(6, 4) NOT NULL CHECK (score_value BETWEEN 0.0 AND 1.0),
  risk_band             VARCHAR(10) NOT NULL
                          CHECK (risk_band IN ('HIGH', 'MEDIUM', 'LOW', 'NEGLIGIBLE')),
  percentile_rank       NUMERIC(6, 2) CHECK (percentile_rank BETWEEN 0 AND 100),
  method                VARCHAR(100),   -- gradient_boost_v2 | isolation_forest | gnn_v1
  contributing_factors  JSONB,          -- Human-readable key:value explanation
  computed_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  model_version         VARCHAR(50),
  is_latest             BOOLEAN NOT NULL DEFAULT true,
  UNIQUE (parcel_id, score_type, model_version)
);
COMMENT ON TABLE ml.conflict_scores IS 'ML-computed conflict and anomaly scores per parcel. is_latest=true for the current score; old scores retained for trend analysis.';

-- Entity Resolution Links (cross-system record matching)
CREATE TABLE ml.entity_resolution_links (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  parcel_id           UUID NOT NULL REFERENCES identity.parcels(id),
  source_system_a     VARCHAR(100) NOT NULL,
  record_id_a         VARCHAR(200) NOT NULL,
  source_system_b     VARCHAR(100) NOT NULL,
  record_id_b         VARCHAR(200) NOT NULL,
  confidence_score    NUMERIC(6, 4) NOT NULL CHECK (confidence_score BETWEEN 0.0 AND 1.0),
  method              VARCHAR(50) NOT NULL
                        CHECK (method IN ('SPATIAL', 'DETERMINISTIC', 'PROBABILISTIC', 'PHONETIC', 'HUMAN_REVIEW', 'HYBRID')),
  is_confirmed        BOOLEAN,       -- NULL = not yet reviewed; true = confirmed; false = rejected
  confirmed_by        VARCHAR(100),  -- Officer ID
  confirmed_at        TIMESTAMPTZ,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (parcel_id, source_system_a, record_id_a, source_system_b, record_id_b)
);
COMMENT ON TABLE ml.entity_resolution_links IS 'Probabilistic and deterministic links between records of the same parcel across different source systems. Human review can confirm or reject.';

-- Transaction Network Anomaly Flags
CREATE TABLE ml.transaction_network_flags (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  flag_type         VARCHAR(50) NOT NULL
                      CHECK (flag_type IN ('CIRCULAR_CHAIN', 'ABNORMAL_COOCCURRENCE', 'RAPID_FLIP', 'PRICE_ANOMALY', 'MULTI_STATE_CHAIN', 'DORMANT_PARCEL_ACTIVATION')),
  parcel_ids        UUID[] NOT NULL,    -- All parcels involved
  party_ids         UUID[],             -- All parties in the network
  chain_length      INTEGER,            -- For CIRCULAR_CHAIN
  time_window_days  INTEGER,            -- How many days the pattern spans
  description       TEXT NOT NULL,
  confidence_score  NUMERIC(6, 4) CHECK (confidence_score BETWEEN 0.0 AND 1.0),
  detected_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  reviewed_status   VARCHAR(20) NOT NULL DEFAULT 'UNREVIEWED'
                      CHECK (reviewed_status IN ('UNREVIEWED', 'UNDER_REVIEW', 'CONFIRMED_SUSPICIOUS', 'FALSE_POSITIVE'))
);
COMMENT ON TABLE ml.transaction_network_flags IS 'Graph-network anomaly flags. CIRCULAR_CHAIN: A→B→C→A within short time. RAPID_FLIP: Multiple sales of same parcel within 90 days. All array fields enable efficient overlap queries.';

-- Satellite Land-Use Change Detection
CREATE TABLE ml.land_use_changes (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  parcel_id             UUID NOT NULL REFERENCES identity.parcels(id),
  change_type           VARCHAR(50) NOT NULL
                          CHECK (change_type IN ('AGRI_TO_NON_AGRI', 'ENCROACHMENT_WATER', 'ENCROACHMENT_FOREST', 'LAYOUT_DEVELOPMENT', 'CONSTRUCTION_NEW', 'DEMOLITION', 'DEFORESTATION', 'WATER_BODY_FILL')),
  detected_from_date    DATE,           -- Start of time window (before image)
  detected_to_date      DATE,           -- End of time window (after image)
  confidence_score      NUMERIC(6, 4) CHECK (confidence_score BETWEEN 0.0 AND 1.0),
  satellite_source      VARCHAR(100),   -- Sentinel-2 | Landsat-8 | Resourcesat-2 | Cartosat-3
  image_date_before     DATE,
  image_date_after      DATE,
  ndvi_change           NUMERIC(8, 4),  -- Negative = vegetation loss
  ndbi_change           NUMERIC(8, 4),  -- Positive = built-up increase
  ndwi_change           NUMERIC(8, 4),  -- Negative = water body reduction
  change_area_sq_m      NUMERIC(20, 4),
  bounding_geometry     GEOMETRY(POLYGON, 4326),
  reviewed_status       VARCHAR(20) NOT NULL DEFAULT 'UNREVIEWED'
                          CHECK (reviewed_status IN ('UNREVIEWED', 'UNDER_REVIEW', 'CONFIRMED', 'FALSE_POSITIVE', 'REFERRED_TO_DEPT')),
  reviewed_by           VARCHAR(100),
  reviewed_at           TIMESTAMPTZ,
  review_notes          TEXT,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE ml.land_use_changes IS 'Satellite-derived land-use change events. NDVI/NDBI/NDWI spectral indices drive classification. reviewed_status tracks field verification.';

-- ═════════════════════════════════════════════════════════════════════════════
-- Updated_at triggers for mutable tables
-- ═════════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$;

CREATE TRIGGER identity_parcels_updated_at
  BEFORE UPDATE ON identity.parcels
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

CREATE TRIGGER reference_lgd_hierarchy_updated_at
  BEFORE UPDATE ON reference.lgd_hierarchy
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

CREATE TRIGGER geo_admin_boundaries_updated_at
  BEFORE UPDATE ON geo.administrative_boundaries
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

CREATE TRIGGER geo_restriction_zones_updated_at
  BEFORE UPDATE ON geo.restriction_zones
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

CREATE TRIGGER revenue_parties_updated_at
  BEFORE UPDATE ON revenue.parties
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
