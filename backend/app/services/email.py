import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from html import escape
from urllib.parse import quote

import resend
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.core.config import settings
from app.services.email_templates import render_branded_email

try:
    WAT_TIMEZONE = ZoneInfo("Africa/Lagos")
except ZoneInfoNotFoundError:
    WAT_TIMEZONE = timezone(timedelta(hours=1))


def _wat_datetime(value: datetime | None = None) -> datetime:
    if value is None:
        value = datetime.now(timezone.utc)
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(WAT_TIMEZONE)

logger = logging.getLogger(__name__)
resend.api_key = settings.RESEND_API_KEY

def _send(recipient: str, subject: str, title: str, body: str, text: str) -> bool:
    if not settings.RESEND_API_KEY or not settings.EMAIL_FROM:
        logger.warning("Email delivery skipped because RESEND_API_KEY or EMAIL_FROM is not configured.")
        return True
    if recipient.lower().endswith("example.com"):
        logger.info("Email delivery skipped for example.com test recipient.")
        return True
    try:
        if body.lstrip().lower().startswith("<!doctype html>"):
            html, plaintext = body, text
        else:
            _, html, plaintext = render_branded_email(title=title, subject=subject, content_html=body, content_text=text)
        sender = f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM}>"
        resend.Emails.send({"from": sender, "to": [recipient], "subject": subject, "html": html, "text": plaintext})
        return True
    except Exception:
        logger.exception("Transactional email delivery failed")
        return False


def send_generic_email(recipient: str, subject: str, title: str, body: str, text: str) -> bool:
    return _send(recipient, subject, title, body, text)


def send_verification_email(recipient: str, name: str, token: str) -> bool:
    url = f"{settings.FRONTEND_URL.rstrip('/')}/verify-email?token={quote(token)}"
    return _send(recipient, "Verify your Daymark email", "Verify your email", f"<p>Hi {name},</p><p>Confirm your email address to start using Daymark.</p><p><a href=\"{url}\" style=\"display:inline-block;padding:12px 18px;background:#ff5c35;color:#fff;text-decoration:none;border-radius:6px;font-weight:700\">Verify email</a></p><p>This link expires in 30 minutes and can only be used once.</p>", f"Hi {name},\n\nConfirm your Daymark email: {url}\n\nThis link expires in 30 minutes and can only be used once.")

def send_password_reset_email(recipient: str, reset_url: str) -> bool:
    return _send(recipient, "Reset your Daymark password", "Reset your password", f"<p>We received a request to change your Daymark password.</p><p><a href=\"{reset_url}\" style=\"display:inline-block;padding:12px 18px;background:#ff5c35;color:#fff;text-decoration:none;border-radius:6px;font-weight:700\">Reset password</a></p><p>This link expires in 30 minutes. If you did not request this, you can ignore this email.</p>", f"We received a request to change your Daymark password.\n\nReset your password: {reset_url}\n\nThis link expires in 30 minutes.")

def send_organization_invitation_email(recipient: str, organization_name: str, inviter_name: str, role: str, invitation_url: str, expires_at=None) -> bool:
    expiry = expires_at.strftime("%d %B %Y at %H:%M UTC") if expires_at else "7 days after this email is sent"
    safe_org, safe_inviter, safe_role = escape(organization_name), escape(inviter_name), escape(role)
    safe_url = escape(invitation_url, quote=True)
    safe_expiry = escape(expiry)
    body = (
        "<div style=\"font-family:Arial,Helvetica,sans-serif;color:#17211e;line-height:1.7\">"
        f"<p style=\"margin:0 0 14px;font-size:16px;color:#2c3734\"><strong>{safe_inviter}</strong> invited you to join <strong>{safe_org}</strong> as a <strong>{safe_role}</strong>.</p>"
        f"<p style=\"margin:0 0 24px;font-size:16px;color:#4d5d59\">This invitation expires on <strong>{safe_expiry}</strong>.</p>"
        f"<p style=\"margin:0\"><a href=\"{safe_url}\" style=\"display:inline-block;padding:16px 28px;background:linear-gradient(180deg, #ff744d 0%, #ff5c35 100%);color:#fffaf4;text-decoration:none;border-radius:12px;font-weight:700;font-size:16px;border:1px solid #eb4f2f;box-shadow:0 12px 22px rgba(255,92,53,.18)\">Accept invitation</a></p>"
        "</div>"
    )
    return _send(
        recipient,
        f"Invitation to join {organization_name}",
        f"You're invited to {organization_name}",
        body,
        f"{inviter_name} invited you to join {organization_name} as {role}. This invitation expires on {expiry}. Accept your invitation: {invitation_url}",
    )


