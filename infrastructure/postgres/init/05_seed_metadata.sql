-- ─────────────────────────────────────────────────────────────────────────────
-- Bhoomi Dhrishti – 05_seed_metadata.sql
-- LGD administrative hierarchy (key states), unit conversions, code lists
-- This seed provides enough data for the demo and development scenarios.
-- Production should ingest the full LGD from data.gov.in
-- ─────────────────────────────────────────────────────────────────────────────

-- ═════════════════════════════════════════════════════════════════════════════
-- LGD Hierarchy – States (selected)
-- ═════════════════════════════════════════════════════════════════════════════

INSERT INTO reference.lgd_hierarchy (lgd_code, entity_type, name_en, name_local, script_local, hierarchy_type, state_code)
VALUES
  -- States
  ('33',  'STATE', 'Tamil Nadu',           'தமிழ் நாடு',    'TAMIL',      'REVENUE',     NULL),
  ('04',  'STATE', 'Chandigarh',           'ਚੰਡੀਗੜ੍ਹ',      'GURMUKHI',   'LOCAL_BODY',  NULL),
  ('06',  'STATE', 'Haryana',              'हरियाणा',       'DEVANAGARI', 'REVENUE',     NULL),
  ('29',  'STATE', 'Karnataka',            'ಕರ್ನಾಟಕ',       'KANNADA',    'REVENUE',     NULL),
  ('36',  'STATE', 'Telangana',            'తెలంగాణ',       'TELUGU',     'REVENUE',     NULL),
  ('27',  'STATE', 'Maharashtra',          'महाराष्ट्र',     'DEVANAGARI', 'REVENUE',     NULL),
  ('09',  'STATE', 'Uttar Pradesh',        'उत्तर प्रदेश',  'DEVANAGARI', 'REVENUE',     NULL),
  ('08',  'STATE', 'Rajasthan',            'राजस्थान',      'DEVANAGARI', 'REVENUE',     NULL),
  ('19',  'STATE', 'West Bengal',          'পশ্চিমবঙ্গ',    'BENGALI',    'REVENUE',     NULL)
ON CONFLICT (lgd_code) DO NOTHING;

-- ── Tamil Nadu Districts (selected)
INSERT INTO reference.lgd_hierarchy (lgd_code, entity_type, name_en, name_local, script_local, parent_lgd_code, hierarchy_type, state_code)
VALUES
  ('603', 'DISTRICT', 'Tirunelveli',    'திருநெல்வேலி',   'TAMIL', '33', 'REVENUE', '33'),
  ('601', 'DISTRICT', 'Chennai',        'சென்னை',          'TAMIL', '33', 'REVENUE', '33'),
  ('602', 'DISTRICT', 'Coimbatore',     'கோயம்புத்தூர்',  'TAMIL', '33', 'REVENUE', '33'),
  ('604', 'DISTRICT', 'Madurai',        'மதுரை',           'TAMIL', '33', 'REVENUE', '33'),
  ('605', 'DISTRICT', 'Salem',          'சேலம்',           'TAMIL', '33', 'REVENUE', '33')
ON CONFLICT (lgd_code) DO NOTHING;

-- ── Tamil Nadu Sub-Districts (Tirunelveli)
INSERT INTO reference.lgd_hierarchy (lgd_code, entity_type, name_en, name_local, script_local, parent_lgd_code, hierarchy_type, state_code)
VALUES
  ('3301', 'SUBDISTRICT', 'Tirunelveli',     'திருநெல்வேலி', 'TAMIL', '603', 'REVENUE', '33'),
  ('3302', 'SUBDISTRICT', 'Palayamkottai',   'பாளையங்கோட்டை', 'TAMIL', '603', 'REVENUE', '33'),
  ('3303', 'SUBDISTRICT', 'Nanguneri',       'நங்குநேரி',    'TAMIL', '603', 'REVENUE', '33'),
  ('3304', 'SUBDISTRICT', 'Ambasamudram',    'அம்பாசமுத்திரம்', 'TAMIL', '603', 'REVENUE', '33'),
  ('3305', 'SUBDISTRICT', 'Cheranmahadevi',  'சேரன்மகாதேவி', 'TAMIL', '603', 'REVENUE', '33')
ON CONFLICT (lgd_code) DO NOTHING;

