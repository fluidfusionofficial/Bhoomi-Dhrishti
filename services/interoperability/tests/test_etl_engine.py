"""
Test ETL Mapping Engine

Demonstrates programmatic usage of the mapper, validator, and loader.
Run with: pytest tests/test_etl_engine.py -v
"""

import json
from pathlib import Path

import pandas as pd
import pytest

from app.engine import (
    SourceMapper,
    DataQualityValidator,
    apply_field_mapping,
    normalize_survey_number,
    convert_area,
    normalize_date,
    transliterate_to_latin,
    generate_phonetic_key,
)


BASE_DIR = Path(__file__).parent.parent
MAPPING_PATH = BASE_DIR / "data" / "mappings" / "tn_rural" / "mapping.yaml"
SAMPLE_CSV = BASE_DIR / "data" / "samples" / "tn_revenue_sample.csv"


class TestTransforms:
    """Test transformation functions."""

    def test_normalize_survey_number(self):
        """Test survey number normalization."""
        assert normalize_survey_number("0123/4A") == "123/4A"
        assert normalize_survey_number("123-4-A") == "123/4/A"
        assert normalize_survey_number("001/2") == "1/2"

    def test_convert_area(self):
        """Test area conversion."""
        # Cent to sq_m
        result = convert_area(5.5, "cent", "sq_m")
        assert result == pytest.approx(222.59, abs=0.1)

        # Acre to sq_m
        result = convert_area(2.3, "acre", "sq_m")
        assert result == pytest.approx(9307.78, abs=0.1)

        # Veli to sq_m (Tamil Nadu)
        result = convert_area(12.8, "veli", "sq_m")
        assert result == pytest.approx(85376.0, abs=0.1)

    def test_normalize_date(self):
        """Test date normalization."""
        assert normalize_date("15/08/2020") == "2020-08-15"
        assert normalize_date("2020-08-15") == "2020-08-15"
        assert normalize_date("1430 Fasli") == "2022-01-01"  # Approximate

    def test_transliterate_to_latin(self):
        """Test transliteration."""
        # Basic test (actual output depends on Unidecode)
        result = transliterate_to_latin("முருகன்", script="tamil")
        assert result is not None
        assert len(result) > 0

    def test_generate_phonetic_key(self):
        """Test phonetic key generation."""
        key1 = generate_phonetic_key("Ramesh Kumar")
        key2 = generate_phonetic_key("Ramesh Kumarr")  # Slight variation
        assert key1 is not None
        assert key2 is not None
        assert len(key1) == 6
        # Similar names should have similar phonetic keys
        assert key1[0] == key2[0]  # Same first letter


class TestMapper:
    """Test mapping engine."""

    def test_load_mapping_yaml(self):
        """Test loading mapping configuration."""
        mapper = SourceMapper(MAPPING_PATH)
        assert mapper.config["source_type"] == "revenue_ror"
        assert "field_mapping" in mapper.config
        assert "survey_number" in mapper.config["field_mapping"]

    def test_apply_mapping_single_record(self):
        """Test mapping a single record."""
        mapper = SourceMapper(MAPPING_PATH)

        source_record = {
            "Survey_No": "0123/4A",
            "Extent": "5.5",
            "Unit": "cent",
            "Pattadar_Name": "Ramesh Kumar",
            "Pattadar_Name_Tamil": "ரமேஷ் குமார்",
            "District_Code": "33001",
            "Village_Code": "3300101",
            "Land_Class": "AGRICULTURAL",
            "Patta_Date": "15/08/2020",
            "FMB_No": "FMB-123",
            "Chitta_No": "CHT-4567",
        }

        context = {"district_lgd_code": "33001"}
        canonical = mapper.apply_mapping(source_record, context)

        # Check mapped fields
        assert canonical["survey_number"] == "123/4A"
        assert canonical["area_native"] == 5.5
        assert canonical["unit_native"] == "cent"
        assert canonical["owner_name"] == "Ramesh Kumar"
        assert canonical["district_code"] == "33001"
        assert canonical["village_code"] == "3300101"
        assert canonical["land_use"] == "AGRICULTURAL"
        assert canonical["registration_date"] == "2020-08-15"

    def test_apply_mapping_batch(self):
        """Test mapping multiple records from CSV."""
        if not SAMPLE_CSV.exists():
            pytest.skip(f"Sample CSV not found: {SAMPLE_CSV}")

        mapper = SourceMapper(MAPPING_PATH)
        df = pd.read_csv(SAMPLE_CSV)
        source_records = df.to_dict("records")

        canonical_records = []
        for record in source_records:
            context = {"district_lgd_code": record.get("District_Code")}
            canonical = mapper.apply_mapping(record, context)
            canonical_records.append(canonical)

        assert len(canonical_records) == len(source_records)

        # Check first record
        first = canonical_records[0]
        assert first["survey_number"] == "123/4A"
        assert first["district_code"] == "33001"


