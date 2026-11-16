from collections import defaultdict
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_super_admin
from app.core.database import get_db
from app.models.notification import EmailNotification, NotificationCategory, NotificationStatus
from app.models.user import User

router = APIRouter(tags=["Platform Admin"])


def _month_key(value: datetime) -> str:
    return value.strftime("%Y-%m")


def _month_label(value: datetime) -> str:
    return value.strftime("%b")


@router.get("/email/metrics")
def get_email_metrics(
    current_user: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    del current_user
    notifications = db.query(EmailNotification).all()
    now = datetime.now(timezone.utc)
    current_month = (now.year, now.month)
    month_rows: dict[str, int] = defaultdict(int)
    sent_this_month = 0
    transactional_this_month = 0
    promotional_this_month = 0
    failed_this_month = 0
    queued_this_month = 0

    for notification in notifications:
        created_at = notification.created_at
        if created_at is None:
            continue
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        month_rows[_month_key(created_at)] += 1
        if (created_at.year, created_at.month) != current_month:
            continue
        if notification.status == NotificationStatus.SENT:
            sent_this_month += 1
        elif notification.status == NotificationStatus.FAILED:
            failed_this_month += 1
        elif notification.status == NotificationStatus.QUEUED:
            queued_this_month += 1
        if notification.is_promotional:
            promotional_this_month += 1
        else:
            transactional_this_month += 1

    series = []
    for offset in range(11, -1, -1):
        month = now.month - offset
        year = now.year
        while month <= 0:
            month += 12
            year -= 1
        date = datetime(year, month, 1, tzinfo=timezone.utc)
        series.append({
            "month": _month_label(date),
            "count": month_rows.get(_month_key(date), 0),
        })

    delivered_total = sum(1 for item in notifications if item.status == NotificationStatus.SENT)
    return {
        "delivered_this_month": sent_this_month,
        "delivered_total": delivered_total,
        "transactional_this_month": transactional_this_month,
        "promotional_this_month": promotional_this_month,
        "failed_this_month": failed_this_month,
        "queued_this_month": queued_this_month,
        "open_rate": None,
        "monthly_volume": series,
    }


@router.get("/email/history")
def get_email_history(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=25, ge=1, le=100),
    current_user: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    del current_user
    query = db.query(EmailNotification).order_by(
        EmailNotification.created_at.desc(),
        EmailNotification.id.desc(),
    )
    total = query.count()
    records = query.offset((page - 1) * limit).limit(limit).all()
    return {
        "items": [
            {
                "id": item.id,
                "subject": item.subject,
                "recipient_email": item.recipient_email,
                "status": item.status.value,
                "category": item.category.value,
                "is_promotional": item.is_promotional,
                "retry_count": item.retry_count,
                "error_message": item.error_message,
                "sent_at": item.sent_at.isoformat() if item.sent_at else None,
                "created_at": item.created_at.isoformat() if item.created_at else None,
            }
            for item in records
        ],
        "page": page,
        "limit": limit,
        "total": total,
    }