-- ── Tamil Nadu Villages (sample – Tirunelveli sub-district)
INSERT INTO reference.lgd_hierarchy (lgd_code, entity_type, name_en, name_local, script_local, parent_lgd_code, hierarchy_type, state_code)
VALUES
  ('330101', 'VILLAGE', 'Melapalayam',    'மேலப்பாளையம்',  'TAMIL', '3301', 'REVENUE', '33'),
  ('330102', 'VILLAGE', 'Palavansathu',   'பழவன்சத்து',     'TAMIL', '3301', 'REVENUE', '33'),
  ('330103', 'VILLAGE', 'Srivaikuntam',   'ஸ்ரீவைகுண்டம்', 'TAMIL', '3301', 'REVENUE', '33'),
  ('330104', 'VILLAGE', 'Thachanallur',   'தாட்சணல்லூர்',   'TAMIL', '3301', 'REVENUE', '33'),
  ('330105', 'VILLAGE', 'Perumalpuram',   'பெருமாள்புரம்',  'TAMIL', '3301', 'REVENUE', '33')
ON CONFLICT (lgd_code) DO NOTHING;

-- ── Chandigarh (Union Territory – urban only)
INSERT INTO reference.lgd_hierarchy (lgd_code, entity_type, name_en, name_local, script_local, parent_lgd_code, hierarchy_type, state_code)
VALUES
  ('401',    'DISTRICT',         'Chandigarh',   'ਚੰਡੀਗੜ੍ਹ',  'GURMUKHI', '04', 'LOCAL_BODY', '04'),
  ('404001', 'URBAN_LOCAL_BODY', 'Chandigarh Municipal Corporation', 'ਚੰਡੀਗੜ੍ਹ ਨਗਰ ਨਿਗਮ', 'GURMUKHI', '401', 'LOCAL_BODY', '04')
ON CONFLICT (lgd_code) DO NOTHING;

-- Chandigarh Wards (Sectors as planning units)
INSERT INTO reference.lgd_hierarchy (lgd_code, entity_type, name_en, name_local, script_local, parent_lgd_code, hierarchy_type, state_code)
VALUES
  ('404001W01', 'WARD', 'Sector 1',  'ਸੈਕਟਰ 1',  'GURMUKHI', '404001', 'LOCAL_BODY', '04'),
  ('404001W02', 'WARD', 'Sector 2',  'ਸੈਕਟਰ 2',  'GURMUKHI', '404001', 'LOCAL_BODY', '04'),
  ('404001W03', 'WARD', 'Sector 7',  'ਸੈਕਟਰ 7',  'GURMUKHI', '404001', 'LOCAL_BODY', '04'),
  ('404001W04', 'WARD', 'Sector 11', 'ਸੈਕਟਰ 11', 'GURMUKHI', '404001', 'LOCAL_BODY', '04'),
  ('404001W05', 'WARD', 'Sector 17', 'ਸੈਕਟਰ 17', 'GURMUKHI', '404001', 'LOCAL_BODY', '04'),
  ('404001W06', 'WARD', 'Sector 22', 'ਸੈਕਟਰ 22', 'GURMUKHI', '404001', 'LOCAL_BODY', '04'),
  ('404001W07', 'WARD', 'Sector 35', 'ਸੈਕਟਰ 35', 'GURMUKHI', '404001', 'LOCAL_BODY', '04')
ON CONFLICT (lgd_code) DO NOTHING;

-- ═════════════════════════════════════════════════════════════════════════════
-- Area Unit Conversions
-- ═════════════════════════════════════════════════════════════════════════════

