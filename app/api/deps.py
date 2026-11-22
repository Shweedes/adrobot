"""Зависимости FastAPI: ресурсы приложения и сервисы."""

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request

from app.config import Settings
from app.db.uow import UnitOfWork
from app.services.campaign_creator import CampaignCreator
from app.services.campaign_editor import CampaignEditor
from app.services.catalog import CatalogService
from app.services.ports import KeitaroPort


def get_settings_dep(request: Request) -> Settings:
    """Настройки, сохранённые при старте приложения."""
    return request.app.state.settings


async def get_uow(request: Request) -> AsyncIterator[UnitOfWork]:
    """Единица работы на время запроса; сессия закрывается после ответа."""
    async with request.app.state.session_factory() as session:
        yield UnitOfWork(session)


def get_client(request: Request) -> KeitaroPort:
    """Клиент Keitaro, созданный при старте приложения."""
    return request.app.state.keitaro


def get_catalog(request: Request) -> CatalogService:
    """Общий сервис справочников с кэшем."""
    return request.app.state.catalog


SettingsDep = Annotated[Settings, Depends(get_settings_dep)]
UowDep = Annotated[UnitOfWork, Depends(get_uow)]
ClientDep = Annotated[KeitaroPort, Depends(get_client)]
CatalogDep = Annotated[CatalogService, Depends(get_catalog)]


def get_creator(
    client: ClientDep, catalog: CatalogDep, settings: SettingsDep, uow: UowDep
) -> CampaignCreator:
    """Сервис создания кампаний."""
    return CampaignCreator(client=client, catalog=catalog, settings=settings, uow=uow)


def get_editor(
    client: ClientDep, catalog: CatalogDep, settings: SettingsDep, uow: UowDep
) -> CampaignEditor:
    """Сервис редактора кампаний."""
    return CampaignEditor(client=client, catalog=catalog, settings=settings, uow=uow)


CreatorDep = Annotated[CampaignCreator, Depends(get_creator)]
EditorDep = Annotated[CampaignEditor, Depends(get_editor)]
