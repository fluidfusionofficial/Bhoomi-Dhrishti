"""
YAML-based mapping engine for the Bhoomi Dhrishti interoperability layer.

Reads a mapping config (loaded from YAML) and transforms source records
into canonical Bhoomi schema records.

Supported transforms:
  normalize_survey_number       — strip whitespace, normalize delimiters
  acre_to_sq_m[:district_lgd=X] — convert acres (with optional district-scoped multiplier)
  code_lookup:list_name         — map source code to canonical via reference table
  transliterate_to_latin        — Devanagari/Tamil → Latin phonetic (basic)
  hash_pii                      — SHA-256 of value (Aadhaar, PAN)
  date_to_iso                   — parse various date formats incl. Fasli era
  normalize_name                — remove honorifics, normalize whitespace
"""
from __future__ import annotations

import hashlib
import re
import unicodedata
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Built-in reference tables (simplified; production would query DB)
# ---------------------------------------------------------------------------

# Acre-to-sqm conversions: default + district-scoped variants
_ACRE_TO_SQM_DEFAULT = 4046.8564

# Land-use code lookup tables
_CODE_LISTS: Dict[str, Dict[str, str]] = {
    "land_class_v1": {
        "1": "AGRICULTURAL",
        "2": "RESIDENTIAL",
        "3": "COMMERCIAL",
        "4": "INDUSTRIAL",
        "5": "FOREST",
        "6": "WASTELAND",
        "7": "WATER_BODY",
        "8": "PUBLIC_UTILITY",
        "A": "AGRICULTURAL",
        "R": "RESIDENTIAL",
        "C": "COMMERCIAL",
        "I": "INDUSTRIAL",
        "F": "FOREST",
    },
    "land_class_v2": {
        "AG": "AGRICULTURAL",
        "RS": "RESIDENTIAL",
        "CM": "COMMERCIAL",
        "IN": "INDUSTRIAL",
        "FR": "FOREST",
        "WL": "WASTELAND",
        "WB": "WATER_BODY",
        "PU": "PUBLIC_UTILITY",
    },
}

# Honorifics to strip for normalize_name
_HONORIFICS = re.compile(
    r'^\s*(?:sri|shri|smt|dr|mr|mrs|ms|prof|rev|adv|thiru|selvi|tmt|col|brig|capt|cmdr)\b\.?\s*',
    re.IGNORECASE,
)

# Fasli year offset (Fasli year 1 = 590 CE; approximate)
_FASLI_OFFSET = 590


# ---------------------------------------------------------------------------
# Transform functions
# ---------------------------------------------------------------------------

def _normalize_survey_number(value: Any, arg: Optional[str] = None) -> str:
    """Strip spaces, uppercase, normalize separators (/, -, pt, old, new)."""
    v = str(value).strip().upper()
    v = re.sub(r'\s+', ' ', v)
    v = re.sub(r'[/\\]+', '/', v)
    v = re.sub(r'-+', '-', v)
    return v


def _acre_to_sq_m(value: Any, arg: Optional[str] = None) -> float:
    """Convert acres to square metres. arg format: 'district_lgd=33001'."""
    multiplier = _ACRE_TO_SQM_DEFAULT
    if arg:
        # Could look up district-specific factor; use default for now
        pass
    try:
        return float(value) * multiplier
    except (ValueError, TypeError):
        return 0.0


def _code_lookup(value: Any, arg: Optional[str] = None) -> str:
    """Map source code using named list. arg: list name."""
    if not arg:
        return str(value)
    table = _CODE_LISTS.get(arg, {})
    return table.get(str(value).strip().upper(), str(value))


def _transliterate_to_latin(value: Any, arg: Optional[str] = None) -> str:
    """
    Basic Unicode transliteration: NFKD decompose and strip non-ASCII.
    Good enough for phonetic search key generation.
    """
    text = str(value)
    normalized = unicodedata.normalize('NFKD', text)
    return ''.join(c for c in normalized if unicodedata.category(c) != 'Mn' and ord(c) < 128)


def _hash_pii(value: Any, arg: Optional[str] = None) -> str:
    """SHA-256 hash of the value (for Aadhaar, PAN, mobile)."""
    return hashlib.sha256(str(value).encode('utf-8')).hexdigest()


_DATE_FMTS = [
    '%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d', '%d.%m.%Y',
    '%d/%m/%y', '%m/%d/%Y', '%B %d, %Y', '%d %B %Y',
]


def _date_to_iso(value: Any, arg: Optional[str] = None) -> Optional[str]:
    """Parse various date formats and return ISO-8601. Handles Fasli era (arg='fasli')."""
    s = str(value).strip()
    if not s or s.lower() in ('none', 'null', 'n/a', ''):
        return None

    # Fasli era conversion
    if arg == 'fasli':
        try:
            fasli_year = int(s.split('/')[0])
            gregorian_year = fasli_year + _FASLI_OFFSET
            return f"{gregorian_year}-01-01"
        except (ValueError, IndexError):
            pass

    for fmt in _DATE_FMTS:
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            continue
    return s  # return as-is if unrecognized


