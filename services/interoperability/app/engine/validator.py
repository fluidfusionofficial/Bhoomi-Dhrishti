"""Data quality validation using Pydantic and Great Expectations."""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

import pandas as pd
import structlog
from pydantic import BaseModel, Field, field_validator

logger = structlog.get_logger()


class RevenueRORSchema(BaseModel):
    """Pydantic schema for Revenue Record of Rights (RoR)."""

    survey_number: str = Field(..., description="Normalized survey number")
    area_native: Optional[float] = Field(None, ge=0, description="Area in native unit")
    area_sq_m: Optional[float] = Field(None, ge=0, description="Area in square meters")
    unit_native: Optional[str] = Field(None, description="Native unit name")
    owner_name: Optional[str] = Field(None, description="Owner/Pattadar name")
    owner_name_local: Optional[str] = Field(None, description="Name in local script")
    owner_name_phonetic: Optional[str] = Field(None, description="Phonetic key for matching")
    district_code: Optional[str] = Field(None, description="District LGD code")
    village_code: Optional[str] = Field(None, description="Village LGD code")
    land_use: Optional[str] = Field(None, description="Land use classification")
    geometry_wkt: Optional[str] = Field(None, description="Parcel geometry as WKT")
    registration_date: Optional[date] = Field(None, description="RoR registration date")

    @field_validator("survey_number")
    @classmethod
    def validate_survey_number(cls, v):
        if not v or v.strip() == "":
            raise ValueError("Survey number cannot be empty")
        return v.strip()

    @field_validator("area_native", "area_sq_m")
    @classmethod
    def validate_area(cls, v):
        if v is not None and v < 0:
            raise ValueError("Area cannot be negative")
        if v is not None and v > 1000000:  # 100 hectares
            logger.warning("unusually_large_area", area=v)
        return v

    class Config:
        str_strip_whitespace = True


class SRORegistrationSchema(BaseModel):
    """Pydantic schema for Sub-Registrar Office (SRO) sale deed registration."""

    registration_number: str = Field(..., description="Deed registration number")
    registration_date: date = Field(..., description="Date of registration")
    survey_number: Optional[str] = Field(None, description="Survey number")
    area_sq_m: Optional[float] = Field(None, ge=0, description="Transaction area")
    consideration_amount: Optional[float] = Field(None, ge=0, description="Sale consideration")
    seller_name: Optional[str] = Field(None, description="Seller name")
    buyer_name: Optional[str] = Field(None, description="Buyer name")
    district_code: Optional[str] = Field(None, description="District LGD code")
    village_code: Optional[str] = Field(None, description="Village LGD code")
    sro_code: Optional[str] = Field(None, description="SRO office code")
    document_type: Optional[str] = Field(None, description="Type of document")

    @field_validator("registration_number")
    @classmethod
    def validate_registration_number(cls, v):
        if not v or v.strip() == "":
            raise ValueError("Registration number cannot be empty")
        return v.strip()

    @field_validator("consideration_amount")
    @classmethod
    def validate_consideration(cls, v):
        if v is not None and v < 0:
            raise ValueError("Consideration amount cannot be negative")
        if v is not None and v > 10000000000:  # 1000 crore
            logger.warning("unusually_large_consideration", amount=v)
        return v

    class Config:
        str_strip_whitespace = True


class DQReport(BaseModel):
    """Data Quality Report structure."""

    source_type: str
    total_rows: int
    valid_rows: int
    quality_score: float = Field(ge=0, le=100)
    field_statistics: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    issues: List[Dict[str, Any]] = Field(default_factory=list)
    cross_source_stats: Dict[str, Any] = Field(default_factory=dict)


