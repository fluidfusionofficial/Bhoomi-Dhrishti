"""
Interoperability service router — state onboarding, sync management,
YAML mapping validation, and conformance testing.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import structlog
import yaml
from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.mapping_engine import MappingEngine
from app.conformance import run_conformance_suite, BRONZE_REQUIREMENTS, SILVER_REQUIREMENTS, GOLD_REQUIREMENTS

logger = structlog.get_logger()
router = APIRouter()
_mapping_engine = MappingEngine()


# --------------------------------------------------------------------------
# Schemas
# --------------------------------------------------------------------------

class StateInfo(BaseModel):
    state_code: str
    state_name: str
    tier: str
    total_parcels: int
    last_sync: Optional[datetime]
    departments: List[str]


class OnboardRequest(BaseModel):
    state_name: str
    contact_email: str
    mapping_yaml: str                # YAML string of mapping config
    departments: List[str] = []


class MappingValidateRequest(BaseModel):
    mapping_yaml: str


class MappingValidateResponse(BaseModel):
    valid: bool
    errors: List[str]


class SyncTriggerRequest(BaseModel):
    force: bool = False
    source_file_url: Optional[str] = None


# --------------------------------------------------------------------------
# GET /api/v1/interop/states
# --------------------------------------------------------------------------

@router.get("/api/v1/interop/states")
async def list_states(db: AsyncSession = Depends(get_db)):
    rows = await db.execute(
        text(
            """
            SELECT
                s.state_code,
                s.state_name,
                s.tier,
                COALESCE(p.total, 0) AS total_parcels,
                s.last_sync_at,
                COALESCE(s.departments, '[]')::text AS depts
            FROM interop.onboarded_states s
            LEFT JOIN (
                SELECT state_code, COUNT(*) AS total
                FROM identity.parcels WHERE is_active = true
                GROUP BY state_code
            ) p ON p.state_code = s.state_code
            ORDER BY s.state_name
            """
        )
    )
    states = [
        StateInfo(
            state_code=r[0],
            state_name=r[1],
            tier=r[2] or "BRONZE",
            total_parcels=r[3],
            last_sync=r[4],
            departments=json.loads(r[5]) if r[5] else [],
        )
        for r in rows.fetchall()
    ]
    return {"states": states, "total": len(states)}


# --------------------------------------------------------------------------
# POST /api/v1/interop/states/{code}/onboard
# --------------------------------------------------------------------------

@router.post("/api/v1/interop/states/{code}/onboard", status_code=201)
async def onboard_state(
    code: str,
    body: OnboardRequest,
    db: AsyncSession = Depends(get_db),
):
    # Validate the mapping YAML
    try:
        mapping_config = yaml.safe_load(body.mapping_yaml)
    except yaml.YAMLError as exc:
        raise HTTPException(status_code=422, detail=f"Invalid YAML: {exc}")

    errors = _mapping_engine.validate_mapping(mapping_config)
    if errors:
        raise HTTPException(status_code=422, detail={"mapping_errors": errors})

    now = datetime.utcnow()
    config_id = uuid.uuid4()

    # Upsert onboarded state
    await db.execute(
        text(
            """
            INSERT INTO interop.onboarded_states (state_code, state_name, contact_email, tier, departments, onboarded_at)
            VALUES (:sc, :name, :email, 'BRONZE', :depts::jsonb, :now)
            ON CONFLICT (state_code) DO UPDATE
            SET state_name = EXCLUDED.state_name,
                contact_email = EXCLUDED.contact_email,
                departments = EXCLUDED.departments,
                updated_at = :now
            """
        ),
        {
            "sc": code,
            "name": body.state_name,
            "email": body.contact_email,
            "depts": json.dumps(body.departments),
            "now": now,
        },
    )

    # Register mapping config
    await db.execute(
        text(
            """
            INSERT INTO interop.mapping_configs (id, state_code, config_yaml, is_active, created_at)
            VALUES (:id, :sc, :yaml, true, :now)
            """
        ),
        {"id": config_id, "sc": code, "yaml": body.mapping_yaml, "now": now},
    )
    await db.commit()

    logger.info("state_onboarded", state_code=code, state_name=body.state_name)
    return {
        "state_code": code,
        "state_name": body.state_name,
        "tier": "BRONZE",
        "mapping_config_id": str(config_id),
        "message": "State onboarded successfully. Run conformance suite to assess tier.",
    }


# --------------------------------------------------------------------------
# GET /api/v1/interop/states/{code}/sync-status
# --------------------------------------------------------------------------

@router.get("/api/v1/interop/states/{code}/sync-status")
async def sync_status(code: str, db: AsyncSession = Depends(get_db)):
    rows = await db.execute(
        text(
            """
            SELECT
                ae.payload->>'department' AS dept,
                MAX(ae.event_time) AS last_sync,
                COUNT(*) AS sync_count
            FROM audit.events ae
            JOIN identity.parcels p ON p.id = ae.parcel_id
            WHERE p.state_code = :sc AND ae.event_type = 'INTEGRATION_SYNC'
            GROUP BY ae.payload->>'department'
            """
        ),
        {"sc": code},
    )
    depts = [
        {"department": r[0] or "unknown", "last_sync": r[1].isoformat() if r[1] else None, "sync_count": r[2]}
        for r in rows.fetchall()
    ]
    return {"state_code": code, "department_syncs": depts}


# --------------------------------------------------------------------------
# POST /api/v1/interop/sync/{state_code}/{department}
# --------------------------------------------------------------------------

@router.post("/api/v1/interop/sync/{state_code}/{department}", status_code=202)
async def trigger_sync(
    state_code: str,
    department: str,
    body: SyncTriggerRequest = Body(default_factory=SyncTriggerRequest),
    db: AsyncSession = Depends(get_db),
):
    # In production: enqueue a Celery/Redis task.
    # Here we record a pending sync audit event and return immediately.
    job_id = str(uuid.uuid4())
    await db.execute(
        text(
            """
            INSERT INTO interop.sync_jobs (id, state_code, department, status, requested_at, force, source_url)
            VALUES (:id, :sc, :dept, 'QUEUED', NOW(), :force, :url)
            """
        ),
        {
            "id": job_id,
            "sc": state_code,
            "dept": department,
            "force": body.force,
            "url": body.source_file_url,
        },
    )
    await db.commit()

    logger.info("sync_triggered", state=state_code, department=department, job_id=job_id)
    return {
        "job_id": job_id,
        "state_code": state_code,
        "department": department,
        "status": "QUEUED",
        "message": "Sync job queued. Poll /sync-status for progress.",
    }


# --------------------------------------------------------------------------
# GET /api/v1/interop/mappings
# --------------------------------------------------------------------------

@router.get("/api/v1/interop/mappings")
async def list_mappings(
    state_code: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    params: dict = {}
    where = "WHERE is_active = true"
    if state_code:
        where += " AND state_code = :sc"
        params["sc"] = state_code

    rows = await db.execute(
        text(f"SELECT id, state_code, created_at FROM interop.mapping_configs {where} ORDER BY created_at DESC"),
        params,
    )
    configs = [
        {"id": str(r[0]), "state_code": r[1], "created_at": r[2].isoformat() if r[2] else None}
        for r in rows.fetchall()
    ]
    return {"mappings": configs, "total": len(configs)}


# --------------------------------------------------------------------------
# POST /api/v1/interop/mappings/validate
# --------------------------------------------------------------------------

@router.post("/api/v1/interop/mappings/validate", response_model=MappingValidateResponse)
async def validate_mapping(body: MappingValidateRequest):
    try:
        config = yaml.safe_load(body.mapping_yaml)
    except yaml.YAMLError as exc:
        return MappingValidateResponse(valid=False, errors=[f"YAML parse error: {exc}"])

    errors = _mapping_engine.validate_mapping(config)
    return MappingValidateResponse(valid=len(errors) == 0, errors=errors)


# --------------------------------------------------------------------------
# GET /api/v1/interop/conformance/{state_code}
# --------------------------------------------------------------------------

@router.get("/api/v1/interop/conformance/{state_code}")
async def get_conformance(state_code: str, db: AsyncSession = Depends(get_db)):
    """Return the most recent stored conformance report."""
    row = await db.execute(
        text(
            """
            SELECT report_json, run_at FROM interop.conformance_reports
            WHERE state_code = :sc ORDER BY run_at DESC LIMIT 1
            """
        ),
        {"sc": state_code},
    )
    r = row.fetchone()
    if not r:
        raise HTTPException(status_code=404, detail="No conformance report found. Run the suite first.")

    return {
        "state_code": state_code,
        "run_at": r[1].isoformat() if r[1] else None,
        "report": r[0],
    }


# --------------------------------------------------------------------------
# POST /api/v1/interop/conformance/{state_code}/run
# --------------------------------------------------------------------------

@router.post("/api/v1/interop/conformance/{state_code}/run")
async def run_conformance(state_code: str, db: AsyncSession = Depends(get_db)):
    report = await run_conformance_suite(state_code, db)
    report_dict = report.to_dict()

    # Persist report
    await db.execute(
        text(
            """
            INSERT INTO interop.conformance_reports (id, state_code, tier, run_at, report_json)
            VALUES (:id, :sc, :tier, :run_at, :report::jsonb)
            ON CONFLICT (state_code) DO UPDATE
            SET tier = EXCLUDED.tier, run_at = EXCLUDED.run_at, report_json = EXCLUDED.report_json
            """
        ),
        {
            "id": str(uuid.uuid4()),
            "sc": state_code,
            "tier": report.tier,
            "run_at": report.run_at,
            "report": json.dumps(report_dict),
        },
    )

    # Update state tier
    await db.execute(
        text("UPDATE interop.onboarded_states SET tier = :tier WHERE state_code = :sc"),
        {"tier": report.tier, "sc": state_code},
    )
    await db.commit()

    logger.info("conformance_run", state_code=state_code, tier=report.tier)
    return report_dict
