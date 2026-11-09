import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta
from urllib.parse import urljoin
import requests
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.api.organization import get_user_membership, require_roles
from app.api.dependencies import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.billing import BillingInterval, OrganizationSubscription, PaymentStatus, PaymentTransaction, PaymentWebhookEvent, SubscriptionPlan, SubscriptionStatus
from app.models.membership import Membership, MembershipRole
from app.models.user import User
from app.schemas.billing import PlanResponse, StartSubscriptionRequest, VerifyPaymentRequest
from app.services.billing import ensure_plans, get_or_create_trial, usage

router = APIRouter(tags=["Billing"])


@router.get("/api/billing/plans", response_model=list[PlanResponse])
def list_plans(db: Session = Depends(get_db)):
    ensure_plans(db)
    return db.query(SubscriptionPlan).filter(SubscriptionPlan.is_active.is_(True)).order_by(SubscriptionPlan.display_order).all()


def subscription_payload(db, subscription):
    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == subscription.plan_id).one()
    return {"id": subscription.id, "status": subscription.status, "billing_interval": subscription.billing_interval, "start_date": subscription.start_date, "current_period_start": subscription.current_period_start, "current_period_end": subscription.current_period_end, "trial_end": subscription.trial_end, "cancellation_date": subscription.cancellation_date, "plan": PlanResponse.model_validate(plan).model_dump(), "usage": usage(db, subscription.organization_id, subscription.current_period_start)}


@router.get("/api/organizations/{organization_id}/billing", response_model=dict)
def get_billing(organization_id: int, membership: Membership = Depends(get_user_membership), db: Session = Depends(get_db)):
    return subscription_payload(db, get_or_create_trial(db, organization_id))


@router.get("/api/organizations/{organization_id}/billing/history")
def billing_history(organization_id: int, membership: Membership = Depends(get_user_membership), db: Session = Depends(get_db)):
    return db.query(PaymentTransaction).filter(PaymentTransaction.organization_id == organization_id).order_by(PaymentTransaction.created_at.desc()).all()


@router.post("/api/organizations/{organization_id}/billing/checkout")
def initialize_checkout(organization_id: int, data: StartSubscriptionRequest, membership: Membership = Depends(require_roles(MembershipRole.OWNER, MembershipRole.ADMIN)), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not settings.PAYSTACK_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Payment provider is not configured")
    ensure_plans(db)
    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.key == data.plan_key, SubscriptionPlan.is_active.is_(True)).first()
    if not plan: raise HTTPException(status_code=404, detail="Subscription plan not found")
    subscription = get_or_create_trial(db, organization_id)
    interval = BillingInterval(data.interval)
    amount = plan.monthly_price if interval == BillingInterval.MONTHLY else plan.annual_price
    reference = f"daymark_{organization_id}_{secrets.token_urlsafe(16)}"
    transaction = PaymentTransaction(organization_id=organization_id, subscription_id=subscription.id, plan_id=plan.id, reference=reference, amount=amount, currency=plan.currency, interval=interval, status=PaymentStatus.INITIALIZED)
    db.add(transaction); db.commit()
    response = requests.post("https://api.paystack.co/transaction/initialize", headers={"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}", "Content-Type": "application/json"}, json={"email": current_user.email if current_user else "", "amount": amount * 100, "currency": plan.currency, "reference": reference, "callback_url": f"{settings.FRONTEND_URL.rstrip('/')}/app/{organization_id}/settings/billing/payment-return"}, timeout=15)
    if response.status_code >= 400: transaction.status = PaymentStatus.FAILED; db.commit(); raise HTTPException(status_code=502, detail="Unable to initialize payment")
    return response.json().get("data", {})


