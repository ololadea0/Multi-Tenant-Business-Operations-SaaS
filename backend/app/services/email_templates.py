from __future__ import annotations

from html import escape
import re

from jinja2 import Environment, select_autoescape

from app.core.config import settings


EMAIL_TEMPLATES = {
    "welcome": {
        "subject": "Welcome to Daymark, {{ first_name }}",
        "body": "<p>Hello {{ first_name }},</p><p>Welcome to Daymark. Your workspace is ready for launch and your team can get started right away.</p><p>Need help? Reach us at {{ support_email }}.</p>",
    },
    "announcement": {
        "subject": "{{ subject_prefix }}",
        "body": "<p>Hello {{ first_name }},</p><p>{{ announcement_message }}</p><p>Thanks for being part of the Daymark community.</p>",
    },
    "billing": {
        "subject": "Your billing update from Daymark",
        "body": "<p>Hello {{ first_name }},</p><p>Your billing status has been updated to {{ billing_status }}.</p><p>For support, contact {{ support_email }}.</p>",
    },
}

_ENV = Environment(autoescape=select_autoescape(["html", "xml"]), trim_blocks=True, lstrip_blocks=True)


def _text_from_html(value: str) -> str:
    value = re.sub(r"<\s*br\s*/?>", "\n", value, flags=re.I)
    value = re.sub(r"</p\s*>", "\n\n", value, flags=re.I)
    value = re.sub(r"<[^>]+>", "", value)
    return escape(value).strip()


def render_branded_email(*, title: str, subject: str, content_html: str, content_text: str | None = None) -> tuple[str, str, str]:
    """Render the shared Daymark email shell for every transactional email."""
    logo = (
        f'<img src="{escape(settings.EMAIL_LOGO_URL, quote=True)}" alt="Daymark" '
        'style="display:block;max-width:160px;max-height:48px;width:auto;height:auto">'
        if settings.EMAIL_LOGO_URL
        else '<span style="font-size:26px;font-weight:800;letter-spacing:-0.03em;color:#fffaf4">Daymark</span>'
    )
    html = _ENV.from_string("""<!doctype html><html><body style="margin:0;background:#efeae4;color:#17211e;font-family:Arial,sans-serif;line-height:1.6">
<div style="padding:36px 16px">
  <div style="max-width:700px;margin:0 auto;background:#fffdf9;border:1px solid rgba(23,33,30,.08);border-radius:24px;overflow:hidden;box-shadow:0 24px 50px rgba(23,33,30,.08)">
    <div style="background:linear-gradient(135deg, #17211e 0%, #17211e 72%, #ff5c35 72%, #ff5c35 100%);padding:20px 28px 22px;color:#fffaf4">
      <div style="display:flex;align-items:center;justify-content:space-between;gap:16px">
        <div style="display:flex;align-items:center;gap:12px;font-weight:800;font-size:22px;letter-spacing:-0.06em">{{ logo|safe }}</div>
        <div style="font-size:10px;letter-spacing:.18em;font-weight:700;text-transform:uppercase;border:1px solid rgba(255,255,255,.15);border-radius:999px;padding:8px 10px;background:rgba(255,255,255,.08)">DAYMARK</div>
      </div>
    </div>
    <main style="padding:28px 28px 0">
      <div style="margin:0 0 12px;color:#697772;font-size:11px;letter-spacing:.16em;text-transform:uppercase;font-weight:700">DAYMARK</div>
      <h1 style="margin:0 0 18px;font-size:36px;line-height:1.06;letter-spacing:-0.07em;font-weight:600;color:#17211e">{{ title }}</h1>
      <div style="padding:0 0 10px">{{ content|safe }}</div>
    </main>
    <div style="padding:18px 28px 0">
      <div style="margin:0;color:#69736d;font-size:13px;line-height:1.7">Need help? <a href="mailto:{{ support }}" style="color:#17211e;font-weight:700">{{ support }}</a></div>
    </div>
    <footer style="padding:18px 28px 24px;border-top:1px solid #ece4db;color:#61716b;font-size:12px;line-height:1.8;background:#fffdf9">© Daymark · This is an automated message from Daymark.{% if website %} <a href="{{ website }}" style="color:#17211e; font-weight:700">Website</a>{% endif %}{% if privacy %} · <a href="{{ privacy }}" style="color:#17211e; font-weight:700">Privacy</a>{% endif %}{% if terms %} · <a href="{{ terms }}" style="color:#17211e; font-weight:700">Terms</a>{% endif %}</footer>
  </div>
</div>
</body></html>""").render(logo=logo, title=title, content=content_html, support=settings.EMAIL_SUPPORT_EMAIL, website=settings.WEBSITE_URL, privacy=settings.PRIVACY_POLICY_URL, terms=settings.TERMS_URL)
    return subject, html, content_text or _text_from_html(content_html)


def render_email_template(template_key: str, *, subject: str | None = None, variables: dict | None = None, is_promotional: bool = False) -> tuple[str, str, str]:
    template = EMAIL_TEMPLATES.get(template_key, EMAIL_TEMPLATES["announcement"])
    env = _ENV
    context = {
        "first_name": "there",
        "support_email": settings.EMAIL_SUPPORT_EMAIL,
        "subject_prefix": "Daymark update",
        "announcement_message": "We've shipped a new update to help your operations run more smoothly.",
        "billing_status": "active",
        **(variables or {}),
    }
    subject_text = subject or template["subject"]
    rendered_subject = env.from_string(subject_text).render(**context)
    rendered_html = env.from_string(template["body"]).render(**context)
    sanitized_html = rendered_html
    if is_promotional:
        sanitized_html = (
            '<div style="background:#fffaf5;padding:20px;border:1px solid #ffe3d3;border-radius:12px;">'
            f"{sanitized_html}</div>"
        )
    return render_branded_email(title=rendered_subject, subject=rendered_subject, content_html=sanitized_html)
