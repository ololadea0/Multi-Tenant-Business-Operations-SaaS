from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_super_admin, get_current_user
from app.core.database import get_db
from app.models.announcement import PlatformAnnouncement
from app.models.billing import SubscriptionPlan
from app.models.notification import EmailNotification, NotificationCategory, NotificationStatus
from app.models.user import User
from app.services.billing import ensure_plans
from app.services.email import send_generic_email
from app.services.email_templates import render_email_template
from app.api.platform_admin.common import (
    AdminEmailPreviewRequest,
    AdminEmailSendRequest,
    PlatformAnnouncementCreateRequest,
    PlanCreateRequest,
    PlanUpdateRequest,
    PlatformSettingsUpdateRequest,
    ensure_platform_announcements_table,
    get_or_create_platform_settings,
    get_template_category,
    normalize_billing_intervals,
    record_platform_audit,
    serialize_announcement,
)

router = APIRouter(tags=["Platform Admin"])


@router.post("/plans", status_code=status.HTTP_201_CREATED)
def create_plan(
    data: PlanCreateRequest,
    current_user: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    ensure_plans(db)
    key = data.key.lower()
    if db.query(SubscriptionPlan).filter(SubscriptionPlan.key == key).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A plan with the key '{key}' already exists. Use a unique plan key.",
        )

    last_plan = db.query(SubscriptionPlan).order_by(SubscriptionPlan.display_order.desc()).first()
    plan = SubscriptionPlan(
        key=key,
        name=data.name.strip(),
        description=data.description.strip(),
        monthly_price=data.monthly_price,
        annual_price=data.annual_price,
        currency=data.currency.upper(),
        max_team_members=data.max_team_members,
        max_products=data.max_products,
        max_monthly_orders=data.max_monthly_orders,
        is_active=data.is_active,
        display_order=data.display_order if data.display_order else (last_plan.display_order + 1 if last_plan else 1),
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    record_platform_audit(
        db,
        actor=current_user,
        action="created_subscription_plan",
        entity_type="subscription_plan",
        entity_id=plan.id,
        description=f"Created {plan.name} subscription plan",
        metadata={"key": plan.key, "is_active": plan.is_active, "display_order": plan.display_order},
    )
    return {
        "key": plan.key,
        "name": plan.name,
        "description": plan.description,
        "monthly_price": plan.monthly_price,
        "annual_price": plan.annual_price,
        "currency": plan.currency,
        "max_team_members": plan.max_team_members,
        "max_products": plan.max_products,
        "max_monthly_orders": plan.max_monthly_orders,
        "is_active": plan.is_active,
        "display_order": plan.display_order,
    }


@router.get("/audit-logs")
def get_platform_audit_logs(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    action: str | None = Query(default=None),
    current_user: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    from app.models.audit_log import PlatformAuditLog

    query = db.query(PlatformAuditLog)
    if action:
        query = query.filter(PlatformAuditLog.action == action)

    total = query.count()
    entries = (
        query.order_by(PlatformAuditLog.created_at.desc(), PlatformAuditLog.id.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    return {
        "items": [{
            "id": item.id,
            "actor_id": item.actor_id,
            "actor_name": item.actor_name,
            "action": item.action,
            "entity_type": item.entity_type,
            "entity_id": item.entity_id,
            "description": item.description,
            "source": item.source,
            "ip_address": item.ip_address,
            "user_agent": item.user_agent,
            "metadata": item.metadata_json,
            "created_at": item.created_at.isoformat() if item.created_at else None,
        } for item in entries],
        "page": page,
        "limit": limit,
        "total": total,
        "pages": (total + limit - 1) // limit if total else 0,
    }


@router.post("/email/preview")
def preview_admin_email(
    data: AdminEmailPreviewRequest,
    current_user: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    if data.template_key not in {"welcome", "announcement", "billing"}:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email template not found")

    rendered_subject, html, text = render_email_template(
        data.template_key,
        subject=data.subject,
        variables=data.variables,
        is_promotional=data.is_promotional,
    )

    return {
        "template_key": data.template_key,
        "recipient_email": data.recipient_email,
        "subject": rendered_subject,
        "html": html,
        "text": text,
        "is_promotional": data.is_promotional,
    }


@router.post("/email/send")
def send_admin_email(
    data: AdminEmailSendRequest,
    current_user: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    if data.template_key not in {"welcome", "announcement", "billing"}:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email template not found")

    idempotency_key = data.idempotency_key or f"{current_user.id}:{data.template_key}:{data.recipient_email}:{data.subject}"
    existing = (
        db.query(EmailNotification)
        .filter(EmailNotification.idempotency_key == idempotency_key)
        .first()
    )
    if existing:
        return {
            "message": "Email submitted successfully",
            "status": existing.status.value,
            "delivery_id": existing.id,
            "idempotency_key": existing.idempotency_key,
        }

    rendered_subject, html, text = render_email_template(
        data.template_key,
        subject=data.subject,
        variables=data.variables,
        is_promotional=data.is_promotional,
    )

    category = get_template_category(data.template_key, data.is_promotional)
    notification = EmailNotification(
        user_id=current_user.id,
        category=category,
        subject=rendered_subject,
        title=data.subject or rendered_subject,
        recipient_email=data.recipient_email,
        body_html=html,
        text_body=text,
        status=NotificationStatus.QUEUED,
        idempotency_key=idempotency_key,
        is_promotional=data.is_promotional,
        metadata_json={
            "template_key": data.template_key,
            "variables": data.variables,
            "test_only": bool(data.test_only),
            "is_promotional": data.is_promotional,
            "created_by": current_user.email,
        },
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)

    sent = send_generic_email(
        recipient=data.recipient_email,
        subject=rendered_subject,
        title=data.subject or rendered_subject,
        body=html,
        text=text,
    )

    if sent:
        notification.status = NotificationStatus.SENT
        notification.sent_at = datetime.now(timezone.utc)
        notification.retry_count = 0
    else:
        notification.status = NotificationStatus.FAILED
        notification.error_message = "Temporary provider failure while sending email."
        notification.retry_count = 1
        notification.next_retry_at = datetime.now(timezone.utc) + timedelta(minutes=2)

    db.commit()
    db.refresh(notification)

    return {
        "message": "Email submitted successfully",
        "status": notification.status.value,
        "delivery_id": notification.id,
        "idempotency_key": notification.idempotency_key,
    }


@router.get("/settings")
def get_platform_settings(current_user: User = Depends(get_current_super_admin), db: Session = Depends(get_db)):
    settings_record = get_or_create_platform_settings(db)
    return {
        "trial_duration_days": settings_record.trial_duration_days,
        "trial_enabled": settings_record.trial_enabled,
        "trial_plan_key": settings_record.trial_plan_key,
        "billing_intervals": [item.strip() for item in settings_record.billing_intervals.split(",") if item.strip()] if settings_record.billing_intervals else ["monthly", "annual"],
        "renewal_policy": settings_record.renewal_policy,
        "annual_billing_discount_percent": settings_record.annual_billing_discount_percent,
        "payment_grace_period_days": settings_record.payment_grace_period_days,
        "support_email": settings_record.support_email,
        "support_phone": settings_record.support_phone,
        "help_center_url": settings_record.help_center_url,
        "allow_new_registrations": settings_record.allow_new_registrations,
        "maintenance_notice_enabled": settings_record.maintenance_notice_enabled,
        "maintenance_message": settings_record.maintenance_message,
        "maintenance_until": settings_record.maintenance_until.isoformat() if settings_record.maintenance_until else None,
    }


@router.get("/public/settings")
def get_public_platform_settings(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    settings_record = get_or_create_platform_settings(db)
    return {
        "maintenance_notice_enabled": settings_record.maintenance_notice_enabled,
        "maintenance_message": settings_record.maintenance_message,
        "maintenance_until": settings_record.maintenance_until.isoformat() if settings_record.maintenance_until else None,
    }


@router.put("/settings")
def update_platform_settings(
    data: PlatformSettingsUpdateRequest,
    current_user: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    settings_record = get_or_create_platform_settings(db)
    settings_record.trial_duration_days = data.trial_duration_days
    settings_record.trial_enabled = data.trial_enabled
    settings_record.trial_plan_key = data.trial_plan_key.strip().lower()
    settings_record.billing_intervals = ",".join(normalize_billing_intervals(data.billing_intervals))
    settings_record.renewal_policy = data.renewal_policy.strip().lower() or "manual"
    settings_record.annual_billing_discount_percent = data.annual_billing_discount_percent
    settings_record.payment_grace_period_days = data.payment_grace_period_days
    settings_record.support_email = data.support_email.strip()
    settings_record.support_phone = data.support_phone.strip()
    settings_record.help_center_url = data.help_center_url.strip()
    settings_record.allow_new_registrations = data.allow_new_registrations
    settings_record.maintenance_notice_enabled = data.maintenance_notice_enabled
    settings_record.maintenance_message = data.maintenance_message.strip() or settings_record.maintenance_message
    settings_record.maintenance_until = data.maintenance_until
    db.commit()
    db.refresh(settings_record)
    record_platform_audit(
        db,
        actor=current_user,
        action="updated_platform_settings",
        description="Updated platform configuration defaults",
        entity_type="platform_settings",
        metadata={
            "trial_duration_days": settings_record.trial_duration_days,
            "trial_enabled": settings_record.trial_enabled,
            "trial_plan_key": settings_record.trial_plan_key,
            "billing_intervals": settings_record.billing_intervals,
            "annual_billing_discount_percent": settings_record.annual_billing_discount_percent,
            "payment_grace_period_days": settings_record.payment_grace_period_days,
            "allow_new_registrations": settings_record.allow_new_registrations,
            "maintenance_notice_enabled": settings_record.maintenance_notice_enabled,
            "maintenance_until": settings_record.maintenance_until.isoformat() if settings_record.maintenance_until else None,
        },
    )
    return {
        "trial_duration_days": settings_record.trial_duration_days,
        "trial_enabled": settings_record.trial_enabled,
        "trial_plan_key": settings_record.trial_plan_key,
        "billing_intervals": [item.strip() for item in settings_record.billing_intervals.split(",") if item.strip()] if settings_record.billing_intervals else ["monthly", "annual"],
        "renewal_policy": settings_record.renewal_policy,
        "annual_billing_discount_percent": settings_record.annual_billing_discount_percent,
        "payment_grace_period_days": settings_record.payment_grace_period_days,
        "support_email": settings_record.support_email,
        "support_phone": settings_record.support_phone,
        "help_center_url": settings_record.help_center_url,
        "allow_new_registrations": settings_record.allow_new_registrations,
        "maintenance_notice_enabled": settings_record.maintenance_notice_enabled,
        "maintenance_message": settings_record.maintenance_message,
        "maintenance_until": settings_record.maintenance_until.isoformat() if settings_record.maintenance_until else None,
    }


@router.get("/public/announcements")
def list_public_announcements(
    active_only: bool = Query(default=False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ensure_platform_announcements_table(db)
    query = db.query(PlatformAnnouncement).order_by(PlatformAnnouncement.created_at.desc())
    if active_only:
        query = query.filter(PlatformAnnouncement.is_active.is_(True))

    items = [serialize_announcement(item) for item in query.all()]
    return {"items": items, "total": len(items)}


@router.get("/announcements")
def list_announcements(
    active_only: bool = Query(default=False),
    current_user: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    ensure_platform_announcements_table(db)
    query = db.query(PlatformAnnouncement).order_by(PlatformAnnouncement.created_at.desc())
    if active_only:
        query = query.filter(PlatformAnnouncement.is_active.is_(True))

    items = [serialize_announcement(item) for item in query.all()]
    return {"items": items, "total": len(items)}


@router.post("/announcements", status_code=status.HTTP_201_CREATED)
def create_announcement(
    data: PlatformAnnouncementCreateRequest,
    current_user: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    ensure_platform_announcements_table(db)
    if data.starts_at and data.ends_at and data.ends_at < data.starts_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Announcement end time must be after the start time.")

    announcement = PlatformAnnouncement(
        title=data.title.strip(),
        message=data.message.strip(),
        kind=data.kind,
        is_active=data.is_active,
        starts_at=data.starts_at,
        ends_at=data.ends_at,
        created_by_id=current_user.id,
    )
    db.add(announcement)
    db.commit()
    db.refresh(announcement)

    record_platform_audit(
        db,
        actor=current_user,
        action="created_announcement",
        entity_type="announcement",
        entity_id=announcement.id,
        description=f"Created announcement: {announcement.title}",
        metadata={"kind": announcement.kind, "is_active": announcement.is_active},
    )
    return serialize_announcement(announcement)


@router.patch("/plans/{plan_key}")
def update_plan(
    plan_key: str,
    data: PlanUpdateRequest,
    current_user: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.key == plan_key).first()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription plan not found")

    plan.name = data.name.strip()
    plan.description = data.description.strip()
    plan.monthly_price = data.monthly_price
    plan.annual_price = data.annual_price
    plan.currency = data.currency.upper()
    plan.max_team_members = data.max_team_members
    plan.max_products = data.max_products
    plan.max_monthly_orders = data.max_monthly_orders
    plan.is_active = data.is_active
    plan.display_order = data.display_order
    db.commit()
    db.refresh(plan)
    record_platform_audit(
        db,
        actor=current_user,
        action="updated_subscription_plan",
        entity_type="subscription_plan",
        entity_id=plan.id,
        description=f"Updated {plan.name} subscription plan pricing and limits",
        metadata={
            "key": plan.key,
            "monthly_price": plan.monthly_price,
            "annual_price": plan.annual_price,
            "max_team_members": plan.max_team_members,
            "max_products": plan.max_products,
            "max_monthly_orders": plan.max_monthly_orders,
            "is_active": plan.is_active,
            "display_order": plan.display_order,
        },
    )
    return {
        "key": plan.key,
        "name": plan.name,
        "description": plan.description,
        "monthly_price": plan.monthly_price,
        "annual_price": plan.annual_price,
        "currency": plan.currency,
        "max_team_members": plan.max_team_members,
        "max_products": plan.max_products,
        "max_monthly_orders": plan.max_monthly_orders,
        "is_active": plan.is_active,
        "display_order": plan.display_order,
    }
