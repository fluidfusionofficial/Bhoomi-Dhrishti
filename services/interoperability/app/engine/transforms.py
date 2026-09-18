"""Transformation functions for ETL mapping."""

import hashlib
import re
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

import structlog
from dateutil import parser as date_parser
from shapely import wkt
from shapely.geometry import shape
from unidecode import unidecode

logger = structlog.get_logger()


# District-specific area conversion factors (bigha varies by district)
# In real implementation, this would query reference.unit_conversions table
DISTRICT_AREA_FACTORS = {
    # Example: District LGD code -> conversion factors
    "33001": {  # Example TN district
        "bigha": 1618.7,  # sq_m per bigha
        "cent": 40.47,
        "acre": 4046.86,
        "hectare": 10000,
        "veli": 6670,
        "kuli": 1.67,
    },
}

# Default conversion factors (used when district not specified)
DEFAULT_AREA_FACTORS = {
    "bigha": 2529.3,  # Standard bigha
    "cent": 40.47,
    "acre": 4046.86,
    "hectare": 10000,
    "sq_m": 1,
    "sq_km": 1000000,
    "veli": 6670,  # Tamil Nadu
    "kuli": 1.67,  # Tamil Nadu
    "ground": 223,  # South India
}


def convert_area(
    value: Any,
    from_unit: str,
    to_unit: str = "sq_m",
    district_lgd_code: Optional[str] = None
) -> Optional[float]:
    """
    Convert area between units with district-specific handling.

    Args:
        value: Area value to convert
        from_unit: Source unit (e.g., "bigha", "cent", "acre")
        to_unit: Target unit (default: "sq_m")
        district_lgd_code: Optional district code for district-specific conversions

    Returns:
        Converted area value or None if conversion fails
    """
    if value is None or value == "":
        return None

    try:
        value = float(value)
        if value < 0:
            logger.warning("negative_area_value", value=value)
            return None

        # Get conversion factors
        factors = DEFAULT_AREA_FACTORS
        if district_lgd_code and district_lgd_code in DISTRICT_AREA_FACTORS:
            factors = {**DEFAULT_AREA_FACTORS, **DISTRICT_AREA_FACTORS[district_lgd_code]}

        from_unit_lower = from_unit.lower() if from_unit else "sq_m"
        to_unit_lower = to_unit.lower()

        if from_unit_lower not in factors:
            logger.warning("unknown_from_unit", unit=from_unit_lower)
            return value

        if to_unit_lower not in factors:
            logger.warning("unknown_to_unit", unit=to_unit_lower)
            return value

        # Convert to sq_m first, then to target unit
        value_in_sq_m = value * factors[from_unit_lower]
        result = value_in_sq_m / factors[to_unit_lower]

        return round(result, 4)

    except (ValueError, TypeError) as e:
        logger.warning("area_conversion_error", value=value, error=str(e))
        return None


def normalize_date(value: Any) -> Optional[str]:
    """
    Normalize date to ISO 8601 format (YYYY-MM-DD).

    Handles:
    - DD/MM/YYYY
    - YYYY-MM-DD
    - Fasli year (approximate conversion)
    - Saka era (approximate conversion)

    Args:
        value: Date value in various formats

    Returns:
        ISO 8601 formatted date string or None
    """
    if value is None or value == "":
        return None

    if isinstance(value, datetime):
        return value.date().isoformat()

    value_str = str(value).strip()

    # Handle Fasli year (e.g., "1430 Fasli")
    fasli_match = re.match(r"(\d{4})\s*fasli", value_str, re.IGNORECASE)
    if fasli_match:
        fasli_year = int(fasli_match.group(1))
        # Fasli year starts around September; approximate to Gregorian
        gregorian_year = fasli_year + 592  # Approximate conversion
        return f"{gregorian_year}-01-01"  # Approximate to year start

    # Handle Saka era (e.g., "1945 Saka")
    saka_match = re.match(r"(\d{4})\s*saka", value_str, re.IGNORECASE)
    if saka_match:
        saka_year = int(saka_match.group(1))
        # Saka era starts in 78 CE
        gregorian_year = saka_year + 78
        return f"{gregorian_year}-01-01"  # Approximate to year start

    # Try parsing various date formats
    try:
        # Try dateutil parser (handles many formats)
        parsed_date = date_parser.parse(value_str, dayfirst=True)
        return parsed_date.date().isoformat()
    except (ValueError, date_parser.ParserError):
        # Try manual parsing for DD/MM/YYYY
        dd_mm_yyyy = re.match(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})", value_str)
        if dd_mm_yyyy:
            day, month, year = dd_mm_yyyy.groups()
            try:
                dt = datetime(int(year), int(month), int(day))
                return dt.date().isoformat()
            except ValueError:
                pass

        logger.warning("date_parse_error", value=value_str)
        return None


