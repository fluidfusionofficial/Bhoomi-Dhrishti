"""
Conformance test suite for state adapters.
Bronze / Silver / Gold tier assessment.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


BRONZE_REQUIREMENTS = [
    "mapping_config_registered",
    "at_least_one_successful_sync",
    "parcel_search_works",
]

SILVER_REQUIREMENTS = BRONZE_REQUIREMENTS + [
    "live_api_connection",
    "sync_within_7_days",
    "provenance_badges_accurate",
]

GOLD_REQUIREMENTS = SILVER_REQUIREMENTS + [
    "bidirectional_integration",
    "conflict_queue_populated",
    "99pct_ulpin_coverage",
]

ALL_CHECKS = set(GOLD_REQUIREMENTS)


@dataclass
class CheckResult:
    name: str
    passed: bool
    message: str
    detail: Optional[Any] = None


@dataclass
class ConformanceReport:
    state_code: str
    run_at: datetime
    tier: str                          # BRONZE / SILVER / GOLD / NONE
    checks: List[CheckResult] = field(default_factory=list)
    passed: List[str] = field(default_factory=list)
    failed: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "state_code": self.state_code,
            "run_at": self.run_at.isoformat(),
            "tier": self.tier,
            "passed": self.passed,
            "failed": self.failed,
            "checks": [
                {
                    "name": c.name,
                    "passed": c.passed,
                    "message": c.message,
                    "detail": c.detail,
                }
                for c in self.checks
            ],
        }


def _determine_tier(passed: set) -> str:
    if all(r in passed for r in GOLD_REQUIREMENTS):
        return "GOLD"
    if all(r in passed for r in SILVER_REQUIREMENTS):
        return "SILVER"
    if all(r in passed for r in BRONZE_REQUIREMENTS):
        return "BRONZE"
    return "NONE"


async def run_conformance_suite(state_code: str, db) -> ConformanceReport:
    """
    Execute all conformance checks for a state and return a ConformanceReport.
    `db` is an AsyncSession.
    """
    from sqlalchemy import text

    checks: List[CheckResult] = []
    passed_names: List[str] = []
    failed_names: List[str] = []
    now = datetime.utcnow()

    # ------------------------------------------------------------------
    # CHECK 1: mapping_config_registered
    # ------------------------------------------------------------------
    row = await db.execute(
        text("SELECT COUNT(*) FROM interop.mapping_configs WHERE state_code = :sc AND is_active = true"),
        {"sc": state_code},
    )
    count = row.scalar() or 0
    c = CheckResult(
        name="mapping_config_registered",
        passed=count > 0,
        message=f"{count} active mapping config(s) registered" if count > 0 else "No mapping config found",
        detail={"config_count": count},
    )
    checks.append(c)
    (passed_names if c.passed else failed_names).append(c.name)

    # ------------------------------------------------------------------
    # CHECK 2: at_least_one_successful_sync
    # ------------------------------------------------------------------
    sync_row = await db.execute(
        text(
            """
            SELECT COUNT(*) FROM audit.events ae
            JOIN identity.parcels p ON p.id = ae.parcel_id
            WHERE p.state_code = :sc AND ae.event_type = 'INTEGRATION_SYNC'
            """
        ),
        {"sc": state_code},
    )
    sync_count = sync_row.scalar() or 0
    c = CheckResult(
        name="at_least_one_successful_sync",
        passed=sync_count > 0,
        message=f"{sync_count} sync event(s) recorded" if sync_count > 0 else "No sync events found",
        detail={"sync_event_count": sync_count},
    )
    checks.append(c)
    (passed_names if c.passed else failed_names).append(c.name)

    # ------------------------------------------------------------------
    # CHECK 3: parcel_search_works
    # ------------------------------------------------------------------
    parcel_row = await db.execute(
        text("SELECT COUNT(*) FROM identity.parcels WHERE state_code = :sc AND is_active = true"),
        {"sc": state_code},
    )
    parcel_count = parcel_row.scalar() or 0
    c = CheckResult(
        name="parcel_search_works",
        passed=parcel_count > 0,
        message=f"{parcel_count} active parcel(s) found for state" if parcel_count > 0 else "No parcels indexed",
        detail={"parcel_count": parcel_count},
    )
    checks.append(c)
    (passed_names if c.passed else failed_names).append(c.name)

    # ------------------------------------------------------------------
    # CHECK 4: live_api_connection (Silver)
    # ------------------------------------------------------------------
    api_row = await db.execute(
        text(
            """
            SELECT connection_type, last_tested_at
            FROM interop.state_connections
            WHERE state_code = :sc AND status = 'ACTIVE'
            ORDER BY last_tested_at DESC LIMIT 1
            """
        ),
        {"sc": state_code},
    )
    api_r = api_row.fetchone()
    c = CheckResult(
        name="live_api_connection",
        passed=api_r is not None and api_r[0] in ('REST', 'GraphQL', 'SOAP'),
        message=f"Live {api_r[0]} connection active" if api_r else "No live API connection registered",
        detail={"connection_type": api_r[0] if api_r else None},
    )
    checks.append(c)
    (passed_names if c.passed else failed_names).append(c.name)

    # ------------------------------------------------------------------
    # CHECK 5: sync_within_7_days (Silver)
    # ------------------------------------------------------------------
    recent_row = await db.execute(
        text(
            """
            SELECT MAX(ae.event_time) FROM audit.events ae
            JOIN identity.parcels p ON p.id = ae.parcel_id
            WHERE p.state_code = :sc AND ae.event_type = 'INTEGRATION_SYNC'
            """
        ),
        {"sc": state_code},
    )
    last_sync = recent_row.scalar()
    sync_fresh = last_sync is not None and (now - last_sync).days < 7
    c = CheckResult(
        name="sync_within_7_days",
        passed=sync_fresh,
        message=f"Last sync: {last_sync.isoformat() if last_sync else 'never'} ({'fresh' if sync_fresh else 'stale'})",
        detail={"last_sync": last_sync.isoformat() if last_sync else None, "days_ago": (now - last_sync).days if last_sync else None},
    )
    checks.append(c)
    (passed_names if c.passed else failed_names).append(c.name)

    # ------------------------------------------------------------------
    # CHECK 6: provenance_badges_accurate (Silver)
    # ------------------------------------------------------------------
    badge_row = await db.execute(
        text(
            """
            SELECT COUNT(*) FROM identity.parcels p
            WHERE p.state_code = :sc
              AND p.provenance_source IS NOT NULL
              AND p.data_last_verified_at >= NOW() - INTERVAL '7 days'
            """
        ),
        {"sc": state_code},
    )
    badge_count = badge_row.scalar() or 0
    c = CheckResult(
        name="provenance_badges_accurate",
        passed=badge_count > 0,
        message=f"{badge_count} parcel(s) with fresh provenance badges",
        detail={"fresh_badge_count": badge_count},
    )
    checks.append(c)
    (passed_names if c.passed else failed_names).append(c.name)

    # ------------------------------------------------------------------
    # CHECK 7: bidirectional_integration (Gold)
    # ------------------------------------------------------------------
    bidi_row = await db.execute(
        text(
            """
            SELECT COUNT(*) FROM interop.state_connections
            WHERE state_code = :sc AND supports_inbound = true AND status = 'ACTIVE'
            """
        ),
        {"sc": state_code},
    )
    bidi = (bidi_row.scalar() or 0) > 0
    c = CheckResult(
        name="bidirectional_integration",
        passed=bidi,
        message="Bidirectional integration active" if bidi else "No inbound integration configured",
        detail={"inbound_active": bidi},
    )
    checks.append(c)
    (passed_names if c.passed else failed_names).append(c.name)

    # ------------------------------------------------------------------
    # CHECK 8: conflict_queue_populated (Gold)
    # ------------------------------------------------------------------
    cq_row = await db.execute(
        text(
            """
            SELECT COUNT(*) FROM ml.conflict_scores cs
            JOIN identity.parcels p ON p.id = cs.parcel_id
            WHERE p.state_code = :sc AND cs.risk_band IN ('HIGH', 'MEDIUM')
            """
        ),
        {"sc": state_code},
    )
    cq_count = cq_row.scalar() or 0
    c = CheckResult(
        name="conflict_queue_populated",
        passed=cq_count > 0,
        message=f"{cq_count} conflict score(s) in queue",
        detail={"conflict_count": cq_count},
    )
    checks.append(c)
    (passed_names if c.passed else failed_names).append(c.name)

    # ------------------------------------------------------------------
    # CHECK 9: 99pct_ulpin_coverage (Gold)
    # ------------------------------------------------------------------
    ulpin_row = await db.execute(
        text(
            """
            SELECT
                COUNT(*) AS total,
                COUNT(*) FILTER (WHERE ulpin IS NOT NULL AND ulpin != '') AS with_ulpin
            FROM identity.parcels
            WHERE state_code = :sc AND is_active = true
            """
        ),
        {"sc": state_code},
    )
    ur = ulpin_row.fetchone()
    ulpin_total = ur[0] if ur else 0
    ulpin_with = ur[1] if ur else 0
    ulpin_pct = (ulpin_with / ulpin_total * 100) if ulpin_total > 0 else 0
    c = CheckResult(
        name="99pct_ulpin_coverage",
        passed=ulpin_pct >= 99.0,
        message=f"ULPIN coverage: {ulpin_pct:.2f}% ({ulpin_with}/{ulpin_total})",
        detail={"ulpin_pct": round(ulpin_pct, 2), "total": ulpin_total, "with_ulpin": ulpin_with},
    )
    checks.append(c)
    (passed_names if c.passed else failed_names).append(c.name)

    tier = _determine_tier(set(passed_names))

    return ConformanceReport(
        state_code=state_code,
        run_at=now,
        tier=tier,
        checks=checks,
        passed=passed_names,
        failed=failed_names,
    )