@router.post("/api/organizations/{organization_id}/billing/verify")
def verify_payment(organization_id: int, data: VerifyPaymentRequest, membership: Membership = Depends(require_roles(MembershipRole.OWNER, MembershipRole.ADMIN)), db: Session = Depends(get_db)):
    transaction = db.query(PaymentTransaction).filter(PaymentTransaction.organization_id == organization_id, PaymentTransaction.reference == data.reference).first()
    if not transaction: raise HTTPException(status_code=404, detail="Payment transaction not found")
    if not settings.PAYSTACK_SECRET_KEY: raise HTTPException(status_code=503, detail="Payment provider is not configured")
    result = requests.get(f"https://api.paystack.co/transaction/verify/{transaction.reference}", headers={"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}, timeout=15).json()
    details = result.get("data", {})
    expected = transaction.amount * 100
    if not result.get("status") or details.get("status") != "success" or details.get("amount") != expected or details.get("currency") != transaction.currency or details.get("reference") != transaction.reference:
        transaction.status = PaymentStatus.FAILED; db.commit(); raise HTTPException(status_code=400, detail="Payment could not be verified")
    activate_transaction(db, transaction, details)
    return subscription_payload(db, db.query(OrganizationSubscription).filter(OrganizationSubscription.id == transaction.subscription_id).one())


@router.post("/api/organizations/{organization_id}/billing/cancel")
def cancel_subscription(organization_id: int, membership: Membership = Depends(require_roles(MembershipRole.OWNER, MembershipRole.ADMIN)), db: Session = Depends(get_db)):
    subscription = get_or_create_trial(db, organization_id)
    if subscription.status in {SubscriptionStatus.CANCELLED, SubscriptionStatus.EXPIRED}:
        return subscription_payload(db, subscription)
    subscription.status = SubscriptionStatus.CANCELLED
    subscription.cancellation_date = datetime.utcnow()
    db.commit()
    return subscription_payload(db, subscription)


def activate_transaction(db, transaction, details):
    if transaction.status == PaymentStatus.SUCCESS: return
    subscription = db.query(OrganizationSubscription).filter(OrganizationSubscription.id == transaction.subscription_id).one()
    now = datetime.utcnow(); duration = 365 if transaction.interval == BillingInterval.ANNUAL else 30
    transaction.status = PaymentStatus.SUCCESS; transaction.provider_transaction_id = str(details.get("id")); transaction.provider_response = details
    subscription.plan_id = transaction.plan_id; subscription.billing_interval = transaction.interval; subscription.status = SubscriptionStatus.ACTIVE; subscription.payment_provider = "paystack"; subscription.trial_end = None; subscription.current_period_start = now; subscription.current_period_end = now + timedelta(days=duration)
    db.commit()


@router.post("/api/payments/paystack/webhook")
async def paystack_webhook(request: Request, db: Session = Depends(get_db), paystack_signature: str | None = Header(default=None, alias="Paystack-Signature"), legacy_signature: str | None = Header(default=None, alias="x-paystack-signature")):
    body = await request.body(); signature = paystack_signature or legacy_signature
    if not settings.PAYSTACK_WEBHOOK_SECRET and not settings.PAYSTACK_SECRET_KEY: raise HTTPException(status_code=503, detail="Webhook verification is not configured")
    secret = settings.PAYSTACK_WEBHOOK_SECRET or settings.PAYSTACK_SECRET_KEY
    valid = False
    if paystack_signature and paystack_signature.startswith("t="):
        parts = dict(part.split("=", 1) for part in paystack_signature.split(",") if "=" in part); timestamp = parts.get("t")
        if timestamp and abs(datetime.utcnow().timestamp() - int(timestamp)) <= 300:
            digest = hmac.new(secret.encode(), f"{timestamp}.".encode() + body, hashlib.sha512).hexdigest(); valid = hmac.compare_digest(digest, parts.get("v1", "").split(":", 1)[-1])
    elif signature: valid = hmac.compare_digest(hmac.new(secret.encode(), body, hashlib.sha512).hexdigest(), signature)
    if not valid: raise HTTPException(status_code=401, detail="Invalid Paystack signature")
    event = json.loads(body); event_id = str(event.get("data", {}).get("id") or event.get("data", {}).get("reference") or hashlib.sha256(body).hexdigest())
    if db.query(PaymentWebhookEvent).filter(PaymentWebhookEvent.provider_event_id == event_id).first(): return {"received": True, "duplicate": True}
    record = PaymentWebhookEvent(provider_event_id=event_id, event_type=event.get("event", ""), payload=event); db.add(record); db.flush()
    if event.get("event") == "charge.success":
        reference = event.get("data", {}).get("reference"); transaction = db.query(PaymentTransaction).filter(PaymentTransaction.reference == reference).first()
        if transaction: activate_transaction(db, transaction, event["data"])
    record.processed_at = datetime.utcnow(); db.commit(); return {"received": True}
