"""Модели результатов сервисов; они же схемы ответов API."""

from datetime import date
from typing import Literal

from pydantic import BaseModel

from app.domain.ranges import RangeKey


class OfferView(BaseModel):
    """Оффер."""

    id: int
    name: str
    state: str | None = None


class CampaignSummary(BaseModel):
    """Кампания в списках и заголовке редактора."""

    id: int
    name: str
    state: str | None = None
    alias: str | None = None
    tracking_url: str | None = None


class CreatedCampaign(CampaignSummary):
    """Результат создания кампании."""

    geo: list[str]
    offer: OfferView


class StatsView(BaseModel):
    """Клики, уникальные клики и боты."""

    clicks: int = 0
    unique: int = 0
    bots: int = 0


class FilterView(BaseModel):
    """Фильтр потока."""

    name: str
    mode: str
    values: list[str]


class StreamOfferView(BaseModel):
    """Оффер в потоке и его доля трафика."""

    offer_id: int
    name: str
    share: int
    state: str | None = None


class StreamView(BaseModel):
    """Поток: фильтры, цель редиректа или офферы и статистика."""

    id: int
    name: str
    position: int
    enabled: bool
    kind: Literal["redirect", "offers"]
    target: str | None = None
    filters: list[FilterView]
    offers: list[StreamOfferView]
    stats: StatsView


class CampaignDetails(BaseModel):
    """Кампания с потоками и статистикой за период."""

    campaign: CampaignSummary
    streams: list[StreamView]
    totals: StatsView
    range: RangeKey
    date_from: date
    date_to: date
