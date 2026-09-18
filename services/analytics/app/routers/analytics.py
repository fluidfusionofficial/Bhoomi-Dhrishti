"""
Analytics service router — dashboard KPIs, conflict taxonomy,
resolution metrics, onboarding tiers, land-use trends, service delivery.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

import structlog
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db

logger = structlog.get_logger()
router = APIRouter()


# --------------------------------------------------------------------------
# Schemas
# --------------------------------------------------------------------------

class ConflictTypeSummary(BaseModel):
    type: str
    count: int


class DistrictDashboardResponse(BaseModel):
    district_name: str
    lgd_code: str
    total_parcels: int
    parcels_with_ulpin: int
    parcels_with_conflicts: int
    high_risk_parcels: int
    pending_mutations: int
    avg_mutation_time_days: float
    data_completeness_pct: float
    last_sync_revenue: Optional[datetime]
    last_sync_registration: Optional[datetime]
    top_conflict_types: List[Dict[str, Any]]
    recent_land_use_changes: int


class StateDashboardResponse(BaseModel):
    state_name: str
    state_code: str
    total_parcels: int
    parcels_with_ulpin: int
    districts_with_data: int
    high_risk_parcels: int
    onboarding_tier: str   # BRONZE / SILVER / GOLD
    data_completeness_pct: float
    top_conflict_types: List[Dict[str, Any]]


class ResolutionMetrics(BaseModel):
    er_precision: float
    er_recall: float
    er_f1: float
    total_candidate_pairs: int
    confirmed_matches: int
    false_positives: int
    false_negatives: int
    as_of: datetime


class OnboardingState(BaseModel):
    state_code: str
    state_name: str
    tier: str
    total_parcels: int
    ulpin_pct: float
    last_sync: Optional[datetime]
    requirements_met: List[str]
    requirements_missing: List[str]


class LandUseTrend(BaseModel):
    change_type: str
    count: int
    avg_confidence: float
    month: str


class ServiceDeliveryMetrics(BaseModel):
    application_type: str
    total: int
    completed: int
    avg_days: float
    p90_days: float
    sla_met_pct: float


# --------------------------------------------------------------------------
# District dashboard
# --------------------------------------------------------------------------

@router.get("/api/v1/analytics/dashboard/district/{lgd_code}", response_model=DistrictDashboardResponse)
async def district_dashboard(
    lgd_code: str,
    db: AsyncSession = Depends(get_db),
):
    # Total and ULPIN coverage
    totals = await db.execute(
        text(
            """
            SELECT
                COUNT(*) AS total,
                COUNT(*) FILTER (WHERE ulpin IS NOT NULL AND ulpin != '') AS with_ulpin
            FROM identity.parcels
            WHERE district_code = :lgd AND is_active = true
            """
        ),
        {"lgd": lgd_code},
    )
    t = totals.fetchone()
    total_parcels = t[0] if t else 0
    parcels_with_ulpin = t[1] if t else 0

    # High-risk and conflict parcels
    risks = await db.execute(
        text(
            """
            SELECT
                COUNT(DISTINCT cs.parcel_id) FILTER (WHERE cs.risk_band = 'HIGH') AS high_risk,
                COUNT(DISTINCT cs.parcel_id) AS with_conflicts
            FROM ml.conflict_scores cs
            JOIN identity.parcels p ON p.id = cs.parcel_id
            WHERE p.district_code = :lgd
            """
        ),
        {"lgd": lgd_code},
    )
    r = risks.fetchone()
    high_risk = r[0] if r else 0
    parcels_with_conflicts = r[1] if r else 0

    # Pending mutations (from audit events as proxy)
    mut_row = await db.execute(
        text(
            """
            SELECT COUNT(*) FROM audit.events ae
            JOIN identity.parcels p ON p.id = ae.parcel_id
            WHERE p.district_code = :lgd
              AND ae.event_type = 'MUTATION_SUBMITTED'
              AND (ae.payload->>'status' = 'PENDING' OR ae.payload->>'status' IS NULL)
            """
        ),
        {"lgd": lgd_code},
    )
    pending_mutations = mut_row.scalar() or 0

    # Avg mutation time (days from submitted to approved/rejected)
    avg_row = await db.execute(
        text(
            """
            WITH submitted AS (
                SELECT parcel_id, event_time AS t_start, payload->>'ref_id' AS ref_id
                FROM audit.events ae
                JOIN identity.parcels p ON p.id = ae.parcel_id
                WHERE p.district_code = :lgd AND ae.event_type = 'MUTATION_SUBMITTED'
            ),
            decided AS (
                SELECT parcel_id, event_time AS t_end, payload->>'ref_id' AS ref_id
                FROM audit.events ae
                JOIN identity.parcels p ON p.id = ae.parcel_id
                WHERE p.district_code = :lgd
                  AND ae.event_type IN ('MUTATION_APPROVED', 'MUTATION_REJECTED')
            )
            SELECT COALESCE(AVG(EXTRACT(EPOCH FROM (d.t_end - s.t_start)) / 86400), 0)
            FROM submitted s JOIN decided d ON d.parcel_id = s.parcel_id AND d.ref_id = s.ref_id
            """
        ),
        {"lgd": lgd_code},
    )
    avg_mutation_days = float(avg_row.scalar() or 0.0)

    # Data completeness: % of parcels with geometry + RoR + registration + tax record
    comp_row = await db.execute(
        text(
            """
            SELECT
                ROUND(100.0 * COUNT(*) FILTER (
                    WHERE EXISTS(SELECT 1 FROM geo.parcel_geometries pg WHERE pg.parcel_id = p.id)
                      AND EXISTS(SELECT 1 FROM revenue.records_of_rights ror WHERE ror.parcel_id = p.id)
                      AND EXISTS(SELECT 1 FROM registration.deeds d WHERE d.parcel_id = p.id)
                      AND EXISTS(SELECT 1 FROM fiscal.property_tax pt WHERE pt.parcel_id = p.id)
                ) / NULLIF(COUNT(*), 0), 2)
            FROM identity.parcels p
            WHERE p.district_code = :lgd AND p.is_active = true
            """
        ),
        {"lgd": lgd_code},
    )
    data_completeness = float(comp_row.scalar() or 0.0)

    # Top conflict types
    ct_rows = await db.execute(
        text(
            """
            SELECT cs.score_type, COUNT(*) AS cnt
            FROM ml.conflict_scores cs
            JOIN identity.parcels p ON p.id = cs.parcel_id
            WHERE p.district_code = :lgd
            GROUP BY cs.score_type
            ORDER BY cnt DESC
            LIMIT 5
            """
        ),
        {"lgd": lgd_code},
    )
    top_conflict_types = [{"type": r[0], "count": r[1]} for r in ct_rows.fetchall()]

    # Recent land-use changes (90 days)
    luc_row = await db.execute(
        text(
            """
            SELECT COUNT(*) FROM ml.land_use_changes luc
            JOIN identity.parcels p ON p.id = luc.parcel_id
            WHERE p.district_code = :lgd
              AND luc.reviewed_status = 'PENDING'
              AND luc.created_at >= NOW() - INTERVAL '90 days'
            """
        ),
        {"lgd": lgd_code},
    )
    recent_luc = luc_row.scalar() or 0

    # Sync timestamps
    sync_row = await db.execute(
        text(
            """
            SELECT
                MAX(event_time) FILTER (WHERE event_type = 'INTEGRATION_SYNC'
                    AND payload->>'department' = 'revenue') AS rev_sync,
                MAX(event_time) FILTER (WHERE event_type = 'INTEGRATION_SYNC'
                    AND payload->>'department' = 'registration') AS reg_sync
            FROM audit.events ae
            JOIN identity.parcels p ON p.id = ae.parcel_id
            WHERE p.district_code = :lgd
            """
        ),
        {"lgd": lgd_code},
    )
    sr = sync_row.fetchone()
    last_sync_revenue = sr[0] if sr else None
    last_sync_registration = sr[1] if sr else None

    # District name from reference
    name_row = await db.execute(
        text("SELECT name_en FROM reference.admin_units WHERE lgd_code = :lgd LIMIT 1"),
        {"lgd": lgd_code},
    )
    nr = name_row.fetchone()
    district_name = nr[0] if nr else lgd_code

    return DistrictDashboardResponse(
        district_name=district_name,
        lgd_code=lgd_code,
        total_parcels=total_parcels,
        parcels_with_ulpin=parcels_with_ulpin,
        parcels_with_conflicts=parcels_with_conflicts,
        high_risk_parcels=high_risk,
        pending_mutations=pending_mutations,
        avg_mutation_time_days=round(avg_mutation_days, 2),
        data_completeness_pct=data_completeness,
        last_sync_revenue=last_sync_revenue,
        last_sync_registration=last_sync_registration,
        top_conflict_types=top_conflict_types,
        recent_land_use_changes=recent_luc,
    )


# --------------------------------------------------------------------------
# State dashboard
# --------------------------------------------------------------------------

@router.get("/api/v1/analytics/dashboard/state/{state_code}", response_model=StateDashboardResponse)
async def state_dashboard(
    state_code: str,
    db: AsyncSession = Depends(get_db),
):
    totals = await db.execute(
        text(
            """
            SELECT
                COUNT(*) AS total,
                COUNT(*) FILTER (WHERE ulpin IS NOT NULL AND ulpin != '') AS with_ulpin,
                COUNT(DISTINCT district_code) AS districts
            FROM identity.parcels WHERE state_code = :sc AND is_active = true
            """
        ),
        {"sc": state_code},
    )
    t = totals.fetchone()

    risks = await db.execute(
        text(
            """
            SELECT COUNT(DISTINCT cs.parcel_id)
            FROM ml.conflict_scores cs JOIN identity.parcels p ON p.id = cs.parcel_id
            WHERE p.state_code = :sc AND cs.risk_band = 'HIGH'
            """
        ),
        {"sc": state_code},
    )
    high_risk = risks.scalar() or 0

    comp_row = await db.execute(
        text(
            """
            SELECT ROUND(100.0 * COUNT(*) FILTER (
                    WHERE EXISTS(SELECT 1 FROM geo.parcel_geometries pg WHERE pg.parcel_id = p.id)
                      AND EXISTS(SELECT 1 FROM revenue.records_of_rights ror WHERE ror.parcel_id = p.id)
                ) / NULLIF(COUNT(*), 0), 2)
            FROM identity.parcels p WHERE p.state_code = :sc AND p.is_active = true
            """
        ),
        {"sc": state_code},
    )
    data_completeness = float(comp_row.scalar() or 0.0)

    ct_rows = await db.execute(
        text(
            """
            SELECT cs.score_type, COUNT(*) AS cnt
            FROM ml.conflict_scores cs JOIN identity.parcels p ON p.id = cs.parcel_id
            WHERE p.state_code = :sc
            GROUP BY cs.score_type ORDER BY cnt DESC LIMIT 5
            """
        ),
        {"sc": state_code},
    )
    top_ct = [{"type": r[0], "count": r[1]} for r in ct_rows.fetchall()]

    name_row = await db.execute(
        text("SELECT name_en FROM reference.admin_units WHERE lgd_code = :sc LIMIT 1"),
        {"sc": state_code},
    )
    nr = name_row.fetchone()
    state_name = nr[0] if nr else state_code

    # Derive tier
    total = t[0] if t else 0
    with_ulpin = t[1] if t else 0
    ulpin_pct = (with_ulpin / total * 100) if total else 0
    tier = "BRONZE" if ulpin_pct < 50 else ("SILVER" if ulpin_pct < 99 else "GOLD")

    return StateDashboardResponse(
        state_name=state_name,
        state_code=state_code,
        total_parcels=total,
        parcels_with_ulpin=with_ulpin,
        districts_with_data=t[2] if t else 0,
        high_risk_parcels=high_risk,
        onboarding_tier=tier,
        data_completeness_pct=data_completeness,
        top_conflict_types=top_ct,
    )


# --------------------------------------------------------------------------
# Conflict summary
# --------------------------------------------------------------------------

@router.get("/api/v1/analytics/conflicts/summary")
async def conflict_summary(
    state_code: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    params: dict = {}
    where = ""
    if state_code:
        where = "JOIN identity.parcels p ON p.id = cs.parcel_id WHERE p.state_code = :sc"
        params["sc"] = state_code

    rows = await db.execute(
        text(
            f"""
            SELECT cs.score_type, cs.risk_band, COUNT(*) AS cnt,
                   ROUND(AVG(cs.score_value)::numeric, 3) AS avg_score
            FROM ml.conflict_scores cs {where}
            GROUP BY cs.score_type, cs.risk_band
            ORDER BY cnt DESC
            """
        ),
        params,
    )
    items = [
        {"score_type": r[0], "risk_band": r[1], "count": r[2], "avg_score": float(r[3] or 0)}
        for r in rows.fetchall()
    ]
    return {"conflict_types": items}


# --------------------------------------------------------------------------
# Resolution metrics (ER precision / recall / F1)
# --------------------------------------------------------------------------

@router.get("/api/v1/analytics/resolution/metrics", response_model=ResolutionMetrics)
async def resolution_metrics(db: AsyncSession = Depends(get_db)):
    row = await db.execute(
        text(
            """
            SELECT
                COUNT(*) FILTER (WHERE match_status = 'CANDIDATE') AS candidates,
                COUNT(*) FILTER (WHERE match_status = 'CONFIRMED') AS confirmed,
                COUNT(*) FILTER (WHERE match_status = 'FALSE_POSITIVE') AS fp,
                COUNT(*) FILTER (WHERE match_status = 'FALSE_NEGATIVE') AS fn
            FROM identity.parcel_match_candidates
            """
        )
    )
    r = row.fetchone()
    candidates = r[0] or 0
    confirmed = r[1] or 0
    fp = r[2] or 0
    fn = r[3] or 0

    precision = confirmed / (confirmed + fp) if (confirmed + fp) > 0 else 0.0
    recall = confirmed / (confirmed + fn) if (confirmed + fn) > 0 else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    return ResolutionMetrics(
        er_precision=round(precision, 4),
        er_recall=round(recall, 4),
        er_f1=round(f1, 4),
        total_candidate_pairs=candidates,
        confirmed_matches=confirmed,
        false_positives=fp,
        false_negatives=fn,
        as_of=datetime.utcnow(),
    )


# --------------------------------------------------------------------------
# State onboarding progress
# --------------------------------------------------------------------------

@router.get("/api/v1/analytics/onboarding/states")
async def onboarding_states(db: AsyncSession = Depends(get_db)):
    rows = await db.execute(
        text(
            """
            SELECT
                p.state_code,
                COUNT(*) AS total,
                COUNT(*) FILTER (WHERE p.ulpin IS NOT NULL AND p.ulpin != '') AS with_ulpin,
                MAX(ae.event_time) AS last_sync
            FROM identity.parcels p
            LEFT JOIN audit.events ae ON ae.parcel_id = p.id
                AND ae.event_type = 'INTEGRATION_SYNC'
            WHERE p.is_active = true
            GROUP BY p.state_code
            """
        )
    )

    BRONZE = ["mapping_config_registered", "at_least_one_successful_sync", "parcel_search_works"]
    SILVER = BRONZE + ["live_api_connection", "sync_within_7_days", "provenance_badges_accurate"]
    GOLD = SILVER + ["bidirectional_integration", "conflict_queue_populated", "99pct_ulpin_coverage"]

    states = []
    for r in rows.fetchall():
        sc, total, with_ulpin, last_sync = r
        ulpin_pct = (with_ulpin / total * 100) if total else 0
        sync_age_days = (
            (datetime.utcnow() - last_sync).days if last_sync else 9999
        )

        met = []
        missing = []

        # Bronze checks
        met.append("mapping_config_registered")  # simplified: assume registered if data exists
        if total > 0:
            met.append("at_least_one_successful_sync")
        else:
            missing.append("at_least_one_successful_sync")
        met.append("parcel_search_works")

        # Silver checks
        if sync_age_days < 7:
            met.append("sync_within_7_days")
            met.append("live_api_connection")
            met.append("provenance_badges_accurate")
        else:
            missing.extend(["live_api_connection", "sync_within_7_days", "provenance_badges_accurate"])

        # Gold checks
        if ulpin_pct >= 99:
            met.append("99pct_ulpin_coverage")
        else:
            missing.append("99pct_ulpin_coverage")
        # bidirectional + conflict_queue — heuristic from audit events
        missing.extend(["bidirectional_integration", "conflict_queue_populated"])

        gold_met = all(r in met for r in GOLD)
        silver_met = all(r in met for r in SILVER)
        tier = "GOLD" if gold_met else ("SILVER" if silver_met else "BRONZE")

        states.append(
            OnboardingState(
                state_code=sc,
                state_name=sc,
                tier=tier,
                total_parcels=total,
                ulpin_pct=round(ulpin_pct, 2),
                last_sync=last_sync,
                requirements_met=met,
                requirements_missing=missing,
            )
        )

    return {"states": states}


# --------------------------------------------------------------------------
# Land-use change trends
# --------------------------------------------------------------------------

@router.get("/api/v1/analytics/land-use/trends")
async def land_use_trends(
    state_code: Optional[str] = Query(None),
    months: int = Query(12, ge=1, le=36),
    db: AsyncSession = Depends(get_db),
):
    params: dict = {"months": months}
    state_filter = ""
    if state_code:
        state_filter = "JOIN identity.parcels p ON p.id = luc.parcel_id AND p.state_code = :sc"
        params["sc"] = state_code

    rows = await db.execute(
        text(
            f"""
            SELECT
                luc.change_type,
                TO_CHAR(DATE_TRUNC('month', luc.created_at), 'YYYY-MM') AS month,
                COUNT(*) AS cnt,
                ROUND(AVG(luc.confidence_score)::numeric, 3) AS avg_conf
            FROM ml.land_use_changes luc
            {state_filter}
            WHERE luc.created_at >= NOW() - (:months || ' months')::interval
            GROUP BY luc.change_type, DATE_TRUNC('month', luc.created_at)
            ORDER BY month DESC, cnt DESC
            """
        ),
        params,
    )
    trends = [
        LandUseTrend(
            change_type=r[0], month=r[1], count=r[2], avg_confidence=float(r[3] or 0)
        )
        for r in rows.fetchall()
    ]
    return {"trends": trends}


# --------------------------------------------------------------------------
# Service delivery time metrics
# --------------------------------------------------------------------------

@router.get("/api/v1/analytics/service-delivery/time")
async def service_delivery_time(
    state_code: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    params: dict = {}
    state_join = ""
    if state_code:
        state_join = "JOIN identity.parcels p ON p.id = a.parcel_id AND p.state_code = :sc"
        params["sc"] = state_code

    rows = await db.execute(
        text(
            f"""
            SELECT
                a.application_type,
                COUNT(*) AS total,
                COUNT(*) FILTER (WHERE a.status IN ('APPROVED', 'REJECTED')) AS completed,
                COALESCE(ROUND(AVG(
                    EXTRACT(EPOCH FROM (a.last_updated - a.submitted_at)) / 86400
                ) FILTER (WHERE a.status IN ('APPROVED', 'REJECTED'))::numeric, 2), 0) AS avg_days,
                COALESCE(ROUND(PERCENTILE_CONT(0.9) WITHIN GROUP (
                    ORDER BY EXTRACT(EPOCH FROM (a.last_updated - a.submitted_at)) / 86400
                ) FILTER (WHERE a.status IN ('APPROVED', 'REJECTED'))::numeric, 2), 0) AS p90_days
            FROM citizen.applications a
            {state_join}
            GROUP BY a.application_type
            """
        ),
        params,
    )

    # SLA lookup
    SLA = {
        "MUTATION_REQUEST": 30,
        "ENCUMBRANCE_CERTIFICATE": 3,
        "LAND_USE_CHANGE_PERMISSION": 90,
        "BUILDING_PERMIT": 60,
        "PARCEL_BOUNDARY_CORRECTION": 45,
        "DISPUTE_FILING": 999,
    }

    metrics = []
    for r in rows.fetchall():
        atype, total, completed, avg_days, p90_days = r
        avg_d = float(avg_days or 0)
        sla = SLA.get(atype, 30)
        sla_met_pct = round(100 * (completed / total) if total > 0 and avg_d <= sla else 0.0, 2)
        metrics.append(
            ServiceDeliveryMetrics(
                application_type=atype,
                total=total,
                completed=completed or 0,
                avg_days=avg_d,
                p90_days=float(p90_days or 0),
                sla_met_pct=sla_met_pct,
            )
        )
    return {"service_delivery": metrics}
