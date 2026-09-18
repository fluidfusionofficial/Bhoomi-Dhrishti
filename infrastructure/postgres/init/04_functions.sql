-- ─────────────────────────────────────────────────────────────────────────────
-- Bhoomi Dhrishti – 04_functions.sql
-- ST_AsMVT tile function, phonetic helpers, BDPR generator, search helpers
-- ─────────────────────────────────────────────────────────────────────────────

-- ═════════════════════════════════════════════════════════════════════════════
-- MVT (Mapbox Vector Tile) tile generation
-- Called by geospatial service: GET /tiles/{z}/{x}/{y}.pbf
-- ═════════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE FUNCTION geo.get_parcel_tile(
  z INTEGER,
  x INTEGER,
  y INTEGER,
  state_filter VARCHAR DEFAULT NULL,
  district_filter VARCHAR DEFAULT NULL
)
RETURNS BYTEA
LANGUAGE plpgsql STABLE
AS $$
DECLARE
  tile_bbox  GEOMETRY;
  tile_data  BYTEA;
BEGIN
  -- Convert tile coordinates to a web-mercator bounding box
  tile_bbox := ST_TileEnvelope(z, x, y);

  WITH parcel_clip AS (
    SELECT
      p.id,
      p.bdpr,
      p.ulpin,
      p.is_urban,
      p.state_code,
      p.district_code,
      ST_AsMVTGeom(
        ST_Transform(g.geometry, 3857),  -- Reproject to web-mercator
        tile_bbox,
        4096,    -- extent
        64,      -- buffer
        true     -- clip to tile
      ) AS mvt_geom,
      g.accuracy_class,
      -- Attach latest conflict score for choropleth coloring
      cs.risk_band,
      cs.score_value AS conflict_score
    FROM identity.parcels p
    JOIN geo.parcel_geometries g ON g.parcel_id = p.id AND g.is_active = true
    LEFT JOIN LATERAL (
      SELECT risk_band, score_value
      FROM ml.conflict_scores
      WHERE parcel_id = p.id AND is_latest = true AND score_type = 'COMPOSITE'
      LIMIT 1
    ) cs ON true
    WHERE ST_Intersects(ST_Transform(g.geometry, 3857), tile_bbox)
      AND p.is_active = true
      AND (state_filter IS NULL OR p.state_code = state_filter)
      AND (district_filter IS NULL OR p.district_code = district_filter)
  )
  SELECT ST_AsMVT(parcel_clip.*, 'parcels', 4096, 'mvt_geom')
  INTO tile_data
  FROM parcel_clip
  WHERE mvt_geom IS NOT NULL;

  RETURN COALESCE(tile_data, ''::BYTEA);
END;
$$;

COMMENT ON FUNCTION geo.get_parcel_tile IS 'Returns a Mapbox Vector Tile (MVT) protobuf for the given z/x/y tile coordinate. Optionally filtered by state/district. Includes risk_band for choropleth rendering.';

-- ═════════════════════════════════════════════════════════════════════════════
-- MVT for restriction zones overlay
-- ═════════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE FUNCTION geo.get_restriction_tile(
  z INTEGER,
  x INTEGER,
  y INTEGER
)
RETURNS BYTEA
LANGUAGE plpgsql STABLE
AS $$
DECLARE
  tile_bbox GEOMETRY;
  tile_data BYTEA;
BEGIN
  tile_bbox := ST_TileEnvelope(z, x, y);

  WITH zone_clip AS (
    SELECT
      id,
      zone_type,
      name,
      buffer_metres,
      ST_AsMVTGeom(
        ST_Transform(
          CASE WHEN buffer_metres > 0
            THEN ST_Buffer(geometry::geography, buffer_metres)::geometry
            ELSE geometry
          END,
          3857
        ),
        tile_bbox, 4096, 64, true
      ) AS mvt_geom
    FROM geo.restriction_zones
    WHERE ST_Intersects(ST_Transform(geometry, 3857), tile_bbox)
      AND is_active = true
  )
  SELECT ST_AsMVT(zone_clip.*, 'restriction_zones', 4096, 'mvt_geom')
  INTO tile_data
  FROM zone_clip
  WHERE mvt_geom IS NOT NULL;

  RETURN COALESCE(tile_data, ''::BYTEA);
END;
$$;

-- ═════════════════════════════════════════════════════════════════════════════
-- BDPR Sequence Generator
-- Format: BD-<2-char-state>-<7-digit-sequence>
-- e.g. BD-TN-0000001
-- ═════════════════════════════════════════════════════════════════════════════

