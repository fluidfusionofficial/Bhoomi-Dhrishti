"""
Audit service router — append-only event trail with hash chain.
Security-critical: NO updates or deletes ever.
"""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, date
from typing import List, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.schemas.event import (
    AuditEventCreate,
    AuditEventPage,
    AuditEventResponse,
    CitizenAccessEvent,
    CitizenAccessResponse,
    IntegrityReport,
    AUDIT_EVENT_TYPES,
)

logger = structlog.get_logger()
router = APIRouter()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _compute_event_hash(prev_hash: str, event_id: str, event_time: str, actor_id: str, resource_id: str) -> str:
    raw = f"{prev_hash}|{event_id}|{event_time}|{actor_id}|{resource_id}"
    return hashlib.sha256(raw.encode()).hexdigest()


# ---------------------------------------------------------------------------
# POST /api/v1/audit/events  — record an event (fire-and-forget safe)
# ---------------------------------------------------------------------------

@router.post("/api/v1/audit/events", status_code=202, response_model=dict)
async def record_event(
    body: AuditEventCreate,
    db: AsyncSession = Depends(get_db),
):
    if body.event_type not in AUDIT_EVENT_TYPES:
        raise HTTPException(status_code=422, detail=f"Unknown event_type: {body.event_type}")

    event_id = uuid.uuid4()
    event_time = datetime.utcnow()

    # Fetch the last event's hash to chain onto
    prev_row = await db.execute(
        text(
            "SELECT event_hash FROM audit.events "
            "ORDER BY event_time DESC, id DESC LIMIT 1"
        )
    )
    prev = prev_row.fetchone()
    prev_hash = prev[0] if (prev and prev[0]) else "GENESIS"

    event_hash = _compute_event_hash(
        prev_hash,
        str(event_id),
        event_time.isoformat(),
        body.actor_id,
        str(body.resource_id) if body.resource_id else "",
    )

    await db.execute(
        text(
            """
            INSERT INTO audit.events (
                id, event_time, event_type,
                actor_id, actor_role, actor_org,
                resource_type, resource_id,
                parcel_id, purpose, payload,
                ip_address, user_agent, event_hash
            ) VALUES (
                :id, :event_time, :event_type,
                :actor_id, :actor_role, :actor_org,
                :resource_type, :resource_id,
                :parcel_id, :purpose, :payload::jsonb,
                :ip_address, :user_agent, :event_hash
            )
            """
        ),
        {
            "id": event_id,
            "event_time": event_time,
            "event_type": body.event_type,
            "actor_id": body.actor_id,
            "actor_role": body.actor_role,
            "actor_org": body.actor_org,
            "resource_type": body.resource_type,
            "resource_id": body.resource_id,
            "parcel_id": body.parcel_id,
            "purpose": body.purpose,
            "payload": body.payload and str(body.payload).replace("'", '"'),
            "ip_address": body.ip_address,
            "user_agent": body.user_agent,
            "event_hash": event_hash,
        },
    )
    await db.commit()

    logger.info("audit_event_recorded", event_type=body.event_type, event_id=str(event_id))
    return {"id": str(event_id), "accepted": True}


# ---------------------------------------------------------------------------
# GET /api/v1/audit/parcels/{parcel_id}/events  — officer/admin view
# ---------------------------------------------------------------------------

