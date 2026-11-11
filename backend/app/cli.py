import argparse
import sys


def _ensure_backend_environment() -> None:
    try:
        import fastapi  # noqa: F401
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "Daymark backend dependencies are not installed in this Python environment.\n"
            "Use the project virtualenv instead:\n"
            "  backend\\venv\\Scripts\\python.exe -m app.cli create-super-admin --email admin@daymark.app --password 'StrongPassword123!' --full-name 'Platform Admin'"
        ) from exc


_ensure_backend_environment()

from sqlalchemy import text

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.user import PlatformRole, User


def ensure_platform_role_column() -> None:
    db = SessionLocal()
    try:
        has_column = db.execute(
            text(
                "SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'platform_role'"
            )
        ).first()
        if has_column is None:
            db.execute(
                text(
                    "ALTER TABLE users ADD COLUMN platform_role VARCHAR(20) NOT NULL DEFAULT 'user'"
                )
            )
            db.commit()
    finally:
        db.close()


def bootstrap_super_admin(email: str, password: str, full_name: str) -> dict:
    ensure_platform_role_column()
    db = SessionLocal()
    try:
        if db.query(User).filter(User.platform_role == PlatformRole.SUPER_ADMIN).first():
            raise RuntimeError("A platform super admin already exists.")

        normalized_email = email.strip().lower()
        normalized_name = " ".join(full_name.strip().split())
        if not normalized_name:
            raise ValueError("Full name cannot be blank.")

        existing_user = db.query(User).filter(User.email == normalized_email).first()
        if existing_user:
            existing_user.full_name = normalized_name
            existing_user.password_hash = hash_password(password)
            existing_user.platform_role = PlatformRole.SUPER_ADMIN
            existing_user.is_active = True
            existing_user.is_email_verified = True
            db.commit()
            db.refresh(existing_user)
            return {
                "id": existing_user.id,
                "email": existing_user.email,
                "full_name": existing_user.full_name,
                "platform_role": existing_user.platform_role.value,
            }

        user = User(
            email=normalized_email,
            full_name=normalized_name,
            password_hash=hash_password(password),
            platform_role=PlatformRole.SUPER_ADMIN,
            is_active=True,
            is_email_verified=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "platform_role": user.platform_role.value,
        }
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Daymark platform bootstrap")
    parser.add_argument(
        "command",
        nargs="?",
        choices=["create-super-admin"],
        help="Create the one-time platform super admin account.",
    )
    parser.add_argument("--email", help="Super admin email address")
    parser.add_argument("--password", help="Super admin password")
    parser.add_argument("--full-name", help="Super admin full name")
    args = parser.parse_args()

    command = args.command or "create-super-admin"
    email = args.email
    password = args.password
    full_name = args.full_name

    if command == "create-super-admin":
        if not email or not password or not full_name:
            parser.error(
                "create-super-admin requires --email, --password and --full-name"
            )

        try:
            result = bootstrap_super_admin(email, password, full_name)
            print(f"Bootstrapped super admin: {result['email']} ({result['platform_role']})")
        except Exception as exc:
            raise SystemExit(str(exc))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
