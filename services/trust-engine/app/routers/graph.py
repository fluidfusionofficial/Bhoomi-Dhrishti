"""
Graph network analysis API endpoints.

Provides access to transaction network patterns: circular chains, rapid flips, party risk scores.
"""

from __future__ import annotations

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from bhoomi_common.auth import Actor, get_current_actor
from bhoomi_common.db import get_db
from app.modules.graph_analysis import (
    CircularChain,
    RapidFlip,
    PartyRiskScore,
    GraphAnalysisReport,
    build_transaction_graph,
    detect_circular_chains,
    detect_rapid_flips,
    compute_party_risk_score,
    run_full_graph_analysis,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/graph", tags=["Graph Analysis"])

# ─────────────────────────────────────────────────────────────────────────────
# Response Models
# ─────────────────────────────────────────────────────────────────────────────


class NetworkNode(BaseModel):
    """Node in transaction network (for D3 visualization)."""
    id: str  # party_id
    name: str
    transaction_count: int
    risk_score: Optional[float] = None


class NetworkEdge(BaseModel):
    """Edge in transaction network."""
    source: str  # from party_id
    target: str  # to party_id
    weight: int  # transaction count
    transactions: List[dict]


class NetworkGraph(BaseModel):
    """Full network graph for visualization."""
    nodes: List[NetworkNode]
    edges: List[NetworkEdge]
    metadata: dict


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/circular-chains", response_model=List[CircularChain])
async def get_circular_chains(
    state_code: Optional[str] = Query(None, description="Filter by state"),
    min_length: int = Query(3, ge=3, le=10, description="Minimum chain length"),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    actor: Actor = Depends(get_current_actor),
):
    """
    Get detected circular transaction chains.

    Circular chains indicate potential circular trading or shell company networks.
    """
    logger.info(
        "get_circular_chains",
        actor=actor.subject,
        state_code=state_code,
        min_length=min_length,
    )

    # Apply actor filtering
    district_code = None
    if "revenue_officer" in actor.roles and actor.district_code:
        district_code = actor.district_code

    # Build graph
    G, metadata = await build_transaction_graph(
        db,
        state_code=state_code,
        district_code=district_code,
    )

    # Detect chains
    chains = await detect_circular_chains(G, min_length=min_length)

    # Limit results
    chains = chains[:limit]

    logger.info("get_circular_chains.complete", count=len(chains))
    return chains


@router.get("/rapid-flips", response_model=List[RapidFlip])
async def get_rapid_flips(
    state_code: Optional[str] = Query(None),
    days_threshold: int = Query(30, ge=7, le=365, description="Max days between transactions"),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    actor: Actor = Depends(get_current_actor),
):
    """
    Get parcels with rapid succession of transactions (potential flipping).

    Rapid flips may indicate speculative trading or value manipulation.
    """
    logger.info(
        "get_rapid_flips",
        actor=actor.subject,
        state_code=state_code,
        days_threshold=days_threshold,
    )

    # Apply actor filtering
    if "revenue_officer" in actor.roles and actor.state_code:
        state_code = actor.state_code

    # Detect rapid flips
    flips = await detect_rapid_flips(
        db,
        state_code=state_code,
        days_threshold=days_threshold,
    )

    # Limit results
    flips = flips[:limit]

    logger.info("get_rapid_flips.complete", count=len(flips))
    return flips


@router.get("/party/{party_id}/risk", response_model=PartyRiskScore)
async def get_party_risk(
    party_id: UUID,
    db: AsyncSession = Depends(get_db),
    actor: Actor = Depends(get_current_actor),
):
    """
    Get risk score for a specific party.

    Risk score is based on network topology: centrality, involvement in
    circular chains, and rapid flips.
    """
    logger.info("get_party_risk", party_id=str(party_id), actor=actor.subject)

    # Build graph (state-wide for party analysis)
    G, metadata = await build_transaction_graph(db)

    # Get circular chains and rapid flips for context
    chains = await detect_circular_chains(G)
    flips = await detect_rapid_flips(db)

    # Compute risk score
    risk_score = await compute_party_risk_score(G, party_id, chains, flips)

    if risk_score is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Party {party_id} not found in transaction network",
        )

    logger.info("get_party_risk.complete", party_id=str(party_id), risk_score=risk_score.risk_score)
    return risk_score


