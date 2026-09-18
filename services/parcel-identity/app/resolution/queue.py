"""
Review queue manager for ambiguous entity resolution matches.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .types import LinkCandidate


class ReviewQueueManager:
    """Manages the human review queue for low-confidence matches."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def enqueue_for_review(
        self,
        source_type: str,
        candidate: LinkCandidate,
        source_record: Dict[str, Any],
    ) -> None:
        """
        Add a link candidate to the review queue.

        Args:
            source_type: Type of source system
            candidate: LinkCandidate with confidence in [threshold_review, threshold_confirm)
            source_record: Full source record dict for reviewer context
        """
        insert_stmt = text("""
            INSERT INTO identity.link_reviews
                (source_id, source_type, target_parcel_id, confidence_score,
                 match_method, evidence_json, source_record_json, status, created_at)
            VALUES
                (:source_id, :source_type, :target_parcel_id, :confidence_score,
                 :match_method, :evidence_json::jsonb, :source_record_json::jsonb, 'PENDING', NOW())
        """)

        await self.db.execute(insert_stmt, {
            "source_id": candidate.source_record_id,
            "source_type": source_type,
            "target_parcel_id": candidate.target_parcel_id,
            "confidence_score": candidate.confidence_score,
            "match_method": candidate.match_method,
            "evidence_json": candidate.evidence,
            "source_record_json": source_record,
        })
        await self.db.commit()

    async def approve_review(
        self,
        review_id: int,
        reviewer_actor_id: str,
    ) -> None:
        """
        Approve a review, promoting it to a confirmed link.

        Args:
            review_id: ID of the review record
            reviewer_actor_id: Actor (officer) who approved it
        """
        # Update review status
        update_review = text("""
            UPDATE identity.link_reviews
            SET status = 'APPROVED',
                reviewed_by = :reviewer_actor_id,
                reviewed_at = NOW()
            WHERE review_id = :review_id
        """)
        await self.db.execute(update_review, {
            "review_id": review_id,
            "reviewer_actor_id": reviewer_actor_id,
        })

        # Create confirmed link
        create_link = text("""
            INSERT INTO identity.parcel_links
                (source_id, source_type, target_parcel_id, confidence_score,
                 match_method, evidence_json, status, created_at)
            SELECT
                source_id, source_type, target_parcel_id, confidence_score,
                match_method, evidence_json, 'CONFIRMED', NOW()
            FROM identity.link_reviews
            WHERE review_id = :review_id
            ON CONFLICT (source_id, source_type)
            DO UPDATE SET
                target_parcel_id = EXCLUDED.target_parcel_id,
                confidence_score = EXCLUDED.confidence_score,
                status = 'CONFIRMED',
                updated_at = NOW()
        """)
        await self.db.execute(create_link, {"review_id": review_id})
        await self.db.commit()

    async def reject_review(
        self,
        review_id: int,
        reviewer_actor_id: str,
        rejection_reason: str = "",
    ) -> None:
        """
        Reject a review, marking the link as invalid.

        Args:
            review_id: ID of the review record
            reviewer_actor_id: Actor (officer) who rejected it
            rejection_reason: Optional reason for rejection
        """
        update_stmt = text("""
            UPDATE identity.link_reviews
            SET status = 'REJECTED',
                reviewed_by = :reviewer_actor_id,
                reviewed_at = NOW(),
                evidence_json = jsonb_set(
                    evidence_json,
                    '{rejection_reason}',
                    to_jsonb(:rejection_reason::text)
                )
            WHERE review_id = :review_id
        """)
        await self.db.execute(update_stmt, {
            "review_id": review_id,
            "reviewer_actor_id": reviewer_actor_id,
            "rejection_reason": rejection_reason or "No specific reason provided",
        })
        await self.db.commit()
