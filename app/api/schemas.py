"""Схемы запросов и служебных ответов API."""

from pydantic import BaseModel, Field


class CreateCampaignIn(BaseModel):
    """Тело запроса на создание кампании."""

    name: str = Field(min_length=1, max_length=100)
    geo: str = Field(min_length=2, max_length=60)
    offer_id: int = Field(gt=0)


class AddOfferIn(BaseModel):
    """Тело запроса на добавление оффера в поток."""

    offer_id: int = Field(gt=0)


class MetaOut(BaseModel):
    """Настройки, которые интерфейс показывает пользователю."""

    prefix: str
    domain: str
    group: str
    source: str
    redirect_url: str
