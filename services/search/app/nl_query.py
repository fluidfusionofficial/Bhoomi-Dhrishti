"""
Natural Language → Spatial SQL mapper.
Template-based, no LLM dependency — uses regex pattern matching to extract
spatial, land-use, administrative, and status filters from free-text queries.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class ParsedQuery:
    """Structured representation of a parsed NL query."""
    # Spatial
    within_meters: Optional[float] = None
    near_point_wkt: Optional[str] = None   # WKT POINT for ST_DWithin
    bbox: Optional[Tuple[float, float, float, float]] = None  # minx,miny,maxx,maxy

    # Administrative
    state_code: Optional[str] = None
    district_name: Optional[str] = None
    village_name: Optional[str] = None

    # Land attributes
    land_use: Optional[str] = None
    is_urban: Optional[bool] = None

    # Status filters
    has_active_dispute: bool = False
    has_encumbrance: bool = False
    tax_overdue: bool = False
    has_mutation_pending: bool = False

    # Owner filter
    owner_name: Optional[str] = None

    # Risk
    risk_band: Optional[str] = None   # HIGH / MEDIUM / LOW

    # Free-text remainder
    free_text: Optional[str] = None

    # For transparency
    extracted_clauses: List[str] = field(default_factory=list)


# Land-use vocabulary
_LAND_USE_MAP = {
    r'\bresidential\b': 'RESIDENTIAL',
    r'\bagricultural?\b': 'AGRICULTURAL',
    r'\bcommercial\b': 'COMMERCIAL',
    r'\bindustrial\b': 'INDUSTRIAL',
    r'\bforest\b': 'FOREST',
    r'\bwaste\s*land\b': 'WASTELAND',
    r'\bwater\s*body\b': 'WATER_BODY',
    r'\bpublic\s*utility\b': 'PUBLIC_UTILITY',
    r'\bmixed\s*use\b': 'MIXED_USE',
}

# Risk vocabulary
_RISK_MAP = {
    r'\bhigh[- ]?risk\b': 'HIGH',
    r'\bmedium[- ]?risk\b': 'MEDIUM',
    r'\blow[- ]?risk\b': 'LOW',
    r'\bhigh\s+conflict\b': 'HIGH',
}


def parse_nl_query(query: str) -> ParsedQuery:
    """
    Parse a natural-language query string into a ParsedQuery.
    Each matched pattern is stripped from the working copy; anything
    remaining becomes free_text for pg_trgm fallback.
    """
    pq = ParsedQuery()
    text = query.lower().strip()
    clauses: List[str] = []

    # --- Spatial: "within Nm of [location]" ---
    m = re.search(r'within\s+(\d+(?:\.\d+)?)\s*(km|m|meter|metre|kilometer|kilometre)s?\s+of\b', text)
    if m:
        dist, unit = float(m.group(1)), m.group(2)
        pq.within_meters = dist * 1000 if unit.startswith('k') else dist
        clauses.append(f"within {pq.within_meters}m proximity filter")
        text = text[:m.start()] + text[m.end():]

    # --- Land use ---
    for pattern, canonical in _LAND_USE_MAP.items():
        if re.search(pattern, text):
            pq.land_use = canonical
            clauses.append(f"land_use = {canonical}")
            text = re.sub(pattern, '', text)
            break

    # --- Urban/rural ---
    if re.search(r'\burban\b', text):
        pq.is_urban = True
        clauses.append("is_urban = true")
        text = re.sub(r'\burban\b', '', text)
    elif re.search(r'\brural\b', text):
        pq.is_urban = False
        clauses.append("is_urban = false")
        text = re.sub(r'\brural\b', '', text)

    # --- Active disputes ---
    if re.search(r'\b(active\s+dispute|dispute|disputed)\b', text):
        pq.has_active_dispute = True
        clauses.append("has active dispute")
        text = re.sub(r'\b(active\s+dispute|dispute|disputed)\b', '', text)

    # --- Encumbrance / mortgage ---
    if re.search(r'\b(encumbrance|mortgage|lien|charge)\b', text):
        pq.has_encumbrance = True
        clauses.append("has active encumbrance")
        text = re.sub(r'\b(encumbrance|mortgage|lien|charge)\b', '', text)

    # --- Tax overdue ---
    if re.search(r'\b(tax\s+overdue|overdue\s+tax|tax\s+arrear)\b', text):
        pq.tax_overdue = True
        clauses.append("property tax overdue")
        text = re.sub(r'\b(tax\s+overdue|overdue\s+tax|tax\s+arrear)\b', '', text)

    # --- Pending mutation ---
    if re.search(r'\b(pending\s+mutation|mutation\s+pending)\b', text):
        pq.has_mutation_pending = True
        clauses.append("has pending mutation")
        text = re.sub(r'\b(pending\s+mutation|mutation\s+pending)\b', '', text)

    # --- Owner name: "owned by <name>" ---
    m = re.search(r'owned\s+by\s+([a-z][a-z\s]{1,40})', text)
    if m:
        pq.owner_name = m.group(1).strip().title()
        clauses.append(f"owner name ILIKE '%{pq.owner_name}%'")
        text = text[:m.start()] + text[m.end():]

    # --- District/village: "in <place>" ---
    m = re.search(r'\bin\s+([a-z][a-z\s]{1,30}(?:district|taluk|village|tehsil)?)\b', text)
    if m:
        place = m.group(1).strip().title()
        if 'district' in place.lower():
            pq.district_name = re.sub(r'(?i)district', '', place).strip()
            clauses.append(f"district = {pq.district_name}")
        elif any(w in place.lower() for w in ('village', 'taluk', 'tehsil')):
            pq.village_name = re.sub(r'(?i)(village|taluk|tehsil)', '', place).strip()
            clauses.append(f"village = {pq.village_name}")
        else:
            pq.district_name = place
            clauses.append(f"district/area = {place}")
        text = text[:m.start()] + text[m.end():]

    # --- Risk band ---
    for pattern, band in _RISK_MAP.items():
        if re.search(pattern, text):
            pq.risk_band = band
            clauses.append(f"risk_band = {band}")
            text = re.sub(pattern, '', text)
            break

    # --- Remainder ---
    remainder = re.sub(r'\s+', ' ', text).strip()
    remainder = re.sub(r'^(show|find|list|all|the|parcels?|land)\s*', '', remainder).strip()
    if remainder:
        pq.free_text = remainder

    pq.extracted_clauses = clauses
    return pq


def build_sql(pq: ParsedQuery, limit: int = 100) -> Tuple[str, Dict]:
    """
    Convert a ParsedQuery to a parameterized SQL string + params dict.
    Returns (sql, params).
    """
    joins: List[str] = []
    where: List[str] = ["p.is_active = true"]
    params: Dict = {"limit": limit}

    # Base FROM
    sql_from = """
