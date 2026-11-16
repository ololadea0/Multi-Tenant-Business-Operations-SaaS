from app.services.email_templates import render_branded_email


def test_render_branded_email_uses_premium_daymark_shell():
    _, html, _ = render_branded_email(
        title="Verify your email",
        subject="Verify your Daymark email",
        content_html="<p>Hi Ada,</p><p>Confirm your email address to get started.</p>",
    )

    assert "Verify your email" in html
    assert "Daymark" in html
    assert "ff5c35" in html
    assert "linear-gradient" in html
    assert "This is an automated message from Daymark." in html