@router.get("/network", response_model=NetworkGraph)
async def get_network_graph(
    parcel_id: Optional[UUID] = Query(None, description="Center on parcel's transaction network"),
    party_id: Optional[UUID] = Query(None, description="Center on party's ego network"),
    hops: int = Query(2, ge=1, le=3, description="Number of hops from center node"),
    db: AsyncSession = Depends(get_db),
    actor: Actor = Depends(get_current_actor),
):
    """
    Get transaction network for D3 visualization.

    Returns ego network (N-hop neighborhood) centered on a parcel or party.
    """
    logger.info(
        "get_network_graph",
        actor=actor.subject,
        parcel_id=parcel_id,
        party_id=party_id,
        hops=hops,
    )

    if not parcel_id and not party_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide either parcel_id or party_id",
        )

    # Build full graph
    G, metadata = await build_transaction_graph(db)

    # If parcel_id, find related parties
    center_nodes = set()
    if parcel_id:
        from sqlalchemy import text
        query = text("""
            SELECT DISTINCT from_party_id, to_party_id
            FROM revenue.mutations
            WHERE parcel_id = :parcel_id
                AND from_party_id IS NOT NULL
                AND to_party_id IS NOT NULL
        """)
        result = await db.execute(query, {"parcel_id": str(parcel_id)})
        rows = result.fetchall()
        for row in rows:
            center_nodes.add(str(row.from_party_id))
            center_nodes.add(str(row.to_party_id))

    if party_id:
        center_nodes.add(str(party_id))

    if not center_nodes:
        return NetworkGraph(nodes=[], edges=[], metadata={"message": "No network found"})

    # Extract ego network (N-hop neighborhood)
    import networkx as nx
    ego_nodes = set()
    for center in center_nodes:
        if G.has_node(center):
            try:
                # Get N-hop neighbors
                neighbors = nx.single_source_shortest_path_length(G, center, cutoff=hops)
                ego_nodes.update(neighbors.keys())
            except Exception:
                ego_nodes.add(center)

    # Build subgraph
    subgraph = G.subgraph(ego_nodes).copy()

    # Convert to response format
    nodes = []
    for node_id in subgraph.nodes():
        node_data = subgraph.nodes[node_id]
        nodes.append(NetworkNode(
            id=node_id,
            name=node_data.get("party_name", "Unknown")[:50],
            transaction_count=node_data.get("transaction_count", 0),
        ))

    edges = []
    for from_party, to_party, edge_data in subgraph.edges(data=True):
        edges.append(NetworkEdge(
            source=from_party,
            target=to_party,
            weight=edge_data.get("weight", 1),
            transactions=edge_data.get("transactions", [])[:5],  # Limit to 5
        ))

    graph = NetworkGraph(
        nodes=nodes,
        edges=edges,
        metadata={
            "node_count": len(nodes),
            "edge_count": len(edges),
            "hops": hops,
            "center_parcel_id": str(parcel_id) if parcel_id else None,
            "center_party_id": str(party_id) if party_id else None,
        },
    )

    logger.info("get_network_graph.complete", nodes=len(nodes), edges=len(edges))
    return graph


@router.get("/analysis/full", response_model=GraphAnalysisReport)
async def get_full_analysis(
    state_code: Optional[str] = Query(None),
    district_code: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    actor: Actor = Depends(get_current_actor),
):
    """
    Run complete graph analysis (heavy operation).

    Returns circular chains, rapid flips, high-risk parties, and network statistics.
    Restricted to officers and admins.
    """
    if "citizen" in actor.roles and len(actor.roles) == 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Full graph analysis is restricted to officers",
        )

    logger.info(
        "get_full_analysis",
        actor=actor.subject,
        state_code=state_code,
        district_code=district_code,
    )

    # Apply actor filtering
    if "revenue_officer" in actor.roles and actor.district_code:
        district_code = actor.district_code

    # Run analysis
    report = await run_full_graph_analysis(
        db,
        state_code=state_code,
        district_code=district_code,
    )

    logger.info("get_full_analysis.complete", circular_chains=len(report.circular_chains))
    return report
