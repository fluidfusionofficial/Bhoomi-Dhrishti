"""
Notifications service — IN_APP always, EMAIL / SMS_OTP for critical events.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import List, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.templates import NOTIFICATION_TEMPLATES, render_template

logger = structlog.get_logger()
router = APIRouter()


class NotificationSendRequest:
    pass


from pydantic import BaseModel


class SendRequest(BaseModel):
    template_key: str
    user_id: str
    lang: str = "en"
    variables: dict = {}
    channels: Optional[List[str]] = None   # override; if None use template defaults


class NotificationResponse(BaseModel):
    id: uuid.UUID
    user_id: str
    template_key: str
    message: str
    channel: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    total: int
    unread: int
    items: List[NotificationResponse]


@router.post("/api/v1/notifications/send", status_code=202)
async def send_notification(
    body: SendRequest,
    db: AsyncSession = Depends(get_db),
):
    tmpl = NOTIFICATION_TEMPLATES.get(body.template_key)
    if not tmpl:
        raise HTTPException(status_code=422, detail=f"Unknown template: {body.template_key}")

    message = render_template(body.template_key, body.lang, body.variables)
    channels = body.channels or tmpl.get("channels", ["IN_APP"])

    created_ids = []
    now = datetime.utcnow()

    for channel in channels:
        nid = uuid.uuid4()
        await db.execute(
            text(
                """
                INSERT INTO notifications.notifications (
                    id, user_id, template_key, message, channel,
                    is_read, created_at, variables
                ) VALUES (
                    :id, :user_id, :tkey, :message, :channel,
                    false, :now, :variables::jsonb
                )
                """
            ),
            {
                "id": nid,
                "user_id": body.user_id,
                "tkey": body.template_key,
                "message": message,
                "channel": channel,
                "now": now,
                "variables": json.dumps(body.variables),
            },
        )
        created_ids.append(str(nid))

    await db.commit()

    # TODO: For EMAIL/SMS channels, enqueue to delivery worker (Redis queue)
    logger.info("notification_sent", user_id=body.user_id, template=body.template_key, channels=channels)
    return {"accepted": True, "notification_ids": created_ids, "channels": channels}


@router.get("/api/v1/notifications/user/{user_id}", response_model=NotificationListResponse)
async def user_notifications(
    user_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    filter_clause = "WHERE user_id = :uid"
    params: dict = {"uid": user_id, "limit": page_size, "offset": (page - 1) * page_size}

    if unread_only:
        filter_clause += " AND is_read = false"

    count_row = await db.execute(
        text(f"SELECT COUNT(*) FROM notifications.notifications {filter_clause}"), params
    )
    total = count_row.scalar() or 0

    unread_row = await db.execute(
        text("SELECT COUNT(*) FROM notifications.notifications WHERE user_id = :uid AND is_read = false"),
        {"uid": user_id},
    )
    unread = unread_row.scalar() or 0

    rows = await db.execute(
        text(
            f"""
            SELECT id, user_id, template_key, message, channel, is_read, created_at
            FROM notifications.notifications
            {filter_clause}
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
            """
        ),
        params,
    )
    items = [
        NotificationResponse(
            id=r[0], user_id=r[1], template_key=r[2],
            message=r[3], channel=r[4], is_read=r[5], created_at=r[6],
        )
        for r in rows.fetchall()
    ]
    return NotificationListResponse(total=total, unread=unread, items=items)


@router.put("/api/v1/notifications/{notification_id}/read")
async def mark_read(
    notification_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text(
            "UPDATE notifications.notifications SET is_read = true, read_at = NOW() "
            "WHERE id = :id RETURNING id"
        ),
        {"id": notification_id},
    )
    if not result.fetchone():
        raise HTTPException(status_code=404, detail="Notification not found")
    await db.commit()
    return {"id": str(notification_id), "is_read": True}


@router.get("/api/v1/notifications/templates")
async def list_templates():
    summary = []
    for key, tmpl in NOTIFICATION_TEMPLATES.items():
        summary.append(
            {
                "key": key,
                "available_languages": [k for k in tmpl if k not in ("critical", "channels")],
                "channels": tmpl.get("channels", ["IN_APP"]),
                "critical": tmpl.get("critical", False),
                "sample_en": tmpl.get("en", ""),
            }
        )
    return {"templates": summary}
