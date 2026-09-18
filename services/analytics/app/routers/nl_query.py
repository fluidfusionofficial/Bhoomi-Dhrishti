"""
Natural language query API endpoints.

Provides template-based natural language to SQL conversion for common spatial
and administrative queries.
"""

from __future__ import annotations

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from bhoomi_common.auth import Actor, get_current_actor
from bhoomi_common.db import get_db
from app.modules.nl_query import (
    NLQueryResult,
    QueryExample,
    execute_nl_query,
    get_example_queries,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/query", tags=["Natural Language Query"])

# ─────────────────────────────────────────────────────────────────────────────
# Request Models
# ─────────────────────────────────────────────────────────────────────────────


class NLQueryRequest(BaseModel):
    """Natural language query request."""
    text: str


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────


@router.post("/natural-language", response_model=NLQueryResult)
async def query_natural_language(
    request: NLQueryRequest,
    db: AsyncSession = Depends(get_db),
    actor: Actor = Depends(get_current_actor),
):
    """
    Execute a natural language query.

    Supports common query patterns:

    **Spatial:**
    - "Show me all agricultural parcels within 500 metres of forest"
    - "Find parcels with area mismatch greater than 20%"

    **Administrative:**
    - "How many parcels in Bangalore have open disputes?"
    - "List all encumbered parcels in 560001 village"

    **Ownership:**
    - "Show owner Ramesh Kumar all parcels"

    **Cross-registry:**
    - "Parcels with building permissions but no RoR update in last 3 years"

    **Intelligence:**
    - "Show parcels with high anomaly scores in Mysore"

    The system uses template matching (no LLM API required) to convert
    natural language to SQL. Results are filtered based on actor roles
    and district scope.

    See `/query/examples` for complete list of supported patterns.
    """
    logger.info(
        "query_natural_language",
        actor=actor.subject,
        query_text=request.text[:100],
    )

    if not request.text or len(request.text.strip()) < 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query text must be at least 5 characters",
        )

    # Extract actor context
    actor_roles = list(actor.roles)
    state_code = actor.state_code
    district_code = actor.district_code

    # Execute query
    try:
        result = await execute_nl_query(
            db,
            query_text=request.text,
            actor_roles=actor_roles,
            state_code=state_code,
            district_code=district_code,
        )

        logger.info(
            "query_natural_language.complete",
            actor=actor.subject,
            pattern=result.pattern_matched,
            result_count=result.result_count,
            execution_time_ms=result.execution_time_ms,
        )

        return result

    except Exception as e:
        logger.error("query_natural_language: error", error=str(e), query=request.text)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query execution failed: {str(e)}",
        )


@router.get("/examples", response_model=List[QueryExample])
async def get_query_examples():
    """
    Get list of example natural language queries.

    Returns pre-defined query patterns that the system can recognize.
    Use these as templates for your own queries.
    """
    logger.info("get_query_examples")
    return get_example_queries()


@router.get("/capabilities")
async def get_query_capabilities():
    """
    Get information about natural language query capabilities and limitations.

    Explains the template-based approach and supported patterns.
    """
    return {
        "approach": "Template-based pattern matching (no LLM API required)",
        "supported_patterns": [
            "Spatial proximity queries (within N metres of)",
            "Area mismatch detection (greater than N%)",
            "Owner name search (phonetic and fuzzy matching)",
            "Dispute and encumbrance queries",
            "Building permission cross-checks",
            "Anomaly score queries",
            "Land classification statistics",
        ],
        "access_control": "Queries are automatically filtered by actor role and jurisdiction",
        "tiered_access": {
            "citizen": "Public records only, limited query types",
            "revenue_officer": "District-scoped, full query access",
            "district_collector": "District-scoped, full query access",
            "system_admin": "State-wide access, all query types",
        },
        "limitations": [
            "Complex joins across more than 3 tables may not be supported",
            "Free-form questions without recognized patterns will fail",
            "Requires precise entity names (village codes, district names)",
            "No semantic understanding or inference",
        ],
        "performance": "Sub-second for most queries on indexed tables",
        "extensibility": "New patterns can be added via regex templates",
    }


@router.get("/help")
async def get_query_help():
    """
    Get help text for constructing natural language queries.

    Provides tips and best practices.
    """
    return {
        "title": "Natural Language Query Help",
        "overview": "Ask questions about parcels, owners, and land records in plain English.",
        "tips": [
            "Use specific entity names: 'Bangalore' not 'some city'",
            "Include units: 'within 500 metres' not 'nearby'",
            "Be explicit about thresholds: 'greater than 15%' not 'high mismatch'",
            "Use standard terminology: 'RoR' for Records of Rights, 'building permissions', etc.",
            "Check /query/examples for supported patterns",
        ],
        "common_keywords": {
            "spatial": ["within", "metres", "near", "around"],
            "administrative": ["village", "district", "state", "LGD code"],
            "quality": ["mismatch", "divergence", "conflict", "dispute"],
            "ownership": ["owner", "party", "name"],
            "intelligence": ["anomaly", "high risk", "suspicious", "circular"],
            "temporal": ["last N years", "in N days", "between"],
        },
        "examples_by_role": {
            "citizen": [
                "Show owner John Smith all parcels",
                "How many encumbered parcels in my village?",
            ],
            "revenue_officer": [
                "Find parcels with area mismatch greater than 15% in my district",
                "Show parcels with high anomaly scores",
                "Parcels with building permissions but no RoR update in last 2 years",
            ],
            "district_collector": [
                "How many agricultural parcels in Hassan",
                "Show all parcels within 100 metres of forest in my district",
                "List circular transaction chains",
            ],
        },
    }
