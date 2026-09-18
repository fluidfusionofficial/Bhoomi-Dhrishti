"""
Transaction network graph analysis using NetworkX.

Detects circular chains, rapid flips, abnormal co-occurrence patterns,
and computes party risk scores based on network topology.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
from uuid import UUID

import networkx as nx
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Models
# ─────────────────────────────────────────────────────────────────────────────


class CircularChain(BaseModel):
    """Detected circular transaction chain."""
    chain_id: str
    party_ids: List[UUID]
    parcel_ids: List[UUID]
    chain_length: int
    time_window_days: int
    description: str
    confidence_score: float


class RapidFlip(BaseModel):
    """Rapid succession of transactions on the same parcel."""
    parcel_id: UUID
    bdpr: str
    transaction_count: int
    time_window_days: int
    parties_involved: List[UUID]
    description: str
    confidence_score: float


class PartyRiskScore(BaseModel):
    """Risk score for a party based on graph topology."""
    party_id: UUID
    party_name: str
    risk_score: float  # 0-1, higher = more suspicious
    degree_centrality: float
    betweenness_centrality: float
    in_circular_chains: int
    rapid_flips_involved: int
    transaction_count: int
    reason_text: str


class GraphAnalysisReport(BaseModel):
    """Complete graph analysis report."""
    state_code: Optional[str]
    district_code: Optional[str]
    analysis_timestamp: datetime
    total_nodes: int  # Parties
    total_edges: int  # Transactions
    circular_chains: List[CircularChain]
    rapid_flips: List[RapidFlip]
    high_risk_parties: List[PartyRiskScore]
    network_density: float
    largest_component_size: int


# ─────────────────────────────────────────────────────────────────────────────
# Graph Construction
# ─────────────────────────────────────────────────────────────────────────────


async def build_transaction_graph(
    db: AsyncSession,
    state_code: Optional[str] = None,
    district_code: Optional[str] = None,
    lookback_days: int = 730,  # 2 years
) -> Tuple[nx.DiGraph, Dict]:
    """
    Build a directed transaction graph from revenue mutations and deeds.

    Nodes: parties (individuals/entities)
    Edges: transactions (directed from seller to buyer)

    Args:
        db: Database session
        state_code: Optional state filter
        district_code: Optional district filter
        lookback_days: How far back to include transactions

    Returns:
        (graph, metadata_dict)
    """
    logger.info(
        "build_transaction_graph",
        state_code=state_code,
        district_code=district_code,
        lookback_days=lookback_days,
    )

    filters = []
    if state_code:
        filters.append("p.state_code = :state_code")
    if district_code:
        filters.append("p.district_code = :district_code")

    where_clause = f"AND {' AND '.join(filters)}" if filters else ""

    # Query mutations (revenue records)
    mutation_query = text(f"""
        SELECT
            m.id AS transaction_id,
            m.parcel_id,
            p.bdpr,
            m.from_party_id,
            m.to_party_id,
            m.mutation_date,
            m.mutation_type,
            m.consideration_amount,
            p1.name_en AS from_party_name,
            p2.name_en AS to_party_name
        FROM revenue.mutations m
        INNER JOIN identity.parcels p ON m.parcel_id = p.id
        LEFT JOIN revenue.parties p1 ON m.from_party_id = p1.id
        LEFT JOIN revenue.parties p2 ON m.to_party_id = p2.id
        WHERE m.mutation_date >= CURRENT_DATE - INTERVAL ':lookback_days days'
            AND m.from_party_id IS NOT NULL
            AND m.to_party_id IS NOT NULL
            AND m.mutation_type IN ('SALE', 'GIFT', 'EXCHANGE')
            {where_clause}
        ORDER BY m.mutation_date DESC
        LIMIT 10000
    """)

    params = {"lookback_days": lookback_days}
    if state_code:
        params["state_code"] = state_code
    if district_code:
        params["district_code"] = district_code

    result = await db.execute(mutation_query, params)
    transactions = result.fetchall()

    # Build graph
    G = nx.DiGraph()
    parcel_map = {}  # party_id -> set of parcel_ids

    for txn in transactions:
        from_party = str(txn.from_party_id)
        to_party = str(txn.to_party_id)
        parcel_id = str(txn.parcel_id)

        # Add nodes (parties)
        if not G.has_node(from_party):
            G.add_node(
                from_party,
                party_name=txn.from_party_name or "Unknown",
                transaction_count=0,
            )
        if not G.has_node(to_party):
            G.add_node(
                to_party,
                party_name=txn.to_party_name or "Unknown",
                transaction_count=0,
            )

        # Add edge (transaction)
        if G.has_edge(from_party, to_party):
            # Multiple transactions between same parties
            G[from_party][to_party]["weight"] += 1
            G[from_party][to_party]["transactions"].append({
                "transaction_id": str(txn.transaction_id),
                "parcel_id": parcel_id,
                "bdpr": txn.bdpr,
                "date": txn.mutation_date.isoformat() if txn.mutation_date else None,
                "type": txn.mutation_type,
                "amount": float(txn.consideration_amount) if txn.consideration_amount else None,
            })
        else:
            G.add_edge(
                from_party,
                to_party,
                weight=1,
                transactions=[{
                    "transaction_id": str(txn.transaction_id),
                    "parcel_id": parcel_id,
                    "bdpr": txn.bdpr,
                    "date": txn.mutation_date.isoformat() if txn.mutation_date else None,
                    "type": txn.mutation_type,
                    "amount": float(txn.consideration_amount) if txn.consideration_amount else None,
                }],
            )

        # Update transaction counts
        G.nodes[from_party]["transaction_count"] += 1
        G.nodes[to_party]["transaction_count"] += 1

        # Track parcels per party
        if from_party not in parcel_map:
            parcel_map[from_party] = set()
        if to_party not in parcel_map:
            parcel_map[to_party] = set()
        parcel_map[from_party].add(parcel_id)
        parcel_map[to_party].add(parcel_id)

    metadata = {
        "parcel_map": parcel_map,
        "transaction_count": len(transactions),
    }

    logger.info(
        "build_transaction_graph.complete",
        nodes=G.number_of_nodes(),
        edges=G.number_of_edges(),
    )

    return G, metadata


# ─────────────────────────────────────────────────────────────────────────────
# Circular Chain Detection
# ─────────────────────────────────────────────────────────────────────────────


async def detect_circular_chains(
    G: nx.DiGraph,
    min_length: int = 3,
    max_length: int = 10,
) -> List[CircularChain]:
    """
    Detect circular transaction chains using NetworkX cycle detection.

    A circular chain: Party A → Party B → Party C → Party A

    Args:
        G: Transaction graph
        min_length: Minimum cycle length (default 3)
        max_length: Maximum cycle length (default 10)

    Returns:
        List of CircularChain
    """
    logger.info("detect_circular_chains", min_length=min_length)

    circular_chains = []

    try:
        # Find all simple cycles
        cycles = list(nx.simple_cycles(G))
        logger.info("detect_circular_chains: cycles found", count=len(cycles))

        for cycle in cycles:
            cycle_length = len(cycle)

            if cycle_length < min_length or cycle_length > max_length:
                continue

            # Extract transaction details
            parcels_involved = set()
            all_transactions = []
            min_date = None
            max_date = None

            for i in range(cycle_length):
                from_party = cycle[i]
                to_party = cycle[(i + 1) % cycle_length]

                if G.has_edge(from_party, to_party):
                    edge_data = G[from_party][to_party]
                    transactions = edge_data.get("transactions", [])
                    all_transactions.extend(transactions)

                    for txn in transactions:
                        if txn["parcel_id"]:
                            parcels_involved.add(txn["parcel_id"])
                        if txn["date"]:
                            txn_date = datetime.fromisoformat(txn["date"])
                            if min_date is None or txn_date < min_date:
                                min_date = txn_date
                            if max_date is None or txn_date > max_date:
                                max_date = txn_date

            # Compute time window
            time_window_days = 0
            if min_date and max_date:
                time_window_days = (max_date - min_date).days

            # Build description
            party_names = [G.nodes[p].get("party_name", "Unknown")[:30] for p in cycle]
            chain_desc = " → ".join(party_names) + f" → {party_names[0]}"

            # Confidence: higher for shorter time windows and more transactions
            confidence = 1.0
            if time_window_days > 90:
                confidence *= 0.7
            if time_window_days > 365:
                confidence *= 0.5

            circular_chains.append(CircularChain(
                chain_id=f"CYCLE_{len(circular_chains)+1}",
                party_ids=[UUID(p) for p in cycle],
                parcel_ids=[UUID(p) for p in parcels_involved],
                chain_length=cycle_length,
                time_window_days=time_window_days,
                description=f"Circular chain detected: {chain_desc}",
                confidence_score=round(confidence, 2),
            ))

    except Exception as e:
        logger.error("detect_circular_chains: error", error=str(e))

    logger.info("detect_circular_chains.complete", count=len(circular_chains))
    return circular_chains


# ─────────────────────────────────────────────────────────────────────────────
# Rapid Flip Detection
# ─────────────────────────────────────────────────────────────────────────────


async def detect_rapid_flips(
    db: AsyncSession,
    state_code: Optional[str] = None,
    days_threshold: int = 30,
    min_transactions: int = 3,
) -> List[RapidFlip]:
    """
    Detect parcels with rapid succession of transactions (potential flipping).

    Args:
        db: Database session
        state_code: Optional state filter
        days_threshold: Time window for rapid flips (default 30 days)
        min_transactions: Minimum transactions to flag (default 3)

    Returns:
        List of RapidFlip
    """
    logger.info(
        "detect_rapid_flips",
        state_code=state_code,
        days_threshold=days_threshold,
    )

    state_filter = "AND p.state_code = :state_code" if state_code else ""

    query = text(f"""
        WITH transaction_windows AS (
            SELECT
                m.parcel_id,
                p.bdpr,
                m.mutation_date,
                m.from_party_id,
                m.to_party_id,
                LAG(m.mutation_date) OVER (PARTITION BY m.parcel_id ORDER BY m.mutation_date) AS prev_date,
                EXTRACT(EPOCH FROM (m.mutation_date - LAG(m.mutation_date) OVER (PARTITION BY m.parcel_id ORDER BY m.mutation_date))) / 86400 AS days_since_prev
            FROM revenue.mutations m
            INNER JOIN identity.parcels p ON m.parcel_id = p.id
            WHERE m.mutation_type IN ('SALE', 'GIFT', 'EXCHANGE')
                AND m.mutation_date IS NOT NULL
                AND m.mutation_date >= CURRENT_DATE - INTERVAL '2 years'
                {state_filter}
        ),
        rapid_parcels AS (
            SELECT
                parcel_id,
                bdpr,
                COUNT(*) AS transaction_count,
                MIN(mutation_date) AS first_date,
                MAX(mutation_date) AS last_date,
                EXTRACT(EPOCH FROM (MAX(mutation_date) - MIN(mutation_date))) / 86400 AS time_window_days,
                ARRAY_AGG(DISTINCT from_party_id) FILTER (WHERE from_party_id IS NOT NULL) ||
                ARRAY_AGG(DISTINCT to_party_id) FILTER (WHERE to_party_id IS NOT NULL) AS party_ids
            FROM transaction_windows
            WHERE days_since_prev IS NOT NULL
                AND days_since_prev <= :days_threshold
            GROUP BY parcel_id, bdpr
            HAVING COUNT(*) >= :min_transactions
        )
        SELECT * FROM rapid_parcels
        ORDER BY transaction_count DESC, time_window_days ASC
        LIMIT 100
    """)

    params = {
        "days_threshold": days_threshold,
        "min_transactions": min_transactions,
    }
    if state_code:
        params["state_code"] = state_code

    result = await db.execute(query, params)
    rows = result.fetchall()

    rapid_flips = []
    for row in rows:
        time_window = int(row.time_window_days)
        txn_count = int(row.transaction_count)

        # Confidence: higher for more transactions in shorter time
        confidence = min(1.0, txn_count / 5.0)  # 5+ transactions = high confidence
        if time_window <= 7:
            confidence = min(1.0, confidence * 1.5)

        # Extract unique party IDs
        party_ids_raw = row.party_ids or []
        party_ids_unique = list(set([UUID(str(p)) for p in party_ids_raw if p]))

        rapid_flips.append(RapidFlip(
            parcel_id=UUID(str(row.parcel_id)),
            bdpr=row.bdpr,
            transaction_count=txn_count,
            time_window_days=time_window,
            parties_involved=party_ids_unique,
            description=f"Parcel {row.bdpr}: {txn_count} transactions within {time_window} days",
            confidence_score=round(confidence, 2),
        ))

    logger.info("detect_rapid_flips.complete", count=len(rapid_flips))
    return rapid_flips


# ─────────────────────────────────────────────────────────────────────────────
# Abnormal Co-occurrence
# ─────────────────────────────────────────────────────────────────────────────


async def detect_abnormal_co_occurrence(
    G: nx.DiGraph,
    threshold_transactions: int = 5,
) -> List[Tuple[str, str, int]]:
    """
    Detect party pairs that appear together in an abnormal number of transactions.

    Args:
        G: Transaction graph
        threshold_transactions: Flag if party pair has >= this many transactions

    Returns:
        List of (party_1, party_2, transaction_count)
    """
    logger.info("detect_abnormal_co_occurrence", threshold=threshold_transactions)

    abnormal_pairs = []

    for from_party, to_party, edge_data in G.edges(data=True):
        weight = edge_data.get("weight", 1)
        if weight >= threshold_transactions:
            abnormal_pairs.append((from_party, to_party, weight))

    abnormal_pairs.sort(key=lambda x: x[2], reverse=True)

    logger.info("detect_abnormal_co_occurrence.complete", count=len(abnormal_pairs))
    return abnormal_pairs


# ─────────────────────────────────────────────────────────────────────────────
# Party Risk Score
# ─────────────────────────────────────────────────────────────────────────────


async def compute_party_risk_score(
    G: nx.DiGraph,
    party_id: UUID,
    circular_chains: List[CircularChain],
    rapid_flips: List[RapidFlip],
) -> Optional[PartyRiskScore]:
    """
    Compute risk score for a party based on network topology.

    Factors:
    - Degree centrality (how connected)
    - Betweenness centrality (broker position)
    - Involvement in circular chains
    - Involvement in rapid flips

    Args:
        G: Transaction graph
        party_id: Party UUID
        circular_chains: Detected circular chains
        rapid_flips: Detected rapid flips

    Returns:
        PartyRiskScore or None if party not in graph
    """
    party_str = str(party_id)

    if not G.has_node(party_str):
        return None

    # Centrality measures
    degree_cent = nx.degree_centrality(G).get(party_str, 0.0)

    # Betweenness centrality (expensive, compute on-demand)
    try:
        betweenness_cent = nx.betweenness_centrality(G).get(party_str, 0.0)
    except Exception:
        betweenness_cent = 0.0

    # Count involvement in circular chains
    chains_count = sum(1 for chain in circular_chains if party_id in chain.party_ids)

    # Count involvement in rapid flips
    flips_count = sum(1 for flip in rapid_flips if party_id in flip.parties_involved)

    # Transaction count
    txn_count = G.nodes[party_str].get("transaction_count", 0)

    # Compute risk score (weighted)
    risk_score = (
        0.2 * degree_cent +
        0.3 * betweenness_cent +
        0.3 * min(1.0, chains_count / 2.0) +
        0.2 * min(1.0, flips_count / 3.0)
    )

    # Generate reason text
    reasons = []
    if degree_cent > 0.1:
        reasons.append(f"High connectivity ({int(degree_cent * 100)}th percentile)")
    if betweenness_cent > 0.1:
        reasons.append("Broker position in network")
    if chains_count > 0:
        reasons.append(f"Involved in {chains_count} circular chain(s)")
    if flips_count > 0:
        reasons.append(f"Involved in {flips_count} rapid flip(s)")

    reason_text = "; ".join(reasons) if reasons else "Multiple weak signals"

    party_name = G.nodes[party_str].get("party_name", "Unknown")

    return PartyRiskScore(
        party_id=party_id,
        party_name=party_name,
        risk_score=round(risk_score, 4),
        degree_centrality=round(degree_cent, 4),
        betweenness_centrality=round(betweenness_cent, 4),
        in_circular_chains=chains_count,
        rapid_flips_involved=flips_count,
        transaction_count=txn_count,
        reason_text=reason_text,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Full Analysis
# ─────────────────────────────────────────────────────────────────────────────


async def run_full_graph_analysis(
    db: AsyncSession,
    state_code: Optional[str] = None,
    district_code: Optional[str] = None,
) -> GraphAnalysisReport:
    """
    Run complete graph-based transaction network analysis.

    Args:
        db: Database session
        state_code: Optional state filter
        district_code: Optional district filter

    Returns:
        GraphAnalysisReport with all findings
    """
    logger.info(
        "run_full_graph_analysis.start",
        state_code=state_code,
        district_code=district_code,
    )

    # 1. Build graph
    G, metadata = await build_transaction_graph(db, state_code, district_code)

    # 2. Detect patterns
    circular_chains = await detect_circular_chains(G)
    rapid_flips = await detect_rapid_flips(db, state_code=state_code)

    # 3. Compute high-risk parties
    high_risk_parties = []

    # Get top parties by transaction count
    top_parties = sorted(
        G.nodes(data=True),
        key=lambda x: x[1].get("transaction_count", 0),
        reverse=True,
    )[:100]  # Top 100

    for party_str, _ in top_parties:
        party_id = UUID(party_str)
        risk_score = await compute_party_risk_score(
            G, party_id, circular_chains, rapid_flips
        )
        if risk_score and risk_score.risk_score > 0.3:  # Threshold
            high_risk_parties.append(risk_score)

    high_risk_parties.sort(key=lambda x: x.risk_score, reverse=True)

    # 4. Network statistics
    network_density = nx.density(G)

    if G.number_of_nodes() > 0:
        largest_component_size = len(max(nx.weakly_connected_components(G), key=len))
    else:
        largest_component_size = 0

    report = GraphAnalysisReport(
        state_code=state_code,
        district_code=district_code,
        analysis_timestamp=datetime.utcnow(),
        total_nodes=G.number_of_nodes(),
        total_edges=G.number_of_edges(),
        circular_chains=circular_chains,
        rapid_flips=rapid_flips,
        high_risk_parties=high_risk_parties[:20],  # Top 20
        network_density=round(network_density, 4),
        largest_component_size=largest_component_size,
    )

    logger.info(
        "run_full_graph_analysis.complete",
        circular_chains=len(circular_chains),
        rapid_flips=len(rapid_flips),
        high_risk_parties=len(high_risk_parties),
    )

    return report
