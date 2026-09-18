#!/usr/bin/env python3
"""
Workflow 3: Unauthorized Land-Use Conversion Detection

Demonstrates proactive enforcement:
1. Satellite change detection runs (weekly cron)
2. Detects agricultural → built conversion (>500 sq_m)
3. Cross-references with building permissions
4. If no permit found → flags as unauthorized
5. Auto-generates enforcement case
6. Assigns to field officer
7. Officer investigates, updates status
"""

import asyncio
import httpx
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field


class ConversionType(str, Enum):
    AGRICULTURAL_TO_BUILT = "agricultural_to_built"
    FOREST_TO_AGRICULTURAL = "forest_to_agricultural"
    WATER_BODY_TO_BUILT = "water_body_to_built"
    OPEN_LAND_TO_BUILT = "open_land_to_built"


class EnforcementStatus(str, Enum):
    FLAGGED = "FLAGGED"
    UNDER_INVESTIGATION = "UNDER_INVESTIGATION"
    CONFIRMED_UNAUTHORIZED = "CONFIRMED_UNAUTHORIZED"
    AUTHORIZED = "AUTHORIZED"
    CLOSED = "CLOSED"


class ChangeDetection(BaseModel):
    ulpin: str
    conversion_type: ConversionType
    change_area_sqm: float
    detected_date: datetime
    confidence_score: float
    previous_landuse: str
    current_landuse: str
    satellite_source: str
    geometry_wkt: Optional[str] = None


