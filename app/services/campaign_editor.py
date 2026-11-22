"""Сценарии редактора: просмотр кампаний, добавление и удаление офферов."""

import asyncio
from dataclasses import asdict

from app.config import Settings
from app.db.models import AuditAction
from app.db.uow import UnitOfWork
from app.domain.ranges import RangeKey, resolve_range
from app.domain.shares import split_evenly
from app.errors import ConflictError, ForbiddenError, NotFoundError
from app.keitaro import payloads
from app.keitaro.models import Campaign, Stats, Stream, StreamOffer
from app.services.catalog import CatalogService, tracking_url
from app.services.ports import KeitaroPort
from app.services.views import (
    CampaignDetails,
    CampaignSummary,
    FilterView,
    StatsView,
    StreamOfferView,
    StreamView,
)


def _stream_view(stream: Stream, offer_names: dict[int, str], stats: Stats) -> StreamView:
    """Собирает представление потока для интерфейса."""
    return StreamView(
        id=stream.id,
        name=stream.name or f"Поток {stream.id}",
        position=stream.position or 0,
        enabled=(stream.state or "active") == "active",
        kind="offers" if stream.has_offers else "redirect",
        target=None if stream.has_offers else (stream.action_payload or stream.action_type),
        filters=[FilterView(name=f.name, mode=f.mode, values=f.values()) for f in stream.filters],
        offers=[
            StreamOfferView(
                offer_id=o.offer_id,
                name=offer_names.get(o.offer_id, f"Оффер #{o.offer_id}"),
                share=o.share,
                state=o.state,
            )
            for o in stream.offers
        ],
        stats=StatsView(**asdict(stats)),
    )


class CampaignEditor:
    """Просмотр кампании со статистикой и правка офферов в её потоках."""

    def __init__(
        self,
        *,
        client: KeitaroPort,
        catalog: CatalogService,
        settings: Settings,
        uow: UnitOfWork,
    ) -> None:
        self._client = client
        self._catalog = catalog
        self._settings = settings
        self._uow = uow

    async def list_campaigns(self, query: str, limit: int = 30) -> list[CampaignSummary]:
        """Ищет кампании по части названия или точному ID; новые первыми."""
        q = query.strip().lower()
        result: list[CampaignSummary] = []
        for c in sorted(await self._client.list_campaigns(), key=lambda c: c.id, reverse=True):
            if c.state == "deleted" or not self._is_visible(c):
                continue
            if q and q not in c.name.lower() and q != str(c.id):
                continue
            result.append(CampaignSummary(id=c.id, name=c.name, state=c.state, alias=c.alias))
            if len(result) >= limit:
                break
        return result

    async def get_details(self, campaign_id: int, range_key: RangeKey) -> CampaignDetails:
        """Собирает кампанию с потоками и статистикой за период."""
        campaign = await self._editable(campaign_id)
        timezone = self._settings.stats_timezone
        date_from, date_to = resolve_range(range_key, timezone)
        streams, report, offers, host = await asyncio.gather(
            self._client.list_streams(campaign_id),
            self._client.stream_stats(campaign_id, date_from, date_to, timezone),
            self._catalog.offers(),
            self._catalog.host_for(campaign.domain_id),
        )
        names = {o.id: o.name for o in offers}
        ordered = sorted(streams, key=lambda s: (s.position or 0, s.id))
        return CampaignDetails(
            campaign=CampaignSummary(
                id=campaign.id,
                name=campaign.name,
                state=campaign.state,
                alias=campaign.alias,
                tracking_url=tracking_url(host, campaign.alias),
            ),
            streams=[_stream_view(s, names, report.per_stream.get(s.id, Stats())) for s in ordered],
            totals=StatsView(**asdict(report.total)),
            range=range_key,
            date_from=date_from,
            date_to=date_to,
        )

    async def add_offer(
        self, campaign_id: int, stream_id: int, offer_id: int, range_key: RangeKey
    ) -> CampaignDetails:
        """Добавляет оффер в поток; доли пересчитываются поровну.

        Raises:
            ConflictError: оффер уже в потоке или поток не раздаёт трафик офферам.
            NotFoundError: нет потока или оффера.
            ForbiddenError: кампания не подходит под префикс.
        """
        await self._editable(campaign_id)
        stream = await self._offer_stream(campaign_id, stream_id)
        if any(o.offer_id == offer_id for o in stream.offers):
            raise ConflictError("Этот оффер уже есть в потоке")
        offer = await self._catalog.get_offer(offer_id)

        await self._save_offers(stream, [*stream.offers, StreamOffer(offer_id=offer.id)])
        self._uow.audit.add(
            AuditAction.OFFER_ADDED, campaign_id, {"stream_id": stream_id, "offer_id": offer_id}
        )
        await self._uow.commit()
        return await self.get_details(campaign_id, range_key)

    async def remove_offer(
        self, campaign_id: int, stream_id: int, offer_id: int, range_key: RangeKey
    ) -> CampaignDetails:
        """Удаляет оффер из потока; доли оставшихся пересчитываются поровну.

        Можно удалить и последний оффер: поток останется пустым.

        Raises:
            NotFoundError: нет потока или оффера в нём.
            ConflictError: поток не раздаёт трафик офферам.
            ForbiddenError: кампания не подходит под префикс.
        """
        await self._editable(campaign_id)
        stream = await self._offer_stream(campaign_id, stream_id)
        if not any(o.offer_id == offer_id for o in stream.offers):
            raise NotFoundError("Такого оффера нет в этом потоке")

        await self._save_offers(stream, [o for o in stream.offers if o.offer_id != offer_id])
        self._uow.audit.add(
            AuditAction.OFFER_REMOVED, campaign_id, {"stream_id": stream_id, "offer_id": offer_id}
        )
        await self._uow.commit()
        return await self.get_details(campaign_id, range_key)

    def _is_visible(self, campaign: Campaign) -> bool:
        """Редактор работает с кампанией: префикс подходит или проверка отключена."""
        prefix = self._settings.campaign_prefix
        return not self._settings.edit_only_prefixed or campaign.name.startswith(prefix)

    async def _editable(self, campaign_id: int) -> Campaign:
        """Загружает кампанию и проверяет, что её можно редактировать."""
        campaign = await self._client.get_campaign(campaign_id)
        if not self._is_visible(campaign):
            raise ForbiddenError(
                "Редактор работает только с кампаниями, название которых начинается с "
                f"«{self._settings.campaign_prefix}»"
            )
        return campaign

    async def _offer_stream(self, campaign_id: int, stream_id: int) -> Stream:
        """Находит поток кампании, который раздаёт трафик офферам."""
        for stream in await self._client.list_streams(campaign_id):
            if stream.id == stream_id:
                if not stream.has_offers:
                    raise ConflictError("В этом потоке нет офферов: он только перенаправляет")
                return stream
        raise NotFoundError(f"Поток {stream_id} не найден в кампании {campaign_id}")

    async def _save_offers(self, stream: Stream, offers: list[StreamOffer]) -> None:
        """Сохраняет состав офферов; сумма долей всегда 100%."""
        await self._client.update_stream(
            stream.id, payloads.offers_update_payload(offers, split_evenly(len(offers)))
        )