def transliterate_to_latin(text: Any, script: str = "devanagari") -> Optional[str]:
    """
    Transliterate text from Indian scripts to Latin.

    Uses basic IAST/Hunterian-style transliteration via Unidecode.

    Args:
        text: Text to transliterate
        script: Source script (devanagari, tamil, bengali, etc.)

    Returns:
        Transliterated text or None
    """
    if text is None or text == "":
        return None

    try:
        text_str = str(text).strip()
        # Unidecode provides reasonable transliteration for most scripts
        transliterated = unidecode(text_str)
        return transliterated
    except Exception as e:
        logger.warning("transliteration_error", text=text, script=script, error=str(e))
        return None


def generate_phonetic_key(name: Any) -> Optional[str]:
    """
    Generate phonetic key for Indian names using Soundex-like algorithm.

    Useful for matching similar-sounding names with spelling variations.

    Args:
        name: Name to generate phonetic key for

    Returns:
        Phonetic key (uppercase alphanumeric) or None
    """
    if name is None or name == "":
        return None

    try:
        name_str = str(name).strip().upper()

        # First, transliterate to Latin if needed
        name_latin = unidecode(name_str)

        # Remove common Indian name prefixes/suffixes
        prefixes = ["SHRI", "SRI", "SMT", "KUM", "MR", "MRS", "MS", "DR"]
        for prefix in prefixes:
            if name_latin.startswith(prefix + " "):
                name_latin = name_latin[len(prefix) + 1:]
                break

        # Keep only alphabetic characters
        name_clean = re.sub(r"[^A-Z]", "", name_latin)

        if not name_clean:
            return None

        # Modified Soundex for Indian names
        # Retain first letter
        soundex = name_clean[0]

        # Consonant encoding with special handling for Indian phonetics
        consonant_map = {
            "B": "1", "F": "1", "P": "1", "V": "1",
            "C": "2", "G": "2", "J": "2", "K": "2", "Q": "2", "S": "2", "X": "2", "Z": "2",
            "D": "3", "T": "3",
            "L": "4",
            "M": "5", "N": "5",
            "R": "6",
        }

        prev_code = consonant_map.get(soundex, "0")

        for char in name_clean[1:]:
            code = consonant_map.get(char, "0")
            if code != "0" and code != prev_code:
                soundex += code
            prev_code = code

        # Pad or truncate to 6 characters
        soundex = (soundex + "000000")[:6]

        return soundex

    except Exception as e:
        logger.warning("phonetic_key_error", name=name, error=str(e))
        return None


def normalize_survey_number(value: Any) -> Optional[str]:
    """
    Normalize survey number by stripping leading zeros and normalizing separators.

    Examples:
        "0123/4A" -> "123/4A"
        "123-4-A" -> "123/4/A"
        "123.4.A" -> "123/4/A"

    Args:
        value: Survey number to normalize

    Returns:
        Normalized survey number or None
    """
    if value is None or value == "":
        return None

    try:
        value_str = str(value).strip()

        # Replace various separators with /
        value_normalized = re.sub(r"[-.]", "/", value_str)

        # Strip leading zeros from numeric parts
        parts = value_normalized.split("/")
        normalized_parts = []

        for part in parts:
            # Check if part starts with digits
            match = re.match(r"^0*(\d+)(.*)$", part)
            if match:
                number, suffix = match.groups()
                normalized_parts.append(number + suffix if number else "0" + suffix)
            else:
                normalized_parts.append(part)

        return "/".join(normalized_parts)

    except Exception as e:
        logger.warning("survey_number_normalize_error", value=value, error=str(e))
        return None


