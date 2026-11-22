"""HTTP-роуты: разбирают запрос, вызывают сервис, возвращают результат."""

from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import CatalogDep, CreatorDep, EditorDep, SettingsDep
from app.api.schemas import AddOfferIn, CreateCampaignIn, MetaOut
from app.domain.ranges import RangeKey
from app.services.views import CampaignDetails, CampaignSummary, CreatedCampaign, OfferView

router = APIRouter()

SearchText = Annotated[str, Query(max_length=100)]
Period = Annotated[RangeKey, Query(alias="range")]


@router.get("/health")
async def health() -> dict[str, str]:
    """Проверка живости."""
    return {"status": "ok"}


@router.get("/meta", response_model=MetaOut)
async def meta(settings: SettingsDep) -> MetaOut:
    """Настройки, которые интерфейс показывает пользователю."""
    return MetaOut(
        prefix=settings.campaign_prefix,
        domain=settings.keitaro_domain,
        group=settings.keitaro_group,
        source=settings.keitaro_source,
        redirect_url=settings.redirect_url,
    )


@router.get("/offers", response_model=list[OfferView])
async def search_offers(catalog: CatalogDep, q: SearchText = "") -> list[OfferView]:
    """Поиск офферов для автокомплита."""
    return await catalog.search_offers(q)


@router.get("/campaigns", response_model=list[CampaignSummary])
async def list_campaigns(editor: EditorDep, q: SearchText = "") -> list[CampaignSummary]:
    """Список кампаний, доступных редактору."""
    return await editor.list_campaigns(q)


@router.post("/campaigns", response_model=CreatedCampaign, status_code=201)
async def create_campaign(body: CreateCampaignIn, creator: CreatorDep) -> CreatedCampaign:
    """Создаёт кампанию с двумя потоками."""
    return await creator.create(name=body.name, geo=body.geo, offer_id=body.offer_id)


@router.get("/campaigns/{campaign_id}", response_model=CampaignDetails)
async def get_campaign(
    campaign_id: int, editor: EditorDep, period: Period = "today"
) -> CampaignDetails:
    """Кампания с потоками и статистикой за период."""
    return await editor.get_details(campaign_id, period)


@router.post("/campaigns/{campaign_id}/streams/{stream_id}/offers", response_model=CampaignDetails)
async def add_offer(
    campaign_id: int,
    stream_id: int,
    body: AddOfferIn,
    editor: EditorDep,
    period: Period = "today",
) -> CampaignDetails:
    """Добавляет оффер в поток."""
    return await editor.add_offer(campaign_id, stream_id, body.offer_id, period)


@router.delete(
    "/campaigns/{campaign_id}/streams/{stream_id}/offers/{offer_id}",
    response_model=CampaignDetails,
)
async def remove_offer(
    campaign_id: int,
    stream_id: int,
    offer_id: int,
    editor: EditorDep,
    period: Period = "today",
) -> CampaignDetails:
    """Удаляет оффер из потока."""
    return await editor.remove_offer(campaign_id, stream_id, offer_id, period)
