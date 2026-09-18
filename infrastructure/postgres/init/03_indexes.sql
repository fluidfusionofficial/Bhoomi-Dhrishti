-- ─────────────────────────────────────────────────────────────────────────────
-- Bhoomi Dhrishti – 03_indexes.sql
-- Spatial (GIST), full-text (GIN), and B-tree indexes for performance
-- ─────────────────────────────────────────────────────────────────────────────

-- ═════════════════════════════════════════════════════════════════════════════
-- SCHEMA: identity
-- ═════════════════════════════════════════════════════════════════════════════

-- Primary lookup paths for parcels
CREATE INDEX idx_parcels_ulpin          ON identity.parcels (ulpin) WHERE ulpin IS NOT NULL;
CREATE INDEX idx_parcels_state          ON identity.parcels (state_code);
CREATE INDEX idx_parcels_district       ON identity.parcels (district_code);
CREATE INDEX idx_parcels_village        ON identity.parcels (village_code) WHERE village_code IS NOT NULL;
CREATE INDEX idx_parcels_urban_ward     ON identity.parcels (urban_ward_code) WHERE urban_ward_code IS NOT NULL;
CREATE INDEX idx_parcels_active         ON identity.parcels (is_active) WHERE is_active = true;
CREATE INDEX idx_parcels_bdpr_pattern   ON identity.parcels USING gin (bdpr gin_trgm_ops);

-- Aliases: fast lookup by alias value
CREATE INDEX idx_aliases_parcel         ON identity.parcel_aliases (parcel_id);
CREATE INDEX idx_aliases_type_value     ON identity.parcel_aliases (alias_type, alias_value);
CREATE INDEX idx_aliases_value_trgm     ON identity.parcel_aliases USING gin (alias_value gin_trgm_ops);

-- Lineage: parent/child traversal
CREATE INDEX idx_lineage_parent         ON identity.parcel_lineage (parent_parcel_id);
CREATE INDEX idx_lineage_child          ON identity.parcel_lineage (child_parcel_id);
CREATE INDEX idx_lineage_event_date     ON identity.parcel_lineage (event_date);

-- ═════════════════════════════════════════════════════════════════════════════
-- SCHEMA: geo
-- ═════════════════════════════════════════════════════════════════════════════

-- Spatial index (GIST) — the most critical index in this system
CREATE INDEX idx_parcel_geom_spatial    ON geo.parcel_geometries USING gist (geometry);
CREATE INDEX idx_parcel_geom_parcel     ON geo.parcel_geometries (parcel_id);
CREATE INDEX idx_parcel_geom_active     ON geo.parcel_geometries (is_active, parcel_id) WHERE is_active = true;
CREATE INDEX idx_parcel_geom_accuracy   ON geo.parcel_geometries (accuracy_class);

-- Admin boundaries spatial
CREATE INDEX idx_admin_bnd_spatial      ON geo.administrative_boundaries USING gist (geometry);
CREATE INDEX idx_admin_bnd_lgd          ON geo.administrative_boundaries (lgd_code);
CREATE INDEX idx_admin_bnd_level        ON geo.administrative_boundaries (level);
CREATE INDEX idx_admin_bnd_parent       ON geo.administrative_boundaries (parent_lgd_code);

-- Restriction zones spatial
CREATE INDEX idx_restr_zones_spatial    ON geo.restriction_zones USING gist (geometry);
CREATE INDEX idx_restr_zones_type       ON geo.restriction_zones (zone_type);
CREATE INDEX idx_restr_zones_active     ON geo.restriction_zones (is_active) WHERE is_active = true;

-- Topology conflicts
CREATE INDEX idx_topo_conflicts_p1      ON geo.topology_conflicts (parcel_id_1);
CREATE INDEX idx_topo_conflicts_p2      ON geo.topology_conflicts (parcel_id_2);
CREATE INDEX idx_topo_conflicts_status  ON geo.topology_conflicts (resolution_status) WHERE resolution_status = 'OPEN';
CREATE INDEX idx_topo_conflicts_spatial ON geo.topology_conflicts USING gist (geometry) WHERE geometry IS NOT NULL;

