#!/usr/bin/env python3
"""
Workflow 1: Property Sale with Pre-registration Checks

Demonstrates cross-departmental integration:
1. Citizen submits sale deed for registration (SRO)
2. System runs pre-checks (encumbrances, disputes, ownership, area, zoning)
3. Generate pre-check report (PASS/WARN/FAIL)
4. If PASS → SRO officer registers deed
5. Trigger downstream notifications (mutation request, tax assessment)
6. Revenue officer approves mutation
7. Timeline visible to citizen
"""

import asyncio
import httpx
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field


class CheckStatus(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"


class PreCheckResult(BaseModel):
    check_name: str
    status: CheckStatus
    message: str
    details: Optional[Dict[str, Any]] = None
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PropertySaleRequest(BaseModel):
    ulpin: str
    seller_aadhaar: str
    buyer_aadhaar: str
    sale_price: float
    sale_area_sqm: float
    document_id: str
    sro_code: str


class PropertySaleWorkflow:
    """End-to-end property sale workflow with pre-registration checks"""

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        timeout: float = 30.0
    ):
        self.base_url = base_url
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

    async def check_encumbrances(self, ulpin: str) -> PreCheckResult:
        """Check for pending encumbrances via Fiscal service"""
        try:
            response = await self.client.get(
                f"{self.base_url}/fiscal/encumbrances/{ulpin}"
            )

            if response.status_code == 200:
                data = response.json()
                encumbrances = data.get("encumbrances", [])
                pending = [e for e in encumbrances if e.get("status") == "active"]

                if not pending:
                    return PreCheckResult(
                        check_name="encumbrances",
                        status=CheckStatus.PASS,
                        message="No pending encumbrances found",
                        details={"count": 0}
                    )
                else:
                    return PreCheckResult(
                        check_name="encumbrances",
                        status=CheckStatus.FAIL,
                        message=f"{len(pending)} active encumbrances found",
                        details={"count": len(pending), "encumbrances": pending}
                    )
            else:
                return PreCheckResult(
                    check_name="encumbrances",
                    status=CheckStatus.WARN,
                    message="Unable to verify encumbrances",
                    details={"error": "Service unavailable"}
                )
        except Exception as e:
            return PreCheckResult(
                check_name="encumbrances",
                status=CheckStatus.WARN,
                message=f"Encumbrance check failed: {str(e)}",
                details={"error": str(e)}
            )

    async def check_disputes(self, ulpin: str) -> PreCheckResult:
        """Check for pending court disputes (stub integration)"""
        try:
            # Mock court integration - in production would integrate with eCourts API
            response = await self.client.get(
                f"{self.base_url}/trust-engine/disputes/{ulpin}"
            )

            if response.status_code == 200:
                data = response.json()
                disputes = data.get("disputes", [])
                pending = [d for d in disputes if d.get("status") in ["pending", "under_hearing"]]

                if not pending:
                    return PreCheckResult(
                        check_name="disputes",
                        status=CheckStatus.PASS,
                        message="No pending disputes found",
                        details={"count": 0}
                    )
                elif len(pending) == 1:
                    return PreCheckResult(
                        check_name="disputes",
                        status=CheckStatus.WARN,
                        message="1 pending dispute found - review required",
                        details={"count": 1, "disputes": pending}
                    )
                else:
                    return PreCheckResult(
                        check_name="disputes",
                        status=CheckStatus.FAIL,
                        message=f"{len(pending)} pending disputes found",
                        details={"count": len(pending), "disputes": pending}
                    )
            else:
                return PreCheckResult(
                    check_name="disputes",
                    status=CheckStatus.WARN,
                    message="Unable to verify disputes",
                    details={"error": "Service unavailable"}
                )
        except Exception as e:
            return PreCheckResult(
                check_name="disputes",
                status=CheckStatus.WARN,
                message=f"Dispute check failed: {str(e)}",
                details={"error": str(e)}
            )

    async def verify_ownership(self, ulpin: str, seller_aadhaar: str) -> PreCheckResult:
        """Verify ownership via Revenue RoR"""
        try:
            response = await self.client.get(
                f"{self.base_url}/revenue-records/parcels/{ulpin}/ownership"
            )

            if response.status_code == 200:
                data = response.json()
                owners = data.get("owners", [])

                # Check if seller is listed as owner
                is_owner = any(
                    owner.get("aadhaar_hash") == self._hash_aadhaar(seller_aadhaar)
                    for owner in owners
                )

                if is_owner:
                    return PreCheckResult(
                        check_name="ownership",
                        status=CheckStatus.PASS,
                        message="Seller ownership verified",
                        details={"verified": True, "owner_count": len(owners)}
                    )
                else:
                    return PreCheckResult(
                        check_name="ownership",
                        status=CheckStatus.FAIL,
                        message="Seller not listed as owner in Revenue records",
                        details={"verified": False, "owner_count": len(owners)}
                    )
            else:
                return PreCheckResult(
                    check_name="ownership",
                    status=CheckStatus.WARN,
                    message="Unable to verify ownership",
                    details={"error": "Service unavailable"}
                )
        except Exception as e:
            return PreCheckResult(
                check_name="ownership",
                status=CheckStatus.FAIL,
                message=f"Ownership verification failed: {str(e)}",
                details={"error": str(e)}
            )

    async def check_area_consistency(self, ulpin: str, sale_area: float) -> PreCheckResult:
        """Check area consistency across Revenue and Registration sources"""
        try:
            # Fetch area from multiple sources
            revenue_resp = await self.client.get(
                f"{self.base_url}/revenue-records/parcels/{ulpin}"
            )
            registration_resp = await self.client.get(
                f"{self.base_url}/registration/parcels/{ulpin}/last-deed"
            )

            areas = {"sale_area": sale_area}

            if revenue_resp.status_code == 200:
                areas["revenue_area"] = revenue_resp.json().get("area_sqm")

            if registration_resp.status_code == 200:
                areas["registration_area"] = registration_resp.json().get("area_sqm")

            # Calculate variance
            if len(areas) >= 2:
                area_values = list(areas.values())
                max_area = max(area_values)
                min_area = min(area_values)
                variance_pct = ((max_area - min_area) / min_area) * 100

                if variance_pct < 5.0:
                    return PreCheckResult(
                        check_name="area_consistency",
                        status=CheckStatus.PASS,
                        message=f"Area variance {variance_pct:.2f}% (acceptable)",
                        details={"variance_pct": variance_pct, "areas": areas}
                    )
                elif variance_pct < 15.0:
                    return PreCheckResult(
                        check_name="area_consistency",
                        status=CheckStatus.WARN,
                        message=f"Area variance {variance_pct:.2f}% (review recommended)",
                        details={"variance_pct": variance_pct, "areas": areas}
                    )
                else:
                    return PreCheckResult(
                        check_name="area_consistency",
                        status=CheckStatus.FAIL,
                        message=f"Area variance {variance_pct:.2f}% (exceeds threshold)",
                        details={"variance_pct": variance_pct, "areas": areas}
                    )
            else:
                return PreCheckResult(
                    check_name="area_consistency",
                    status=CheckStatus.WARN,
                    message="Insufficient data sources for area comparison",
                    details={"areas": areas}
                )
        except Exception as e:
            return PreCheckResult(
                check_name="area_consistency",
                status=CheckStatus.WARN,
                message=f"Area consistency check failed: {str(e)}",
                details={"error": str(e)}
            )

    async def check_zoning_restrictions(self, ulpin: str) -> PreCheckResult:
        """Check zoning restrictions via Planning service"""
        try:
            response = await self.client.get(
                f"{self.base_url}/planning-zoning/parcels/{ulpin}/zone"
            )

            if response.status_code == 200:
                data = response.json()
                zone_type = data.get("zone_type")
                restrictions = data.get("restrictions", {})

                # Check for sale restrictions
                sale_restricted = restrictions.get("sale_restricted", False)

                if not sale_restricted:
                    return PreCheckResult(
                        check_name="zoning_restrictions",
                        status=CheckStatus.PASS,
                        message=f"No sale restrictions (Zone: {zone_type})",
                        details={"zone_type": zone_type, "restrictions": restrictions}
                    )
                else:
                    restriction_reason = restrictions.get("restriction_reason", "Unknown")
                    return PreCheckResult(
                        check_name="zoning_restrictions",
                        status=CheckStatus.FAIL,
                        message=f"Sale restricted: {restriction_reason}",
                        details={"zone_type": zone_type, "restrictions": restrictions}
                    )
            else:
                return PreCheckResult(
                    check_name="zoning_restrictions",
                    status=CheckStatus.WARN,
                    message="Unable to verify zoning restrictions",
                    details={"error": "Service unavailable"}
                )
        except Exception as e:
            return PreCheckResult(
                check_name="zoning_restrictions",
                status=CheckStatus.WARN,
                message=f"Zoning check failed: {str(e)}",
                details={"error": str(e)}
            )

    async def run_prechecks(self, request: PropertySaleRequest) -> List[PreCheckResult]:
        """Run all pre-registration checks in parallel"""
        checks = await asyncio.gather(
            self.check_encumbrances(request.ulpin),
            self.check_disputes(request.ulpin),
            self.verify_ownership(request.ulpin, request.seller_aadhaar),
            self.check_area_consistency(request.ulpin, request.sale_area_sqm),
            self.check_zoning_restrictions(request.ulpin)
        )
        return list(checks)

    async def register_deed(self, request: PropertySaleRequest) -> Dict[str, Any]:
        """Register sale deed with SRO"""
        try:
            response = await self.client.post(
                f"{self.base_url}/registration/deeds",
                json={
                    "ulpin": request.ulpin,
                    "seller_aadhaar": request.seller_aadhaar,
                    "buyer_aadhaar": request.buyer_aadhaar,
                    "sale_price": request.sale_price,
                    "area_sqm": request.sale_area_sqm,
                    "document_id": request.document_id,
                    "sro_code": request.sro_code,
                    "transaction_type": "sale",
                    "registered_at": datetime.now(timezone.utc).isoformat()
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"Deed registration failed: {str(e)}")

    async def trigger_mutation_request(self, ulpin: str, deed_id: str, new_owner: str) -> Dict[str, Any]:
        """Trigger pre-filled mutation request to Revenue"""
        try:
            response = await self.client.post(
                f"{self.base_url}/revenue-records/mutations",
                json={
                    "ulpin": ulpin,
                    "deed_id": deed_id,
                    "new_owner_aadhaar": new_owner,
                    "mutation_type": "sale",
                    "status": "pending_approval",
                    "requested_at": datetime.now(timezone.utc).isoformat()
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"Mutation request failed: {str(e)}")

    async def notify_tax_assessment(self, ulpin: str, deed_id: str, sale_price: float) -> Dict[str, Any]:
        """Notify ULB for tax assessment update"""
        try:
            response = await self.client.post(
                f"{self.base_url}/fiscal/tax-assessments/update",
                json={
                    "ulpin": ulpin,
                    "deed_id": deed_id,
                    "sale_price": sale_price,
                    "trigger": "property_sale",
                    "notified_at": datetime.now(timezone.utc).isoformat()
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            # Non-critical - log but don't fail workflow
            return {"status": "failed", "error": str(e)}

    async def log_audit_event(self, workflow_id: str, event_type: str, details: Dict[str, Any]) -> None:
        """Log audit event"""
        try:
            await self.client.post(
                f"{self.base_url}/audit/events",
                json={
                    "workflow_id": workflow_id,
                    "event_type": event_type,
                    "details": details,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        except Exception as e:
            # Non-critical - log locally
            print(f"Audit logging failed: {str(e)}")

    async def execute(self, request: PropertySaleRequest) -> Dict[str, Any]:
        """
        Execute complete property sale workflow

        Returns:
            Dict with workflow status, checks results, registration details, and timeline
        """
        workflow_id = f"PS-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{request.ulpin[:8]}"
        timeline = []

        try:
            # Step 1: Run pre-checks
            await self.log_audit_event(workflow_id, "prechecks_started", {"ulpin": request.ulpin})
            timeline.append({
                "step": "Pre-checks started",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

            prechecks = await self.run_prechecks(request)

            timeline.append({
                "step": "Pre-checks completed",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "details": [
                    {"check": c.check_name, "status": c.status.value}
                    for c in prechecks
                ]
            })

            # Determine overall status
            has_fail = any(c.status == CheckStatus.FAIL for c in prechecks)
            has_warn = any(c.status == CheckStatus.WARN for c in prechecks)

            if has_fail:
                overall_status = "REJECTED"
                await self.log_audit_event(workflow_id, "prechecks_failed", {
                    "ulpin": request.ulpin,
                    "failed_checks": [c.check_name for c in prechecks if c.status == CheckStatus.FAIL]
                })

                return {
                    "workflow_id": workflow_id,
                    "status": overall_status,
                    "message": "Pre-checks failed - registration cannot proceed",
                    "prechecks": [c.dict() for c in prechecks],
                    "timeline": timeline
                }

            overall_status = "APPROVED_WITH_WARNINGS" if has_warn else "APPROVED"

            # Step 2: Register deed (if approved)
            timeline.append({
                "step": "Deed registration started",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

            deed_result = await self.register_deed(request)
            deed_id = deed_result.get("deed_id")

            timeline.append({
                "step": "Deed registered",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "deed_id": deed_id
            })

            await self.log_audit_event(workflow_id, "deed_registered", {
                "ulpin": request.ulpin,
                "deed_id": deed_id
            })

            # Step 3: Trigger downstream notifications
            mutation_result = await self.trigger_mutation_request(
                request.ulpin, deed_id, request.buyer_aadhaar
            )

            timeline.append({
                "step": "Mutation request triggered",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "mutation_id": mutation_result.get("mutation_id")
            })

            tax_result = await self.notify_tax_assessment(
                request.ulpin, deed_id, request.sale_price
            )

            if tax_result.get("status") != "failed":
                timeline.append({
                    "step": "Tax assessment notified",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })

            await self.log_audit_event(workflow_id, "workflow_completed", {
                "ulpin": request.ulpin,
                "deed_id": deed_id,
                "status": overall_status
            })

            return {
                "workflow_id": workflow_id,
                "status": overall_status,
                "message": "Property sale registration completed successfully",
                "prechecks": [c.dict() for c in prechecks],
                "registration": {
                    "deed_id": deed_id,
                    "sro_code": request.sro_code
                },
                "downstream": {
                    "mutation_request": mutation_result,
                    "tax_assessment": tax_result
                },
                "timeline": timeline
            }

        except Exception as e:
            await self.log_audit_event(workflow_id, "workflow_failed", {
                "ulpin": request.ulpin,
                "error": str(e)
            })

            return {
                "workflow_id": workflow_id,
                "status": "ERROR",
                "message": f"Workflow failed: {str(e)}",
                "timeline": timeline
            }

    def _hash_aadhaar(self, aadhaar: str) -> str:
        """Hash Aadhaar for privacy (SHA-256)"""
        import hashlib
        return hashlib.sha256(aadhaar.encode()).hexdigest()


# CLI entry point
async def main():
    """CLI for testing property sale workflow"""
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage: python property_sale.py <request.json>")
        print("\nExample request.json:")
        print(json.dumps({
            "ulpin": "09-01-015-123-456",
            "seller_aadhaar": "123456789012",
            "buyer_aadhaar": "987654321098",
            "sale_price": 5000000.0,
            "sale_area_sqm": 250.5,
            "document_id": "DOC-2026-001",
            "sro_code": "TN-TVL-01"
        }, indent=2))
        sys.exit(1)

    request_file = sys.argv[1]
    with open(request_file) as f:
        request_data = json.load(f)

    request = PropertySaleRequest(**request_data)

    workflow = PropertySaleWorkflow()
    try:
        result = await workflow.execute(request)
        print(json.dumps(result, indent=2, default=str))
    finally:
        await workflow.close()


if __name__ == "__main__":
    asyncio.run(main())
