"""ORM-модели локальной БД."""

from datetime import datetime
from enum import StrEnum

from sqlalchemy import JSON, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AuditAction(StrEnum):
    """Типы записей журнала действий."""

    CAMPAIGN_CREATED = "campaign_created"
    OFFER_ADDED = "offer_added"
    OFFER_REMOVED = "offer_removed"


class CampaignRecord(Base):
    """Кампания, созданная через приложение; источник правды — Keitaro."""

    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(primary_key=True)
    keitaro_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    geo: Mapped[str] = mapped_column(String(64))
    offer_id: Mapped[int] = mapped_column(Integer)
    alias: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ActionLog(Base):
    """Запись журнала: что и когда изменили через приложение."""

    __tablename__ = "action_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    action: Mapped[str] = mapped_column(String(32), index=True)
    keitaro_campaign_id: Mapped[int] = mapped_column(Integer, index=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
