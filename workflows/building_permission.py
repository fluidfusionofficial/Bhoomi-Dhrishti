#!/usr/bin/env python3
"""
Workflow 2: Building Permission with Zoning Checks

Demonstrates automated compliance screening:
1. Citizen submits building permit application
2. System auto-screens (zoning, FSI/FAR, setbacks, tax dues, encumbrances)
3. Generate screening report
4. If compliant → route to planning officer
5. Officer approves
6. Notification to applicant
"""

import asyncio
import httpx
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field


class ScreeningStatus(str, Enum):
    COMPLIANT = "COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


class ScreeningResult(BaseModel):
    check_name: str
    status: ScreeningStatus
    message: str
    details: Optional[Dict[str, Any]] = None
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BuildingPermitRequest(BaseModel):
    ulpin: str
    applicant_aadhaar: str
    building_type: str  # residential, commercial, industrial
    proposed_area_sqm: float
    proposed_floors: int
    proposed_height_m: float
    setback_front_m: float
    setback_rear_m: float
    setback_sides_m: float
    plot_area_sqm: float
    architect_registration: str
    structural_engineer_registration: str


class BuildingPermissionWorkflow:
    """End-to-end building permission workflow with automated screening"""

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

    async def check_zoning_compliance(self, ulpin: str, building_type: str) -> ScreeningResult:
        """Check zoning compliance via Planning service"""
        try:
            response = await self.client.get(
                f"{self.base_url}/planning-zoning/parcels/{ulpin}/zone"
            )

            if response.status_code == 200:
                data = response.json()
                zone_type = data.get("zone_type")
                permitted_uses = data.get("permitted_uses", [])

                # Map building types to use categories
                use_mapping = {
                    "residential": ["residential", "mixed"],
                    "commercial": ["commercial", "mixed"],
                    "industrial": ["industrial"]
                }

                allowed_uses = use_mapping.get(building_type, [])
                is_permitted = any(use in permitted_uses for use in allowed_uses)

                if is_permitted:
                    return ScreeningResult(
                        check_name="zoning_compliance",
                        status=ScreeningStatus.COMPLIANT,
                        message=f"Building type '{building_type}' permitted in {zone_type} zone",
                        details={
                            "zone_type": zone_type,
                            "permitted_uses": permitted_uses,
                            "building_type": building_type
                        }
                    )
                else:
                    return ScreeningResult(
                        check_name="zoning_compliance",
                        status=ScreeningStatus.NON_COMPLIANT,
                        message=f"Building type '{building_type}' not permitted in {zone_type} zone",
                        details={
                            "zone_type": zone_type,
                            "permitted_uses": permitted_uses,
                            "building_type": building_type
                        }
                    )
            else:
                return ScreeningResult(
                    check_name="zoning_compliance",
                    status=ScreeningStatus.REVIEW_REQUIRED,
                    message="Unable to verify zoning compliance",
                    details={"error": "Service unavailable"}
                )
        except Exception as e:
            return ScreeningResult(
                check_name="zoning_compliance",
                status=ScreeningStatus.REVIEW_REQUIRED,
                message=f"Zoning check failed: {str(e)}",
                details={"error": str(e)}
            )

    async def check_fsi_far_limits(
        self,
        ulpin: str,
        proposed_area: float,
        plot_area: float,
        building_type: str
    ) -> ScreeningResult:
        """Check Floor Space Index (FSI) / Floor Area Ratio (FAR) limits"""
        try:
            response = await self.client.get(
                f"{self.base_url}/planning-zoning/parcels/{ulpin}/zone"
            )

            if response.status_code == 200:
                data = response.json()
                regulations = data.get("regulations", {})

                # Get FSI limit based on building type
                fsi_limits = {
                    "residential": regulations.get("fsi_residential", 2.0),
                    "commercial": regulations.get("fsi_commercial", 3.0),
                    "industrial": regulations.get("fsi_industrial", 1.5)
                }

                max_fsi = fsi_limits.get(building_type, 2.0)
                proposed_fsi = proposed_area / plot_area

                if proposed_fsi <= max_fsi:
                    return ScreeningResult(
                        check_name="fsi_far_limits",
                        status=ScreeningStatus.COMPLIANT,
                        message=f"FSI {proposed_fsi:.2f} within limit {max_fsi:.2f}",
                        details={
                            "proposed_fsi": proposed_fsi,
                            "max_fsi": max_fsi,
                            "utilization_pct": (proposed_fsi / max_fsi) * 100
                        }
                    )
                elif proposed_fsi <= max_fsi * 1.05:
                    # Within 5% tolerance - may qualify for premium FSI
                    return ScreeningResult(
                        check_name="fsi_far_limits",
                        status=ScreeningStatus.REVIEW_REQUIRED,
                        message=f"FSI {proposed_fsi:.2f} slightly exceeds limit {max_fsi:.2f} (premium FSI may apply)",
                        details={
                            "proposed_fsi": proposed_fsi,
                            "max_fsi": max_fsi,
                            "excess_pct": ((proposed_fsi - max_fsi) / max_fsi) * 100
                        }
                    )
                else:
                    return ScreeningResult(
                        check_name="fsi_far_limits",
                        status=ScreeningStatus.NON_COMPLIANT,
                        message=f"FSI {proposed_fsi:.2f} exceeds limit {max_fsi:.2f}",
                        details={
                            "proposed_fsi": proposed_fsi,
                            "max_fsi": max_fsi,
                            "excess_pct": ((proposed_fsi - max_fsi) / max_fsi) * 100
                        }
                    )
            else:
                return ScreeningResult(
                    check_name="fsi_far_limits",
                    status=ScreeningStatus.REVIEW_REQUIRED,
                    message="Unable to verify FSI limits",
                    details={"error": "Service unavailable"}
                )
        except Exception as e:
            return ScreeningResult(
                check_name="fsi_far_limits",
                status=ScreeningStatus.REVIEW_REQUIRED,
                message=f"FSI check failed: {str(e)}",
                details={"error": str(e)}
            )

    async def check_setback_requirements(
        self,
        ulpin: str,
        setback_front: float,
        setback_rear: float,
        setback_sides: float,
        building_height: float
    ) -> ScreeningResult:
        """Check setback requirements"""
        try:
            response = await self.client.get(
                f"{self.base_url}/planning-zoning/parcels/{ulpin}/zone"
            )

            if response.status_code == 200:
                data = response.json()
                regulations = data.get("regulations", {})

                # Setback requirements typically scale with building height
                # Base requirements for buildings up to 10m
                min_front = regulations.get("setback_front_min", 3.0)
                min_rear = regulations.get("setback_rear_min", 3.0)
                min_sides = regulations.get("setback_sides_min", 1.5)

                # Additional setback for height > 10m (1m per 3m of additional height)
                if building_height > 10.0:
                    additional = (building_height - 10.0) / 3.0
                    min_front += additional
                    min_rear += additional
                    min_sides += additional * 0.5

                violations = []

                if setback_front < min_front:
                    violations.append(f"Front setback {setback_front}m < required {min_front:.2f}m")

                if setback_rear < min_rear:
                    violations.append(f"Rear setback {setback_rear}m < required {min_rear:.2f}m")

                if setback_sides < min_sides:
                    violations.append(f"Side setback {setback_sides}m < required {min_sides:.2f}m")

                if not violations:
                    return ScreeningResult(
                        check_name="setback_requirements",
                        status=ScreeningStatus.COMPLIANT,
                        message="All setback requirements met",
                        details={
                            "provided": {
                                "front": setback_front,
                                "rear": setback_rear,
                                "sides": setback_sides
                            },
                            "required": {
                                "front": min_front,
                                "rear": min_rear,
                                "sides": min_sides
                            }
                        }
                    )
                else:
                    return ScreeningResult(
                        check_name="setback_requirements",
                        status=ScreeningStatus.NON_COMPLIANT,
                        message="; ".join(violations),
                        details={
                            "violations": violations,
                            "provided": {
                                "front": setback_front,
                                "rear": setback_rear,
                                "sides": setback_sides
                            },
                            "required": {
                                "front": min_front,
                                "rear": min_rear,
                                "sides": min_sides
                            }
                        }
                    )
            else:
                return ScreeningResult(
                    check_name="setback_requirements",
                    status=ScreeningStatus.REVIEW_REQUIRED,
                    message="Unable to verify setback requirements",
                    details={"error": "Service unavailable"}
                )
        except Exception as e:
            return ScreeningResult(
                check_name="setback_requirements",
                status=ScreeningStatus.REVIEW_REQUIRED,
                message=f"Setback check failed: {str(e)}",
                details={"error": str(e)}
            )

    async def check_property_tax_dues(self, ulpin: str) -> ScreeningResult:
        """Check for pending property tax dues"""
        try:
            response = await self.client.get(
                f"{self.base_url}/fiscal/property-tax/{ulpin}/dues"
            )

            if response.status_code == 200:
                data = response.json()
                pending_amount = data.get("pending_amount", 0.0)
                pending_years = data.get("pending_years", [])

                if pending_amount == 0:
                    return ScreeningResult(
                        check_name="property_tax_dues",
                        status=ScreeningStatus.COMPLIANT,
                        message="No pending property tax dues",
                        details={"pending_amount": 0.0}
                    )
                elif pending_amount < 10000.0 and len(pending_years) <= 1:
                    return ScreeningResult(
                        check_name="property_tax_dues",
                        status=ScreeningStatus.REVIEW_REQUIRED,
                        message=f"Minimal pending dues: ₹{pending_amount:.2f}",
                        details={
                            "pending_amount": pending_amount,
                            "pending_years": pending_years
                        }
                    )
                else:
                    return ScreeningResult(
                        check_name="property_tax_dues",
                        status=ScreeningStatus.NON_COMPLIANT,
                        message=f"Outstanding property tax: ₹{pending_amount:.2f} for {len(pending_years)} year(s)",
                        details={
                            "pending_amount": pending_amount,
                            "pending_years": pending_years
                        }
                    )
            else:
                return ScreeningResult(
                    check_name="property_tax_dues",
                    status=ScreeningStatus.REVIEW_REQUIRED,
                    message="Unable to verify property tax dues",
                    details={"error": "Service unavailable"}
                )
        except Exception as e:
            return ScreeningResult(
                check_name="property_tax_dues",
                status=ScreeningStatus.REVIEW_REQUIRED,
                message=f"Tax dues check failed: {str(e)}",
                details={"error": str(e)}
            )

    async def check_encumbrances(self, ulpin: str) -> ScreeningResult:
        """Check for encumbrances that may affect building permission"""
        try:
            response = await self.client.get(
                f"{self.base_url}/fiscal/encumbrances/{ulpin}"
            )

            if response.status_code == 200:
                data = response.json()
                encumbrances = data.get("encumbrances", [])
                blocking = [
                    e for e in encumbrances
                    if e.get("type") in ["mortgage", "lien"] and e.get("status") == "active"
                ]

                if not blocking:
                    return ScreeningResult(
                        check_name="encumbrances",
                        status=ScreeningStatus.COMPLIANT,
                        message="No blocking encumbrances found",
                        details={"count": 0}
                    )
                else:
                    return ScreeningResult(
                        check_name="encumbrances",
                        status=ScreeningStatus.REVIEW_REQUIRED,
                        message=f"{len(blocking)} encumbrances found - lender NOC may be required",
                        details={"count": len(blocking), "encumbrances": blocking}
                    )
            else:
                return ScreeningResult(
                    check_name="encumbrances",
                    status=ScreeningStatus.REVIEW_REQUIRED,
                    message="Unable to verify encumbrances",
                    details={"error": "Service unavailable"}
                )
        except Exception as e:
            return ScreeningResult(
                check_name="encumbrances",
                status=ScreeningStatus.REVIEW_REQUIRED,
                message=f"Encumbrance check failed: {str(e)}",
                details={"error": str(e)}
            )

    async def run_screening(self, request: BuildingPermitRequest) -> List[ScreeningResult]:
        """Run all screening checks in parallel"""
        checks = await asyncio.gather(
            self.check_zoning_compliance(request.ulpin, request.building_type),
            self.check_fsi_far_limits(
                request.ulpin,
                request.proposed_area_sqm,
                request.plot_area_sqm,
                request.building_type
            ),
            self.check_setback_requirements(
                request.ulpin,
                request.setback_front_m,
                request.setback_rear_m,
                request.setback_sides_m,
                request.proposed_height_m
            ),
            self.check_property_tax_dues(request.ulpin),
            self.check_encumbrances(request.ulpin)
        )
        return list(checks)

    async def route_to_officer(self, application_id: str, ulpin: str) -> Dict[str, Any]:
        """Route application to planning officer for approval"""
        try:
            response = await self.client.post(
                f"{self.base_url}/planning-zoning/applications/{application_id}/assign",
                json={
                    "ulpin": ulpin,
                    "assigned_to": "planning_officer",
                    "status": "under_review",
                    "assigned_at": datetime.now(timezone.utc).isoformat()
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"Officer routing failed: {str(e)}")

    async def send_notification(self, recipient: str, notification_type: str, details: Dict[str, Any]) -> None:
        """Send notification to applicant"""
        try:
            await self.client.post(
                f"{self.base_url}/notifications/send",
                json={
                    "recipient": recipient,
                    "notification_type": notification_type,
                    "details": details,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        except Exception as e:
            print(f"Notification failed: {str(e)}")

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
            print(f"Audit logging failed: {str(e)}")

    async def execute(self, request: BuildingPermitRequest) -> Dict[str, Any]:
        """
        Execute complete building permission workflow

        Returns:
            Dict with workflow status, screening results, and application details
        """
        application_id = f"BP-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{request.ulpin[:8]}"
        timeline = []

        try:
            # Step 1: Run automated screening
            await self.log_audit_event(application_id, "screening_started", {"ulpin": request.ulpin})
            timeline.append({
                "step": "Automated screening started",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

            screening_results = await self.run_screening(request)

            timeline.append({
                "step": "Screening completed",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "details": [
                    {"check": r.check_name, "status": r.status.value}
                    for r in screening_results
                ]
            })

            # Determine overall screening status
            has_non_compliant = any(r.status == ScreeningStatus.NON_COMPLIANT for r in screening_results)
            has_review_required = any(r.status == ScreeningStatus.REVIEW_REQUIRED for r in screening_results)

            if has_non_compliant:
                overall_status = "REJECTED"
                await self.log_audit_event(application_id, "screening_failed", {
                    "ulpin": request.ulpin,
                    "non_compliant_checks": [
                        r.check_name for r in screening_results
                        if r.status == ScreeningStatus.NON_COMPLIANT
                    ]
                })

                await self.send_notification(
                    request.applicant_aadhaar,
                    "building_permit_rejected",
                    {
                        "application_id": application_id,
                        "reason": "Non-compliant with regulations",
                        "screening_results": [r.dict() for r in screening_results]
                    }
                )

                return {
                    "application_id": application_id,
                    "status": overall_status,
                    "message": "Application rejected due to non-compliance",
                    "screening_results": [r.dict() for r in screening_results],
                    "timeline": timeline
                }

            # Step 2: Route to planning officer
            overall_status = "UNDER_REVIEW" if has_review_required else "APPROVED_AUTO"

            timeline.append({
                "step": "Routing to planning officer",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

            routing_result = await self.route_to_officer(application_id, request.ulpin)

            timeline.append({
                "step": "Assigned to planning officer",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "officer": routing_result.get("assigned_to")
            })

            # Step 3: Notify applicant
            await self.send_notification(
                request.applicant_aadhaar,
                "building_permit_screening_complete",
                {
                    "application_id": application_id,
                    "status": overall_status,
                    "screening_results": [r.dict() for r in screening_results]
                }
            )

            timeline.append({
                "step": "Applicant notified",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

            await self.log_audit_event(application_id, "workflow_completed", {
                "ulpin": request.ulpin,
                "status": overall_status
            })

            return {
                "application_id": application_id,
                "status": overall_status,
                "message": "Application screening completed and routed to officer" if has_review_required else "Application meets all automated compliance checks",
                "screening_results": [r.dict() for r in screening_results],
                "routing": routing_result,
                "timeline": timeline
            }

        except Exception as e:
            await self.log_audit_event(application_id, "workflow_failed", {
                "ulpin": request.ulpin,
                "error": str(e)
            })

            return {
                "application_id": application_id,
                "status": "ERROR",
                "message": f"Workflow failed: {str(e)}",
                "timeline": timeline
            }


# CLI entry point
async def main():
    """CLI for testing building permission workflow"""
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage: python building_permission.py <request.json>")
        print("\nExample request.json:")
        print(json.dumps({
            "ulpin": "09-01-015-123-456",
            "applicant_aadhaar": "123456789012",
            "building_type": "residential",
            "proposed_area_sqm": 400.0,
            "proposed_floors": 3,
            "proposed_height_m": 12.0,
            "setback_front_m": 4.5,
            "setback_rear_m": 3.5,
            "setback_sides_m": 2.0,
            "plot_area_sqm": 250.0,
            "architect_registration": "COA/TN/2024/12345",
            "structural_engineer_registration": "IEI/TN/2024/67890"
        }, indent=2))
        sys.exit(1)

    request_file = sys.argv[1]
    with open(request_file) as f:
        request_data = json.load(f)

    request = BuildingPermitRequest(**request_data)

    workflow = BuildingPermissionWorkflow()
    try:
        result = await workflow.execute(request)
        print(json.dumps(result, indent=2, default=str))
    finally:
        await workflow.close()


if __name__ == "__main__":
    asyncio.run(main())
