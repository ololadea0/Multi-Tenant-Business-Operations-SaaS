import logging
from urllib.parse import quote
import resend
from app.core.config import settings

logger = logging.getLogger(__name__)
resend.api_key = settings.RESEND_API_KEY

def _layout(title: str, body: str) -> str:
    brand = f'<img src="{settings.EMAIL_LOGO_URL}" alt="Daymark" style="max-width:160px;max-height:48px">' if settings.EMAIL_LOGO_URL else '<div style="font-size:24px;font-weight:700;color:#ff5c35">Daymark</div>'
    return f'''<div style="max-width:600px;margin:32px auto;padding:32px;background:#fff;color:#17211e;font-family:Arial,sans-serif;border:1px solid #e4e8df;border-radius:12px">{brand}<hr style="border:0;border-top:1px solid #e4e8df;margin:24px 0"><h1 style="font-size:28px">{title}</h1>{body}<p style="color:#69736d;font-size:12px;margin-top:28px">Need help? {settings.EMAIL_SUPPORT_EMAIL}</p></div>'''

def _send(recipient: str, subject: str, title: str, body: str, text: str) -> bool:
    try:
        resend.Emails.send({"from": settings.EMAIL_FROM, "to": [recipient], "subject": subject, "html": _layout(title, body), "text": text})
        return True
    except Exception:
        logger.exception("Transactional email delivery failed")
        return False

def send_verification_email(recipient: str, name: str, token: str) -> bool:
    url = f"{settings.FRONTEND_URL.rstrip('/')}/verify-email?token={quote(token)}"
    return _send(recipient, "Verify your Daymark email", "Verify your email", f"<p>Hi {name}, confirm your email to start using Daymark.</p><p><a href=\"{url}\">Verify email</a></p><p>This link expires in 30 minutes and can only be used once.</p>", f"Verify your Daymark email: {url}")

def send_password_reset_email(recipient: str, reset_url: str) -> bool:
    return _send(recipient, "Reset your Daymark password", "Reset your password", f"<p><a href=\"{reset_url}\">Reset password</a></p><p>This link expires in 30 minutes.</p>", f"Reset your Daymark password: {reset_url}")

def send_organization_invitation_email(recipient: str, organization_name: str, inviter_name: str, role: str, invitation_url: str, expires_at=None) -> bool:
    expiry = expires_at.strftime("%d %B %Y at %H:%M UTC") if expires_at else "7 days after this email is sent"
    body = f"<p><strong>{inviter_name}</strong> invited you to join <strong>{organization_name}</strong> as a <strong>{role}</strong>.</p><p>This invitation expires on <strong>{expiry}</strong>.</p><p><a href=\"{invitation_url}\" style=\"display:inline-block;padding:13px 20px;background:#ff5c35;color:#fff;text-decoration:none;border-radius:6px;font-weight:700\">Accept invitation</a></p>"
    return _send(recipient, f"Invitation to join {organization_name}", f"You're invited to {organization_name}", body, f"{inviter_name} invited you to join {organization_name} as {role}. This invitation expires on {expiry}. Accept your invitation: {invitation_url}")
