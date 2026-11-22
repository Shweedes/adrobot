"""Контракт внешней системы: сервисы зависят от него, а не от конкретного клиента."""

from datetime import date
from typing import Protocol

from app.keitaro.models import (
    Campaign,
    Domain,
    Group,
    Offer,
    StatsReport,
    Stream,
    TrafficSource,
)


class KeitaroPort(Protocol):
    """Операции Keitaro Admin API, нужные сервисам."""

    async def list_domains(self) -> list[Domain]:
        """Список доменов."""

    async def list_groups(self, group_type: str = "campaigns") -> list[Group]:
        """Список групп заданного типа."""

    async def list_traffic_sources(self) -> list[TrafficSource]:
        """Список источников трафика."""

    async def list_offers(self) -> list[Offer]:
        """Список офферов."""

    async def list_campaigns(self) -> list[Campaign]:
        """Список кампаний."""

    async def get_campaign(self, campaign_id: int) -> Campaign:
        """Кампания по ID."""

    async def create_campaign(self, payload: dict) -> Campaign:
        """Создаёт кампанию."""

    async def delete_campaign(self, campaign_id: int) -> None:
        """Удаляет кампанию."""

    async def list_streams(self, campaign_id: int) -> list[Stream]:
        """Потоки кампании."""

    async def create_stream(self, payload: dict) -> Stream:
        """Создаёт поток."""

    async def update_stream(self, stream_id: int, payload: dict) -> Stream:
        """Обновляет поля потока."""

    async def stream_stats(
        self, campaign_id: int, date_from: date, date_to: date, timezone: str
    ) -> StatsReport:
        """Статистика кампании по потокам и итого за период."""
