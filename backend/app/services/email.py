import resend

from app.core.config import settings


resend.api_key = settings.RESEND_API_KEY


def send_password_reset_email(
    recipient: str,
    reset_url: str
) -> None:
    resend.Emails.send({
        "from": settings.EMAIL_FROM,
        "to": [recipient],
        "subject": "Reset your password",
        "html": f"""
            <h2>Password Reset</h2>

            <p>
                We received a request to reset your password.
            </p>

            <p>
                Click the link below to choose a new password:
            </p>

            <p>
                <a href="{reset_url}">
                    Reset Password
                </a>
            </p>

            <p>
                This link will expire in 30 minutes.
            </p>

            <p>
                If you did not request this, you can safely ignore this email.
            </p>
        """
    })