"""
Service applications — submission and tracking.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.schemas.application import (
    ApplicationCreate,
    ApplicationResponse,
    ApplicationListResponse,
    ApplicationStatus,
    SERVICE_CATALOG,
)

logger = structlog.get_logger()
router = APIRouter()


def _ref_number(app_type: str, app_id: uuid.UUID) -> str:
    prefix = {
        "MUTATION_REQUEST": "MUT",
        "ENCUMBRANCE_CERTIFICATE": "EC",
        "LAND_USE_CHANGE_PERMISSION": "LUC",
        "BUILDING_PERMIT": "BP",
        "PARCEL_BOUNDARY_CORRECTION": "PBC",
        "DISPUTE_FILING": "DIS",
    }.get(app_type, "APP")
    short = str(app_id).split("-")[0].upper()
    year = datetime.utcnow().year
    return f"{prefix}-{year}-{short}"


@router.post("/api/v1/services/applications", response_model=ApplicationResponse, status_code=201)
async def submit_application(
    body: ApplicationCreate,
    db: AsyncSession = Depends(get_db),
):
    # Verify parcel exists
    p = await db.execute(
        text("SELECT id FROM identity.parcels WHERE id = :pid AND is_active = true"),
        {"pid": body.parcel_id},
    )
    if not p.fetchone():
        raise HTTPException(status_code=404, detail="Parcel not found or inactive")

    app_id = uuid.uuid4()
    now = datetime.utcnow()
    ref = _ref_number(body.application_type.value, app_id)

    import json
    await db.execute(
        text(
            """
            INSERT INTO citizen.applications (
                id, application_type, parcel_id, applicant_id,
                status, reference_number, submitted_at, last_updated,
                details, contact_mobile, contact_email
            ) VALUES (
                :id, :atype, :parcel_id, :applicant_id,
                :status, :ref, :now, :now,
                :details::jsonb, :mobile, :email
            )
            """
        ),
        {
            "id": app_id,
            "atype": body.application_type.value,
            "parcel_id": body.parcel_id,
            "applicant_id": body.applicant_id,
            "status": ApplicationStatus.SUBMITTED.value,
            "ref": ref,
            "now": now,
            "details": json.dumps(body.details),
            "mobile": body.contact_mobile,
            "email": body.contact_email,
        },
    )
    await db.commit()

    logger.info("application_submitted", ref=ref, type=body.application_type.value)
    return ApplicationResponse(
        id=app_id,
        application_type=body.application_type,
        parcel_id=body.parcel_id,
        applicant_id=body.applicant_id,
        status=ApplicationStatus.SUBMITTED,
        reference_number=ref,
        submitted_at=now,
        last_updated=now,
        details=body.details,
        remarks=None,
    )


@router.get("/api/v1/services/applications/{app_id}", response_model=ApplicationResponse)
async def get_application(
    app_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    row = await db.execute(
        text(
            """
            SELECT id, application_type, parcel_id, applicant_id,
                   status, reference_number, submitted_at, last_updated,
                   details, remarks
            FROM citizen.applications WHERE id = :id
            """
        ),
        {"id": app_id},
    )
    r = row.fetchone()
    if not r:
        raise HTTPException(status_code=404, detail="Application not found")

    return ApplicationResponse(
        id=r[0], application_type=r[1], parcel_id=r[2],
        applicant_id=r[3], status=r[4], reference_number=r[5],
        submitted_at=r[6], last_updated=r[7], details=r[8], remarks=r[9],
    )


@router.get("/api/v1/services/applications/my", response_model=ApplicationListResponse)
async def my_applications(
    applicant_id: str = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * page_size
    count_row = await db.execute(
        text("SELECT COUNT(*) FROM citizen.applications WHERE applicant_id = :aid"),
        {"aid": applicant_id},
    )
    total = count_row.scalar() or 0

    rows = await db.execute(
        text(
            """
            SELECT id, application_type, parcel_id, applicant_id,
                   status, reference_number, submitted_at, last_updated,
                   details, remarks
            FROM citizen.applications
            WHERE applicant_id = :aid
            ORDER BY submitted_at DESC
            LIMIT :limit OFFSET :offset
            """
        ),
        {"aid": applicant_id, "limit": page_size, "offset": offset},
    )
    items = [
        ApplicationResponse(
            id=r[0], application_type=r[1], parcel_id=r[2],
            applicant_id=r[3], status=r[4], reference_number=r[5],
            submitted_at=r[6], last_updated=r[7], details=r[8], remarks=r[9],
        )
        for r in rows.fetchall()
    ]
    return ApplicationListResponse(total=total, items=items)


@router.get("/api/v1/services/catalog")
async def service_catalog():
    return {"services": SERVICE_CATALOG}
