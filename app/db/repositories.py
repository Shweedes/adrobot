"""Репозитории локальной БД."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ActionLog, AuditAction, CampaignRecord


class CampaignRepository:
    """Реестр созданных кампаний."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def name_exists(self, name: str) -> bool:
        """Есть ли уже кампания с таким названием."""
        stmt = select(func.count()).select_from(CampaignRecord).where(CampaignRecord.name == name)
        return (await self._session.scalar(stmt) or 0) > 0

    def add(self, **fields) -> CampaignRecord:
        """Добавляет запись в сессию; сохранение — через `UnitOfWork.commit`."""
        record = CampaignRecord(**fields)
        self._session.add(record)
        return record


class ActionLogRepository:
    """Журнал действий."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, action: AuditAction, campaign_id: int, details: dict | None = None) -> None:
        """Добавляет запись в сессию; сохранение — через `UnitOfWork.commit`."""
        self._session.add(
            ActionLog(action=action.value, keitaro_campaign_id=campaign_id, details=details or {})
        )
