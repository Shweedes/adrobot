"""Справочники Keitaro (офферы, домены, группы, источники) с коротким TTL-кэшем."""

import asyncio
import re
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from app.config import Settings
from app.errors import ConfigurationError, NotFoundError
from app.keitaro.models import Domain, Offer
from app.services.ports import KeitaroPort
from app.services.views import OfferView


def normalize_name(value: str) -> str:
    """Приводит имя к виду для сравнения: без схемы, слэшей и регистра."""
    return re.sub(r"^https?://", "", value.strip().lower()).strip("/")


def tracking_url(host: str | None, alias: str | None) -> str | None:
    """Ссылка кампании или `None`, если неизвестен хост или alias."""
    return f"https://{host}/{alias}" if host and alias else None


@dataclass(frozen=True)
class CampaignDefaults:
    """Домен, группа и источник, которые подставляются в новую кампанию."""

    domain: Domain
    group_id: int
    source_id: int


class CatalogService:
    """Читает справочники Keitaro и кэширует их на `cache_ttl_seconds`."""

    def __init__(self, client: KeitaroPort, settings: Settings) -> None:
        self._client = client
        self._settings = settings
        self._ttl = settings.cache_ttl_seconds
        self._store: dict[str, tuple[float, Any]] = {}
        self._lock = asyncio.Lock()

    async def _cached(self, key: str, loader: Callable[[], Awaitable[Any]]) -> Any:
        """Возвращает значение из кэша или загружает его через `loader`."""
        async with self._lock:
            hit = self._store.get(key)
            now = time.monotonic()
            if hit and now - hit[0] < self._ttl:
                return hit[1]
            value = await loader()
            self._store[key] = (now, value)
            return value

    async def offers(self) -> list[Offer]:
        """Все офферы."""
        return await self._cached("offers", self._client.list_offers)

    async def get_offer(self, offer_id: int) -> Offer:
        """Оффер по ID.

        Raises:
            NotFoundError: оффера нет в Keitaro.
        """
        for offer in await self.offers():
            if offer.id == offer_id:
                return offer
        raise NotFoundError(f"Оффер {offer_id} не найден в Keitaro")

    async def search_offers(self, query: str, limit: int = 20) -> list[OfferView]:
        """Ищет офферы: сначала точный ID, затем начало названия, затем вхождение."""
        q = query.strip().lower()
        pool = [o for o in await self.offers() if o.state != "deleted"]
        if q:
            ranked = [(r, o) for o in pool if (r := self._rank(o, q)) is not None]
            ranked.sort(key=lambda pair: pair[0])
            pool = [o for _, o in ranked]
        return [OfferView(id=o.id, name=o.name, state=o.state) for o in pool[:limit]]

    @staticmethod
    def _rank(offer: Offer, q: str) -> int | None:
        """Релевантность оффера запросу: меньше — лучше, `None` — не подходит."""
        name = offer.name.lower()
        if q == str(offer.id):
            return 0
        if name.startswith(q):
            return 1
        if q in name or str(offer.id).startswith(q):
            return 2
        return None

    async def domains(self) -> list[Domain]:
        """Все домены."""
        return await self._cached("domains", self._client.list_domains)

    async def host_for(self, domain_id: int | None) -> str | None:
        """Хост домена по ID или `None`."""
        if domain_id is None:
            return None
        for domain in await self.domains():
            if domain.id == domain_id:
                return normalize_name(domain.name)
        return None

    async def campaign_defaults(self) -> CampaignDefaults:
        """Находит домен, группу и источник, заданные в настройках.

        Raises:
            ConfigurationError: что-то не найдено; в сообщении перечислены все
                несовпадения и имена, которые есть в Keitaro.
        """
        domains, groups, sources = await asyncio.gather(
            self.domains(),
            self._cached("groups", self._client.list_groups),
            self._cached("sources", self._client.list_traffic_sources),
        )
        s = self._settings
        campaign_groups = [g for g in groups if g.type in (None, "campaigns", "campaign")]
        domain = self._find(domains, s.keitaro_domain)
        group = self._find(campaign_groups, s.keitaro_group)
        source = self._find(sources, s.keitaro_source)

        checks = (
            ("домен", "KEITARO_DOMAIN", s.keitaro_domain, domain, domains),
            ("группа кампаний", "KEITARO_GROUP", s.keitaro_group, group, campaign_groups),
            ("источник трафика", "KEITARO_SOURCE", s.keitaro_source, source, sources),
        )
        missing = [
            f"{label} «{wanted}» ({env}), в Keitaro есть: "
            f"{', '.join(i.name for i in items[:10]) or 'ничего'}"
            for label, env, wanted, found, items in checks
            if found is None
        ]
        if missing:
            raise ConfigurationError(
                "Не найдено в Keitaro: " + "; ".join(missing) + ". Исправьте значения в .env"
            )
        return CampaignDefaults(domain=domain, group_id=group.id, source_id=source.id)

    @staticmethod
    def _find(items: list, wanted: str):
        """Первый элемент с подходящим именем или `None`."""
        key = normalize_name(wanted)
        return next((item for item in items if normalize_name(item.name) == key), None)
