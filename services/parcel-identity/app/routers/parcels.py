"""
Parcel identity API endpoints.

Route ordering matters: /parcels/search must appear BEFORE /parcels/{identifier}
so FastAPI matches the literal path before the path parameter.
"""

from __future__ import annotations

import uuid
from typing import Optional

import structlog
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.schemas.identity import (
    CreateParcelRequest,
    LineageTree,
    ParcelAliasResponse,
    ParcelIdentityResponse,
    ParcelLineageEvent,
    ParcelSearchResponse,
    PromoteUlpinRequest,
)
from app.services import identity_service as svc

logger = structlog.get_logger()

router = APIRouter(prefix="/parcels", tags=["Parcels"])


# ---------------------------------------------------------------------------
# GET /parcels/search  ← MUST be defined BEFORE /{identifier}
# ---------------------------------------------------------------------------

@router.get(
    "/search",
    response_model=ParcelSearchResponse,
    summary="Search parcels by administrative codes or survey number",
)
async def search_parcels(
    state_code: Optional[str] = Query(None, description="LGD state code (uppercase)"),
    district_code: Optional[str] = Query(None, description="LGD district code (uppercase)"),
    village_code: Optional[str] = Query(None, description="LGD village code"),
    survey_number: Optional[str] = Query(
        None, description="Survey / khasra number — searches the alias table"
    ),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(50, ge=1, le=200, description="Results per page"),
    db: AsyncSession = Depends(get_db),
) -> ParcelSearchResponse:
    result = await svc.search_parcels(
        db=db,
        state_code=state_code,
        district_code=district_code,
        village_code=village_code,
        survey_number=survey_number,
        page=page,
        page_size=page_size,
    )
    return ParcelSearchResponse(
        items=result["items"],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
    )


# ---------------------------------------------------------------------------
# GET /parcels/{identifier}
# ---------------------------------------------------------------------------

@router.get(
    "/{identifier}",
    response_model=ParcelIdentityResponse,
    summary="Resolve a parcel by BDPR, ULPIN, or alias",
    responses={
        404: {
            "description": "Parcel not found",
            "content": {
                "application/json": {
                    "example": {"error": "NOT_FOUND", "message": "Parcel not found: BD-TN-UNKNOWN"}
                }
            },
        }
    },
)
async def get_parcel(
    identifier: str,
    db: AsyncSession = Depends(get_db),
) -> ParcelIdentityResponse:
    """
    Resolve a parcel by any of:
    - **BDPR** exact match (e.g. `BD-TN-A3F12B9C`)
    - **ULPIN** exact match (20-char national identifier)
    - **Alias value** from the `identity.parcel_aliases` table (survey numbers, khasra, etc.)

    Returns 404 with code `PARCEL_NOT_FOUND` when no match is found.
    """
    return await svc.resolve_parcel(identifier=identifier, db=db)


# ---------------------------------------------------------------------------
# POST /parcels
# ---------------------------------------------------------------------------

@router.post(
    "",
    response_model=ParcelIdentityResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new parcel",
)
async def create_parcel(
    req: CreateParcelRequest,
    db: AsyncSession = Depends(get_db),
) -> ParcelIdentityResponse:
    """
    Register a new land parcel in the platform.

    - Generates a unique BDPR of the form `BD-{STATE}-{8HEX}`.
    - Optionally registers an initial survey number as a parcel alias.
    - Returns 201 with the full parcel identity record.
    """
    return await svc.create_parcel(req=req, db=db)


# ---------------------------------------------------------------------------
# POST /parcels/{id}/promote-ulpin
# ---------------------------------------------------------------------------