@router.get("/api/v1/audit/parcels/{parcel_id}/events", response_model=AuditEventPage)
async def parcel_events(
    parcel_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    event_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * page_size
    filters = "WHERE parcel_id = :parcel_id"
    params: dict = {"parcel_id": parcel_id, "limit": page_size, "offset": offset}

    if event_type:
        filters += " AND event_type = :event_type"
        params["event_type"] = event_type

    count_row = await db.execute(
        text(f"SELECT COUNT(*) FROM audit.events {filters}"), params
    )
    total = count_row.scalar() or 0

    rows = await db.execute(
        text(
            f"""
            SELECT id, event_time, event_type, actor_id, actor_role, actor_org,
                   resource_type, resource_id, parcel_id, purpose, payload, event_hash
            FROM audit.events {filters}
            ORDER BY event_time DESC
            LIMIT :limit OFFSET :offset
            """
        ),
        params,
    )
    items = [
        AuditEventResponse(
            id=r[0], event_time=r[1], event_type=r[2],
            actor_id=r[3], actor_role=r[4], actor_org=r[5],
            resource_type=r[6], resource_id=r[7], parcel_id=r[8],
            purpose=r[9], payload=r[10], event_hash=r[11],
        )
        for r in rows.fetchall()
    ]
    return AuditEventPage(total=total, items=items)


# ---------------------------------------------------------------------------
# GET /api/v1/audit/citizen/my-parcel-access  — tiered citizen disclosure
# "Who accessed my land" — never shows officer name, never shows self-access
# ---------------------------------------------------------------------------

@router.get("/api/v1/audit/citizen/my-parcel-access")
async def citizen_parcel_access(
    citizen_id: str = Query(..., description="Authenticated citizen's actor_id"),
    db: AsyncSession = Depends(get_db),
):
    # Fetch parcels owned by this citizen
    parcels_row = await db.execute(
        text(
            """
            SELECT DISTINCT p.id, p.ulpin
            FROM identity.parcels p
            JOIN revenue.rights r ON r.parcel_id = p.id
            JOIN revenue.parties pa ON pa.id = r.party_id
            WHERE pa.aadhaar_hash = :citizen_id
               OR pa.mobile_hash = :citizen_id
               OR pa.voter_id_hash = :citizen_id
            """
        ),
        {"citizen_id": citizen_id},
    )
    owned_parcels = parcels_row.fetchall()
    if not owned_parcels:
        return []

    result = []
    for parcel_id, ulpin in owned_parcels:
        rows = await db.execute(
            text(
                """
                SELECT
                    DATE(event_time) AS access_date,
                    actor_role,
                    actor_org,
                    purpose,
                    COUNT(*) AS access_count
                FROM audit.events
                WHERE parcel_id = :parcel_id
                  AND actor_id != :citizen_id
                  AND event_type IN (
                    'PARCEL_VIEWED','ROR_VIEWED','DEED_VIEWED',
                    'ENCUMBRANCE_CHECKED','ML_SCORE_ACCESSED','DATA_EXPORT'
                  )
                GROUP BY DATE(event_time), actor_role, actor_org, purpose
                ORDER BY access_date DESC
                LIMIT 100
                """
            ),
            {"parcel_id": parcel_id, "citizen_id": citizen_id},
        )
        events = [
            CitizenAccessEvent(
                date=str(r[0]),
                accessor_role=r[1],
                organization=r[2],
                purpose=r[3],
                access_count=r[4],
            )
            for r in rows.fetchall()
        ]
        result.append(
            CitizenAccessResponse(parcel_id=parcel_id, ulpin=ulpin, events=events)
        )
    return result


# ---------------------------------------------------------------------------
# GET /api/v1/audit/events/search  — admin search (actor, type, date range)
# ---------------------------------------------------------------------------

@router.get("/api/v1/audit/events/search", response_model=AuditEventPage)
async def search_events(
    actor_id: Optional[str] = Query(None),
    actor_role: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    parcel_id: Optional[uuid.UUID] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    clauses = []
    params: dict = {"limit": page_size, "offset": (page - 1) * page_size}

    if actor_id:
        clauses.append("actor_id = :actor_id")
        params["actor_id"] = actor_id
    if actor_role:
        clauses.append("actor_role = :actor_role")
        params["actor_role"] = actor_role
    if event_type:
        clauses.append("event_type = :event_type")
        params["event_type"] = event_type
    if parcel_id:
        clauses.append("parcel_id = :parcel_id")
        params["parcel_id"] = parcel_id
    if date_from:
        clauses.append("event_time >= :date_from")
        params["date_from"] = date_from
    if date_to:
        clauses.append("event_time <= :date_to")
        params["date_to"] = date_to

    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""

    count_row = await db.execute(text(f"SELECT COUNT(*) FROM audit.events {where}"), params)
    total = count_row.scalar() or 0

    rows = await db.execute(
        text(
            f"""
            SELECT id, event_time, event_type, actor_id, actor_role, actor_org,
                   resource_type, resource_id, parcel_id, purpose, payload, event_hash
            FROM audit.events {where}
            ORDER BY event_time DESC
            LIMIT :limit OFFSET :offset
            """
        ),
        params,
    )
    items = [
        AuditEventResponse(
            id=r[0], event_time=r[1], event_type=r[2],
            actor_id=r[3], actor_role=r[4], actor_org=r[5],
            resource_type=r[6], resource_id=r[7], parcel_id=r[8],
            purpose=r[9], payload=r[10], event_hash=r[11],
        )
        for r in rows.fetchall()
    ]
    return AuditEventPage(total=total, items=items)


# ---------------------------------------------------------------------------
# GET /api/v1/audit/integrity/verify  — hash chain tamper detection
# ---------------------------------------------------------------------------

@router.get("/api/v1/audit/integrity/verify", response_model=IntegrityReport)
async def verify_integrity(
    limit: int = Query(10000, ge=100, le=100000),
    db: AsyncSession = Depends(get_db),
):
    rows = await db.execute(
        text(
            """
            SELECT id, event_time, actor_id, resource_id, event_hash
            FROM audit.events
            ORDER BY event_time ASC, id ASC
            LIMIT :limit
            """
        ),
        {"limit": limit},
    )
    events = rows.fetchall()

    if not events:
        return IntegrityReport(verified=True, total_events=0, message="No events to verify.")

    prev_hash = "GENESIS"
    for i, (eid, etime, actor, resource, stored_hash) in enumerate(events):
        expected = _compute_event_hash(
            prev_hash,
            str(eid),
            etime.isoformat(),
            actor,
            str(resource) if resource else "",
        )
        if stored_hash and stored_hash != expected:
            return IntegrityReport(
                verified=False,
                total_events=len(events),
                broken_at=eid,
                broken_position=i + 1,
                message=f"Hash chain broken at event {eid} (position {i + 1})",
            )
        prev_hash = stored_hash or expected

    return IntegrityReport(
        verified=True,
        total_events=len(events),
        message=f"Hash chain intact across {len(events)} events.",
    )