CREATE SEQUENCE IF NOT EXISTS identity.bdpr_sequence
  START 1 INCREMENT 1 MINVALUE 1 MAXVALUE 9999999 CYCLE;

CREATE OR REPLACE FUNCTION identity.generate_bdpr(state_lgd VARCHAR)
RETURNS VARCHAR(20)
LANGUAGE plpgsql
AS $$
DECLARE
  seq_val  BIGINT;
  state_abbr VARCHAR(5);
BEGIN
  SELECT UPPER(SUBSTRING(name_en, 1, 2))
  INTO state_abbr
  FROM reference.lgd_hierarchy
  WHERE lgd_code = state_lgd AND entity_type = 'STATE';

  IF state_abbr IS NULL THEN
    state_abbr := UPPER(SUBSTRING(state_lgd, 1, 2));
  END IF;

  seq_val := nextval('identity.bdpr_sequence');
  RETURN 'BD-' || state_abbr || '-' || LPAD(seq_val::text, 7, '0');
END;
$$;

COMMENT ON FUNCTION identity.generate_bdpr IS 'Generates a new BDPR (Bhoomi Dhrishti Parcel Reference) in format BD-<STATE_ABBR>-<SEQUENCE>.';

-- ═════════════════════════════════════════════════════════════════════════════
-- Phonetic Key Generator (for party name matching)
-- Uses Metaphone approximation for Indian names
-- ═════════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE FUNCTION revenue.compute_phonetic_key(name TEXT)
RETURNS TEXT
LANGUAGE plpgsql IMMUTABLE
AS $$
BEGIN
  IF name IS NULL THEN RETURN NULL; END IF;
  -- Apply unaccent first (handles diacritics in romanized transliterations)
  -- Then double_metaphone for phonetic key
  RETURN lower(dmetaphone(unaccent(regexp_replace(name, '[^a-zA-Z\s]', '', 'g'))));
END;
$$;

-- Trigger to auto-update phonetic key and tsvector on party insert/update
CREATE OR REPLACE FUNCTION revenue.parties_before_upsert()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  -- Compute phonetic key from English name
  NEW.name_phonetic_key := revenue.compute_phonetic_key(NEW.name_en);
  -- Build tsvector from both English and local name
  NEW.name_trigram := to_tsvector('bhoomi_search',
    COALESCE(NEW.name_en, '') || ' ' || COALESCE(NEW.name_local, '')
  );
  RETURN NEW;
END;
$$;

CREATE TRIGGER revenue_parties_phonetic_update
  BEFORE INSERT OR UPDATE ON revenue.parties
  FOR EACH ROW EXECUTE FUNCTION revenue.parties_before_upsert();

-- ═════════════════════════════════════════════════════════════════════════════
-- Spatial Containment Helper
-- Returns all parcels whose geometry intersects a given bounding box or polygon
-- ═════════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE FUNCTION geo.parcels_in_bbox(
  min_lon FLOAT,
  min_lat FLOAT,
  max_lon FLOAT,
  max_lat FLOAT
)
RETURNS TABLE (
  parcel_id    UUID,
  bdpr         VARCHAR,
  ulpin        VARCHAR,
  accuracy_class VARCHAR,
  area_sq_m    NUMERIC
)
LANGUAGE sql STABLE
AS $$
  SELECT p.id, p.bdpr, p.ulpin, g.accuracy_class, g.area_sq_m
  FROM identity.parcels p
  JOIN geo.parcel_geometries g ON g.parcel_id = p.id AND g.is_active = true
  WHERE ST_Intersects(
    g.geometry,
    ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat, 4326)
  )
  AND p.is_active = true;
$$;

-- ═════════════════════════════════════════════════════════════════════════════
-- Topology Conflict Auto-Detector
-- Detects overlapping parcels and inserts into geo.topology_conflicts
-- Run as a periodic maintenance job (daily)
-- ═════════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE FUNCTION geo.detect_topology_conflicts()
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
  inserted_count INTEGER := 0;
