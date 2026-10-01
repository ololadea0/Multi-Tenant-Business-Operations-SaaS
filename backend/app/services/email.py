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

def send_organization_invitation_email(
    recipient: str,
    organization_name: str,
    inviter_name: str,
    role: str,
    invitation_url: str
) -> None:
    resend.Emails.send({
        "from": settings.EMAIL_FROM,
        "to": [recipient],
        "subject": f"Invitation to join {organization_name}",
        "html": f"""
            <h2>You're invited to join {organization_name}</h2>

            <p>
                {inviter_name} has invited you to join
                <strong>{organization_name}</strong>
                as a <strong>{role}</strong>.
            </p>

            <p>
                <a href="{invitation_url}">
                    Accept Invitation
                </a>
            </p>

            <p>
                This invitation will expire in 7 days.
            </p>

            <p>
                If you were not expecting this invitation,
                you can safely ignore this email.
            </p>
        """
    })