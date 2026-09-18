"""
Workflow Orchestrator Service - FastAPI endpoints for all workflows
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any
import sys
from pathlib import Path

# Add workflows directory to path
workflows_dir = Path(__file__).resolve().parents[3] / "workflows"
sys.path.insert(0, str(workflows_dir))

from property_sale import PropertySaleWorkflow, PropertySaleRequest
from building_permission import BuildingPermissionWorkflow, BuildingPermitRequest
from unauthorized_conversion import UnauthorizedConversionWorkflow

app = FastAPI(
    title="Bhoomi Dhrishti Workflow Orchestrator",
    description="End-to-end workflow execution service",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check
@app.get("/health")
async def health():
    return {"status": "healthy", "service": "workflows"}


# Workflow 1: Property Sale
@app.post("/workflows/property-sale")
async def execute_property_sale_workflow(request: PropertySaleRequest) -> Dict[str, Any]:
    """
    Execute property sale workflow with pre-registration checks

    Steps:
    1. Run pre-checks (encumbrances, disputes, ownership, area, zoning)
    2. Register deed if checks pass
    3. Trigger mutation request to Revenue
    4. Notify tax assessment to ULB
    5. Log audit trail
    """
    workflow = PropertySaleWorkflow()
    try:
        result = await workflow.execute(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await workflow.close()


# Workflow 2: Building Permission
@app.post("/workflows/building-permit")
async def execute_building_permit_workflow(request: BuildingPermitRequest) -> Dict[str, Any]:
    """
    Execute building permission workflow with automated screening

    Steps:
    1. Auto-screen (zoning, FSI, setbacks, tax dues, encumbrances)
    2. Route to planning officer if compliant
    3. Send notification to applicant
    """
    workflow = BuildingPermissionWorkflow()
    try:
        result = await workflow.execute(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await workflow.close()


# Workflow 3: Unauthorized Conversion Detection
class UnauthorizedConversionRequest(BaseModel):
    region_code: str
    lookback_days: int = 90


@app.post("/workflows/land-use-enforcement")
async def execute_unauthorized_conversion_workflow(
    request: UnauthorizedConversionRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Execute unauthorized land-use conversion detection workflow

    Steps:
    1. Run satellite change detection
    2. Cross-reference with building permissions
    3. Flag unauthorized conversions
    4. Create enforcement cases
    5. Assign to field officers
    6. Notify stakeholders

    Note: This can be a long-running operation for large regions.
    """
    workflow = UnauthorizedConversionWorkflow()
    try:
        result = await workflow.execute(request.region_code, request.lookback_days)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await workflow.close()


# Background cron job for scheduled enforcement detection
@app.post("/workflows/land-use-enforcement/schedule")
async def schedule_enforcement_detection(
    request: UnauthorizedConversionRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Schedule enforcement detection to run in background

    Use this for large-scale regional scans that may take time.
    """
    def run_detection():
        import asyncio
        workflow = UnauthorizedConversionWorkflow()
        try:
            result = asyncio.run(
                workflow.execute(request.region_code, request.lookback_days)
            )
            # Store result in database or send notification
            print(f"Enforcement detection completed: {result}")
        finally:
            asyncio.run(workflow.close())

    background_tasks.add_task(run_detection)

    return {
        "status": "scheduled",
        "message": f"Enforcement detection scheduled for region {request.region_code}",
        "region_code": request.region_code
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