class DataQualityValidator:
    """Data quality validator using Great Expectations."""

    def __init__(self, source_type: str):
        """
        Initialize validator for a source type.

        Args:
            source_type: Type of source data (revenue_ror, sro_registration, etc.)
        """
        self.source_type = source_type
        self.schema_map = {
            "revenue_ror": RevenueRORSchema,
            "sro_registration": SRORegistrationSchema,
        }

    def validate_records(self, records: List[Dict[str, Any]]) -> DQReport:
        """
        Validate records and generate data quality report.

        Args:
            records: List of canonical records to validate

        Returns:
            DQReport with validation results
        """
        if not records:
            return DQReport(
                source_type=self.source_type,
                total_rows=0,
                valid_rows=0,
                quality_score=0.0
            )

        df = pd.DataFrame(records)
        total_rows = len(records)
        issues = []
        valid_row_indices = set(range(total_rows))

        # Get Pydantic schema for this source type
        schema_class = self.schema_map.get(self.source_type)

        # Pydantic validation
        if schema_class:
            for idx, record in enumerate(records):
                try:
                    schema_class(**record)
                except Exception as e:
                    issues.append({
                        "row": idx,
                        "field": None,
                        "issue": "schema_validation_failed",
                        "detail": str(e)
                    })
                    valid_row_indices.discard(idx)

        # Field-level statistics and validation
        field_stats = {}

        for column in df.columns:
            stats = {
                "null_count": int(df[column].isnull().sum()),
                "null_rate": float(df[column].isnull().mean()),
            }

            # Numeric field statistics
            if pd.api.types.is_numeric_dtype(df[column]):
                non_null = df[column].dropna()
                if len(non_null) > 0:
                    stats.update({
                        "min": float(non_null.min()),
                        "max": float(non_null.max()),
                        "mean": float(non_null.mean()),
                        "median": float(non_null.median()),
                    })

                # Check for negative values in fields that should be positive
                if column in ["area_native", "area_sq_m", "consideration_amount"]:
                    negative_indices = df[df[column] < 0].index.tolist()
                    for idx in negative_indices:
                        issues.append({
                            "row": idx,
                            "field": column,
                            "issue": "negative_value",
                            "value": float(df.loc[idx, column])
                        })
                        valid_row_indices.discard(idx)

            # String field statistics
            elif pd.api.types.is_string_dtype(df[column]) or pd.api.types.is_object_dtype(df[column]):
                non_null = df[column].dropna()
                if len(non_null) > 0:
                    stats["unique_count"] = int(df[column].nunique())
                    stats["empty_string_count"] = int((df[column] == "").sum())

            field_stats[column] = stats

        # Check required fields
        required_fields = self._get_required_fields()
        for field in required_fields:
            if field in df.columns:
                null_indices = df[df[field].isnull()].index.tolist()
                for idx in null_indices:
                    issues.append({
                        "row": idx,
                        "field": field,
                        "issue": "null_value"
                    })
                    valid_row_indices.discard(idx)

        # Geometry validation
        if "geometry_wkt" in df.columns:
            for idx, geom in df["geometry_wkt"].items():
                if pd.notna(geom) and geom != "":
                    if not self._is_valid_wkt(geom):
                        issues.append({
                            "row": idx,
                            "field": "geometry_wkt",
                            "issue": "invalid_geometry"
                        })

        # Calculate quality score
        valid_rows = len(valid_row_indices)
        quality_score = (valid_rows / total_rows * 100) if total_rows > 0 else 0

        # Build report
        report = DQReport(
            source_type=self.source_type,
            total_rows=total_rows,
            valid_rows=valid_rows,
            quality_score=round(quality_score, 2),
            field_statistics=field_stats,
            issues=issues,
            cross_source_stats={}
        )

        logger.info(
            "validation_complete",
            source_type=self.source_type,
            total_rows=total_rows,
            valid_rows=valid_rows,
            quality_score=report.quality_score,
            issue_count=len(issues)
        )

        return report

    def _get_required_fields(self) -> List[str]:
        """Get list of required fields for this source type."""
        required_map = {
            "revenue_ror": ["survey_number"],
            "sro_registration": ["registration_number", "registration_date"],
        }
        return required_map.get(self.source_type, [])

    def _is_valid_wkt(self, wkt_string: str) -> bool:
        """
        Check if WKT string is valid.

        Args:
            wkt_string: WKT geometry string

        Returns:
            True if valid, False otherwise
        """
        try:
            from shapely import wkt as shapely_wkt
            geom = shapely_wkt.loads(wkt_string)
            return geom.is_valid
        except Exception:
            return False


def run_validation(records: List[Dict[str, Any]], source_type: str) -> Dict[str, Any]:
    """
    Convenience function to run validation and get report as dict.

    Args:
        records: List of records to validate
        source_type: Source type identifier

    Returns:
        DQ report as dictionary
    """
    validator = DataQualityValidator(source_type)
    report = validator.validate_records(records)
    return report.model_dump()
