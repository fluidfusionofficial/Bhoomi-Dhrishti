-- ─────────────────────────────────────────────────────────────────────────────
-- Bhoomi Dhrishti – 00_extensions.sql
-- Load required PostgreSQL extensions
-- Run order: FIRST (before any schema/table creation)
-- ─────────────────────────────────────────────────────────────────────────────

-- Spatial
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS postgis_raster;

-- UUID generation (gen_random_uuid() is built-in in PG14+, but ensure uuid-ossp for compatibility)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Full-text search helpers
CREATE EXTENSION IF NOT EXISTS pg_trgm;        -- Trigram similarity for fuzzy name search
CREATE EXTENSION IF NOT EXISTS unaccent;       -- Accent-insensitive search (Sanskrit/Devanagari romanisation)
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;  -- Soundex / Levenshtein for phonetic party matching

-- Crypto (for hashing Aadhaar tokens etc.)
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- For JSONB path operators in older configs
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "btree_gist";

-- Partitioning helper (built-in, but explicit for documentation)
-- pg_partman is optional but recommended for production auto-partition management
-- CREATE EXTENSION IF NOT EXISTS pg_partman;

-- ─────────────────────────────────────────────────────────────────────────────
-- Unaccent dictionary rule for Devanagari transliteration
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TEXT SEARCH CONFIGURATION IF NOT EXISTS bhoomi_search (COPY = pg_catalog.english);
ALTER TEXT SEARCH CONFIGURATION bhoomi_search
  ALTER MAPPING FOR hword, hword_part, word
  WITH unaccent, simple;