BEGIN
  -- Detect overlapping parcel pairs (only open conflicts not already logged)
  INSERT INTO geo.topology_conflicts (
    id, conflict_type, parcel_id_1, parcel_id_2, geometry,
    overlap_area_sq_m, detection_method
  )
  SELECT
    gen_random_uuid(),
    'OVERLAP',
    g1.parcel_id,
    g2.parcel_id,
    ST_Intersection(g1.geometry, g2.geometry),
    ST_Area(ST_Intersection(g1.geometry, g2.geometry)::geography),
    'AUTO'
  FROM geo.parcel_geometries g1
  JOIN geo.parcel_geometries g2 ON
    g1.parcel_id < g2.parcel_id  -- avoid duplicate pairs
    AND g1.is_active = true
    AND g2.is_active = true
    AND ST_Overlaps(g1.geometry, g2.geometry)
    AND ST_Area(ST_Intersection(g1.geometry, g2.geometry)::geography) > 1.0  -- > 1 sq metre
  -- Skip pairs already recorded as open conflicts
  WHERE NOT EXISTS (
    SELECT 1 FROM geo.topology_conflicts tc
    WHERE tc.parcel_id_1 = g1.parcel_id
      AND tc.parcel_id_2 = g2.parcel_id
      AND tc.conflict_type = 'OVERLAP'
      AND tc.resolution_status = 'OPEN'
  );

  GET DIAGNOSTICS inserted_count = ROW_COUNT;
  RETURN inserted_count;
END;
$$;

COMMENT ON FUNCTION geo.detect_topology_conflicts IS 'Scans all active parcel geometries for overlaps and logs new conflicts. Returns count of new conflicts inserted. Schedule via pg_cron or external job.';

-- ═════════════════════════════════════════════════════════════════════════════
-- Provenance Staleness Check
-- Returns records whose source_as_of_date is older than a threshold
-- ═════════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE FUNCTION revenue.stale_records(threshold_days INTEGER DEFAULT 90)
RETURNS TABLE (
  table_name    TEXT,
  parcel_id     UUID,
  source_system VARCHAR,
  as_of_date    DATE,
  days_old      INTEGER
)
LANGUAGE sql STABLE
AS $$
  SELECT 'revenue.records_of_rights', parcel_id, source_system,
         source_as_of_date, (CURRENT_DATE - source_as_of_date)::INTEGER
  FROM revenue.records_of_rights
  WHERE source_as_of_date < CURRENT_DATE - threshold_days
    AND is_active = true
  UNION ALL
  SELECT 'revenue.rights', parcel_id, source_department,
         source_as_of_date, (CURRENT_DATE - source_as_of_date)::INTEGER
  FROM revenue.rights
  WHERE source_as_of_date < CURRENT_DATE - threshold_days
  UNION ALL
  SELECT 'registration.deeds', parcel_id, source_department,
         source_as_of_date, (CURRENT_DATE - source_as_of_date)::INTEGER
  FROM registration.deeds
  WHERE source_as_of_date < CURRENT_DATE - threshold_days
  ORDER BY days_old DESC;
$$;

-- ═════════════════════════════════════════════════════════════════════════════
-- Parcel Summary View (used by citizen-services and search)
-- ═════════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE VIEW identity.parcel_summary AS
SELECT
  p.id,
  p.bdpr,
  p.ulpin,
  p.state_code,
  p.district_code,
  p.village_code,
  p.urban_ward_code,
  p.is_urban,
  p.system_of_record_flag,
  g.area_sq_m,
  g.accuracy_class,
  g.source_survey_date,
  -- Latest conflict score
  cs.risk_band,
  cs.score_value AS conflict_score,
  -- Open topology conflicts
  (SELECT COUNT(*) FROM geo.topology_conflicts tc
   WHERE (tc.parcel_id_1 = p.id OR tc.parcel_id_2 = p.id)
   AND tc.resolution_status = 'OPEN') AS open_topology_conflicts,
  -- Active encumbrances
  (SELECT COUNT(*) FROM registration.encumbrances e
   WHERE e.parcel_id = p.id AND e.is_active = true) AS active_encumbrances,
  -- Active disputes
  (SELECT COUNT(*) FROM planning.disputes d
   WHERE d.parcel_id = p.id AND d.status NOT IN ('SETTLED', 'WITHDRAWN')) AS active_disputes,
  p.created_at,
  p.updated_at
FROM identity.parcels p
LEFT JOIN geo.parcel_geometries g ON g.parcel_id = p.id AND g.is_active = true
LEFT JOIN LATERAL (
  SELECT risk_band, score_value
  FROM ml.conflict_scores
  WHERE parcel_id = p.id AND is_latest = true AND score_type = 'COMPOSITE'
  LIMIT 1
) cs ON true
WHERE p.is_active = true;

COMMENT ON VIEW identity.parcel_summary IS 'Denormalised summary view for quick API responses. Aggregates geometry, conflict score, encumbrance count, dispute count.';
