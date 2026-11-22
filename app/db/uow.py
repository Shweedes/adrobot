"""Единица работы: репозитории на одной сессии и явное управление транзакцией."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories import ActionLogRepository, CampaignRepository


class UnitOfWork:
    """Скрывает сессию SQLAlchemy от сервисов."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self.campaigns = CampaignRepository(session)
        self.audit = ActionLogRepository(session)

    async def commit(self) -> None:
        """Сохраняет изменения."""
        await self._session.commit()

    async def rollback(self) -> None:
        """Отменяет несохранённые изменения."""
        await self._session.rollback()
