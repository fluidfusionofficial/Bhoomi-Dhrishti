import asyncio
import uuid
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_db
from app.models.revenue import Mutation
from app.schemas.revenue import (
    ApproveMutationRequest,
    CreateMutationRequest,
    MutationResponse,
    RejectMutationRequest,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Audit helper
# ---------------------------------------------------------------------------

async def _emit_audit(client: httpx.AsyncClient, action: str, resource_type: str, resource_id: str):
    try:
        await client.post(
            f"{settings.audit_service_url}/api/v1/events",
            json={
                "service": settings.service_name,
                "action": action,
                "resource_type": resource_type,
                "resource_id": resource_id,
            },
            timeout=2.0,
        )
    except Exception:
        pass


def emit_audit(request: Request, action: str, resource_type: str, resource_id):
    asyncio.create_task(
        _emit_audit(request.app.state.http_client, action, resource_type, str(resource_id))
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/mutations", response_model=MutationResponse, status_code=201)
async def create_mutation(
    body: CreateMutationRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Create a new mutation record with status PENDING."""
    mutation = Mutation(
        id=uuid.uuid4(),
        parcel_id=body.parcel_id,
        mutation_type=body.mutation_type,
        from_party_id=body.from_party_id,
        to_party_id=body.to_party_id,
        status="PENDING",
        submitted_at=datetime.now(timezone.utc),
        notes=body.notes,
    )
    db.add(mutation)
    await db.commit()
    await db.refresh(mutation)

    emit_audit(request, "CREATE_MUTATION", "mutations", mutation.id)

    return mutation


@router.get("/mutations/{mutation_id}", response_model=MutationResponse)
async def get_mutation(
    mutation_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve a single mutation by its UUID."""
    stmt = select(Mutation).where(Mutation.id == mutation_id)
    result = await db.execute(stmt)
    mutation = result.scalar_one_or_none()

    if mutation is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Mutation {mutation_id} not found",
                    "detail": {"mutation_id": str(mutation_id)},
                }
            },
        )

    emit_audit(request, "READ_MUTATION", "mutations", mutation_id)

    return mutation


@router.put("/mutations/{mutation_id}/approve", response_model=MutationResponse)
async def approve_mutation(
    mutation_id: uuid.UUID,
    body: ApproveMutationRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Approve a pending mutation."""
    stmt = select(Mutation).where(Mutation.id == mutation_id)
    result = await db.execute(stmt)
    mutation = result.scalar_one_or_none()

    if mutation is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Mutation {mutation_id} not found",
                    "detail": {"mutation_id": str(mutation_id)},
                }
            },
        )

    if mutation.status != "PENDING":
        raise HTTPException(
            status_code=422,
            detail={
                "error": {
                    "code": "INVALID_STATE",
                    "message": f"Mutation is already in state '{mutation.status}' and cannot be approved",
                    "detail": {"current_status": mutation.status},
                }
            },
        )

    mutation.status = "APPROVED"
    mutation.officer_id = body.officer_id
    mutation.approved_at = datetime.now(timezone.utc)
    if body.notes:
        mutation.notes = body.notes

    await db.commit()
    await db.refresh(mutation)

    emit_audit(request, "APPROVE_MUTATION", "mutations", mutation_id)

    return mutation


@router.put("/mutations/{mutation_id}/reject", response_model=MutationResponse)
async def reject_mutation(
    mutation_id: uuid.UUID,
    body: RejectMutationRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Reject a pending mutation."""
    stmt = select(Mutation).where(Mutation.id == mutation_id)
    result = await db.execute(stmt)
    mutation = result.scalar_one_or_none()

    if mutation is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Mutation {mutation_id} not found",
                    "detail": {"mutation_id": str(mutation_id)},
                }
            },
        )

    if mutation.status != "PENDING":
        raise HTTPException(
            status_code=422,
            detail={
                "error": {
                    "code": "INVALID_STATE",
                    "message": f"Mutation is already in state '{mutation.status}' and cannot be rejected",
                    "detail": {"current_status": mutation.status},
                }
            },
        )

    mutation.status = "REJECTED"
    mutation.officer_id = body.officer_id
    mutation.rejection_reason = body.rejection_reason
    mutation.approved_at = datetime.now(timezone.utc)  # timestamp of the decision

    await db.commit()
    await db.refresh(mutation)

    emit_audit(request, "REJECT_MUTATION", "mutations", mutation_id)

    return mutation