INSERT INTO reference.unit_conversions (state_lgd_code, district_lgd_code, unit_name, unit_local_name, sq_metres_per_unit, is_official, notes, source)
VALUES
  -- National standard
  (NULL, NULL, 'sq_metre',   'वर्ग मीटर',   1.0,          true,  'SI base unit', 'National'),
  (NULL, NULL, 'sq_feet',    'वर्ग फ़ीट',    0.092903,     true,  'International foot', 'National'),
  (NULL, NULL, 'hectare',    'हेक्टेयर',    10000.0,      true,  '100x100m', 'National'),
  (NULL, NULL, 'acre',       'एकड़',         4046.8564,    true,  '4840 sq yards', 'National'),

  -- Tamil Nadu
  ('33', NULL, 'cent',       'சென்ட்',        40.4686,     true,  '1/100 acre; standard TN unit', 'TN Revenue Board'),
  ('33', NULL, 'ground',     'கிரவுண்ட்',     222.967,     true,  'Chennai area: 2400 sq feet', 'TN Revenue Board'),
  ('33', NULL, 'sq_link',    'சதுர இணைப்பு',  0.0404686,   false, '1/1000 acre; survey use', 'TN Survey Dept'),
  ('33', NULL, 'veli',       'வேலி',          2428.112,    true,  '6 acres (Tamil Nadu)', 'TN Revenue Board'),
  ('33', NULL, 'kuli',       'குழி',          24.281,      true,  '1/100 veli', 'TN Revenue Board'),

  -- Karnataka
  ('29', NULL, 'guntha',     'ಗುಂಟೆ',         101.1714,    true,  '1/40 acre; standard Karnataka unit', 'Karnataka Revenue'),
  ('29', NULL, 'acre_karnataka', 'ಎಕರೆ',     4046.8564,    true,  'Same as acre', 'Karnataka Revenue'),

  -- Rajasthan (Bigha varies by district)
  ('08', NULL,  'bigha',      'बीघा',          2529.285,    false, 'Rajasthan pucca bigha (national default)', 'DILRMP'),
  ('08', '0802','bigha',      'बीघा',          1680.0,      true,  'Jaipur district kachcha bigha', 'Rajasthan Revenue'),
  ('08', '0810','bigha',      'बीघा',          2529.285,    true,  'Bikaner pucca bigha', 'Rajasthan Revenue'),

  -- Uttar Pradesh
  ('09', NULL, 'bigha',       'बीघा',          2529.285,    true,  'UP pucca bigha', 'UP Revenue'),
  ('09', NULL, 'biswa',       'बिस्वा',        126.464,     true,  '1/20 bigha', 'UP Revenue'),

  -- Chandigarh / Punjab
  ('04', NULL, 'marla',       'ਮਰਲਾ',          25.2929,     true,  '1/160 acre (standard)', 'Punjab Revenue'),
  ('04', NULL, 'kanal',       'ਕਨਾਲ',          505.857,     true,  '8 marlas', 'Punjab Revenue'),
  ('04', NULL, 'murabba',     'ਮੁਰੱਬਾ',        202343.0,    true,  '25 acres', 'Punjab Revenue'),

  -- West Bengal
  ('19', NULL, 'katha',       'কাঠা',           66.890,      true,  'WB standard: 720 sq ft', 'WB Revenue'),
  ('19', NULL, 'bigha',       'বিঘা',           1337.803,    true,  'WB bigha: 20 katha', 'WB Revenue'),
  ('19', NULL, 'decimal',     'ডেসিমেল',        40.4686,     true,  '1/100 acre', 'WB Revenue')
ON CONFLICT DO NOTHING;

-- ═════════════════════════════════════════════════════════════════════════════
-- Code Lists – Land Classification (Tamil Nadu + national canonical)
-- ═════════════════════════════════════════════════════════════════════════════

