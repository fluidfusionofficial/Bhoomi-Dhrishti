"""
Entity resolution cascade: Spatial → Deterministic → Probabilistic → Phonetic → Human Review
"""
from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, Dict, List
from uuid import UUID, uuid4

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from .types import LinkCandidate, ResolutionResult
from . import spatial, deterministic, probabilistic, phonetic, queue


class ResolutionCascade:
    """Orchestrates the multi-stage entity resolution pipeline."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.spatial_resolver = spatial.SpatialResolver(db_session)
        self.deterministic_resolver = deterministic.DeterministicResolver(db_session)
        self.probabilistic_resolver = probabilistic.ProbabilisticResolver(db_session)
        self.phonetic_resolver = phonetic.PhoneticResolver(db_session)
        self.review_queue = queue.ReviewQueueManager(db_session)

    async def run_resolution(
        self,
        source_type: str,
        source_records: List[Dict[str, Any]],
        confidence_threshold_confirm: float = 0.7,
        confidence_threshold_review: float = 0.4,
    ) -> ResolutionResult:
        """
        Run the full resolution cascade on a batch of source records.

        Args:
            source_type: Type of source (e.g., 'revenue_ror', 'sro_registrations')
            source_records: List of source record dicts with fields relevant to matching
            confidence_threshold_confirm: Score above which to auto-confirm (default 0.7)
            confidence_threshold_review: Score above which to queue for review (default 0.4)

        Returns:
            ResolutionResult with statistics and created links
        """
        start_time = datetime.now()

        matched_count = 0
        possible_count = 0
        review_count = 0
        no_match_count = 0
        links_created = []

        for record in source_records:
            source_id = record.get('id') or record.get('survey_number') or str(uuid4())

            # Stage 1: Spatial matching (if geometry available)
            candidate = None
            if 'geometry' in record or ('latitude' in record and 'longitude' in record):
                candidate = await self.spatial_resolver.find_match(record)
                if candidate and candidate.confidence_score >= confidence_threshold_confirm:
                    candidate.match_method = "SPATIAL"
                    candidate.status = "CONFIRMED"
                    matched_count += 1
                    links_created.append(candidate)
                    await self._persist_link(source_type, candidate)
                    continue

            # Stage 2: Deterministic matching
            candidate = await self.deterministic_resolver.find_match(record)
            if candidate and candidate.confidence_score >= confidence_threshold_confirm:
                candidate.match_method = "DETERMINISTIC"
                candidate.status = "CONFIRMED"
                matched_count += 1
                links_created.append(candidate)
                await self._persist_link(source_type, candidate)
                continue

            # Stage 3: Probabilistic matching (Splink)
            candidate = await self.probabilistic_resolver.find_match(record)
            if candidate:
                if candidate.confidence_score >= confidence_threshold_confirm:
                    candidate.match_method = "PROBABILISTIC"
                    candidate.status = "CONFIRMED"
                    matched_count += 1
                    links_created.append(candidate)
                    await self._persist_link(source_type, candidate)
                    continue
                elif candidate.confidence_score >= confidence_threshold_review:
                    candidate.match_method = "PROBABILISTIC"
                    candidate.status = "REQUIRES_REVIEW"
                    possible_count += 1
                    review_count += 1
                    links_created.append(candidate)
                    await self.review_queue.enqueue_for_review(source_type, candidate, record)
                    continue

            # Stage 4: Phonetic matching (owner names)
            if 'owner' in record or 'owners' in record:
                candidate = await self.phonetic_resolver.find_match(record)
                if candidate:
                    if candidate.confidence_score >= confidence_threshold_confirm:
                        candidate.match_method = "PHONETIC"
                        candidate.status = "CONFIRMED"
                        matched_count += 1
                        links_created.append(candidate)
                        await self._persist_link(source_type, candidate)
                        continue
                    elif candidate.confidence_score >= confidence_threshold_review:
                        candidate.match_method = "PHONETIC"
                        candidate.status = "REQUIRES_REVIEW"
                        possible_count += 1
                        review_count += 1
                        links_created.append(candidate)
                        await self.review_queue.enqueue_for_review(source_type, candidate, record)
                        continue

            # No match found
            no_match_count += 1

        duration = (datetime.now() - start_time).total_seconds()

        return ResolutionResult(
            total_records=len(source_records),
            matched=matched_count,
            possible_matches=possible_count,
            requires_review=review_count,
            no_match=no_match_count,
            links_created=links_created,
            duration_seconds=duration,
        )

    async def _persist_link(self, source_type: str, candidate: LinkCandidate) -> None:
        """Persist a confirmed link to the identity.parcel_links table."""
        insert_stmt = text("""
            INSERT INTO identity.parcel_links
                (source_id, source_type, target_parcel_id, confidence_score,
                 match_method, evidence_json, status, created_at)
            VALUES
                (:source_id, :source_type, :target_parcel_id, :confidence_score,
                 :match_method, :evidence_json::jsonb, :status, NOW())
            ON CONFLICT (source_id, source_type)
            DO UPDATE SET
                target_parcel_id = EXCLUDED.target_parcel_id,
                confidence_score = EXCLUDED.confidence_score,
                match_method = EXCLUDED.match_method,
                evidence_json = EXCLUDED.evidence_json,
                status = EXCLUDED.status,
                updated_at = NOW()
        """)

        await self.db.execute(insert_stmt, {
            "source_id": candidate.source_record_id,
            "source_type": source_type,
            "target_parcel_id": candidate.target_parcel_id,
            "confidence_score": candidate.confidence_score,
            "match_method": candidate.match_method,
            "evidence_json": candidate.evidence,
            "status": candidate.status,
        })
        await self.db.commit()
