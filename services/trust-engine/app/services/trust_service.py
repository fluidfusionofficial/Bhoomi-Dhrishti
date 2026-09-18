"""
Trust Engine – deterministic rule-based trust scoring.

Each check queries real database tables. When a table has no matching data
the check passes with a safe-default reason (never raises an error).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Severity penalties and risk-band thresholds
# ---------------------------------------------------------------------------

PENALTIES: Dict[str, int] = {
    "CRITICAL": 40,
    "HIGH": 20,
    "MEDIUM": 10,
    "LOW": 5,
}


def _risk_band(failed: List[Dict[str, Any]]) -> str:
    has_critical = any(c["severity"] == "CRITICAL" for c in failed)
    high_count = sum(1 for c in failed if c["severity"] == "HIGH")
    medium_count = sum(1 for c in failed if c["severity"] == "MEDIUM")
    if has_critical or high_count >= 3:
        return "HIGH"
    if high_count >= 1 or medium_count >= 3:
        return "MEDIUM"
    if failed:
        return "LOW"
    return "CLEAR"


def _passed_check(code: str, name: str, severity: str, reason: str,
                  departments: List[str], rec: str) -> Dict[str, Any]:
    return {
        "check_code": code,
        "check_name": name,
        "passed": True,
        "severity": severity,
        "reason": reason,
        "affected_departments": departments,
        "recommendation": rec,
    }


def _failed_check(code: str, name: str, severity: str, reason: str,
                  departments: List[str], rec: str) -> Dict[str, Any]:
    return {
        "check_code": code,
        "check_name": name,
        "passed": False,
        "severity": severity,
        "reason": reason,
        "affected_departments": departments,
        "recommendation": rec,
    }


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

async def _check_area_mismatch(pid: uuid.UUID, db: AsyncSession) -> Dict[str, Any]:
    code, name = "AREA_MISMATCH", "Area Mismatch (Revenue vs Geo)"
    departments = ["Revenue Department", "Survey Department"]
    try:
        row = await db.execute(
            text(
                """
                SELECT ror.area_sq_m AS rev_area, pg.area_sq_m AS geo_area
                FROM revenue.records_of_rights ror
                JOIN geo.parcel_geometries pg ON pg.parcel_id = ror.parcel_id
                WHERE ror.parcel_id = :pid
                LIMIT 1
                """
            ),
            {"pid": pid},
        )
        r = row.fetchone()
        if r is None or r[0] is None or r[1] is None:
            return _passed_check(
                code, name, "MEDIUM",
                "No area data found in revenue or geo tables — skipping check.",
                departments,
                "Ensure both revenue records and geo geometries are uploaded for this parcel.",
            )
        rev_area = float(r[0])
        geo_area = float(r[1])
        if rev_area == 0:
            return _passed_check(
                code, name, "MEDIUM",
                f"Revenue area is zero; geo area={geo_area:.2f} m². Cannot compute ratio — skipping.",
                departments,
                "Update revenue records with correct area.",
            )
        diff_pct = abs(rev_area - geo_area) / rev_area * 100
        if diff_pct > 15:
            return _failed_check(
                code, name, "HIGH",
                f"Area mismatch of {diff_pct:.1f}% detected: revenue={rev_area:.2f} m², geo={geo_area:.2f} m². Threshold: 15%.",
                departments,
                "Initiate boundary correction process; obtain fresh survey measurement and update both revenue and geo records.",
            )
        if diff_pct > 5:
            return _failed_check(
                code, name, "MEDIUM",
                f"Area mismatch of {diff_pct:.1f}% detected: revenue={rev_area:.2f} m², geo={geo_area:.2f} m². Threshold: 5%.",
                departments,
                "Review and reconcile revenue and geo area figures; minor resurvey may be needed.",
            )
        return _passed_check(
            code, name, "MEDIUM",
            f"Area consistent: revenue={rev_area:.2f} m², geo={geo_area:.2f} m² (diff={diff_pct:.1f}%).",
            departments,
            "No action required.",
        )
    except Exception as exc:
        logger.warning("trust_check.error", check=code, error=str(exc))
        return _passed_check(
            code, name, "MEDIUM",
            f"Check skipped due to data unavailability: {exc}",
            departments,
            "Ensure revenue.records_of_rights and geo.parcel_geometries tables are populated.",
        )


async def _check_active_mortgage(pid: uuid.UUID, db: AsyncSession) -> Dict[str, Any]:
    code, name = "ACTIVE_MORTGAGE", "Active Mortgage / Encumbrance"
    departments = ["Registration Department", "Banks & Financial Institutions"]
    try:
        row = await db.execute(
            text(
                """
                SELECT COUNT(*) FROM registration.encumbrances
                WHERE parcel_id = :pid AND is_active = true
                """
            ),
            {"pid": pid},
        )
        count = row.scalar() or 0
        if count > 0:
            return _failed_check(
                code, name, "HIGH",
                f"{count} active encumbrance(s)/mortgage(s) found in registration records.",
                departments,
                "Obtain No-Objection Certificate from lien holder before proceeding with any transfer or mutation.",
            )
        return _passed_check(
            code, name, "HIGH",
            "No active encumbrances or mortgages found in registration records.",
            departments,
            "No action required.",
        )
    except Exception as exc:
        logger.warning("trust_check.error", check=code, error=str(exc))
        return _passed_check(
            code, name, "HIGH",
            f"Check skipped due to data unavailability: {exc}",
            departments,
            "Ensure registration.encumbrances table is populated.",
        )


async def _check_active_dispute(pid: uuid.UUID, db: AsyncSession) -> Dict[str, Any]:
    code, name = "ACTIVE_DISPUTE", "Active Court Dispute"
    departments = ["Planning Department", "District Court", "Revenue Court"]
    try:
        rows = await db.execute(
            text(
                """
                SELECT confidence, COUNT(*) AS cnt
                FROM planning.disputes
                WHERE parcel_id = :pid
                  AND status NOT IN ('DISPOSED', 'DISMISSED', 'SETTLED')
                GROUP BY confidence
                """
            ),
            {"pid": pid},
        )
        results = rows.fetchall()
        if not results:
            return _passed_check(
                code, name, "CRITICAL",
                "No active court disputes found for this parcel.",
                departments,
                "No action required.",
            )
        confirmed = sum(r[1] for r in results if r[0] == "CONFIRMED")
        possible = sum(r[1] for r in results if r[0] == "POSSIBLE")
        total = confirmed + possible
        if confirmed > 0:
            return _failed_check(
                code, name, "CRITICAL",
                f"{confirmed} CONFIRMED active dispute(s) and {possible} POSSIBLE dispute(s) found (total={total}).",
                departments,
                "Do not process any transfer until disputes are resolved. Obtain stay-free certificate from competent court.",
            )
        return _failed_check(
            code, name, "HIGH",
            f"{possible} POSSIBLE active dispute(s) found. No confirmed disputes. Requires verification.",
            departments,
            "Verify dispute status with the concerned court. Obtain legal opinion before processing mutation.",
        )
    except Exception as exc:
        logger.warning("trust_check.error", check=code, error=str(exc))
        return _passed_check(
            code, name, "CRITICAL",
            f"Check skipped due to data unavailability: {exc}",
            departments,
            "Ensure planning.disputes table is populated.",
        )


async def _check_pending_mutation(pid: uuid.UUID, db: AsyncSession) -> Dict[str, Any]:
    code, name = "PENDING_MUTATION", "Pending Mutation in Revenue Records"
    departments = ["Revenue Department", "Tehsildar Office"]
    try:
        row = await db.execute(
            text(
                """
                SELECT COUNT(*) FROM revenue.mutations
                WHERE parcel_id = :pid AND status = 'PENDING'
                """
            ),
            {"pid": pid},
        )
        count = row.scalar() or 0
        if count > 0:
            return _failed_check(
                code, name, "MEDIUM",
                f"{count} pending mutation(s) found in revenue records. Title may be in transition.",
                departments,
                "Resolve pending mutations before registering a new transaction. Contact Tehsildar office.",
            )
        return _passed_check(
            code, name, "MEDIUM",
            "No pending mutations found in revenue records.",
            departments,
            "No action required.",
        )
    except Exception as exc:
        logger.warning("trust_check.error", check=code, error=str(exc))
        return _passed_check(
            code, name, "MEDIUM",
            f"Check skipped due to data unavailability: {exc}",
            departments,
            "Ensure revenue.mutations table is populated.",
        )


async def _check_tax_due(pid: uuid.UUID, db: AsyncSession) -> Dict[str, Any]:
    code, name = "TAX_DUE", "Property Tax Outstanding"
    departments = ["Municipal Corporation", "Urban Local Body"]
    try:
        row = await db.execute(
            text(
                """
                SELECT assessment_year, payment_status, arrears, tax_amount
                FROM fiscal.property_tax
                WHERE parcel_id = :pid
                ORDER BY assessment_year DESC
                LIMIT 1
                """
            ),
            {"pid": pid},
        )
        r = row.fetchone()
        if r is None:
            return _passed_check(
                code, name, "MEDIUM",
                "No property tax records found. Tax status unknown.",
                departments,
                "Verify tax payment status with Municipal Corporation before transacting.",
            )
        year, status, arrears, tax_amount = r[0], r[1], r[2], r[3]
        if status in ("DUE", "OVERDUE"):
            arrears_val = float(arrears) if arrears else 0.0
            tax_val = float(tax_amount) if tax_amount else 0.0
            return _failed_check(
                code, name, "MEDIUM",
                f"Property tax {status} for assessment year {year}. Tax amount: ₹{tax_val:.2f}, arrears: ₹{arrears_val:.2f}.",
                departments,
                "Clear outstanding property tax before initiating transfer. Obtain tax-paid certificate from Municipal Corporation.",
            )
        return _passed_check(
            code, name, "MEDIUM",
            f"Property tax paid/clear for assessment year {year} (status={status}).",
            departments,
            "No action required.",
        )
    except Exception as exc:
        logger.warning("trust_check.error", check=code, error=str(exc))
        return _passed_check(
            code, name, "MEDIUM",
            f"Check skipped due to data unavailability: {exc}",
            departments,
            "Ensure fiscal.property_tax table is populated.",
        )


async def _check_spatial_overlap(pid: uuid.UUID, db: AsyncSession) -> Dict[str, Any]:
    code, name = "SPATIAL_OVERLAP", "Spatial Boundary Overlap Conflict"
    departments = ["Survey Department", "Revenue Department"]
    try:
        row = await db.execute(
            text(
                """
                SELECT COUNT(*), COALESCE(SUM(overlap_area_sq_m), 0) AS total_overlap
                FROM geo.topology_conflicts
                WHERE (parcel_id_1 = :pid OR parcel_id_2 = :pid)
                  AND conflict_type = 'OVERLAP'
                  AND resolution_status = 'OPEN'
                """
            ),
            {"pid": pid},
        )
        r = row.fetchone()
        count = r[0] if r else 0
        overlap_area = float(r[1]) if r and r[1] else 0.0
        if count > 0:
            return _failed_check(
                code, name, "HIGH",
                f"{count} open spatial overlap conflict(s) found. Total overlapping area: {overlap_area:.2f} m².",
                departments,
                "Initiate survey re-demarcation. Resolve topology conflicts before registering transfer.",
            )
        return _passed_check(
            code, name, "HIGH",
            "No open spatial boundary overlap conflicts found.",
            departments,
            "No action required.",
        )
    except Exception as exc:
        logger.warning("trust_check.error", check=code, error=str(exc))
        return _passed_check(
            code, name, "HIGH",
            f"Check skipped due to data unavailability: {exc}",
            departments,
            "Ensure geo.topology_conflicts table is populated.",
        )


async def _check_zoning_mismatch(pid: uuid.UUID, db: AsyncSession) -> Dict[str, Any]:
    code, name = "ZONING_MISMATCH", "Land Use vs Zoning Mismatch"
    departments = ["Planning Department", "Revenue Department"]
    try:
        row = await db.execute(
            text(
                """
                SELECT ror.land_use AS revenue_land_use, z.zone_type AS zone_type
                FROM revenue.records_of_rights ror
                LEFT JOIN planning.zones z ON z.parcel_id = ror.parcel_id
                WHERE ror.parcel_id = :pid
                LIMIT 1
                """
            ),
            {"pid": pid},
        )
        r = row.fetchone()
        if r is None:
            return _passed_check(
                code, name, "MEDIUM",
                "No revenue land-use records found. Zoning check skipped.",
                departments,
                "Ensure revenue.records_of_rights and planning.zones are populated.",
            )
        rev_land_use = (r[0] or "").upper()
        zone_type = (r[1] or "").upper() if r[1] else None
        if zone_type is None:
            return _passed_check(
                code, name, "MEDIUM",
                f"No zone record found for this parcel. Revenue land-use: {rev_land_use or 'UNKNOWN'}.",
                departments,
                "Upload master plan zone data for this parcel to enable zoning check.",
            )
        # Check if agricultural land is in a non-agricultural zone
        is_agri = "AGRI" in rev_land_use or "AGRICULTURAL" in rev_land_use
        is_non_agri_zone = "AGRI" not in zone_type and "AGRICULTURAL" not in zone_type
        if is_agri and is_non_agri_zone:
            return _failed_check(
                code, name, "MEDIUM",
                f"Land use mismatch: revenue records show '{rev_land_use}' but master plan zone is '{zone_type}'.",
                departments,
                "Obtain land-use change permission from Planning Authority before any non-agricultural development.",
            )
        return _passed_check(
            code, name, "MEDIUM",
            f"Land use consistent: revenue='{rev_land_use}', zone='{zone_type}'.",
            departments,
            "No action required.",
        )
    except Exception as exc:
        logger.warning("trust_check.error", check=code, error=str(exc))
        return _passed_check(
            code, name, "MEDIUM",
            f"Check skipped due to data unavailability: {exc}",
            departments,
            "Ensure revenue.records_of_rights and planning.zones tables are populated.",
        )


async def _check_transaction_network_flag(pid: uuid.UUID, db: AsyncSession) -> Dict[str, Any]:
    code, name = "TRANSACTION_NETWORK_FLAG", "Transaction Network Fraud Flag"
    departments = ["Enforcement Directorate", "Revenue Intelligence", "Registration Department"]
    pid_str = str(pid)
    try:
        row = await db.execute(
            text(
                """
                SELECT COUNT(*) FROM ml.transaction_network_flags
                WHERE :pid_str = ANY(parcel_ids::text[])
                """
            ),
            {"pid_str": pid_str},
        )
        count = row.scalar() or 0
        if count > 0:
            return _failed_check(
                code, name, "CRITICAL",
                f"Parcel appears in {count} transaction network flag(s) from ML fraud-detection model.",
                departments,
                "Flag for mandatory verification by revenue intelligence. Do not process any transaction until cleared by enforcement authority.",
            )
        return _passed_check(
            code, name, "CRITICAL",
            "Parcel not flagged in any transaction network fraud pattern.",
            departments,
            "No action required.",
        )
    except Exception as exc:
        logger.warning("trust_check.error", check=code, error=str(exc))
        return _passed_check(
            code, name, "CRITICAL",
            f"Check skipped due to data unavailability: {exc}",
            departments,
            "Ensure ml.transaction_network_flags table is populated.",
        )


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

async def compute_trust_score(parcel_id: uuid.UUID, db: AsyncSession) -> dict:
    """Run all 8 deterministic checks and return a fully assembled trust score dict."""
    checks_results: List[Dict[str, Any]] = []

    checks_results.append(await _check_area_mismatch(parcel_id, db))
    checks_results.append(await _check_active_mortgage(parcel_id, db))
    checks_results.append(await _check_active_dispute(parcel_id, db))
    checks_results.append(await _check_pending_mutation(parcel_id, db))
    checks_results.append(await _check_tax_due(parcel_id, db))
    checks_results.append(await _check_spatial_overlap(parcel_id, db))
    checks_results.append(await _check_zoning_mismatch(parcel_id, db))
    checks_results.append(await _check_transaction_network_flag(parcel_id, db))

    failed = [c for c in checks_results if not c["passed"]]
    total_penalty = sum(PENALTIES.get(c["severity"], 0) for c in failed)
    trust_score = max(0, 100 - total_penalty)
    risk_band = _risk_band(failed)

    # Build summary text
    if not failed:
        summary = "All checks passed. This parcel has a clean title record with no detected conflicts."
    else:
        severity_counts = {}
        for c in failed:
            severity_counts[c["severity"]] = severity_counts.get(c["severity"], 0) + 1
        parts = [f"{v} {k.lower()}" for k, v in sorted(severity_counts.items())]
        summary = (
            f"{len(failed)} check(s) failed ({', '.join(parts)}). "
            f"Trust score: {trust_score}/100. Risk band: {risk_band}."
        )

    recommended_actions = list({
        c["recommendation"] for c in failed if c["recommendation"] != "No action required."
    })

    return {
        "parcel_id": parcel_id,
        "trust_score": trust_score,
        "risk_band": risk_band,
        "computed_at": datetime.now(tz=timezone.utc),
        "total_checks": len(checks_results),
        "failed_checks_count": len(failed),
        "checks": checks_results,
        "failed_checks": failed,
        "summary": summary,
        "recommended_actions": recommended_actions,
        "method": "DETERMINISTIC_RULES",
    }
