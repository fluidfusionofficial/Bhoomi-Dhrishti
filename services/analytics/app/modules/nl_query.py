"""
Natural language spatial query module - template-based (no LLM API required).

Deterministic pattern matching using regex to convert natural language
queries to SQL. Supports common spatial and administrative queries.
"""

from __future__ import annotations

import logging
import re
from typing import List, Optional, Tuple

from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Models
# ─────────────────────────────────────────────────────────────────────────────


class NLQueryResult(BaseModel):
    """Result of natural language query execution."""
    query_text: str
    interpreted_as: str
    sql_query: str
    results: List[dict]
    result_count: int
    execution_time_ms: float
    pattern_matched: str


class QueryExample(BaseModel):
    """Example query for user reference."""
    example_text: str
    description: str
    category: str


# ─────────────────────────────────────────────────────────────────────────────
# Query Patterns and Templates
# ─────────────────────────────────────────────────────────────────────────────


class NLQueryParser:
    """Template-based natural language query parser."""

    def __init__(self):
        # Define query patterns (regex) and corresponding SQL templates
        self.patterns = [
            # Pattern 1: Spatial proximity
            {
                "name": "spatial_proximity",
                "regex": r"show\s+(?:me\s+)?(?:all\s+)?(\w+)\s+(?:class\s+)?parcels?\s+within\s+(\d+)\s*(?:m|metres?|meters?)\s+of\s+(.+)",
                "template": """
                    SELECT
                        p.id,
                        p.bdpr,
                        p.village_code,
                        ST_Distance(g.geometry::geography, ref.geometry::geography) AS distance_m
                    FROM identity.parcels p
                    INNER JOIN geo.parcel_geometries g ON p.id = g.parcel_id AND g.is_current = true
                    INNER JOIN {ref_table} ref ON ref.{ref_filter}
                    WHERE ST_DWithin(g.geometry::geography, ref.geometry::geography, {distance})
                        AND p.is_active = true
                    ORDER BY distance_m
                    LIMIT 100
                """,
                "description": "Find parcels near a feature",
            },
            # Pattern 2: Dispute count
            {
                "name": "dispute_count",
                "regex": r"how\s+many\s+parcels?\s+in\s+(\w+)\s+(?:district\s+)?have\s+(?:open\s+)?disputes?",
                "template": """
                    SELECT
                        COUNT(DISTINCT p.id) AS parcel_count,
                        p.district_code
                    FROM identity.parcels p
                    INNER JOIN geo.topology_conflicts tc ON p.id = tc.parcel_id_1 OR p.id = tc.parcel_id_2
                    WHERE p.district_code = '{district}'
                        AND tc.resolution_status IN ('OPEN', 'UNDER_REVIEW')
                        AND p.is_active = true
                    GROUP BY p.district_code
                """,
                "description": "Count parcels with disputes in a district",
            },
            # Pattern 3: Area mismatch
            {
                "name": "area_mismatch",
                "regex": r"find\s+parcels?\s+with\s+area\s+mismatch\s+(?:greater\s+than\s+|>\s*)(\d+)%?",
                "template": """
                    SELECT
                        p.id,
                        p.bdpr,
                        ror.area_sq_m AS recorded_area,
                        ST_Area(g.geometry::geography) AS computed_area,
                        ABS(ror.area_sq_m - ST_Area(g.geometry::geography)) / NULLIF(ror.area_sq_m, 0) * 100 AS divergence_percent
                    FROM identity.parcels p
                    INNER JOIN geo.parcel_geometries g ON p.id = g.parcel_id AND g.is_current = true
                    INNER JOIN revenue.records_of_rights ror ON p.id = ror.parcel_id AND ror.is_active = true
                    WHERE p.is_active = true
                        AND ror.area_sq_m > 0
                        AND ABS(ror.area_sq_m - ST_Area(g.geometry::geography)) / NULLIF(ror.area_sq_m, 0) * 100 > {threshold}
                    ORDER BY divergence_percent DESC
                    LIMIT 100
                """,
                "description": "Find parcels with area divergence above threshold",
            },
            # Pattern 4: Owner search
            {
                "name": "owner_search",
                "regex": r"show\s+(?:me\s+)?(?:owner\s+)?[\"']?([^\"']+)[\"']?\s+all\s+parcels?",
                "template": """
                    SELECT
                        p.id,
                        p.bdpr,
                        p.state_code,
                        p.district_code,
                        party.name_en AS owner_name,
                        r.right_type,
                        r.share_numerator,
                        r.share_denominator
                    FROM identity.parcels p
                    INNER JOIN revenue.rights r ON p.id = r.parcel_id
                    INNER JOIN revenue.parties party ON r.party_id = party.id
                    WHERE r.right_type = 'OWNERSHIP'
                        AND p.is_active = true
                        AND (
                            similarity(LOWER(party.name_en), LOWER('{owner_name}')) > 0.6
                            OR LOWER(party.name_en) LIKE '%{owner_name_like}%'
                        )
                    ORDER BY similarity(LOWER(party.name_en), LOWER('{owner_name}')) DESC
                    LIMIT 50
                """,
                "description": "Find parcels owned by a person (fuzzy match)",
            },
            # Pattern 5: Building permissions without RoR update
            {
                "name": "stale_building_permissions",
                "regex": r"parcels?\s+with\s+building\s+permissions?\s+but\s+no\s+ror\s+update\s+in\s+(?:last\s+)?(\d+)\s+years?",
                "template": """
                    SELECT
                        p.id,
                        p.bdpr,
                        bp.application_number,
                        bp.granted_date,
                        MAX(ror.created_at) AS last_ror_update
                    FROM identity.parcels p
                    INNER JOIN planning.building_permissions bp ON p.id = bp.parcel_id
                    LEFT JOIN revenue.records_of_rights ror ON p.id = ror.parcel_id
                    WHERE bp.status = 'GRANTED'
                        AND bp.granted_date IS NOT NULL
                        AND p.is_active = true
                        AND bp.is_active = true
                    GROUP BY p.id, p.bdpr, bp.application_number, bp.granted_date
                    HAVING MAX(ror.created_at) IS NULL
                        OR MAX(ror.created_at) < bp.granted_date + INTERVAL '{years} years'
                    ORDER BY bp.granted_date DESC
                    LIMIT 100
                """,
                "description": "Find parcels with building permissions but stale RoR",
            },
            # Pattern 6: Encumbered parcels
            {
                "name": "encumbered_parcels",
                "regex": r"(?:list\s+)?(?:all\s+)?encumbered\s+parcels?\s+in\s+(\w+)\s+(?:village)?",
                "template": """
                    SELECT
                        p.id,
                        p.bdpr,
                        e.encumbrance_type,
                        e.amount,
                        e.registered_date,
                        e.status
                    FROM identity.parcels p
                    INNER JOIN registration.encumbrances e ON p.id = e.parcel_id
                    WHERE p.village_code = '{village}'
                        AND e.status IN ('ACTIVE', 'PENDING_RELEASE')
                        AND p.is_active = true
                    ORDER BY e.registered_date DESC
                    LIMIT 100
                """,
                "description": "List encumbered parcels in a village",
            },
            # Pattern 7: Anomaly scores
            {
                "name": "high_anomaly_parcels",
                "regex": r"(?:show|find)\s+parcels?\s+with\s+high\s+anomaly\s+scores?(?:\s+in\s+(\w+))?",
                "template": """
                    SELECT
                        p.id,
                        p.bdpr,
                        p.state_code,
                        p.district_code,
                        cs.score_value AS anomaly_score,
                        cs.risk_band,
                        cs.contributing_factors
                    FROM identity.parcels p
                    INNER JOIN ml.conflict_scores cs ON p.id = cs.parcel_id
                    WHERE cs.score_type = 'ANOMALY'
                        AND cs.is_latest = true
                        AND cs.risk_band IN ('HIGH', 'MEDIUM')
                        AND p.is_active = true
                        {district_filter}
                    ORDER BY cs.score_value DESC
                    LIMIT 50
                """,
                "description": "Find parcels with high anomaly scores",
            },
            # Pattern 8: Land class count
            {
                "name": "land_class_count",
                "regex": r"how\s+many\s+(\w+)\s+(?:land\s+)?parcels?\s+in\s+(\w+)",
                "template": """
                    SELECT
                        COUNT(*) AS parcel_count,
                        ror.land_classification
                    FROM identity.parcels p
                    INNER JOIN revenue.records_of_rights ror ON p.id = ror.parcel_id
                    WHERE p.district_code = '{district}'
                        AND ror.land_classification ILIKE '%{land_class}%'
                        AND p.is_active = true
                        AND ror.is_active = true
                    GROUP BY ror.land_classification
                """,
                "description": "Count parcels by land classification",
            },
        ]

    def parse_and_build_sql(
        self,
        query_text: str,
        actor_roles: List[str],
        state_code: Optional[str] = None,
        district_code: Optional[str] = None,
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Parse natural language query and generate SQL.

        Args:
            query_text: User's natural language query
            actor_roles: Actor roles for access filtering
            state_code: Optional state filter for access control
            district_code: Optional district filter for access control

        Returns:
            (sql_query, interpreted_as, pattern_name) or (None, None, None) if no match
        """
        query_lower = query_text.lower().strip()

        for pattern_def in self.patterns:
            match = re.search(pattern_def["regex"], query_lower, re.IGNORECASE)

            if match:
                logger.info(
                    "parse_and_build_sql: pattern matched",
                    pattern=pattern_def["name"],
                    query=query_text,
                )

                # Extract parameters from regex groups
                params = match.groups()

                # Build SQL from template
                sql = self._apply_template(
                    pattern_def["template"],
                    pattern_def["name"],
                    params,
                    actor_roles,
                    state_code,
                    district_code,
                )

                interpreted_as = pattern_def["description"]

                return sql, interpreted_as, pattern_def["name"]

        # No pattern matched
        logger.warning("parse_and_build_sql: no pattern matched", query=query_text)
        return None, None, None

    def _apply_template(
        self,
        template: str,
        pattern_name: str,
        params: Tuple,
        actor_roles: List[str],
        state_code: Optional[str],
        district_code: Optional[str],
    ) -> str:
        """Apply parameters to SQL template."""
        sql = template

        # Pattern-specific parameter substitution
        if pattern_name == "spatial_proximity":
            land_class = params[0] if params else "AGRICULTURAL"
            distance = params[1] if len(params) > 1 else "100"
            feature_name = params[2] if len(params) > 2 else "forest"

            # Map feature to reference table (simplified)
            ref_table = "geo.restricted_zones"
            ref_filter = f"zone_type ILIKE '%{feature_name}%'"

            sql = sql.replace("{ref_table}", ref_table)
            sql = sql.replace("{ref_filter}", ref_filter)
            sql = sql.replace("{distance}", distance)

        elif pattern_name == "dispute_count":
            district = params[0] if params else "unknown"
            sql = sql.replace("{district}", district)

        elif pattern_name == "area_mismatch":
            threshold = params[0] if params else "15"
            sql = sql.replace("{threshold}", threshold)

        elif pattern_name == "owner_search":
            owner_name = params[0] if params else "unknown"
            owner_name_like = owner_name.lower().replace(" ", "%")
            sql = sql.replace("{owner_name}", owner_name)
            sql = sql.replace("{owner_name_like}", owner_name_like)

        elif pattern_name == "stale_building_permissions":
            years = params[0] if params else "3"
            sql = sql.replace("{years}", years)

        elif pattern_name == "encumbered_parcels":
            village = params[0] if params else "unknown"
            sql = sql.replace("{village}", village)

        elif pattern_name == "high_anomaly_parcels":
            if params and params[0]:
                district_filter = f"AND p.district_code = '{params[0]}'"
            else:
                district_filter = ""
            sql = sql.replace("{district_filter}", district_filter)

        elif pattern_name == "land_class_count":
            land_class = params[0] if params else "agricultural"
            district = params[1] if len(params) > 1 else "unknown"
            sql = sql.replace("{land_class}", land_class)
            sql = sql.replace("{district}", district)

        # Apply access control filters
        sql = self._apply_access_control(sql, actor_roles, state_code, district_code)

        return sql.strip()

    def _apply_access_control(
        self,
        sql: str,
        actor_roles: List[str],
        state_code: Optional[str],
        district_code: Optional[str],
    ) -> str:
        """Apply tiered access filtering based on actor roles."""
        # Officers with district scope: add district filter
        if "revenue_officer" in actor_roles and district_code:
            # Check if WHERE clause exists
            if "WHERE" in sql.upper():
                sql = sql.replace("WHERE", f"WHERE p.district_code = '{district_code}' AND", 1)
            else:
                sql = sql.replace("ORDER BY", f"WHERE p.district_code = '{district_code}' ORDER BY", 1)

        # Citizen access: more restrictive (only public records)
        elif "citizen" in actor_roles:
            # Add privacy filters (example: exclude sensitive fields)
            # For demonstration, no additional restriction
            pass

        return sql


# ─────────────────────────────────────────────────────────────────────────────
# Query Execution
# ─────────────────────────────────────────────────────────────────────────────


async def execute_nl_query(
    db: AsyncSession,
    query_text: str,
    actor_roles: List[str],
    state_code: Optional[str] = None,
    district_code: Optional[str] = None,
) -> NLQueryResult:
    """
    Execute a natural language query.

    Args:
        db: Database session
        query_text: User's natural language query
        actor_roles: Actor roles for access control
        state_code: Optional state filter
        district_code: Optional district filter

    Returns:
        NLQueryResult with results and metadata
    """
    import time
    start_time = time.time()

    parser = NLQueryParser()

    # Parse query
    sql, interpreted_as, pattern_name = parser.parse_and_build_sql(
        query_text,
        actor_roles,
        state_code,
        district_code,
    )

    if sql is None:
        # No pattern matched
        return NLQueryResult(
            query_text=query_text,
            interpreted_as="Query not recognized. Please try one of the example queries.",
            sql_query="",
            results=[],
            result_count=0,
            execution_time_ms=0,
            pattern_matched="NONE",
        )

    # Execute SQL
    logger.info("execute_nl_query: executing", pattern=pattern_name)

    try:
        result = await db.execute(text(sql))
        rows = result.fetchall()

        # Convert to dict
        results = []
        if rows:
            columns = result.keys()
            for row in rows:
                results.append(dict(zip(columns, row)))

        execution_time_ms = (time.time() - start_time) * 1000

        return NLQueryResult(
            query_text=query_text,
            interpreted_as=interpreted_as or "Query executed",
            sql_query=sql,
            results=results,
            result_count=len(results),
            execution_time_ms=round(execution_time_ms, 2),
            pattern_matched=pattern_name or "UNKNOWN",
        )

    except Exception as e:
        logger.error("execute_nl_query: error", error=str(e), sql=sql)

        return NLQueryResult(
            query_text=query_text,
            interpreted_as=f"Error executing query: {str(e)}",
            sql_query=sql,
            results=[],
            result_count=0,
            execution_time_ms=(time.time() - start_time) * 1000,
            pattern_matched=pattern_name or "ERROR",
        )


def get_example_queries() -> List[QueryExample]:
    """Return a list of example queries for user reference."""
    return [
        QueryExample(
            example_text="Show me all agricultural parcels within 500 metres of forest",
            description="Find parcels near a restricted zone",
            category="Spatial",
        ),
        QueryExample(
            example_text="How many parcels in Bangalore have open disputes?",
            description="Count parcels with active disputes",
            category="Administrative",
        ),
        QueryExample(
            example_text="Find parcels with area mismatch greater than 20%",
            description="Detect area discrepancies",
            category="Quality",
        ),
        QueryExample(
            example_text="Show owner Ramesh Kumar all parcels",
            description="Search by owner name (fuzzy match)",
            category="Ownership",
        ),
        QueryExample(
            example_text="Parcels with building permissions but no RoR update in last 3 years",
            description="Identify stale records",
            category="Cross-registry",
        ),
        QueryExample(
            example_text="List all encumbered parcels in 560001 village",
            description="Find mortgaged/encumbered land",
            category="Financial",
        ),
        QueryExample(
            example_text="Show parcels with high anomaly scores in Mysore",
            description="ML-flagged suspicious parcels",
            category="Intelligence",
        ),
        QueryExample(
            example_text="How many agricultural parcels in Hassan",
            description="Count by land classification",
            category="Statistics",
        ),
        QueryExample(
            example_text="Find parcels with area mismatch greater than 15%",
            description="Default threshold for area checks",
            category="Quality",
        ),
        QueryExample(
            example_text="Show parcels with high anomaly scores",
            description="State-wide anomaly search",
            category="Intelligence",
        ),
    ]
