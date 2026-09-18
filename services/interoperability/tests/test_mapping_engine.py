"""
Conformance test suite for the MappingEngine.
Tests all built-in transforms and validation logic.
Run with: pytest services/interoperability/tests/
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from app.mapping_engine import MappingEngine, _normalize_survey_number, _acre_to_sq_m, _code_lookup, _hash_pii, _date_to_iso, _normalize_name


# ---------------------------------------------------------------------------
# Unit tests: individual transforms
# ---------------------------------------------------------------------------

class TestNormalizeSurveyNumber:
    def test_strips_whitespace(self):
        assert _normalize_survey_number("  123/4  ") == "123/4"

    def test_uppercases(self):
        assert _normalize_survey_number("abc-12") == "ABC-12"

    def test_normalizes_slashes(self):
        assert _normalize_survey_number("123//4\\5") == "123/4/5"

    def test_preserves_hyphens(self):
        assert _normalize_survey_number("12-A--OLD") == "12-A-OLD"


class TestAcreToSqm:
    def test_basic_conversion(self):
        result = _acre_to_sq_m(1.0)
        assert abs(result - 4046.85) < 1.0

    def test_zero(self):
        assert _acre_to_sq_m(0) == 0.0

    def test_invalid(self):
        assert _acre_to_sq_m("invalid") == 0.0

    def test_two_acres(self):
        result = _acre_to_sq_m(2.0)
        assert abs(result - 8093.71) < 1.0


class TestCodeLookup:
    def test_agricultural(self):
        assert _code_lookup("1", "land_class_v1") == "AGRICULTURAL"

    def test_residential(self):
        assert _code_lookup("R", "land_class_v1") == "RESIDENTIAL"

    def test_v2_lookup(self):
        assert _code_lookup("AG", "land_class_v2") == "AGRICULTURAL"

    def test_unknown_code(self):
        # Unknown code: pass-through
        result = _code_lookup("ZZUNKNOWN", "land_class_v1")
        assert result == "ZZUNKNOWN"

    def test_missing_list(self):
        result = _code_lookup("1", "nonexistent_list")
        assert result == "1"


class TestHashPii:
    def test_deterministic(self):
        h1 = _hash_pii("123456789012")
        h2 = _hash_pii("123456789012")
        assert h1 == h2

    def test_length(self):
        h = _hash_pii("test")
        assert len(h) == 64  # SHA-256 hex

    def test_different_inputs_differ(self):
        assert _hash_pii("aadhaar1") != _hash_pii("aadhaar2")


class TestDateToIso:
    def test_slash_dmy(self):
        assert _date_to_iso("15/08/1947") == "1947-08-15"

    def test_dash_dmy(self):
        assert _date_to_iso("01-01-2020") == "2020-01-01"

    def test_iso(self):
        assert _date_to_iso("2023-06-15") == "2023-06-15"

    def test_none_value(self):
        assert _date_to_iso("") is None
        assert _date_to_iso("null") is None

    def test_fasli(self):
        result = _date_to_iso("1429/1", "fasli")
        assert result == "2019-01-01"


class TestNormalizeName:
    def test_strips_honorifics(self):
        assert _normalize_name("Sri Raman Kumar") == "Raman Kumar"
        assert _normalize_name("Smt. Lakshmi Devi") == "Lakshmi Devi"

    def test_title_case(self):
        assert _normalize_name("rajesh kumar sharma") == "Rajesh Kumar Sharma"

    def test_normalizes_spaces(self):
        assert _normalize_name("  Vijay  Kumar  ") == "Vijay Kumar"


# ---------------------------------------------------------------------------
# Integration tests: MappingEngine
# ---------------------------------------------------------------------------

@pytest.fixture
def engine():
    return MappingEngine()


@pytest.fixture
def sample_config():
    return {
        "source": "test_system",
        "target_schema": "revenue",
        "mappings": [
            {"source_field": "SURVEY_NO", "target_field": "survey_number", "transform": "normalize_survey_number"},
            {"source_field": "EXTENT", "target_field": "area_sq_m", "transform": "acre_to_sq_m"},
            {"source_field": "LAND_CLASS", "target_field": "land_use", "transform": "code_lookup:land_class_v1"},
            {"source_field": "OWNER_NAME", "target_field": "holder_name", "transform": "normalize_name"},
            {"source_field": "REG_DATE", "target_field": "registration_date", "transform": "date_to_iso"},
        ]
    }


class TestMappingEngineApply:
    def test_full_record(self, engine, sample_config):
        source = {
            "SURVEY_NO": "  12/3-a  ",
            "EXTENT": "2.5",
            "LAND_CLASS": "1",
            "OWNER_NAME": "Sri Raman Kumar",
            "REG_DATE": "15/08/2010",
        }
        result = engine.apply_mapping(source, sample_config)
        assert result["survey_number"] == "12/3-A"
        assert abs(result["area_sq_m"] - 10117.14) < 10
        assert result["land_use"] == "AGRICULTURAL"
        assert result["holder_name"] == "Raman Kumar"
        assert result["registration_date"] == "2010-08-15"
        assert "_mapping_errors" not in result

    def test_missing_optional_field(self, engine, sample_config):
        source = {
            "SURVEY_NO": "100",
            "EXTENT": "1.0",
            "LAND_CLASS": "R",
            # OWNER_NAME and REG_DATE missing
        }
        result = engine.apply_mapping(source, sample_config)
        assert "survey_number" in result
        assert "holder_name" not in result  # missing field skipped
        assert "_mapping_errors" not in result

    def test_required_field_missing(self, engine):
        config = {
            "source": "test",
            "target_schema": "revenue",
            "mappings": [
                {"source_field": "MUST_HAVE", "target_field": "must_have", "required": True}
            ]
        }
        result = engine.apply_mapping({}, config)
        assert "_mapping_errors" in result
        assert any("MUST_HAVE" in e for e in result["_mapping_errors"])


class TestMappingEngineValidate:
    def test_valid_config(self, engine, sample_config):
        errors = engine.validate_mapping(sample_config)
        assert errors == []

    def test_missing_source(self, engine):
        config = {"target_schema": "revenue", "mappings": [{"source_field": "A", "target_field": "b"}]}
        errors = engine.validate_mapping(config)
        assert any("source" in e for e in errors)

    def test_missing_mappings(self, engine):
        config = {"source": "x", "target_schema": "revenue"}
        errors = engine.validate_mapping(config)
        assert any("mappings" in e for e in errors)

    def test_unknown_transform(self, engine):
        config = {
            "source": "x",
            "target_schema": "revenue",
            "mappings": [{"source_field": "A", "target_field": "b", "transform": "unknown_fn"}]
        }
        errors = engine.validate_mapping(config)
        assert any("unknown_fn" in e for e in errors)

    def test_duplicate_target(self, engine):
        config = {
            "source": "x",
            "target_schema": "revenue",
            "mappings": [
                {"source_field": "A", "target_field": "same"},
                {"source_field": "B", "target_field": "same"},
            ]
        }
        errors = engine.validate_mapping(config)
        assert any("duplicate" in e.lower() for e in errors)


class TestMappingEngineDryRun:
    def test_shows_all_steps(self, engine, sample_config):
        source = {"SURVEY_NO": "42/1", "EXTENT": "1.0", "LAND_CLASS": "2", "OWNER_NAME": "Mr. Vijay", "REG_DATE": "01-01-2023"}
        report = engine.dry_run(source, sample_config)
        assert "steps" in report
        assert "result" in report
        assert len(report["steps"]) == 5

    def test_shows_missing_field(self, engine, sample_config):
        source = {"SURVEY_NO": "42/1"}
        report = engine.dry_run(source, sample_config)
        missing_steps = [s for s in report["steps"] if s["error"] and "not present" in s["error"]]
        assert len(missing_steps) > 0