class TestValidator:
    """Test data quality validator."""

    def test_validate_valid_records(self):
        """Test validation with valid records."""
        records = [
            {
                "survey_number": "123/4A",
                "area_native": 5.5,
                "area_sq_m": 222.59,
                "unit_native": "cent",
                "owner_name": "Ramesh Kumar",
                "district_code": "33001",
                "village_code": "3300101",
                "land_use": "AGRICULTURAL",
                "registration_date": "2020-08-15",
            }
        ]

        validator = DataQualityValidator("revenue_ror")
        report = validator.validate_records(records)

        assert report.total_rows == 1
        assert report.valid_rows == 1
        assert report.quality_score == 100.0
        assert len(report.issues) == 0

    def test_validate_invalid_records(self):
        """Test validation with invalid records."""
        records = [
            {
                "survey_number": "",  # Empty (invalid)
                "area_native": -5.5,  # Negative (invalid)
                "area_sq_m": None,
                "unit_native": "cent",
                "owner_name": "Test User",
                "district_code": "33001",
            }
        ]

        validator = DataQualityValidator("revenue_ror")
        report = validator.validate_records(records)

        assert report.total_rows == 1
        assert report.valid_rows == 0
        assert report.quality_score < 100.0
        assert len(report.issues) > 0

    def test_validate_batch_with_issues(self):
        """Test validation with mixed valid/invalid records."""
        records = [
            {
                "survey_number": "123/4A",
                "area_native": 5.5,
                "area_sq_m": 222.59,
                "owner_name": "Valid User",
                "district_code": "33001",
            },
            {
                "survey_number": None,  # Invalid
                "area_native": -2.0,  # Invalid
                "area_sq_m": None,
                "owner_name": "Invalid User",
                "district_code": "33001",
            },
            {
                "survey_number": "456/7B",
                "area_native": 3.2,
                "area_sq_m": 129.5,
                "owner_name": "Valid User 2",
                "district_code": "33001",
            },
        ]

        validator = DataQualityValidator("revenue_ror")
        report = validator.validate_records(records)

        assert report.total_rows == 3
        assert report.valid_rows == 2
        assert report.quality_score == pytest.approx(66.67, abs=0.1)
        assert len(report.issues) >= 1


class TestEndToEnd:
    """End-to-end ETL pipeline test."""

    def test_full_etl_pipeline(self):
        """Test complete ETL pipeline: load CSV → map → validate."""
        if not SAMPLE_CSV.exists():
            pytest.skip(f"Sample CSV not found: {SAMPLE_CSV}")

        # Step 1: Load source data
        df = pd.read_csv(SAMPLE_CSV)
        source_records = df.to_dict("records")
        print(f"\nLoaded {len(source_records)} source records")

        # Step 2: Apply mappings
        mapper = SourceMapper(MAPPING_PATH)
        canonical_records = []

        for record in source_records:
            context = {"district_lgd_code": record.get("District_Code")}
            canonical = mapper.apply_mapping(record, context)
            canonical_records.append(canonical)

        print(f"Mapped to {len(canonical_records)} canonical records")

        # Step 3: Validate
        validator = DataQualityValidator("revenue_ror")
        report = validator.validate_records(canonical_records)

        print(f"Quality Score: {report.quality_score}")
        print(f"Valid Rows: {report.valid_rows}/{report.total_rows}")
        print(f"Issues: {len(report.issues)}")

        # Assertions
        assert len(canonical_records) == len(source_records)
        assert report.total_rows == len(source_records)
        assert report.quality_score >= 80.0  # At least 80% quality
        assert report.valid_rows >= int(len(source_records) * 0.8)

        # Check field statistics
        assert "survey_number" in report.field_statistics
        assert "area_sq_m" in report.field_statistics

        # Print sample canonical record
        print("\nSample Canonical Record:")
        print(json.dumps(canonical_records[0], indent=2, default=str))


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])
