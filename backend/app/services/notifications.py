from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.notification import EmailNotification, NotificationStatus
from app.services.email import send_generic_email


def deliver_queued_notification(db: Session, notification: EmailNotification) -> EmailNotification:
    if notification.status in {NotificationStatus.SENT, NotificationStatus.SKIPPED}:
        return notification

    sent = send_generic_email(
        recipient=notification.recipient_email,
        subject=notification.subject,
        title=notification.title or notification.subject,
        body=notification.body_html,
        text=notification.text_body,
    )

    notification.status = NotificationStatus.SENT if sent else NotificationStatus.FAILED
    notification.sent_at = datetime.now(timezone.utc) if sent else None
    notification.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(notification)
    return notification
