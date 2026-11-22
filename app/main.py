"""Точка входа: сборка приложения и управление его ресурсами."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.error_handlers import register_error_handlers
from app.api.routes import router
from app.config import get_settings
from app.db.session import build_engine, build_session_factory
from app.keitaro.client import KeitaroClient, build_http_client
from app.services.catalog import CatalogService

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Создаёт клиент Keitaro, движок БД и сервис справочников; закрывает их при остановке."""
    settings = get_settings()
    if not settings.keitaro_api_key.get_secret_value():
        raise RuntimeError("KEITARO_API_KEY не задан: скопируйте .env.example в .env")

    engine = build_engine(settings.database_url)
    http = build_http_client(settings)
    keitaro = KeitaroClient(http)

    app.state.settings = settings
    app.state.session_factory = build_session_factory(engine)
    app.state.keitaro = keitaro
    app.state.catalog = CatalogService(keitaro, settings)
    try:
        yield
    finally:
        await http.aclose()
        await engine.dispose()


def create_app() -> FastAPI:
    """Собирает приложение; статика монтируется последней, чтобы не перекрывать `/api`."""
    app = FastAPI(title="Adrobot", lifespan=lifespan)
    register_error_handlers(app)
    app.include_router(router, prefix="/api")
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
    return app


app = create_app()