INSERT INTO reference.code_lists (list_name, list_version, source_system, state_lgd_code, code_value, canonical_value, description_en, description_local)
VALUES
  -- Tamil Nadu land classification (Patta land types)
  ('LAND_CLASSIFICATION', '1.0', 'TN_BHOOMI', '33', 'DRY',         'DRYLAND',      'Dry (unirrigated) agricultural land',           'புஞ்சை'),
  ('LAND_CLASSIFICATION', '1.0', 'TN_BHOOMI', '33', 'WET',         'WETLAND',      'Wet (irrigated) agricultural land',             'நஞ்சை'),
  ('LAND_CLASSIFICATION', '1.0', 'TN_BHOOMI', '33', 'GARDEN',      'GARDEN',       'Garden/horticultural land',                     'தோட்டம்'),
  ('LAND_CLASSIFICATION', '1.0', 'TN_BHOOMI', '33', 'WASTE',       'WASTELAND',    'Government wasteland / uncultivated',           'வீண்நிலம்'),
  ('LAND_CLASSIFICATION', '1.0', 'TN_BHOOMI', '33', 'PORAMBOKE',   'PORAMBOKE',    'Common land / commons (not patta-able)',         'போரம்போக்கு'),
  ('LAND_CLASSIFICATION', '1.0', 'TN_BHOOMI', '33', 'NATHAM',      'HABITATION',   'Habitation site',                               'நத்தம்'),
  ('LAND_CLASSIFICATION', '1.0', 'TN_BHOOMI', '33', 'PANNAI',      'PLANTATION',   'Plantation/estate land',                        'பண்ணை'),

  -- Karnataka (Bhoomi RTC codes)
  ('LAND_CLASSIFICATION', '1.0', 'KA_BHOOMI', '29', 'JODI',        'GOVERNMENT',   'Government land (Jodi – revenue assignment)',   'ಜೋಡಿ'),
  ('LAND_CLASSIFICATION', '1.0', 'KA_BHOOMI', '29', 'BAGAIR_HUKUM','UNAUTHORISED', 'Unauthorised occupation of government land',    'ಬಗಾಯರ್ ಹುಕುಂ'),
  ('LAND_CLASSIFICATION', '1.0', 'KA_BHOOMI', '29', 'KHARAB_A',    'WASTELAND',    'Unassessed waste (Type A)',                     'ಖರಾಬ್ ಎ'),
  ('LAND_CLASSIFICATION', '1.0', 'KA_BHOOMI', '29', 'KHARAB_B',    'FOREST',       'Forest / reserve land (Type B)',                'ಖರಾಬ್ ಬಿ'),

  -- National canonical values
  ('LAND_CLASSIFICATION', '1.0', 'NATIONAL',  NULL, 'AGRICULTURAL', 'AGRICULTURAL', 'Agricultural land (generic)',                  'कृषि भूमि'),
  ('LAND_CLASSIFICATION', '1.0', 'NATIONAL',  NULL, 'RESIDENTIAL',  'RESIDENTIAL',  'Residential land',                             'आवासीय भूमि'),
  ('LAND_CLASSIFICATION', '1.0', 'NATIONAL',  NULL, 'COMMERCIAL',   'COMMERCIAL',   'Commercial land',                              'वाणिज्यिक भूमि'),
  ('LAND_CLASSIFICATION', '1.0', 'NATIONAL',  NULL, 'INDUSTRIAL',   'INDUSTRIAL',   'Industrial land',                              'औद्योगिक भूमि'),
  ('LAND_CLASSIFICATION', '1.0', 'NATIONAL',  NULL, 'GOVERNMENT',   'GOVERNMENT',   'Government / public land',                     'सरकारी भूमि'),
  ('LAND_CLASSIFICATION', '1.0', 'NATIONAL',  NULL, 'FOREST',       'FOREST',       'Forest land',                                  'वन भूमि'),
  ('LAND_CLASSIFICATION', '1.0', 'NATIONAL',  NULL, 'WATER_BODY',   'WATER_BODY',   'Water body (river, tank, lake)',               'जलाशय'),

  -- Mutation types (for cross-system normalisation)
  ('MUTATION_TYPE', '1.0', 'TN_BHOOMI', '33', 'SALE_DEED',   'SALE',        'Sale deed executed',             'விற்பனை'),
  ('MUTATION_TYPE', '1.0', 'TN_BHOOMI', '33', 'VARISUKKU',   'INHERITANCE', 'Inheritance/succession',         'வாரிசு'),
  ('MUTATION_TYPE', '1.0', 'TN_BHOOMI', '33', 'PANCHAYAT',   'COURT_ORDER', 'Panchayat / revenue court order','பஞ்சாயத்து'),
  ('MUTATION_TYPE', '1.0', 'KA_BHOOMI', '29', 'KHAREEDI',    'SALE',        'Purchase (Khareedi)',             'ಖರೀದಿ'),
  ('MUTATION_TYPE', '1.0', 'KA_BHOOMI', '29', 'VARASU',      'INHERITANCE', 'Succession / varasu',            'ವಾರಸು'),

  -- Data freshness
  ('DATA_FRESHNESS',      '1.0', 'NATIONAL', NULL, 'LIVE',      'LIVE',       'Data pulled live from source system', NULL),
  ('DATA_FRESHNESS',      '1.0', 'NATIONAL', NULL, 'CACHED',    'CACHED',     'Data from last successful sync (may be stale)', NULL),
  ('DATA_FRESHNESS',      '1.0', 'NATIONAL', NULL, 'SYNTHETIC', 'SYNTHETIC',  'Demo / generated data — not authoritative', NULL)
ON CONFLICT DO NOTHING;

-- ═════════════════════════════════════════════════════════════════════════════
-- Sample BDPR sequence initialisation
-- ═════════════════════════════════════════════════════════════════════════════
-- (Sequences are created in 04_functions.sql; we just verify here)
SELECT nextval('identity.bdpr_sequence');  -- Returns 1 on fresh init

-- Confirm extensions loaded
DO $$
BEGIN
  ASSERT (SELECT COUNT(*) FROM pg_extension WHERE extname = 'postgis') = 1, 'PostGIS not loaded!';
  ASSERT (SELECT COUNT(*) FROM pg_extension WHERE extname = 'pg_trgm') = 1, 'pg_trgm not loaded!';
  RAISE NOTICE 'All required extensions confirmed present.';
END;
$$;

-- Final health check
DO $$
DECLARE tbl_count INTEGER;
BEGIN
  SELECT COUNT(*) INTO tbl_count
  FROM information_schema.tables
  WHERE table_schema IN ('identity', 'geo', 'revenue', 'registration', 'planning', 'fiscal', 'audit', 'ml', 'reference');
  RAISE NOTICE 'Schema init complete. % tables created across 9 schemas.', tbl_count;
END;
$$;