class EnforcementCase(BaseModel):
    case_id: str
    ulpin: str
    detection: ChangeDetection
    permit_status: str  # found, not_found, expired
    status: EnforcementStatus
    assigned_officer: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UnauthorizedConversionWorkflow:
    """Automated land-use conversion detection and enforcement workflow"""

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        timeout: float = 30.0,
        min_change_area_sqm: float = 500.0,
        min_confidence: float = 0.7
    ):
        self.base_url = base_url
        self.timeout = timeout
        self.min_change_area_sqm = min_change_area_sqm
        self.min_confidence = min_confidence
        self.client = httpx.AsyncClient(timeout=timeout)

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

    async def run_change_detection(
        self,
        region_code: str,
        lookback_days: int = 90
    ) -> List[ChangeDetection]:
        """
        Run satellite-based change detection for a region

        Args:
            region_code: State/district code (e.g., "TN-TVL")
            lookback_days: Number of days to look back for changes

        Returns:
            List of detected land-use changes
        """
        try:
            since_date = (datetime.now(timezone.utc) - timedelta(days=lookback_days)).isoformat()

            response = await self.client.post(
                f"{self.base_url}/satellite/change-detection",
                json={
                    "region_code": region_code,
                    "since_date": since_date,
                    "min_change_area_sqm": self.min_change_area_sqm,
                    "min_confidence": self.min_confidence,
                    "detection_types": [
                        "agricultural_to_built",
                        "forest_to_agricultural",
                        "water_body_to_built"
                    ]
                }
            )
            response.raise_for_status()

            data = response.json()
            detections = []

            for item in data.get("detections", []):
                detections.append(ChangeDetection(
                    ulpin=item["ulpin"],
                    conversion_type=ConversionType(item["conversion_type"]),
                    change_area_sqm=item["change_area_sqm"],
                    detected_date=datetime.fromisoformat(item["detected_date"]),
                    confidence_score=item["confidence_score"],
                    previous_landuse=item["previous_landuse"],
                    current_landuse=item["current_landuse"],
                    satellite_source=item.get("satellite_source", "Sentinel-2"),
                    geometry_wkt=item.get("geometry_wkt")
                ))

            return detections

        except Exception as e:
            raise Exception(f"Change detection failed: {str(e)}")

    async def check_building_permission(self, ulpin: str, detection_date: datetime) -> Dict[str, Any]:
        """
        Check if valid building permission exists for the parcel

        Args:
            ulpin: Parcel ULPIN
            detection_date: Date when change was detected

        Returns:
            Dict with permit status and details
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/planning-zoning/permissions/{ulpin}"
            )

            if response.status_code == 404:
                return {
                    "permit_status": "not_found",
                    "message": "No building permission found",
                    "details": None
                }

            if response.status_code == 200:
                data = response.json()
                permissions = data.get("permissions", [])

                if not permissions:
                    return {
                        "permit_status": "not_found",
                        "message": "No building permission found",
                        "details": None
                    }

                # Find most recent permission
                valid_permissions = []
                for perm in permissions:
                    approval_date = datetime.fromisoformat(perm["approval_date"])
                    expiry_date = datetime.fromisoformat(perm["expiry_date"])

                    # Check if permission was valid when construction detected
                    if approval_date <= detection_date <= expiry_date:
                        valid_permissions.append(perm)

                if valid_permissions:
                    # Sort by approval date, get most recent
                    latest_perm = sorted(
                        valid_permissions,
                        key=lambda x: x["approval_date"],
                        reverse=True
                    )[0]

                    return {
                        "permit_status": "found",
                        "message": f"Valid building permission found: {latest_perm['permit_id']}",
                        "details": latest_perm
                    }
                else:
                    # Check if there are expired permissions
                    expired = [
                        p for p in permissions
                        if datetime.fromisoformat(p["expiry_date"]) < detection_date
                    ]

                    if expired:
                        return {
                            "permit_status": "expired",
                            "message": "Building permission expired before construction detected",
                            "details": expired[0]
                        }
                    else:
                        return {
                            "permit_status": "not_found",
                            "message": "No valid building permission for detection period",
                            "details": None
                        }
            else:
                return {
                    "permit_status": "unknown",
                    "message": "Unable to verify building permissions",
                    "details": {"error": "Service unavailable"}
                }

        except Exception as e:
            return {
                "permit_status": "unknown",
                "message": f"Permission check failed: {str(e)}",
                "details": {"error": str(e)}
            }

    async def check_land_conversion_permission(self, ulpin: str) -> Dict[str, Any]:
        """Check if land-use conversion permission was granted"""
        try:
            response = await self.client.get(
                f"{self.base_url}/revenue-records/parcels/{ulpin}/conversions"
            )

            if response.status_code == 404:
                return {
                    "conversion_permission": False,
                    "message": "No land-use conversion permission found"
                }

            if response.status_code == 200:
                data = response.json()
                conversions = data.get("conversions", [])

                approved = [
                    c for c in conversions
                    if c.get("status") == "approved"
                ]

                if approved:
                    latest = approved[-1]
                    return {
                        "conversion_permission": True,
                        "message": f"Land conversion approved: {latest['approval_id']}",
                        "details": latest
                    }
                else:
                    return {
                        "conversion_permission": False,
                        "message": "No approved land-use conversion found"
                    }

        except Exception as e:
            return {
                "conversion_permission": False,
                "message": f"Conversion check failed: {str(e)}",
                "error": str(e)
            }

    async def create_enforcement_case(self, detection: ChangeDetection, permit_status: str) -> EnforcementCase:
        """Create enforcement case for unauthorized conversion"""
        try:
            case_id = f"EC-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{detection.ulpin[:8]}"

            response = await self.client.post(
                f"{self.base_url}/trust-engine/enforcement-cases",
                json={
                    "case_id": case_id,
                    "ulpin": detection.ulpin,
                    "case_type": "unauthorized_construction",
                    "detection_details": {
                        "conversion_type": detection.conversion_type.value,
                        "change_area_sqm": detection.change_area_sqm,
                        "detected_date": detection.detected_date.isoformat(),
                        "confidence_score": detection.confidence_score,
                        "previous_landuse": detection.previous_landuse,
                        "current_landuse": detection.current_landuse
                    },
                    "permit_status": permit_status,
                    "status": EnforcementStatus.FLAGGED.value,
                    "priority": self._calculate_priority(detection),
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
            )
            response.raise_for_status()

            case_data = response.json()

            return EnforcementCase(
                case_id=case_id,
                ulpin=detection.ulpin,
                detection=detection,
                permit_status=permit_status,
                status=EnforcementStatus.FLAGGED
            )

        except Exception as e:
            raise Exception(f"Failed to create enforcement case: {str(e)}")

    async def assign_to_field_officer(self, case_id: str, ulpin: str) -> Dict[str, Any]:
        """Assign enforcement case to field officer based on jurisdiction"""
        try:
            # Get jurisdiction from ULPIN (first 6 digits = state-district-tehsil)
            jurisdiction = "-".join(ulpin.split("-")[:3])

            response = await self.client.post(
                f"{self.base_url}/trust-engine/enforcement-cases/{case_id}/assign",
                json={
                    "jurisdiction": jurisdiction,
                    "role": "field_officer",
                    "status": EnforcementStatus.UNDER_INVESTIGATION.value,
                    "assigned_at": datetime.now(timezone.utc).isoformat()
                }
            )
            response.raise_for_status()

            return response.json()

        except Exception as e:
            raise Exception(f"Officer assignment failed: {str(e)}")

    async def notify_stakeholders(
        self,
        case_id: str,
        ulpin: str,
        detection: ChangeDetection,
        officer_id: Optional[str] = None
    ) -> None:
        """Notify field officer and property owner"""
        try:
            # Notify field officer
            if officer_id:
                await self.client.post(
                    f"{self.base_url}/notifications/send",
                    json={
                        "recipient": officer_id,
                        "notification_type": "enforcement_case_assigned",
                        "details": {
                            "case_id": case_id,
                            "ulpin": ulpin,
                            "conversion_type": detection.conversion_type.value,
                            "change_area_sqm": detection.change_area_sqm
                        },
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                )

            # Notify property owner (get owner from Revenue records)
            owner_resp = await self.client.get(
                f"{self.base_url}/revenue-records/parcels/{ulpin}/ownership"
            )

            if owner_resp.status_code == 200:
                owners = owner_resp.json().get("owners", [])
                for owner in owners:
                    if owner.get("contact"):
                        await self.client.post(
                            f"{self.base_url}/notifications/send",
                            json={
                                "recipient": owner["contact"],
                                "notification_type": "enforcement_notice",
                                "details": {
                                    "case_id": case_id,
                                    "ulpin": ulpin,
                                    "violation": "Unauthorized land-use conversion detected",
                                    "action_required": "Contact field officer for verification"
                                },
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

    def _calculate_priority(self, detection: ChangeDetection) -> str:
        """
        Calculate case priority based on detection characteristics

        Returns:
            Priority level: "high", "medium", "low"
        """
        # High priority cases
        if detection.conversion_type == ConversionType.WATER_BODY_TO_BUILT:
            return "high"

        if detection.conversion_type == ConversionType.FOREST_TO_AGRICULTURAL:
            return "high"

        if detection.change_area_sqm > 5000.0:
            return "high"

        # Medium priority
        if detection.change_area_sqm > 2000.0:
            return "medium"

        if detection.confidence_score < 0.85:
            return "medium"

        # Low priority
        return "low"

    async def process_detection(self, detection: ChangeDetection) -> Dict[str, Any]:
        """
        Process a single change detection

        Returns:
            Dict with processing results and enforcement case details
        """
        case_timeline = []

        try:
            case_timeline.append({
                "step": "Change detection recorded",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "details": {
                    "ulpin": detection.ulpin,
                    "conversion_type": detection.conversion_type.value,
                    "change_area_sqm": detection.change_area_sqm,
                    "confidence": detection.confidence_score
                }
            })

            # Check for building permission
            permit_check = await self.check_building_permission(
                detection.ulpin,
                detection.detected_date
            )

            case_timeline.append({
                "step": "Building permission checked",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "permit_status": permit_check["permit_status"]
            })

            # Check for land conversion permission
            conversion_check = await self.check_land_conversion_permission(detection.ulpin)

            case_timeline.append({
                "step": "Land conversion permission checked",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "conversion_permission": conversion_check["conversion_permission"]
            })

            # Determine if unauthorized
            is_authorized = (
                permit_check["permit_status"] == "found" or
                conversion_check["conversion_permission"]
            )

            if is_authorized:
                # Change is authorized - no enforcement needed
                await self.log_audit_event(
                    f"CD-{detection.ulpin}",
                    "change_authorized",
                    {
                        "ulpin": detection.ulpin,
                        "permit_status": permit_check["permit_status"],
                        "conversion_permission": conversion_check["conversion_permission"]
                    }
                )

                return {
                    "ulpin": detection.ulpin,
                    "status": "AUTHORIZED",
                    "message": "Construction authorized by valid permits",
                    "permit_check": permit_check,
                    "conversion_check": conversion_check,
                    "timeline": case_timeline
                }

            # Create enforcement case
            enforcement_case = await self.create_enforcement_case(
                detection,
                permit_check["permit_status"]
            )

            case_timeline.append({
                "step": "Enforcement case created",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "case_id": enforcement_case.case_id
            })

            # Assign to field officer
            assignment = await self.assign_to_field_officer(
                enforcement_case.case_id,
                detection.ulpin
            )

            case_timeline.append({
                "step": "Assigned to field officer",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "officer": assignment.get("assigned_to")
            })

            # Notify stakeholders
            await self.notify_stakeholders(
                enforcement_case.case_id,
                detection.ulpin,
                detection,
                assignment.get("assigned_to")
            )

            case_timeline.append({
                "step": "Notifications sent",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

            await self.log_audit_event(
                enforcement_case.case_id,
                "enforcement_case_created",
                {
                    "ulpin": detection.ulpin,
                    "case_id": enforcement_case.case_id,
                    "priority": self._calculate_priority(detection)
                }
            )

            return {
                "ulpin": detection.ulpin,
                "status": "ENFORCEMENT_INITIATED",
                "message": "Unauthorized conversion detected - enforcement case created",
                "case": enforcement_case.dict(),
                "assignment": assignment,
                "timeline": case_timeline
            }

        except Exception as e:
            return {
                "ulpin": detection.ulpin,
                "status": "ERROR",
                "message": f"Processing failed: {str(e)}",
                "timeline": case_timeline
            }

    async def execute(self, region_code: str, lookback_days: int = 90) -> Dict[str, Any]:
        """
        Execute complete unauthorized conversion detection workflow

        Args:
            region_code: State/district code (e.g., "TN-TVL")
            lookback_days: Number of days to look back for changes

        Returns:
            Dict with workflow results, enforcement cases, and summary
        """
        workflow_id = f"UC-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{region_code}"

        try:
            await self.log_audit_event(
                workflow_id,
                "workflow_started",
                {"region_code": region_code, "lookback_days": lookback_days}
            )

            # Step 1: Run change detection
            detections = await self.run_change_detection(region_code, lookback_days)

            await self.log_audit_event(
                workflow_id,
                "change_detection_completed",
                {"region_code": region_code, "detections_count": len(detections)}
            )

            if not detections:
                return {
                    "workflow_id": workflow_id,
                    "region_code": region_code,
                    "status": "COMPLETED",
                    "message": "No significant land-use changes detected",
                    "summary": {
                        "detections_count": 0,
                        "enforcement_cases": 0,
                        "authorized_changes": 0
                    }
                }

            # Step 2: Process each detection
            results = []
            for detection in detections:
                result = await self.process_detection(detection)
                results.append(result)

            # Generate summary
            summary = {
                "detections_count": len(detections),
                "enforcement_cases": len([r for r in results if r["status"] == "ENFORCEMENT_INITIATED"]),
                "authorized_changes": len([r for r in results if r["status"] == "AUTHORIZED"]),
                "errors": len([r for r in results if r["status"] == "ERROR"]),
                "total_change_area_sqm": sum(d.change_area_sqm for d in detections),
                "by_conversion_type": {}
            }

            for detection in detections:
                conv_type = detection.conversion_type.value
                summary["by_conversion_type"][conv_type] = \
                    summary["by_conversion_type"].get(conv_type, 0) + 1

            await self.log_audit_event(
                workflow_id,
                "workflow_completed",
                {"region_code": region_code, "summary": summary}
            )

            return {
                "workflow_id": workflow_id,
                "region_code": region_code,
                "status": "COMPLETED",
                "message": f"Processed {len(detections)} change detections",
                "summary": summary,
                "results": results
            }

        except Exception as e:
            await self.log_audit_event(
                workflow_id,
                "workflow_failed",
                {"region_code": region_code, "error": str(e)}
            )

            return {
                "workflow_id": workflow_id,
                "region_code": region_code,
                "status": "ERROR",
                "message": f"Workflow failed: {str(e)}"
            }


# CLI entry point
async def main():
    """CLI for testing unauthorized conversion workflow"""
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage: python unauthorized_conversion.py <region_code> [lookback_days]")
        print("\nExample:")
        print("  python unauthorized_conversion.py TN-TVL 90")
        sys.exit(1)

    region_code = sys.argv[1]
    lookback_days = int(sys.argv[2]) if len(sys.argv) > 2 else 90

    workflow = UnauthorizedConversionWorkflow()
    try:
        result = await workflow.execute(region_code, lookback_days)
        print(json.dumps(result, indent=2, default=str))
    finally:
        await workflow.close()


if __name__ == "__main__":
    asyncio.run(main())