@router.post(
    "/{id}/promote-ulpin",
    response_model=ParcelIdentityResponse,
    summary="Assign a ULPIN to a parcel (one-time, irreversible)",
    responses={
        409: {
            "description": "ULPIN already set",
            "content": {
                "application/json": {
                    "example": {
                        "error": "CONFLICT",
                        "message": "ULPIN_ALREADY_SET: parcel already has a ULPIN",
                    }
                }
            },
        }
    },
)
async def promote_ulpin(
    id: uuid.UUID,
    req: PromoteUlpinRequest,
    db: AsyncSession = Depends(get_db),
) -> ParcelIdentityResponse:
    """
    Promote a parcel to ULPIN-identified status.

    This is a one-shot, irreversible operation.  Once a ULPIN is assigned,
    it cannot be changed via this endpoint (a separate correction workflow
    exists for that edge case).  Returns 409 if a ULPIN is already present.
    """
    return await svc.promote_ulpin(parcel_id=id, req=req, db=db)


# ---------------------------------------------------------------------------
# GET /parcels/{id}/lineage
# ---------------------------------------------------------------------------

@router.get(
    "/{id}/lineage",
    summary="Get the lineage tree for a parcel",
    response_model=LineageTree,
)
async def get_lineage(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> LineageTree:
    """
    Returns the lineage tree showing:
    - **parents**: events that produced this parcel (e.g. the SUBDIVISION that created it)
    - **children**: events where this parcel was the parent (e.g. AMALGAMATION into a new parcel)
    """
    result = await svc.get_lineage(parcel_id=id, db=db)
    return LineageTree(
        parcel=result["parcel"],
        parents=[
            ParcelLineageEvent(
                id=e.id,
                event_type=e.event_type,
                parent_parcel_id=e.parent_parcel_id,
                child_parcel_id=e.child_parcel_id,
                event_date=e.event_date,
                authorising_document=e.authorising_document,
                authorising_authority=e.authorising_authority,
                notes=e.notes,
            )
            for e in result["parents"]
        ],
        children=[
            ParcelLineageEvent(
                id=e.id,
                event_type=e.event_type,
                parent_parcel_id=e.parent_parcel_id,
                child_parcel_id=e.child_parcel_id,
                event_date=e.event_date,
                authorising_document=e.authorising_document,
                authorising_authority=e.authorising_authority,
                notes=e.notes,
            )
            for e in result["children"]
        ],
    )


# ---------------------------------------------------------------------------
# GET /parcels/{id}/aliases
# ---------------------------------------------------------------------------

@router.get(
    "/{id}/aliases",
    response_model=ParcelAliasResponse,
    summary="Get all aliases for a parcel",
)
async def get_aliases(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ParcelAliasResponse:
    """
    Returns all known aliases for the parcel (survey numbers, khasra numbers,
    account numbers, PATTA numbers, etc.) across all source systems.
    """
    result = await svc.get_aliases(parcel_id=id, db=db)
    return ParcelAliasResponse(
        parcel_id=result["parcel_id"],
        aliases=result["aliases"],
    )


# ---------------------------------------------------------------------------
# GET /parcels/{id}/conflicts
# ---------------------------------------------------------------------------

@router.get(
    "/{id}/conflicts",
    summary="Get open conflicts for a parcel",
)
async def get_parcel_conflicts(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Returns all open conflicts detected for this parcel:
    - Area mismatches between departmental records
    - Owner name discrepancies
    - Transaction-mutation lags
    - Status inconsistencies

    Each conflict includes evidence from the sources and severity classification.
    """
    from app.conflicts.conflict_detector import ConflictDetector

    detector = ConflictDetector(db)
    conflicts = await detector.detect_all_conflicts(parcel_id=id)

    return {
        "parcel_id": str(id),
        "open_conflicts_count": len(conflicts),
        "conflicts": [
            {
                "conflict_type": c.conflict_type.value,
                "source_a": c.source_a,
                "source_b": c.source_b,
                "field_name": c.field_name,
                "value_a": c.value_a,
                "value_b": c.value_b,
                "confidence": c.confidence,
                "severity": c.severity,
                "description": c.description,
            }
            for c in conflicts
        ],
    }
