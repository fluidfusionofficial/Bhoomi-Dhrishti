"""
Search router — full-text + spatial parcel search, autocomplete, and NL query.
"""
from __future__ import annotations

import uuid
from typing import List, Optional, Tuple

import structlog
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.nl_query import parse_nl_query, build_sql, ParsedQuery

logger = structlog.get_logger()
router = APIRouter()


# --------------------------------------------------------------------------
# Schemas
# --------------------------------------------------------------------------

class ParcelSearchRequest(BaseModel):
    q: Optional[str] = None              # Free text
    bbox: Optional[List[float]] = None   # [minx, miny, maxx, maxy]
    land_use: Optional[str] = None
    risk_band: Optional[str] = None      # HIGH / MEDIUM / LOW
    state_code: Optional[str] = None
    district_code: Optional[str] = None
    has_dispute: Optional[bool] = None
    has_encumbrance: Optional[bool] = None
    page: int = 1
    page_size: int = 20


class ParcelSearchResult(BaseModel):
    parcel_id: uuid.UUID
    ulpin: Optional[str]
    land_use: Optional[str]
    area_sq_m: Optional[float]
    state_code: Optional[str]
    district_code: Optional[str]
    village_code: Optional[str]
    risk_band: Optional[str]
    is_urban: bool


class SearchResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[ParcelSearchResult]


class NLQueryRequest(BaseModel):
    query: str
    near_lon: Optional[float] = None   # for proximity queries
    near_lat: Optional[float] = None
    limit: int = 50


class NLQueryResponse(BaseModel):
    parsed_clauses: List[str]
    generated_sql: str
    total: int
    items: List[ParcelSearchResult]


# --------------------------------------------------------------------------
# POST /api/v1/search/parcels
# --------------------------------------------------------------------------

@router.post("/api/v1/search/parcels", response_model=SearchResponse)
async def search_parcels(
    body: ParcelSearchRequest,
    db: AsyncSession = Depends(get_db),
):
    where: List[str] = ["p.is_active = true"]
    joins: str = ""
    params: dict = {
        "limit": body.page_size,
        "offset": (body.page - 1) * body.page_size,
    }

    if body.q:
        where.append(
            "(p.ulpin ILIKE :q OR p.survey_number ILIKE :q "
            "OR EXISTS(SELECT 1 FROM revenue.parties pa2 "
            "  JOIN revenue.rights r2 ON r2.party_id = pa2.id "
            "  WHERE r2.parcel_id = p.id AND pa2.name_en ILIKE :q))"
        )
        params["q"] = f"%{body.q}%"

    if body.bbox and len(body.bbox) == 4:
        minx, miny, maxx, maxy = body.bbox
        where.append(
            "pg.geometry && ST_MakeEnvelope(:minx, :miny, :maxx, :maxy, 4326)"
        )
        params.update({"minx": minx, "miny": miny, "maxx": maxx, "maxy": maxy})

    if body.land_use:
        where.append("ror.land_use = :land_use")
        params["land_use"] = body.land_use

    if body.state_code:
        where.append("p.state_code = :state_code")
        params["state_code"] = body.state_code

    if body.district_code:
        where.append("p.district_code = :district_code")
        params["district_code"] = body.district_code

    if body.has_dispute is True:
        joins += " JOIN planning.disputes d ON d.parcel_id = p.id AND d.status = 'ACTIVE'"
    elif body.has_dispute is False:
        where.append(
            "NOT EXISTS(SELECT 1 FROM planning.disputes d WHERE d.parcel_id = p.id AND d.status = 'ACTIVE')"
        )

    if body.has_encumbrance is True:
        joins += " JOIN registration.encumbrances enc ON enc.parcel_id = p.id AND enc.is_active = true"
    elif body.has_encumbrance is False:
        where.append(
            "NOT EXISTS(SELECT 1 FROM registration.encumbrances enc WHERE enc.parcel_id = p.id AND enc.is_active = true)"
        )

    if body.risk_band:
        joins += " JOIN ml.conflict_scores cs ON cs.parcel_id = p.id"
        where.append("cs.risk_band = :risk_band")
        params["risk_band"] = body.risk_band

    where_sql = "WHERE " + " AND ".join(where)

    base_from = f"""
FROM identity.parcels p
LEFT JOIN geo.parcel_geometries pg ON pg.parcel_id = p.id
LEFT JOIN revenue.records_of_rights ror ON ror.parcel_id = p.id
{joins}
"""

    count_row = await db.execute(
        text(f"SELECT COUNT(DISTINCT p.id) {base_from} {where_sql}"), params
    )
    total = count_row.scalar() or 0

    rows = await db.execute(
        text(
            f"""
            SELECT DISTINCT p.id, p.ulpin, ror.land_use, pg.area_sq_m,
                   p.state_code, p.district_code, p.village_code, p.is_urban,
                   (SELECT risk_band FROM ml.conflict_scores
                    WHERE parcel_id = p.id ORDER BY score_value DESC LIMIT 1) AS risk_band
            {base_from}
            {where_sql}
            ORDER BY p.id
            LIMIT :limit OFFSET :offset
            """
        ),
        params,
    )
    items = [
        ParcelSearchResult(
            parcel_id=r[0], ulpin=r[1], land_use=r[2], area_sq_m=r[3],
            state_code=r[4], district_code=r[5], village_code=r[6],
            is_urban=r[7], risk_band=r[8],
        )
        for r in rows.fetchall()
    ]
    return SearchResponse(total=total, page=body.page, page_size=body.page_size, items=items)