-- ═════════════════════════════════════════════════════════════════════════════
-- SCHEMA: revenue
-- ═════════════════════════════════════════════════════════════════════════════

-- Parties: phonetic and trigram search for name matching
CREATE INDEX idx_parties_name_trgm      ON revenue.parties USING gin (name_en gin_trgm_ops);
CREATE INDEX idx_parties_name_local_trgm ON revenue.parties USING gin (name_local gin_trgm_ops);
CREATE INDEX idx_parties_phonetic       ON revenue.parties (name_phonetic_key);
CREATE INDEX idx_parties_id_hash        ON revenue.parties (id_type, id_hash);
CREATE INDEX idx_parties_type           ON revenue.parties (party_type);
CREATE INDEX idx_parties_name_fts       ON revenue.parties USING gin (name_trigram);

-- RoR: primary parcel lookup
CREATE INDEX idx_ror_parcel             ON revenue.records_of_rights (parcel_id);
CREATE INDEX idx_ror_survey_num         ON revenue.records_of_rights (survey_number, state_code)
  WHERE survey_number IS NOT NULL;
CREATE INDEX idx_ror_active             ON revenue.records_of_rights (parcel_id, is_active) WHERE is_active = true;
CREATE INDEX idx_ror_freshness          ON revenue.records_of_rights (data_freshness_status, last_synced_at);

-- Rights
CREATE INDEX idx_rights_parcel          ON revenue.rights (parcel_id);
CREATE INDEX idx_rights_party           ON revenue.rights (party_id);
CREATE INDEX idx_rights_ror             ON revenue.rights (ror_id);
CREATE INDEX idx_rights_type            ON revenue.rights (right_type);

-- Mutations
CREATE INDEX idx_mutations_parcel       ON revenue.mutations (parcel_id);
CREATE INDEX idx_mutations_from_party   ON revenue.mutations (from_party_id);
CREATE INDEX idx_mutations_to_party     ON revenue.mutations (to_party_id);
CREATE INDEX idx_mutations_status       ON revenue.mutations (status);
CREATE INDEX idx_mutations_date         ON revenue.mutations (mutation_date);

-- ═════════════════════════════════════════════════════════════════════════════
-- SCHEMA: registration
-- ═════════════════════════════════════════════════════════════════════════════

CREATE INDEX idx_deeds_parcel           ON registration.deeds (parcel_id);
CREATE INDEX idx_deeds_sro_number       ON registration.deeds (sro_code, deed_number);
CREATE INDEX idx_deeds_date             ON registration.deeds (registration_date DESC);
CREATE INDEX idx_deeds_seller           ON registration.deeds (seller_party_id);
CREATE INDEX idx_deeds_buyer            ON registration.deeds (buyer_party_id);
CREATE INDEX idx_deeds_type             ON registration.deeds (deed_type);

CREATE INDEX idx_encumbrances_parcel    ON registration.encumbrances (parcel_id);
CREATE INDEX idx_encumbrances_active    ON registration.encumbrances (parcel_id, is_active) WHERE is_active = true;
CREATE INDEX idx_encumbrances_party     ON registration.encumbrances (in_favour_of_party_id);

-- ═════════════════════════════════════════════════════════════════════════════
-- SCHEMA: planning
-- ═════════════════════════════════════════════════════════════════════════════

CREATE INDEX idx_zones_parcel           ON planning.zones (parcel_id);
CREATE INDEX idx_bldg_perm_parcel       ON planning.building_permissions (parcel_id);
CREATE INDEX idx_bldg_perm_status       ON planning.building_permissions (status);
CREATE INDEX idx_disputes_parcel        ON planning.disputes (parcel_id);
CREATE INDEX idx_disputes_status        ON planning.disputes (status);

