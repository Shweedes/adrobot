"""Типизированные ответы Keitaro; неизвестные поля игнорируются."""

from dataclasses import dataclass
from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator

OFFER_SCHEMAS = frozenset({"landings", "offers"})
"""Значения `schema`, при которых поток раздаёт трафик офферам."""


class _KeitaroModel(BaseModel):
    """Базовая модель ответа: устойчива к новым полям API."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)


class Offer(_KeitaroModel):
    """Оффер."""

    id: int
    name: str
    state: str | None = None


class Campaign(_KeitaroModel):
    """Кампания."""

    id: int
    name: str
    alias: str | None = None
    state: str | None = None
    domain_id: int | None = None


class Domain(_KeitaroModel):
    """Домен трекера."""

    id: int
    name: str


class Group(_KeitaroModel):
    """Группа кампаний, офферов или лендингов."""

    id: int
    name: str
    type: str | None = None


class TrafficSource(_KeitaroModel):
    """Источник трафика."""

    id: int
    name: str


class StreamFilter(_KeitaroModel):
    """Фильтр потока."""

    name: str
    mode: str = "accept"
    payload: Any = None

    def values(self) -> list[str]:
        """Значения фильтра списком строк."""
        if self.payload is None:
            return []
        if isinstance(self.payload, list):
            return [str(v) for v in self.payload]
        return [str(self.payload)]


class StreamOffer(_KeitaroModel):
    """Оффер внутри потока и его доля трафика."""

    offer_id: int
    share: int = 0
    state: str | None = "active"


class Stream(_KeitaroModel):
    """Поток кампании."""

    id: int
    campaign_id: int | None = None
    name: str | None = None
    position: int | None = 0
    schema_name: str | None = Field(default=None, alias="schema")
    action_type: str | None = None
    action_payload: str | None = None
    state: str | None = "active"
    filters: list[StreamFilter] = Field(default_factory=list)
    offers: list[StreamOffer] = Field(default_factory=list)

    @field_validator("filters", "offers", mode="before")
    @classmethod
    def _none_to_list(cls, value: Any) -> Any:
        """Keitaro иногда отдаёт `null` вместо пустого списка."""
        return value or []

    @property
    def has_offers(self) -> bool:
        """Поток раздаёт трафик офферам."""
        return bool(self.offers) or self.schema_name in OFFER_SCHEMAS


@dataclass(frozen=True)
class Stats:
    """Клики, уникальные клики и боты."""

    clicks: int = 0
    unique: int = 0
    bots: int = 0

    @classmethod
    def from_row(cls, row: dict) -> Self:
        """Создаёт статистику из строки отчёта Keitaro."""

        def num(key: str) -> int:
            try:
                return int(float(row.get(key) or 0))
            except (TypeError, ValueError):
                return 0

        return cls(clicks=num("clicks"), unique=num("campaign_unique_clicks"), bots=num("bots"))


@dataclass(frozen=True)
class StatsReport:
    """Статистика кампании по потокам и итого."""

    per_stream: dict[int, Stats]
    total: Stats