# --------------------------------------------------------------------------
# GET /api/v1/search/suggestions
# --------------------------------------------------------------------------

@router.get("/api/v1/search/suggestions")
async def suggestions(
    q: str = Query(..., min_length=2),
    limit: int = Query(10, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
):
    rows = await db.execute(
        text(
            """
            SELECT ulpin, survey_number, state_code, district_code
            FROM identity.parcels
            WHERE is_active = true
              AND (ulpin ILIKE :q OR survey_number ILIKE :q)
            LIMIT :limit
            """
        ),
        {"q": f"{q}%", "limit": limit},
    )
    results = [
        {"ulpin": r[0], "survey_number": r[1], "state_code": r[2], "district_code": r[3]}
        for r in rows.fetchall()
    ]
    return {"query": q, "suggestions": results}


# --------------------------------------------------------------------------
# POST /api/v1/search/natural-language
# --------------------------------------------------------------------------

@router.post("/api/v1/search/natural-language", response_model=NLQueryResponse)
async def natural_language_search(
    body: NLQueryRequest,
    db: AsyncSession = Depends(get_db),
):
    pq = parse_nl_query(body.query)

    # Inject coordinates for proximity queries
    if pq.within_meters and body.near_lon is not None and body.near_lat is not None:
        pq.near_point_wkt = f"POINT({body.near_lon} {body.near_lat})"
    elif pq.within_meters:
        # No coordinates given — drop the proximity filter with a warning
        pq.within_meters = None
        pq.extracted_clauses.append(
            "WARNING: proximity filter ignored — no near_lon/near_lat provided"
        )

    sql, params = build_sql(pq, limit=body.limit)
    logger.info("nl_query", original=body.query, clauses=pq.extracted_clauses)

    try:
        rows = await db.execute(text(sql), params)
        results = rows.fetchall()
    except Exception as exc:
        logger.error("nl_query_sql_error", error=str(exc), sql=sql)
        results = []

    items = [
        ParcelSearchResult(
            parcel_id=r[0], ulpin=r[1], is_urban=r[2], land_use=r[3],
            area_sq_m=r[4], state_code=r[5], district_code=r[6],
            village_code=r[7], risk_band=None,
        )
        for r in results
    ]

    # Annotate with risk_band if risk filter was used
    if pq.risk_band:
        for item in items:
            item.risk_band = pq.risk_band

    return NLQueryResponse(
        parsed_clauses=pq.extracted_clauses,
        generated_sql=sql,
        total=len(items),
        items=items,
    )
