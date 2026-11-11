from __future__ import annotations

from html import escape

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


def render_email_template(template_key: str, *, subject: str | None = None, variables: dict | None = None, is_promotional: bool = False) -> tuple[str, str, str]:
    template = EMAIL_TEMPLATES.get(template_key, EMAIL_TEMPLATES["announcement"])
    env = Environment(autoescape=select_autoescape(["html", "xml"]), trim_blocks=True, lstrip_blocks=True)
    context = {
        "first_name": "there",
        "support_email": settings.EMAIL_SUPPORT_EMAIL,
        "subject_prefix": "Daymark update",
        "announcement_message": "We’ve shipped a new update to help your operations run more smoothly.",
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
    brand = (
        f'<div style="font-family:Arial,sans-serif;color:#111917;max-width:640px;margin:0 auto;padding:24px;">'
        f'<div style="font-size:28px;font-weight:800;color:#ff5c35;margin-bottom:18px;">Daymark</div>'
        f'<div style="border:1px solid #e9ece8;border-radius:16px;padding:24px;background:#ffffff;">{sanitized_html}</div>'
        f'<p style="margin-top:20px;color:#56615d;font-size:12px;">Need help? {settings.EMAIL_SUPPORT_EMAIL}</p>'
        f'</div>'
    )
    text_body = rendered_html.replace("<p>", "\n").replace("</p>", "\n").replace("<br>", "\n")
    text_body = escape(text_body)
    return rendered_subject, brand, text_body
