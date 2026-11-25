"""Сценарий создания кампании."""

import logging

from app.config import Settings
from app.db.models import AuditAction
from app.db.uow import UnitOfWork
from app.domain.geo import parse_geo
from app.errors import ConflictError, UpstreamError, ValidationFailed
from app.keitaro import payloads
from app.keitaro.models import Campaign, Offer
from app.services.catalog import CampaignDefaults, CatalogService, tracking_url
from app.services.ports import KeitaroPort
from app.services.views import CreatedCampaign, OfferView

log = logging.getLogger(__name__)


class CampaignCreator:
    """Создаёт кампанию с двумя потоками: выбранные страны на редирект, остальные на оффер."""

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

    async def create(self, *, name: str, geo: str, offer_id: int) -> CreatedCampaign:
        """Создаёт кампанию и два потока; при сбое потоков кампания удаляется.

        Гео-поток создаётся первым: ротация идёт по позиции.

        Raises:
            ValidationFailed: некорректные название или гео.
            ConflictError: название уже занято.
            NotFoundError: оффер не найден.
            ConfigurationError: домен, группа или источник из `.env` не найдены в Keitaro.
            UpstreamError: Keitaro вернул ошибку.
        """
        codes = parse_geo(geo)
        full_name = self._full_name(name)
        await self._ensure_name_free(full_name)

        offer = await self._catalog.get_offer(offer_id)
        defaults = await self._catalog.campaign_defaults()

        campaign = await self._create_campaign(full_name, defaults)
        await self._create_streams(campaign.id, codes, offer)
        await self._remember(campaign, codes, offer.id)

        host = await self._catalog.host_for(defaults.domain.id)
        return CreatedCampaign(
            id=campaign.id,
            name=campaign.name,
            state=campaign.state,
            alias=campaign.alias,
            tracking_url=tracking_url(host, campaign.alias),
            geo=codes,
            offer=OfferView(id=offer.id, name=offer.name, state=offer.state),
        )

    def _full_name(self, name: str) -> str:
        """Добавляет префикс из настроек, если его нет в названии."""
        prefix = self._settings.campaign_prefix
        name = name.strip().removeprefix(prefix)
        if not name:
            raise ValidationFailed("Название: добавьте что-нибудь после префикса")
        return prefix + name

    async def _ensure_name_free(self, name: str) -> None:
        """Проверяет название по Keitaro, а не по локальному реестру.

        Keitaro — источник правды: кампанию могли удалить или создать в админке,
        и локальная запись об этом не узнает.

        Raises:
            ConflictError: в Keitaro уже есть кампания с таким названием.
        """
        for campaign in await self._client.list_campaigns():
            if campaign.name == name and campaign.state != "deleted":
                raise ConflictError(f"Кампания «{name}» уже есть в Keitaro (ID {campaign.id})")

    async def _create_campaign(self, name: str, defaults: CampaignDefaults) -> Campaign:
        """Создаёт кампанию; занятое название превращает в понятную ошибку."""
        payload = payloads.campaign_payload(
            name=name,
            group_id=defaults.group_id,
            source_id=defaults.source_id,
            domain_id=defaults.domain.id,
        )
        try:
            return await self._client.create_campaign(payload)
        except UpstreamError as exc:
            if "already been used" in exc.message:
                raise ConflictError(
                    f"Название «{name}» уже занято, возможно кампанией из архива Keitaro. "
                    "Выберите другое"
                ) from exc
            raise

    async def _create_streams(self, campaign_id: int, geo: list[str], offer: Offer) -> None:
        """Создаёт оба потока; при сбое удаляет кампанию и пробрасывает ошибку."""
        try:
            await self._client.create_stream(
                payloads.geo_stream_payload(
                    campaign_id=campaign_id, geo=geo, redirect_url=self._settings.redirect_url
                )
            )
            await self._client.create_stream(
                payloads.offer_stream_payload(campaign_id=campaign_id, offer=offer)
            )
        except Exception:
            log.exception("Не удалось создать потоки, откатываю кампанию %s", campaign_id)
            await self._rollback(campaign_id)
            raise

    async def _rollback(self, campaign_id: int) -> None:
        """Удаляет кампанию без потоков.

        Keitaro переносит её в архив, и название остаётся занятым.
        """
        try:
            await self._client.delete_campaign(campaign_id)
        except Exception:
            log.exception("Не удалось удалить кампанию %s, удалите её вручную", campaign_id)

    async def _remember(self, campaign: Campaign, geo: list[str], offer_id: int) -> None:
        """Сохраняет запись локально; сбой не отменяет кампанию: источник правды — Keitaro."""
        try:
            self._uow.campaigns.add(
                keitaro_id=campaign.id,
                name=campaign.name,
                geo=",".join(geo),
                offer_id=offer_id,
                alias=campaign.alias,
            )
            self._uow.audit.add(
                AuditAction.CAMPAIGN_CREATED, campaign.id, {"geo": geo, "offer_id": offer_id}
            )
            await self._uow.commit()
        except Exception:
            await self._uow.rollback()
            log.exception("Кампания %s создана в Keitaro, но не сохранена локально", campaign.id)
