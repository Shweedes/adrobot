"""Общие фикстуры: фейковый Keitaro, SQLite в памяти и сервисы."""

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import Settings
from app.db import models  # noqa: F401
from app.db.base import Base
from app.db.uow import UnitOfWork
from app.services.campaign_creator import CampaignCreator
from app.services.campaign_editor import CampaignEditor
from app.services.catalog import CatalogService
from tests.fakes import FakeKeitaro


@pytest.fixture
def settings() -> Settings:
    return Settings(
        _env_file=None,
        keitaro_api_key="test",
        campaign_prefix="test_ivanov_",
        keitaro_domain="in.posdk.xyz",
        keitaro_group="FORTESTS",
        keitaro_source="FORTESTS",
    )


@pytest.fixture
def fake() -> FakeKeitaro:
    return FakeKeitaro()


@pytest.fixture
async def uow():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        yield UnitOfWork(session)
    await engine.dispose()


@pytest.fixture
def catalog(fake, settings) -> CatalogService:
    return CatalogService(fake, settings)


@pytest.fixture
def creator(fake, catalog, settings, uow) -> CampaignCreator:
    return CampaignCreator(client=fake, catalog=catalog, settings=settings, uow=uow)


@pytest.fixture
def editor(fake, catalog, settings, uow) -> CampaignEditor:
    return CampaignEditor(client=fake, catalog=catalog, settings=settings, uow=uow)
