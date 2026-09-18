"""YAML-driven field mapping engine."""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import structlog
import yaml

from app.engine import transforms

logger = structlog.get_logger()


class MappingError(Exception):
    """Raised when mapping configuration is invalid."""

    pass


class SourceMapper:
    """Loads and applies YAML-based field mappings."""

    def __init__(self, mapping_path: Union[str, Path]):
        """
        Initialize mapper with YAML configuration.

        Args:
            mapping_path: Path to mapping.yaml file
        """
        self.mapping_path = Path(mapping_path)
        self.config = self._load_yaml()
        self._validate_schema()

    def _load_yaml(self) -> Dict[str, Any]:
        """Load and parse YAML configuration."""
        if not self.mapping_path.exists():
            raise MappingError(f"Mapping file not found: {self.mapping_path}")

        try:
            with open(self.mapping_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            logger.info("mapping_loaded", path=str(self.mapping_path))
            return config
        except yaml.YAMLError as e:
            raise MappingError(f"Invalid YAML syntax: {e}")

    def _validate_schema(self):
        """Validate mapping configuration structure."""
        required_keys = ["source_type", "field_mapping"]
        missing = [k for k in required_keys if k not in self.config]
        if missing:
            raise MappingError(f"Missing required keys in mapping config: {missing}")

        # Validate field mappings
        for field_name, field_config in self.config["field_mapping"].items():
            if not isinstance(field_config, dict):
                raise MappingError(f"Invalid mapping for field '{field_name}': must be a dict")
            if "source_field" not in field_config:
                raise MappingError(f"Field '{field_name}' missing 'source_field'")

    def get_source_type(self) -> str:
        """Get the source type identifier."""
        return self.config["source_type"]

    def get_required_fields(self) -> List[str]:
        """Get list of required target fields."""
        if "data_quality" in self.config and "required_fields" in self.config["data_quality"]:
            return self.config["data_quality"]["required_fields"]
        return []

    def get_unique_fields(self) -> List[str]:
        """Get list of fields that should be unique."""
        if "data_quality" in self.config and "unique_fields" in self.config["data_quality"]:
            return self.config["data_quality"]["unique_fields"]
        return []

    def apply_mapping(self, source_record: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Apply field mapping to a source record.

        Args:
            source_record: Raw source data record
            context: Optional context (e.g., district_lgd_code for area conversions)

        Returns:
            Canonical mapped record
        """
        context = context or {}
        canonical_record = {}

        for target_field, field_config in self.config["field_mapping"].items():
            try:
                value = self._extract_field_value(source_record, field_config)

                # Apply transformations
                if value is not None and "transform" in field_config:
                    value = self._apply_transform(
                        value,
                        field_config["transform"],
                        field_config,
                        context
                    )

                # Type coercion
                if value is not None and "type" in field_config:
                    value = self._coerce_type(value, field_config["type"])

                canonical_record[target_field] = value

            except Exception as e:
                logger.warning(
                    "field_mapping_error",
                    target_field=target_field,
                    source_field=field_config.get("source_field"),
                    error=str(e)
                )
                canonical_record[target_field] = None

        return canonical_record

    def _extract_field_value(self, record: Dict[str, Any], field_config: Dict[str, Any]) -> Any:
        """
        Extract value from source record, supporting nested fields.

        Args:
            record: Source data record
            field_config: Field mapping configuration

        Returns:
            Extracted value or None
        """
        source_field = field_config["source_field"]

        # Handle nested field notation (e.g., "address.district")
        if "." in source_field:
            parts = source_field.split(".")
            value = record
            for part in parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    return None
            return value

        # Handle array field notation (e.g., "owners[0].name")
        match = re.match(r"(\w+)\[(\d+)\]\.?(.+)?", source_field)
        if match:
            array_field, index, nested = match.groups()
            if array_field in record and isinstance(record[array_field], list):
                idx = int(index)
                if idx < len(record[array_field]):
                    value = record[array_field][idx]
                    if nested and isinstance(value, dict):
                        return value.get(nested)
                    return value
            return None

        # Simple field lookup
        return record.get(source_field)

    def _apply_transform(
        self,
        value: Any,
        transform_spec: str,
        field_config: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Any:
        """
        Apply transformation function to value.

        Args:
            value: Input value
            transform_spec: Transform function name or spec (e.g., "normalize_survey_number")
            field_config: Full field configuration
            context: Additional context

        Returns:
            Transformed value
        """
        # Parse transform spec: "function_name" or "function_name:param1=value1,param2=value2"
        if ":" in transform_spec:
            func_name, params_str = transform_spec.split(":", 1)
            params = dict(p.split("=") for p in params_str.split(",") if "=" in p)
        else:
            func_name = transform_spec
            params = {}

        # Map transform names to functions
        transform_map = {
            "normalize_survey_number": transforms.normalize_survey_number,
            "normalize_date": transforms.normalize_date,
            "transliterate_to_latin": lambda v: transforms.transliterate_to_latin(
                v, field_config.get("script", "devanagari")
            ),
            "generate_phonetic_key": transforms.generate_phonetic_key,
            "parse_address": transforms.parse_address,
            "validate_geometry": transforms.validate_geometry,
            "convert_area": lambda v: transforms.convert_area(
                v,
                params.get("from_unit", field_config.get("unit_native")),
                params.get("to_unit", "sq_m"),
                context.get("district_lgd_code")
            ),
        }

        if func_name in transform_map:
            try:
                return transform_map[func_name](value)
            except Exception as e:
                logger.warning("transform_error", transform=func_name, error=str(e))
                return value
        else:
            logger.warning("unknown_transform", transform=func_name)
            return value

    def _coerce_type(self, value: Any, target_type: str) -> Any:
        """
        Coerce value to target type.

        Args:
            value: Input value
            target_type: Target type name

        Returns:
            Type-coerced value
        """
        if value is None or value == "":
            return None

        try:
            if target_type == "float":
                return float(value)
            elif target_type == "int":
                return int(value)
            elif target_type == "str":
                return str(value)
            elif target_type == "bool":
                if isinstance(value, bool):
                    return value
                return str(value).lower() in ("true", "1", "yes", "y")
            else:
                return value
        except (ValueError, TypeError) as e:
            logger.warning("type_coercion_error", target_type=target_type, error=str(e))
            return value


def apply_field_mapping(
    source_record: Dict[str, Any],
    mapping_config: Union[str, Path, SourceMapper],
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Convenience function to apply field mapping.

    Args:
        source_record: Raw source data record
        mapping_config: Path to mapping YAML or SourceMapper instance
        context: Optional context for transformations

    Returns:
        Canonical mapped record
    """
    if isinstance(mapping_config, (str, Path)):
        mapper = SourceMapper(mapping_config)
    else:
        mapper = mapping_config

    return mapper.apply_mapping(source_record, context)