def send_order_receipt_email(
    recipient: str,
    *,
    order_number: str,
    customer_name: str,
    organization_name: str,
    total_amount: Decimal | str,
    items: list[dict],
    order_date: datetime | None = None,
) -> bool:
    safe_customer = escape(customer_name or "Customer")
    safe_organization = escape(organization_name or "Daymark")
    safe_order_number = escape(order_number)
    safe_total = f"{Decimal(str(total_amount)):.2f}" if isinstance(total_amount, Decimal) else str(total_amount)
    order_date_text = _wat_datetime(order_date).strftime("%d %B %Y at %H:%M %Z")

    item_rows = "".join(
        (
            "<tr>"
            f"<td style=\"padding:12px 0;border-bottom:1px solid #ece4db;color:#17211e;font-size:14px;\">{escape(str(item.get('name','Product')))}</td>"
            f"<td style=\"padding:12px 0;border-bottom:1px solid #ece4db;color:#53615d;font-size:13px;text-align:center\">{item.get('quantity', 0)}</td>"
            f"<td style=\"padding:12px 0;border-bottom:1px solid #ece4db;color:#53615d;font-size:13px;text-align:right\">{float(item.get('unit_price', 0)):.2f}</td>"
            f"<td style=\"padding:12px 0;border-bottom:1px solid #ece4db;color:#17211e;font-size:13px;text-align:right;font-weight:700\">{float(item.get('subtotal', 0)):.2f}</td>"
            "</tr>"
        )
        for item in items
    ) or '<tr><td colspan="4" style="padding:12px 0;color:#67736f;font-size:13px;">No items recorded.</td></tr>'

    body = (
        "<div style=\"font-family:Arial,Helvetica,sans-serif;color:#17211e;line-height:1.7\">"
        f"<p style=\"margin:0 0 14px;font-size:16px;color:#2c3734\">Hi <strong>{safe_customer}</strong>,</p>"
        f"<p style=\"margin:0 0 20px;font-size:16px;color:#4d5d59\">Your receipt for <strong>{safe_organization}</strong> is ready.</p>"
        f"<p style=\"margin:0 0 20px;color:#4d5d59\">Order <strong>{safe_order_number}</strong> was completed on <strong>{escape(order_date_text)}</strong>.</p>"
        "<table style=\"width:100%;border-collapse:collapse;margin:0 0 18px;\">"
        "<thead><tr><th style=\"padding:12px 0;border-bottom:1px solid #ece4db;color:#697772;font-size:11px;letter-spacing:.12em;text-transform:uppercase;text-align:left\">Item</th>"
        "<th style=\"padding:12px 0;border-bottom:1px solid #ece4db;color:#697772;font-size:11px;letter-spacing:.12em;text-transform:uppercase;text-align:center\">Qty</th>"
        "<th style=\"padding:12px 0;border-bottom:1px solid #ece4db;color:#697772;font-size:11px;letter-spacing:.12em;text-transform:uppercase;text-align:right\">Unit price</th>"
        "<th style=\"padding:12px 0;border-bottom:1px solid #ece4db;color:#697772;font-size:11px;letter-spacing:.12em;text-transform:uppercase;text-align:right\">Total</th></tr></thead>"
        f"<tbody>{item_rows}</tbody>"
        "</table>"
        f"<p style=\"margin:0 0 10px;padding-top:10px;border-top:1px solid #ece4db;text-align:right;font-size:16px;color:#17211e\"><strong>Total: {safe_total}</strong></p>"
        "<p style=\"margin:0;color:#53615d\">Thank you for shopping with Daymark. This receipt is shared digitally and can be forwarded or saved for your records.</p>"
        "</div>"
    )
    text = (
        f"Hi {customer_name},\n\nYour receipt for {organization_name} is ready.\n"
        f"Order {order_number} was completed on {order_date_text}.\n\n"
        + "\n".join(
            f"- {item.get('name', 'Product')}: {item.get('quantity', 0)} x {item.get('unit_price', 0)} = {item.get('subtotal', 0)}"
            for item in items
        )
        + f"\n\nTotal: {safe_total}\n\nThank you for shopping with Daymark."
    )
    return _send(
        recipient,
        f"Your receipt for {order_number}",
        f"Receipt #{order_number}",
        body,
        text,
    )