def parse_address(text: Any) -> Optional[Dict[str, str]]:
    """
    Parse address text to extract district/village/other components.

    Basic pattern matching for Indian addresses.

    Args:
        text: Address text to parse

    Returns:
        Dict with parsed components (district, village, pincode, etc.) or None
    """
    if text is None or text == "":
        return None

    try:
        text_str = str(text).strip()

        result = {
            "district": None,
            "village": None,
            "pincode": None,
            "state": None,
        }

        # Extract pincode (6 digits)
        pincode_match = re.search(r"\b(\d{6})\b", text_str)
        if pincode_match:
            result["pincode"] = pincode_match.group(1)

        # Extract district (common patterns)
        district_match = re.search(r"(?:district[:\s]+|dist[:\s]+)([A-Za-z\s]+?)(?:,|\.|$)", text_str, re.IGNORECASE)
        if district_match:
            result["district"] = district_match.group(1).strip()

        # Extract village (common patterns)
        village_match = re.search(r"(?:village[:\s]+|vill[:\s]+)([A-Za-z\s]+?)(?:,|\.|$)", text_str, re.IGNORECASE)
        if village_match:
            result["village"] = village_match.group(1).strip()

        # Extract state (common patterns)
        state_match = re.search(r"(?:state[:\s]+)([A-Za-z\s]+?)(?:,|\.|$)", text_str, re.IGNORECASE)
        if state_match:
            result["state"] = state_match.group(1).strip()

        return result

    except Exception as e:
        logger.warning("address_parse_error", text=text, error=str(e))
        return None


def validate_geometry(geometry: Any) -> Optional[str]:
    """
    Validate geometry (WKT or GeoJSON) and return canonical WKT.

    Uses Shapely for validation.

    Args:
        geometry: Geometry in WKT string or GeoJSON dict format

    Returns:
        Validated WKT string or None if invalid
    """
    if geometry is None or geometry == "":
        return None

    try:
        # Handle GeoJSON dict
        if isinstance(geometry, dict):
            geom = shape(geometry)
        else:
            # Handle WKT string
            geometry_str = str(geometry).strip()
            geom = wkt.loads(geometry_str)

        # Check if valid
        if not geom.is_valid:
            logger.warning("invalid_geometry", geometry=str(geometry)[:100])
            return None

        # Return as WKT
        return geom.wkt

    except Exception as e:
        logger.warning("geometry_validation_error", error=str(e))
        return None


def hash_pii(value: Any) -> Optional[str]:
    """
    Hash PII (Personally Identifiable Information) like Aadhaar.

    Uses SHA-256 for one-way hashing.

    Args:
        value: PII value to hash

    Returns:
        SHA-256 hex digest or None
    """
    if value is None or value == "":
        return None

    try:
        value_str = str(value).strip()
        # Add salt for security (in production, use a proper secret)
        salted = f"bhoomi_salt_{value_str}"
        hash_obj = hashlib.sha256(salted.encode("utf-8"))
        return hash_obj.hexdigest()
    except Exception as e:
        logger.warning("hash_pii_error", error=str(e))
        return None


def normalize_name(value: Any) -> Optional[str]:
    """
    Normalize person/entity name.

    - Strips extra whitespace
    - Title case
    - Removes special characters except spaces, dots, commas

    Args:
        value: Name to normalize

    Returns:
        Normalized name or None
    """
    if value is None or value == "":
        return None

    try:
        value_str = str(value).strip()

        # Remove extra whitespace
        value_str = re.sub(r"\s+", " ", value_str)

        # Remove special characters except space, dot, comma, hyphen
        value_str = re.sub(r"[^\w\s.,-]", "", value_str)

        # Title case
        value_str = value_str.title()

        return value_str

    except Exception as e:
        logger.warning("name_normalize_error", value=value, error=str(e))
        return None