-- ═════════════════════════════════════════════════════════════════════════════
-- SCHEMA: fiscal
-- ═════════════════════════════════════════════════════════════════════════════

CREATE INDEX idx_ptax_parcel_year       ON fiscal.property_tax (parcel_id, assessment_year DESC);
CREATE INDEX idx_ptax_status            ON fiscal.property_tax (payment_status);
CREATE INDEX idx_ptax_overdue           ON fiscal.property_tax (parcel_id)
  WHERE payment_status IN ('OVERDUE', 'DUE');

-- ═════════════════════════════════════════════════════════════════════════════
-- SCHEMA: audit
-- ═════════════════════════════════════════════════════════════════════════════

-- Indexes on individual partitions (create on parent; propagate to partitions)
CREATE INDEX idx_audit_parcel           ON audit.events (parcel_id, event_time DESC) WHERE parcel_id IS NOT NULL;
CREATE INDEX idx_audit_actor            ON audit.events (actor_id, event_time DESC);
CREATE INDEX idx_audit_event_type       ON audit.events (event_type, event_time DESC);
CREATE INDEX idx_audit_resource         ON audit.events (resource_type, resource_id) WHERE resource_id IS NOT NULL;

-- ═════════════════════════════════════════════════════════════════════════════
-- SCHEMA: ml
-- ═════════════════════════════════════════════════════════════════════════════

CREATE INDEX idx_conflict_scores_parcel ON ml.conflict_scores (parcel_id, score_type);
CREATE INDEX idx_conflict_scores_latest ON ml.conflict_scores (parcel_id) WHERE is_latest = true;
CREATE INDEX idx_conflict_scores_high   ON ml.conflict_scores (risk_band, score_value DESC)
  WHERE risk_band = 'HIGH';

CREATE INDEX idx_er_links_parcel        ON ml.entity_resolution_links (parcel_id);
CREATE INDEX idx_er_links_unreviewed    ON ml.entity_resolution_links (confidence_score DESC)
  WHERE is_confirmed IS NULL;

CREATE INDEX idx_tnf_flag_type          ON ml.transaction_network_flags (flag_type, detected_at DESC);
CREATE INDEX idx_tnf_unreviewed         ON ml.transaction_network_flags (reviewed_status)
  WHERE reviewed_status = 'UNREVIEWED';
CREATE INDEX idx_tnf_parcel_ids         ON ml.transaction_network_flags USING gin (parcel_ids);

CREATE INDEX idx_luc_parcel             ON ml.land_use_changes (parcel_id, detected_to_date DESC);
CREATE INDEX idx_luc_type               ON ml.land_use_changes (change_type);
CREATE INDEX idx_luc_unreviewed         ON ml.land_use_changes (reviewed_status)
  WHERE reviewed_status = 'UNREVIEWED';
CREATE INDEX idx_luc_spatial            ON ml.land_use_changes USING gist (bounding_geometry)
  WHERE bounding_geometry IS NOT NULL;

-- ═════════════════════════════════════════════════════════════════════════════
-- SCHEMA: reference
-- ═════════════════════════════════════════════════════════════════════════════

CREATE INDEX idx_lgd_parent             ON reference.lgd_hierarchy (parent_lgd_code);
CREATE INDEX idx_lgd_type               ON reference.lgd_hierarchy (entity_type);
CREATE INDEX idx_lgd_state              ON reference.lgd_hierarchy (state_code);
CREATE INDEX idx_lgd_name_trgm          ON reference.lgd_hierarchy USING gin (name_en gin_trgm_ops);

CREATE INDEX idx_code_lists_name        ON reference.code_lists (list_name, state_lgd_code);
CREATE INDEX idx_code_lists_code        ON reference.code_lists (list_name, code_value);
CREATE INDEX idx_unit_conv_district     ON reference.unit_conversions (district_lgd_code);
CREATE INDEX idx_unit_conv_unit_name    ON reference.unit_conversions (unit_name);
