from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    TEST_DATABASE_URL: str | None = None
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 30
    COOKIE_SECURE: bool = False
    CORS_ALLOW_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    AUTH_REGISTER_RATE_LIMIT: int = 20
    AUTH_LOGIN_RATE_LIMIT: int = 10
    AUTH_PASSWORD_RESET_RATE_LIMIT: int = 10
    AUTH_LOGOUT_RATE_LIMIT: int = 20
    EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES: int = 30
    EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES: int = 30
    AUTH_RESEND_VERIFICATION_RATE_LIMIT: int = 5

    RESEND_API_KEY: str
    EMAIL_FROM: str
    EMAIL_FROM_NAME: str = "Daymark"
    EMAIL_SUPPORT_EMAIL: str = "support@daymark.app"
    EMAIL_LOGO_URL: str = ""
    FRONTEND_URL: str
    WEBSITE_URL: str = ""
    PRIVACY_POLICY_URL: str = ""
    TERMS_URL: str = ""

    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str
    PAYSTACK_SECRET_KEY: str = ""
    PAYSTACK_WEBHOOK_SECRET: str = ""
    BILLING_TRIAL_DAYS: int = 14
    BILLING_GRACE_PERIOD_DAYS: int = 7

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()  # pyright: ignore[reportCallIssue]