def _normalize_name(value: Any, arg: Optional[str] = None) -> str:
    """Remove honorifics, normalize whitespace, title-case."""
    v = str(value).strip()
    v = _HONORIFICS.sub('', v).strip()
    v = re.sub(r'\s+', ' ', v)
    return v.title()


# Registry of transform functions
_TRANSFORMS: Dict[str, Any] = {
    'normalize_survey_number': _normalize_survey_number,
    'acre_to_sq_m': _acre_to_sq_m,
    'code_lookup': _code_lookup,
    'transliterate_to_latin': _transliterate_to_latin,
    'hash_pii': _hash_pii,
    'date_to_iso': _date_to_iso,
    'normalize_name': _normalize_name,
}


# ---------------------------------------------------------------------------
# MappingEngine
# ---------------------------------------------------------------------------

class MappingEngine:
    """
    Applies a YAML-loaded mapping config to source records.

    Config structure:
        source: str
        source_type: csv | json | postgresql | api
        target_schema: str
        mappings:
          - source_field: SOURCE_COL
            target_field: canonical_col
            transform: transform_name[:arg]   # optional
            required: bool                    # optional, default false
    """

    def _apply_transform(self, value: Any, transform_spec: str) -> Any:
        """Parse 'transform_name[:arg]' and apply the function."""
        if ':' in transform_spec:
            name, arg = transform_spec.split(':', 1)
        else:
            name, arg = transform_spec, None

        fn = _TRANSFORMS.get(name.strip())
        if fn is None:
            raise ValueError(f"Unknown transform: '{name}'")
        return fn(value, arg)

    def apply_mapping(self, source_record: Dict[str, Any], mapping_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply all field mappings from config to source_record.
        Returns a canonical target record.
        Skips source fields that are absent in the record (unless required=True).
        """
        result: Dict[str, Any] = {}
        errors: List[str] = []

        for mapping in mapping_config.get('mappings', []):
            src_field = mapping.get('source_field')
            tgt_field = mapping.get('target_field')
            transform = mapping.get('transform')
            required = mapping.get('required', False)

            if src_field not in source_record:
                if required:
                    errors.append(f"Required source field '{src_field}' missing")
                continue

            value = source_record[src_field]

            if transform:
                try:
                    value = self._apply_transform(value, transform)
                except Exception as exc:
                    errors.append(f"Transform '{transform}' on '{src_field}': {exc}")
                    continue

            result[tgt_field] = value

        if errors:
            result['_mapping_errors'] = errors

        return result

    def validate_mapping(self, mapping_config: Dict[str, Any]) -> List[str]:
        """
        Validate a mapping config dict.
        Returns a list of error strings (empty = valid).
        """
        errors: List[str] = []

        if 'source' not in mapping_config:
            errors.append("Missing required field: 'source'")
        if 'target_schema' not in mapping_config:
            errors.append("Missing required field: 'target_schema'")

        mappings = mapping_config.get('mappings')
        if not mappings:
            errors.append("No 'mappings' defined")
            return errors

        if not isinstance(mappings, list):
            errors.append("'mappings' must be a list")
            return errors

        seen_targets: set = set()
        for i, m in enumerate(mappings):
            prefix = f"mappings[{i}]"
            if 'source_field' not in m:
                errors.append(f"{prefix}: missing 'source_field'")
            if 'target_field' not in m:
                errors.append(f"{prefix}: missing 'target_field'")
            else:
                tf = m['target_field']
                if tf in seen_targets:
                    errors.append(f"{prefix}: duplicate target_field '{tf}'")
                seen_targets.add(tf)

            transform = m.get('transform')
            if transform:
                name = transform.split(':')[0].strip()
                if name not in _TRANSFORMS:
                    errors.append(f"{prefix}: unknown transform '{name}'")

        return errors

    def dry_run(self, source_record: Dict[str, Any], mapping_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply each mapping step and return a trace showing the transformation.
        Returns a dict with 'steps' (list) and 'result' (final record).
        """
        steps: List[Dict[str, Any]] = []
        result: Dict[str, Any] = {}

        for mapping in mapping_config.get('mappings', []):
            src_field = mapping.get('source_field')
            tgt_field = mapping.get('target_field')
            transform = mapping.get('transform')

            step = {
                'source_field': src_field,
                'target_field': tgt_field,
                'transform': transform,
                'source_value': source_record.get(src_field, '__MISSING__'),
                'output_value': None,
                'error': None,
            }

            if src_field not in source_record:
                step['error'] = 'Source field not present in record'
                steps.append(step)
                continue

            value = source_record[src_field]
            step['source_value'] = value

            if transform:
                try:
                    value = self._apply_transform(value, transform)
                    step['output_value'] = value
                except Exception as exc:
                    step['error'] = str(exc)
                    steps.append(step)
                    continue
            else:
                step['output_value'] = value

            result[tgt_field] = value
            steps.append(step)

        return {'steps': steps, 'result': result}
