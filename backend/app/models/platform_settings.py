from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PlatformSettings(Base):
    __tablename__ = "platform_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    trial_duration_days: Mapped[int] = mapped_column(Integer, default=14)
    annual_billing_discount_percent: Mapped[int] = mapped_column(Integer, default=15)
    payment_grace_period_days: Mapped[int] = mapped_column(Integer, default=3)
    support_email: Mapped[str] = mapped_column(String(255), default="support@daymark.app")
    support_phone: Mapped[str] = mapped_column(String(255), default="+234 800 000 0000")
    help_center_url: Mapped[str] = mapped_column(String(255), default="https://help.daymark.app")
    allow_new_registrations: Mapped[bool] = mapped_column(Boolean, default=True)
    maintenance_notice_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    maintenance_message: Mapped[str] = mapped_column(Text, default="Scheduled maintenance is in progress. Please check back shortly.")
    maintenance_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