FROM identity.parcels p
LEFT JOIN geo.parcel_geometries pg ON pg.parcel_id = p.id
LEFT JOIN revenue.records_of_rights ror ON ror.parcel_id = p.id
"""

    # Spatial proximity
    if pq.within_meters is not None and pq.near_point_wkt:
        where.append(
            "ST_DWithin(pg.geometry::geography, ST_GeomFromText(:near_wkt, 4326)::geography, :within_m)"
        )
        params["near_wkt"] = pq.near_point_wkt
        params["within_m"] = pq.within_meters

    # Land use
    if pq.land_use:
        where.append("ror.land_use = :land_use")
        params["land_use"] = pq.land_use

    # Urban/rural
    if pq.is_urban is not None:
        where.append("p.is_urban = :is_urban")
        params["is_urban"] = pq.is_urban

    # Active dispute
    if pq.has_active_dispute:
        sql_from += "JOIN planning.disputes disp ON disp.parcel_id = p.id AND disp.status = 'ACTIVE'\n"

    # Encumbrance
    if pq.has_encumbrance:
        sql_from += "JOIN registration.encumbrances enc ON enc.parcel_id = p.id AND enc.is_active = true\n"

    # Tax overdue
    if pq.tax_overdue:
        sql_from += "JOIN fiscal.property_tax ptax ON ptax.parcel_id = p.id AND ptax.payment_status = 'OVERDUE'\n"

    # Owner name
    if pq.owner_name:
        sql_from += "JOIN revenue.rights rts ON rts.parcel_id = p.id JOIN revenue.parties pa ON pa.id = rts.party_id\n"
        where.append("pa.name_en ILIKE :owner_name")
        params["owner_name"] = f"%{pq.owner_name}%"

    # Risk band
    if pq.risk_band:
        sql_from += "JOIN ml.conflict_scores cs ON cs.parcel_id = p.id\n"
        where.append("cs.risk_band = :risk_band")
        params["risk_band"] = pq.risk_band

    # District / village (admin boundary)
    if pq.district_name:
        where.append("p.district_code IN (SELECT lgd_code FROM reference.admin_units WHERE name_en ILIKE :dist)")
        params["dist"] = f"%{pq.district_name}%"

    if pq.village_name:
        where.append("p.village_code IN (SELECT code FROM reference.villages WHERE name_en ILIKE :village)")
        params["village"] = f"%{pq.village_name}%"

    # Free-text trigram search
    if pq.free_text:
        where.append(
            "(p.ulpin ILIKE :ft OR p.survey_number % :ft_trgm)"
        )
        params["ft"] = f"%{pq.free_text}%"
        params["ft_trgm"] = pq.free_text

    where_clause = "WHERE " + " AND ".join(where) if where else ""

    sql = (
        "SELECT DISTINCT p.id, p.ulpin, p.is_urban, ror.land_use, pg.area_sq_m,\n"
        "       p.state_code, p.district_code, p.village_code\n"
        + sql_from
        + where_clause
        + "\nLIMIT :limit"
    )

    return sql, params
